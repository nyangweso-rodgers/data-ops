"""Apply Kafka Connect connector configs from ../connectors/<cluster>/configs/.

Layout:  <cluster>/configs/<direction>/<system>/<database>/<table>-<format>.json
         direction: source | sink | cdc     format: json | avro | protobuf
Each file is {"name": ..., "config": {...}} and "name" must equal the name derived
from its path:  <system>-<database>-<table>-<direction>-<format>
  e.g. cp-kafka-connect/configs/source/postgres/users/customers-json.json
       -> postgres-users-customers-source-json

Configs are sent with PUT /connectors/<name>/config, which creates or updates the
connector - so re-running is safe and this folder stays the source of truth.

Usage (normally via `make kafka-connectors-apply [CLUSTER=] [DIRECTION=] [SYSTEM=] [DATABASE=] [FORMAT=]`):
    python apply_connectors.py --cluster cp-kafka-connect=http://localhost:8083 \
                               --cluster debezium-connect=http://localhost:8084 \
                               [--only CLUSTER] [--direction D] [--system S] [--database DB] \
                               [--format F] [--dry-run]
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

CONNECTORS = Path(__file__).resolve().parent.parent / "connectors"
DIRECTIONS = {"source", "sink", "cdc"}
FORMATS = {"json", "avro", "protobuf"}


def request(method: str, url: str, body: dict | None = None) -> tuple[int, dict | str]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw


def parse_path(configs: Path, path: Path) -> dict:
    """Split configs/<direction>/<system>/<database>/<table>-<format>.json into its parts."""
    parts = path.relative_to(configs).parts
    if len(parts) != 4:
        raise ValueError("expected <direction>/<system>/<database>/<table>-<format>.json")
    direction, system, database, filename = parts
    table, _, fmt = path.stem.rpartition("-")
    if direction not in DIRECTIONS:
        raise ValueError(f"direction folder {direction!r} must be one of {sorted(DIRECTIONS)}")
    if not table or fmt not in FORMATS:
        raise ValueError(f"file name must end in -<format>.json with format one of {sorted(FORMATS)}")
    return {"direction": direction, "system": system, "database": database, "table": table, "format": fmt,
            "name": f"{system}-{database}-{table}-{direction}-{fmt}"}


def load(path: Path, expected_name: str) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("name") != expected_name:
        raise ValueError(f'"name" is {doc.get("name")!r} but the path says it must be {expected_name!r}')
    if not isinstance(doc.get("config"), dict):
        raise ValueError('missing "config" object')
    return doc


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cluster", action="append", required=True, metavar="NAME=URL",
                   help="Connect cluster folder name and its REST URL (repeatable)")
    p.add_argument("--only", help="apply only this cluster")
    p.add_argument("--direction", choices=sorted(DIRECTIONS))
    p.add_argument("--system", help="e.g. postgres, bigquery, clickhouse")
    p.add_argument("--database", help="database / dataset folder")
    p.add_argument("--format", choices=sorted(FORMATS))
    p.add_argument("--dry-run", action="store_true", help="validate files, don't call the API")
    args = p.parse_args()

    clusters = dict(c.split("=", 1) for c in args.cluster)
    if args.only:
        if args.only not in clusters:
            p.error(f"--only {args.only!r} is not one of {sorted(clusters)}")
        clusters = {args.only: clusters[args.only]}
    filters = {k: getattr(args, k) for k in ("direction", "system", "database", "format") if getattr(args, k)}

    failures = 0
    for cluster, url in clusters.items():
        configs = CONNECTORS / cluster / "configs"
        selected = []
        for path in sorted(configs.rglob("*.json")):
            label = path.relative_to(configs).as_posix()
            try:
                meta = parse_path(configs, path)
            except ValueError as e:
                print(f"  FAIL  {label}: {e}")
                failures += 1
                continue
            if all(meta[k] == v for k, v in filters.items()):
                selected.append((path, label, meta))

        print(f"== {cluster} ({url}) - {len(selected)} connector(s)")
        applied = []
        for path, label, meta in selected:
            try:
                doc = load(path, meta["name"])
            except (ValueError, json.JSONDecodeError) as e:
                print(f"  FAIL  {label}: {e}")
                failures += 1
                continue
            if args.dry_run:
                print(f"  ok    {label} -> {meta['name']} (dry run)")
                continue
            status, resp = request("PUT", f"{url}/connectors/{doc['name']}/config", doc["config"])
            if status in (200, 201):
                print(f"  {'created' if status == 201 else 'updated'}  {doc['name']}")
                applied.append(doc["name"])
            else:
                msg = resp.get("message", resp) if isinstance(resp, dict) else resp
                print(f"  FAIL  {doc['name']}: HTTP {status} - {msg}")
                failures += 1

        if applied:
            time.sleep(3)  # let tasks start before reporting state
            for name in applied:
                status, resp = request("GET", f"{url}/connectors/{name}/status")
                if status == 200:
                    tasks = ", ".join(t["state"] for t in resp.get("tasks", [])) or "no tasks yet"
                    print(f"  state {name}: {resp['connector']['state']} (tasks: {tasks})")

    if failures:
        print(f"\n{failures} connector(s) failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
