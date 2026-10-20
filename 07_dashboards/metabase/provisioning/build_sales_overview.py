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

    empid, dept = fid["employee_id"], fid["Department_name"]

    # 8 periods shared by every section: current 4 (top row), prior 4 (bottom row)
    PERIODS = [
        ("Today", "current", "day"), ("This Week", "current", "week"),
        ("This Month", "current", "month"), ("YTD", "current", "year"),
        ("Yesterday", "last", "day"), ("Last Week", "last", "week"),
        ("Last Month", "last", "month"), ("Last Year", "last", "year"),
    ]

    def filt(n, unit, field_sales):
        conds = [["not-null", ["field", sdate, None]]]
        if field_sales:
            conds.append(["=", ["field", dept, None], "Field Sales"])
        conds.append(["time-interval", ["field", sdate, None], n, unit])
        return ["and", *conds]

    def query_for(metric, n, unit):
        if metric == "sales":            # SUM(productQty)
            agg, fs = ["sum", ["field", qty, None]], False
        elif metric == "agents":         # COUNT(DISTINCT employee_id), Field Sales only
            agg, fs = ["distinct", ["field", empid, None]], True
        else:                            # productivity: avg qty per selling agent
            agg = ["/", ["sum", ["field", qty, None]], ["distinct", ["field", empid, None]]]; fs = True
        return {"database": DB_ID, "type": "query", "query": {
            "source-table": TABLE_ID, "aggregation": [agg], "filter": filt(n, unit, fs)}}

    # (heading text, card-name prefix, metric)
    SECTIONS = [
        ("Sales Overview",     "Sales ",              "sales"),
        ("Selling Agents",     "# Selling Agents ",   "agents"),
        ("Agent Productivity", "Agent Productivity ", "productivity"),
    ]

    # create/update every scorecard (idempotent by name)
    _, allcards = api("GET", "/api/card", token)
    existing = {c["name"]: c["id"] for c in allcards}
    card_ids = {}
    for _, prefix, metric in SECTIONS:
        for label, n, unit in PERIODS:
            name = prefix + label
            body = {"name": name, "dataset_query": query_for(metric, n, unit),
                    "display": "scalar", "visualization_settings": {}}
            if name in existing:
                st, r = api("PUT", f"/api/card/{existing[name]}", token, body)
            else:
                st, r = api("POST", "/api/card", token, body)
            if st not in (200, 201):
                print(f"✗ {name} ({st}): {r.get('message') or r}"); raise SystemExit(1)
            card_ids[name] = r["id"]
    print(f"✓ {len(card_ids)} scorecards across {len(SECTIONS)} sections created/updated")

    # find or create the dashboard
    _, dashlist = api("GET", "/api/dashboard", token)
    did = next((d["id"] for d in dashlist if d["name"] == DASH_NAME), None)
    if did is None:
        _, d = api("POST", "/api/dashboard", token, {"name": DASH_NAME})
        did = d["id"]; print(f"✓ dashboard created: {DASH_NAME} (id={did})")
    else:
        print(f"• reusing dashboard: {DASH_NAME} (id={did})")

    # layout: each section = heading (24x1) + current row + prior row (each 4x 6w 3h)
    dashcards = []
    neg, base_row = -1, 0
    for htext, prefix, _ in SECTIONS:
        dashcards.append({"id": neg, "card_id": None, "row": base_row, "col": 0,
                          "size_x": 24, "size_y": 1, "series": [], "parameter_mappings": [],
                          "visualization_settings": {
                              "virtual_card": {"name": None, "display": "heading", "dataset_query": {},
                                               "visualization_settings": {}, "archived": False},
                              "text": htext}})
        neg -= 1
        for ri, periods in enumerate((PERIODS[:4], PERIODS[4:])):
            for ci, (label, _, _) in enumerate(periods):
                cid = card_ids[prefix + label]
                dashcards.append({"id": neg, "card_id": cid, "row": base_row + 1 + ri * 3,
                                  "col": ci * 6, "size_x": 6, "size_y": 3, "series": [],
                                  "parameter_mappings": filter_mappings(cid, fid),
                                  "visualization_settings": {}})
                neg -= 1
        base_row += 7  # heading(1) + 2 rows of 3

    st, r = api("PUT", f"/api/dashboard/{did}", token,
                {"dashcards": dashcards, "parameters": filter_defs(), "width": "full"})
    if st != 200:
        print(f"✗ placing cards failed ({st}): {r.get('message') or r}"); raise SystemExit(1)
    print(f"✓ {len(SECTIONS)} sections placed ({len(dashcards)} dashcards); {len(FILTERS)} filters wired")

    # Make each filter a proper dropdown: enable + scan values for its field
    # (low cost; field-value scanning is otherwise disabled for the DB).
    for _, _, _, fld in FILTERS:
        api("PUT", f"/api/field/{fid[fld]}", token, {"has_field_values": "list"})
        api("POST", f"/api/field/{fid[fld]}/rescan_values", token)
    print(f"✓ values scanned for {len(FILTERS)} filter dropdowns")

    print(f"\nOpen: {BASE}/dashboard/{did}")

if __name__ == "__main__":
    main()