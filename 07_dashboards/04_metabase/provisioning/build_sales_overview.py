#!/usr/bin/env python3
"""Build (idempotently) a 'Sales Overview' dashboard of SUM(productQty) scorecards
on test_marts_mv_accounts, filtered to sale_date IS NOT NULL within each period.

Re-runnable: cards are matched by name and updated in place; the dashboard named
'Sales Overview' is reused. Field ids are resolved by NAME at runtime, so this
survives a ClickHouse re-sync.
"""
import json, os, urllib.request, urllib.error

BASE = os.environ.get("METABASE_URL", "http://localhost:3000").rstrip("/")
EMAIL, PASSWORD = "admin@mycompany.com", "MyStrongPassword123!"
DB_ID, TABLE_ID = 3, 102
DASH_NAME = "Sales Overview"

# Shared dashboard filters (apply to BOTH tabs). (param id, name, slug, field name)
FILTERS = [
    ("country_region", "Country",       "country",       "companyRegion"),
    ("product",        "Product",       "product",       "product"),
    ("customer_type",  "Customer Type", "customer_type", "customerType"),
    ("account_type",   "Account Type",  "account_type",  "accountType"),
]

def filter_defs():
    return [{"id": pid, "name": nm, "slug": sl, "type": "string/="} for pid, nm, sl, _ in FILTERS]

def filter_mappings(cid, fmap):
    """parameter_mappings linking every filter to its field on a given card."""
    return [{"parameter_id": pid, "card_id": cid,
             "target": ["dimension", ["field", fmap[fld], None]]} for pid, _, _, fld in FILTERS]

def api(method, path, token=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token: req.add_header("X-Metabase-Session", token)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read().decode(); return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try: return e.code, json.loads(raw)
        except json.JSONDecodeError: return e.code, {"message": raw}

def main():
    _, s = api("POST", "/api/session", body={"username": EMAIL, "password": PASSWORD})
    token = s["id"]

    # resolve field ids by name (portable)
    _, meta = api("GET", f"/api/table/{TABLE_ID}/query_metadata", token)
    fid = {f["name"]: f["id"] for f in meta["fields"]}
    qty, sdate = fid["productQty"], fid["sale_date"]  # filter fields resolved via fid

    def card_query(n, unit):
        return {"database": DB_ID, "type": "query", "query": {
            "source-table": TABLE_ID,
            "aggregation": [["sum", ["field", qty, None]]],
            "filter": ["and",
                       ["not-null", ["field", sdate, None]],
                       ["time-interval", ["field", sdate, None], n, unit]]}}

    # (display name, interval-n, interval-unit)
    # Order = reading flow: current periods (top row) then prior periods (bottom).
    specs = [
        ("Sales Today",      "current", "day"),
        ("Sales This Week",  "current", "week"),
        ("Sales This Month", "current", "month"),
        ("Sales YTD",        "current", "year"),
        ("Sales Yesterday",  "last",    "day"),
        ("Sales Last Week",  "last",    "week"),
        ("Sales Last Month", "last",    "month"),
        ("Sales Last Year",  "last",    "year"),
    ]

    # existing cards by name -> id (for idempotency)
    _, allcards = api("GET", "/api/card", token)
    existing = {c["name"]: c["id"] for c in allcards}

    card_ids = {}
    for name, n, unit in specs:
        body = {"name": name, "dataset_query": card_query(n, unit),
                "display": "scalar", "visualization_settings": {}}
        if name in existing:
            st, r = api("PUT", f"/api/card/{existing[name]}", token, body)
            action = "updated"
        else:
            st, r = api("POST", "/api/card", token, body)
            action = "created"
        if st not in (200, 201):
            print(f"✗ {name} failed ({st}): {r.get('message') or r}"); raise SystemExit(1)
        card_ids[name] = r["id"]
        print(f"✓ {action}: {name} (id={r['id']})")

    # find or create the dashboard
    _, dashlist = api("GET", "/api/dashboard", token)
    did = next((d["id"] for d in dashlist if d["name"] == DASH_NAME), None)
    if did is None:
        _, d = api("POST", "/api/dashboard", token, {"name": DASH_NAME})
        did = d["id"]; print(f"✓ dashboard created: {DASH_NAME} (id={did})")
    else:
        print(f"• reusing dashboard: {DASH_NAME} (id={did})")

    # layout on 24-col grid. Row 0 = big heading title. Then even 4x4:
    # row 1 = current periods (day->year), row 4 = each period's prior beneath it.
    pos = {
        "Sales Today":      (1, 0,  6, 3), "Sales This Week":  (1, 6,  6, 3),
        "Sales This Month": (1, 12, 6, 3), "Sales YTD":        (1, 18, 6, 3),
        "Sales Yesterday":  (4, 0,  6, 3), "Sales Last Week":  (4, 6,  6, 3),
        "Sales Last Month": (4, 12, 6, 3), "Sales Last Year":  (4, 18, 6, 3),
    }

    # heading (virtual text card, display=heading -> large title font)
    heading = {"id": -100, "card_id": None, "row": 0, "col": 0, "size_x": 24, "size_y": 1,
               "series": [], "parameter_mappings": [],
               "visualization_settings": {
                   "virtual_card": {"name": None, "display": "heading", "dataset_query": {},
                                    "visualization_settings": {}, "archived": False},
                   "text": "Sales Overview"}}

    dashcards = [heading]
    for i, (name, _, _) in enumerate(specs):
        row, col, sx, sy = pos[name]
        cid = card_ids[name]
        dashcards.append({"id": -(i + 1), "card_id": cid, "row": row, "col": col,
                          "size_x": sx, "size_y": sy, "series": [],
                          "parameter_mappings": filter_mappings(cid, fid),
                          "visualization_settings": {}})

    st, r = api("PUT", f"/api/dashboard/{did}", token,
                {"dashcards": dashcards, "parameters": filter_defs()})
    if st != 200:
        print(f"✗ placing cards failed ({st}): {r.get('message') or r}"); raise SystemExit(1)
    print(f"✓ heading + {len(dashcards)-1} scorecards placed; {len(FILTERS)} filters wired to all")

    # Make each filter a proper dropdown: enable + scan values for its field
    # (low cost; field-value scanning is otherwise disabled for the DB).
    for _, _, _, fld in FILTERS:
        api("PUT", f"/api/field/{fid[fld]}", token, {"has_field_values": "list"})
        api("POST", f"/api/field/{fid[fld]}/rescan_values", token)
    print(f"✓ values scanned for {len(FILTERS)} filter dropdowns")

    print(f"\nOpen: {BASE}/dashboard/{did}")

if __name__ == "__main__":
    main()
