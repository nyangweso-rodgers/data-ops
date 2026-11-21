# dagster_pipeline/utils/ingest_config_loader.py
"""
Loads ClickHouse ingestion pipeline configs from YAML.

Layout (one file per source database):
    config/_shared/frequency_schedules.yml              - shared frequency tiers
    config/clickhouse/ingest/<from_source>/<db>.yml     - pipeline config

Each pipeline file:
    resource_key, source_database, destination_database, group_name   - REQUIRED
    defaults: {...}                                                     - merged into every table
    tables: [{name, schema_path, destination_table, ...}, ...]

schema_path is explicit per table (relative to schemas/) - never derived from
a naming pattern, and not allowed in defaults.

load_table_specs() returns one dict per table, ready to pass to the
<Source>ToClickHouseBuilder (see each from_<source>/builder.py).
build_jobs_and_schedules() creates one job per (group_name × frequency_tier)
and a schedule for each tier that has a cron.
"""

import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml
from dagster import AssetSelection, ScheduleDefinition, define_asset_job

from dagster_pipeline.utils.logging_config import get_logger

logger = get_logger(__name__)

CONFIG_ROOT = Path(__file__).resolve().parents[1] / "config"
SCHEMAS_ROOT = Path(__file__).resolve().parents[1] / "schemas"
FREQUENCY_SCHEDULES_FILE = CONFIG_ROOT / "_shared" / "frequency_schedules.yml"
INGEST_CONFIG_ROOT = CONFIG_ROOT / "clickhouse" / "ingest"

PIPELINE_REQUIRED_KEYS = {"resource_key", "source_database", "destination_database", "group_name", "tables"}
PIPELINE_ALLOWED_KEYS = PIPELINE_REQUIRED_KEYS | {"defaults"}

TABLE_REQUIRED_KEYS = {
    "name",
    "schema_path",  # Relative to schemas/, e.g. mysql/amtdb/accounts.yml - never derived
    "destination_table",
    "frequency_tier",
    "clickhouse_engine",
    "clickhouse_order_by",
    "clickhouse_partition_by",  # Must be explicit - use null for no partitioning
}
TABLE_ALLOWED_KEYS = TABLE_REQUIRED_KEYS | {
    "asset_name",
    "incremental_key",
    "sync_method",
    "batch_size",
    "tags",
    "clickhouse_primary_key",
    "clickhouse_ttl",
    "clickhouse_settings",
}


class IngestConfigError(ValueError):
    """Raised when a pipeline config is invalid - fails Dagster code location load"""


def load_frequency_tiers() -> Tuple[str, Dict[str, Dict[str, Any]]]:
    """Return (timezone, {tier_name: {cron, timeout_seconds, description}})"""
    data = _read_yaml(FREQUENCY_SCHEDULES_FILE)
    timezone = data.get("timezone")
    tiers = data.get("tiers") or {}

    if not timezone:
        raise IngestConfigError(f"{FREQUENCY_SCHEDULES_FILE}: 'timezone' is required")
    if not tiers:
        raise IngestConfigError(f"{FREQUENCY_SCHEDULES_FILE}: 'tiers' is empty")

    return timezone, tiers


def load_table_specs(source_dir: str, source_type: str) -> List[Dict[str, Any]]:
    """
    Load every pipeline config in config/clickhouse/ingest/<source_dir>/ and
    return one merged, validated table spec per table.

    Args:
        source_dir: Folder under config/clickhouse/ingest, e.g. "from_mysql"
        source_type: Used for derived asset names, e.g. "mysql"
    """
    _, tiers = load_frequency_tiers()
    config_dir = INGEST_CONFIG_ROOT / source_dir
    specs: List[Dict[str, Any]] = []

    for path in sorted(config_dir.glob("*.yml")):
        specs.extend(_load_pipeline_file(path, source_type, tiers))

    _check_unique_asset_names(specs)
    logger.info("ingest_configs_loaded", source_dir=source_dir, tables=len(specs))
    return specs


def build_jobs_and_schedules(specs: List[Dict[str, Any]]) -> Tuple[list, list]:
    """One job per (group_name × frequency_tier); one schedule per job whose tier has a cron"""
    timezone, tiers = load_frequency_tiers()

    asset_names_by_job: Dict[Tuple[str, str], List[str]] = defaultdict(list)
    for spec in specs:
        asset_names_by_job[(spec["group_name"], spec["tags"]["frequency_tier"])].append(spec["asset_name"])

    jobs, schedules = [], []
    for (group_name, tier_name), asset_names in sorted(asset_names_by_job.items()):
        tier = tiers[tier_name]
        job_tags = {"frequency_tier": tier_name}
        if tier.get("timeout_seconds"):
            job_tags["dagster/max_runtime"] = str(tier["timeout_seconds"])

        job = define_asset_job(
            name=f"{group_name}_{tier_name}_job",
            selection=AssetSelection.assets(*asset_names),
            description=f"{group_name} - {tier.get('description', tier_name)}",
            tags=job_tags,
        )
        jobs.append(job)

        if tier.get("cron"):
            schedules.append(
                ScheduleDefinition(
                    name=f"{group_name}_{tier_name}_schedule",
                    job=job,
                    cron_schedule=tier["cron"],
                    execution_timezone=timezone,
                    description=tier.get("description"),
                )
            )

    return jobs, schedules


