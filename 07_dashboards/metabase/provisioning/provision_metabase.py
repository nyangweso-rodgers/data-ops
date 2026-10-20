#!/usr/bin/env python3
"""Idempotently provision Metabase database connections from a declarative manifest.

Reads connection definitions from databases.json (which references secrets by
${ENV_VAR} name only), resolves them against the repo-root .env, authenticates to
the Metabase API with the admin credentials, then creates or updates each database
connection *by name*. Safe to run repeatedly — re-running updates existing
connections in place rather than duplicating them.

Usage:
    python provision_metabase.py [--manifest databases.json] [--dry-run]

Environment (resolved from the repo-root .env, overridable by the process env):
    METABASE_URL        Base URL of the Metabase instance (default http://localhost:3000)
    MB_ADMIN_EMAIL      Admin login email
    MB_ADMIN_PASSWORD   Admin password
    plus any ${VAR} referenced by the manifest's connection details.

Exit code is non-zero if any connection fails to provision (e.g. its backing
service is down), so it is safe to use as a CI/deploy gate.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

# repo root = four levels up from 07_dashboards/04_metabase/provisioning/<this file>
REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = REPO_ROOT / ".env"
VAR_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def load_env(path: Path) -> dict:
    """Minimal .env parser: KEY=VALUE, strips quotes, expands ${VAR} references."""
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip()
        if len(val) >= 2 and val[0] in "\"'" and val[-1] == val[0]:
            val = val[1:-1]
        val = VAR_RE.sub(lambda m: env.get(m.group(1), os.environ.get(m.group(1), "")), val)
        env[key] = val
    return env


def expand(value, env: dict):
    if isinstance(value, str):
        return VAR_RE.sub(lambda m: env.get(m.group(1), os.environ.get(m.group(1), "")), value)
    return value


def api(method: str, url: str, token: str | None = None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("X-Metabase-Session", token)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"message": raw}
    except urllib.error.URLError as e:
        return 0, {"message": str(e)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Provision Metabase DB connections from a manifest.")
    ap.add_argument("--manifest", default=str(Path(__file__).with_name("databases.json")))
    ap.add_argument("--dry-run", action="store_true", help="Print what would change without calling the API.")
    args = ap.parse_args()

    # .env first, process env overrides (so CI/secret managers win)
    env = {**load_env(ENV_PATH), **os.environ}
    base = env.get("METABASE_URL", "http://localhost:3000").rstrip("/")
    email = env.get("MB_ADMIN_EMAIL")
    password = env.get("MB_ADMIN_PASSWORD")
    if not email or not password:
        print("ERROR: MB_ADMIN_EMAIL / MB_ADMIN_PASSWORD not found in .env or environment.", file=sys.stderr)
        return 2

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    desired = manifest.get("databases", [])
    if not desired:
        print("No databases defined in manifest; nothing to do.")
        return 0

    status, body = api("POST", f"{base}/api/session", body={"username": email, "password": password})
    if status != 200:
        print(f"ERROR: authentication failed ({status}): {body}", file=sys.stderr)
        return 2
    token = body["id"]

    status, body = api("GET", f"{base}/api/database", token=token)
    rows = body.get("data", body) if isinstance(body, dict) else body
    existing = {db["name"]: db for db in rows}

    rc = 0
    for spec in desired:
        name = spec["name"]
        # Pass through every manifest key (engine, schedules, auto_run_queries,
        # is_full_sync, ...) except local annotations; expand ${VAR} in details.
        payload = {k: v for k, v in spec.items() if not k.startswith(("_", "$"))}
        payload["details"] = {k: expand(v, env) for k, v in spec.get("details", {}).items()}
        payload.setdefault("is_full_sync", True)
        payload.setdefault("is_on_demand", False)
        if args.dry_run:
            redacted = {k: ("***" if "pass" in k.lower() else v) for k, v in payload["details"].items()}
            verb = "update" if name in existing else "create"
            print(f"[dry-run] would {verb}: {name} (engine={spec['engine']}) details={redacted}")
            continue

        if name in existing:
            db_id = existing[name]["id"]
            status, resp = api("PUT", f"{base}/api/database/{db_id}", token=token, body=payload)
            action, ok = "updated", status == 200
        else:
            status, resp = api("POST", f"{base}/api/database", token=token, body=payload)
            action, ok = "created", status in (200, 201)

        if ok:
            print(f"✓ {action}: {name} (engine={spec['engine']})")
        else:
            rc = 1
            msg = resp.get("message") or resp.get("errors") or resp
            print(f"✗ FAILED to {action[:-1] if action.endswith('d') else action}: {name} ({status}): {msg}")

    # Layer B: apply the global (root) query-cache policy, if defined.
    cache = manifest.get("global_cache")
    if cache and cache.get("strategy"):
        if args.dry_run:
            print(f"[dry-run] would set root cache policy: {cache['strategy']}")
        else:
            status, resp = api("PUT", f"{base}/api/cache", token=token,
                               body={"model": "root", "model_id": 0, "strategy": cache["strategy"]})
            if status == 200:
                print(f"✓ root cache policy: {cache['strategy']}")
            else:
                rc = 1
                print(f"✗ FAILED to set root cache policy ({status}): {resp.get('message') or resp}")

    return rc


if __name__ == "__main__":
    sys.exit(main())
