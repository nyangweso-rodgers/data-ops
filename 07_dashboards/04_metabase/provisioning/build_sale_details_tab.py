#!/usr/bin/env python3
"""Add a second tab 'Sale Details' to the Sales Overview dashboard (id 3) with:
  - Sales by Product        (horizontal bar / row, top 15)
  - Sales by Lead Source    (horizontal bar / row, top 15)
  - Sales by Account Type   (pie)
  - Unique Accounts by Status (bar, count-distinct account_id)

Idempotent: cards matched by name; page-1 content is preserved and re-homed to
the first tab; the shared Country filter is mapped to the new charts too.
Field ids resolved by name at runtime.
"""
import json, os, urllib.request, urllib.error

BASE = os.environ.get("METABASE_URL", "http://localhost:3000").rstrip("/")
EMAIL, PASSWORD = "admin@mycompany.com", "MyStrongPassword123!"
DB_ID, TABLE_ID, DASH_ID = 3, 102, 3
TAB1_NAME, TAB2_NAME = "Sales Overview", "Sale Details"

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
    _, meta = api("GET", f"/api/table/{TABLE_ID}/query_metadata", token)
    f = {x["name"]: x["id"] for x in meta["fields"]}
    qty, product, leadsrc = f["productQty"], f["product"], f["LeadSource"]
    acctype, acctid, status, creg = f["accountType"], f["account_id"], f["status"], f["companyRegion"]
    gender, custid, empname, dept = f["gender"], f["customerId"], f["employee_name"], f["Department_name"]

    def q(query):
        return {"database": DB_ID, "type": "query", "query": query}

    # value labels for bar/row charts; % + total for the pie
    BARVIZ = {"graph.show_values": True, "graph.label_value_formatting": "auto"}
    PIEVIZ = {"pie.percent_visibility": "both", "pie.show_total": True}

    # (name, display, query, visualization_settings)  -- horizontal bar = "row"
    detail_specs = [
        ("Sales by Product", "row", {"source-table": TABLE_ID,
            "aggregation": [["sum", ["field", qty, None]]],
            "breakout": [["field", product, None]],
            "order-by": [["desc", ["aggregation", 0]]], "limit": 15}, BARVIZ),
        ("Sales by Lead Source", "row", {"source-table": TABLE_ID,
            "aggregation": [["sum", ["field", qty, None]]],
            "breakout": [["field", leadsrc, None]],
            "order-by": [["desc", ["aggregation", 0]]], "limit": 15}, BARVIZ),
        ("Sales by Account Type", "pie", {"source-table": TABLE_ID,
            "aggregation": [["sum", ["field", qty, None]]],
            "breakout": [["field", acctype, None]]}, PIEVIZ),
        ("Unique Accounts by Status", "bar", {"source-table": TABLE_ID,
            "aggregation": [["distinct", ["field", acctid, None]]],
            "breakout": [["field", status, None]],
            "order-by": [["desc", ["aggregation", 0]]]}, BARVIZ),
        ("Sales by Country", "pie", {"source-table": TABLE_ID,
            "aggregation": [["sum", ["field", qty, None]]],
            "breakout": [["field", creg, None]]}, PIEVIZ),
        ("Unique Customers by Gender", "pie", {"source-table": TABLE_ID,
            "aggregation": [["distinct", ["field", custid, None]]],
            "breakout": [["field", gender, None]]}, PIEVIZ),
        ("Top 10 Sales Agents (Field Sales)", "bar", {"source-table": TABLE_ID,
            "aggregation": [["sum", ["field", qty, None]]],
            "breakout": [["field", empname, None]],
            "filter": ["=", ["field", dept, None], "Field Sales"],
            "order-by": [["desc", ["aggregation", 0]]], "limit": 10}, BARVIZ),
    ]

    _, allcards = api("GET", "/api/card", token)
    existing = {c["name"]: c["id"] for c in allcards}
    detail_ids = {}
    for name, display, query, viz in detail_specs:
        body = {"name": name, "dataset_query": q(query), "display": display,
                "visualization_settings": viz}
        if name in existing:
            st, r = api("PUT", f"/api/card/{existing[name]}", token, body); act = "updated"
        else:
            st, r = api("POST", "/api/card", token, body); act = "created"
        if st not in (200, 201):
            print(f"✗ {name} ({st}): {r.get('message') or r}"); raise SystemExit(1)
        detail_ids[name] = r["id"]; print(f"✓ {act}: {name} (id={r['id']})")

    # current dashboard state
    _, dash = api("GET", f"/api/dashboard/{DASH_ID}", token)
    tabs = dash.get("tabs") or []
    tab1_id = tabs[0]["id"] if tabs else -1
    tab1_name = tabs[0]["name"] if tabs else TAB1_NAME
    tab2_id = next((t["id"] for t in tabs if t["name"] == TAB2_NAME), -2)

    detail_card_id_set = set(detail_ids.values())
    # keep all existing dashcards that are NOT our detail charts -> tab 1.
    # Re-apply all filters to real cards (skip the heading) so both tabs stay in
    # sync regardless of which builder ran last.
    keep = []
    for dc in dash.get("dashcards", []):
        if dc.get("card_id") in detail_card_id_set:
            continue  # old copy of a detail chart; will be re-added fresh on tab 2
        cid = dc.get("card_id")
        keep.append({"id": dc["id"], "card_id": cid,
                     "row": dc["row"], "col": dc["col"], "size_x": dc["size_x"],
                     "size_y": dc["size_y"], "series": dc.get("series", []),
                     "parameter_mappings": filter_mappings(cid, f) if cid else [],
                     "visualization_settings": dc.get("visualization_settings", {}),
                     "dashboard_tab_id": tab1_id})

    # page-2 layout: each chart on the 24-col grid
    p2pos = {
        "Sales by Product":                  (0,  0,  12, 6),
        "Sales by Lead Source":              (0,  12, 12, 6),
        "Sales by Account Type":             (6,  0,  8,  6),
        "Sales by Country":                  (6,  8,  8,  6),
        "Unique Customers by Gender":        (6,  16, 8,  6),
        "Unique Accounts by Status":         (12, 0,  12, 6),
        "Top 10 Sales Agents (Field Sales)": (12, 12, 12, 6),
    }
    new = []
    for i, (name, _, _, _) in enumerate(detail_specs):
        row, col, sx, sy = p2pos[name]; cid = detail_ids[name]
        new.append({"id": -(200 + i), "card_id": cid, "row": row, "col": col,
                    "size_x": sx, "size_y": sy, "series": [],
                    "parameter_mappings": filter_mappings(cid, f), "visualization_settings": {},
                    "dashboard_tab_id": tab2_id})

    payload = {"tabs": [{"id": tab1_id, "name": tab1_name},
                        {"id": tab2_id, "name": TAB2_NAME}],
               "dashcards": keep + new, "parameters": filter_defs(), "width": "full"}
    st, r = api("PUT", f"/api/dashboard/{DASH_ID}", token, payload)
    if st != 200:
        print(f"✗ save failed ({st}): {r.get('message') or r}"); raise SystemExit(1)
    print(f"✓ '{TAB2_NAME}' tab built with {len(new)} charts (page 1 preserved)")
    print(f"\nOpen: {BASE}/dashboard/{DASH_ID}")

if __name__ == "__main__":
    main()