# ============================================================================
# INTERNALS
# ============================================================================

def _read_yaml(path: Path) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except (OSError, yaml.YAMLError) as e:
        raise IngestConfigError(f"{path}: could not read YAML - {e}") from e

    if not isinstance(data, dict):
        raise IngestConfigError(f"{path}: top level must be a mapping")
    return data


def _load_pipeline_file(path: Path, source_type: str, tiers: Dict[str, Any]) -> List[Dict[str, Any]]:
    pipeline = _read_yaml(path)
    if not pipeline:
        logger.debug("ingest_config_empty_skipped", path=str(path))  # Scaffolding placeholder
        return []

    _check_keys(pipeline, PIPELINE_REQUIRED_KEYS, PIPELINE_ALLOWED_KEYS, where=str(path))

    defaults = pipeline.get("defaults") or {}
    per_table_only = {"name", "asset_name", "schema_path", "destination_table"}
    _check_keys(defaults, set(), TABLE_ALLOWED_KEYS - per_table_only, where=f"{path} defaults")

    specs = []
    for table in pipeline["tables"]:
        merged = {**defaults, **table}
        where = f"{path} table '{merged.get('name', '?')}'"
        _check_keys(merged, TABLE_REQUIRED_KEYS, TABLE_ALLOWED_KEYS, where=where)

        tier = merged.pop("frequency_tier")
        if tier not in tiers:
            raise IngestConfigError(f"{where}: unknown frequency_tier '{tier}'. Available: {sorted(tiers)}")

        if not isinstance(merged["clickhouse_order_by"], list) or not merged["clickhouse_order_by"]:
            raise IngestConfigError(f"{where}: clickhouse_order_by must be a non-empty list")

        _check_schema_path(merged["schema_path"], where)
        _warn_on_version_column_mismatch(merged, where)

        source_table = merged.pop("name")
        specs.append({
            **merged,
            "asset_name": merged.get("asset_name") or _derive_asset_name(source_type, pipeline["source_database"], source_table),
            "group_name": pipeline["group_name"],
            "resource_key": pipeline["resource_key"],
            "source_database": pipeline["source_database"],
            "source_table": source_table,
            "destination_database": pipeline["destination_database"],
            "tags": {**(merged.get("tags") or {}), "frequency_tier": tier},
        })

    return specs


def _check_keys(data: Dict[str, Any], required: set, allowed: set, where: str):
    missing = required - data.keys()
    unknown = data.keys() - allowed
    if missing:
        raise IngestConfigError(f"{where}: missing required keys {sorted(missing)}")
    if unknown:
        raise IngestConfigError(f"{where}: unknown keys {sorted(unknown)}. Allowed: {sorted(allowed)}")


def _derive_asset_name(source_type: str, source_database: str, source_table: str) -> str:
    raw = f"{source_type}_{source_database}_{source_table}_to_clickhouse"
    return re.sub(r"[^A-Za-z0-9_]", "_", raw)


def _check_schema_path(schema_path: Any, where: str):
    """
    schema_path must be a .yml path inside schemas/. A missing file only warns -
    the asset fails at run time - so one table without a schema yet doesn't
    take down the whole code location.
    """
    if not isinstance(schema_path, str) or not schema_path.endswith(".yml"):
        raise IngestConfigError(f"{where}: schema_path must be a .yml path relative to schemas/, got {schema_path!r}")

    resolved = (SCHEMAS_ROOT / schema_path).resolve()
    if SCHEMAS_ROOT.resolve() not in resolved.parents:
        raise IngestConfigError(f"{where}: schema_path '{schema_path}' must stay inside schemas/")

    if not resolved.exists():
        logger.warning("schema_file_missing", where=where, schema_path=f"schemas/{schema_path}")


def _warn_on_version_column_mismatch(spec: Dict[str, Any], where: str):
    """
    ReplacingMergeTree(ver) only helps if updated rows are re-fetched, i.e.
    the incremental cursor tracks the same column as the version column.
    """
    match = re.search(r"ReplacingMergeTree\(\s*(\w+)\s*\)", spec["clickhouse_engine"])
    incremental_key = spec.get("incremental_key")
    if match and incremental_key and match.group(1) != incremental_key:
        logger.warning(
            "incremental_key_version_column_mismatch",
            where=where,
            incremental_key=incremental_key,
            version_column=match.group(1),
            hint="Updated rows will never be re-synced; use the version column as incremental_key",
        )


def _check_unique_asset_names(specs: List[Dict[str, Any]]):
    seen = set()
    for spec in specs:
        if spec["asset_name"] in seen:
            raise IngestConfigError(f"Duplicate asset_name '{spec['asset_name']}'")
        seen.add(spec["asset_name"])
