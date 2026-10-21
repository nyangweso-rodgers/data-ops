#!/usr/bin/env python3
"""Build (idempotently) a 'Sales Funnel' dashboard: a left-to-right journey of
scorecards on test_marts_mv_accounts, with a Country filter.

  Unique Customers -> Sales (Qty) -> Dispatched (Qty) -> Installed (Qty)

  - Unique Customers : distinct customerId where sale_date is set
  - Sales (Qty)      : sum(productQty) where sale_date is set
  - Dispatched (Qty) : sum(productQty) where dispatchDate is set
  - Installed (Qty)  : sum(productQty) where jsfDate is set

Re-runnable: cards matched by name; the dashboard named 'Sales Funnel' is reused.
Field ids resolved by name at runtime.
"""
import json, os, urllib.request, urllib.error

BASE = os.environ.get("METABASE_URL", "http://localhost:3000").rstrip("/")
EMAIL, PASSWORD = "admin@mycompany.com", "MyStrongPassword123!"
DB_ID, TABLE_ID = 3, 102
DASH_NAME = "Sales Funnel"
COUNTRY = {"id": "country_region", "name": "Country", "slug": "country", "type": "string/="}

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
    qty, custid, creg = f["productQty"], f["customerId"], f["companyRegion"]
    sdate, ddate, jdate = f["sale_date"], f["dispatchDate"], f["jsfDate"]

    def q(agg, datefield):
        return {"database": DB_ID, "type": "query", "query": {
            "source-table": TABLE_ID, "aggregation": [agg],
            "filter": ["not-null", ["field", datefield, None]]}}

    # ordered left->right = the funnel journey
    specs = [
        ("Unique Customers", q(["distinct", ["field", custid, None]], sdate)),
        ("Sales (Qty)",      q(["sum", ["field", qty, None]], sdate)),
        ("Dispatched (Qty)", q(["sum", ["field", qty, None]], ddate)),
        ("Installed (Qty)",  q(["sum", ["field", qty, None]], jdate)),
    ]

    _, allcards = api("GET", "/api/card", token)
    existing = {c["name"]: c["id"] for c in allcards}
    ids = {}
    for name, query in specs:
        body = {"name": name, "dataset_query": query, "display": "scalar",
                "visualization_settings": {}}
        if name in existing:
            st, r = api("PUT", f"/api/card/{existing[name]}", token, body); act = "updated"
        else:
            st, r = api("POST", "/api/card", token, body); act = "created"
        if st not in (200, 201):
            print(f"✗ {name} ({st}): {r.get('message') or r}"); raise SystemExit(1)
        ids[name] = r["id"]; print(f"✓ {act}: {name} (id={r['id']})")

    _, dashlist = api("GET", "/api/dashboard", token)
    did = next((d["id"] for d in dashlist if d["name"] == DASH_NAME), None)
    if did is None:
        _, d = api("POST", "/api/dashboard", token, {"name": DASH_NAME}); did = d["id"]
        print(f"✓ dashboard created: {DASH_NAME} (id={did})")
    else:
        print(f"• reusing dashboard: {DASH_NAME} (id={did})")

    def cmap(cid):
        return [{"parameter_id": COUNTRY["id"], "card_id": cid,
                 "target": ["dimension", ["field", creg, None]]}]

    heading = {"id": -100, "card_id": None, "row": 0, "col": 0, "size_x": 24, "size_y": 1,
               "series": [], "parameter_mappings": [],
               "visualization_settings": {
                   "virtual_card": {"name": None, "display": "heading", "dataset_query": {},
                                    "visualization_settings": {}, "archived": False},
                   "text": "Sales Funnel"}}

    dashcards = [heading]
    for i, (name, _) in enumerate(specs):       # row of 4, each 6 wide x 6 tall (fills screen)
        cid = ids[name]
        dashcards.append({"id": -(i + 1), "card_id": cid, "row": 1, "col": i * 6,
                          "size_x": 6, "size_y": 6, "series": [],
                          "parameter_mappings": cmap(cid), "visualization_settings": {}})

    st, r = api("PUT", f"/api/dashboard/{did}", token,
                {"dashcards": dashcards, "parameters": [COUNTRY], "width": "full"})
    if st != 200:
        print(f"✗ save failed ({st}): {r.get('message') or r}"); raise SystemExit(1)
    print(f"✓ heading + {len(specs)} funnel scorecards placed, Country filter wired")

    api("PUT", f"/api/field/{creg}", token, {"has_field_values": "list"})
    api("POST", f"/api/field/{creg}/rescan_values", token)
    print(f"\nOpen: {BASE}/dashboard/{did}")

if __name__ == "__main__":
    main()
