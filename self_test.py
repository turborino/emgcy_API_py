from __future__ import annotations

"""
このスクリプトは、Flask アプリの主要APIを自動で叩いて、
「正常に動くかどうか」を簡単に確認（セルフテスト）します。
"""

from pprint import pprint

from app import app


def main() -> None:
    client = app.test_client()

    r = client.get("/health")
    print("/health:", r.status_code, r.json)

    r2 = client.get("/shelters")
    print("/shelters:", r2.status_code)
    j2 = r2.get_json()
    if not j2:
        raise SystemExit("/shelters returned no JSON")
    print("count:", j2.get("count"))
    items = j2.get("items", [])
    if items:
        print("first item:")
        pprint(items[0])
    else:
        print("no shelters parsed from CSV")

    r3 = client.get("/nearest?lat=35.77&lon=139.80&n=3")
    print("/nearest:", r3.status_code)
    j3 = r3.get_json()
    if j3:
        print("nearest items:", len(j3.get("items", [])))
        if j3.get("items"):
            pprint(j3["items"][0])

    # Query filtering tests
    r4 = client.get("/shelters?q=足立&limit=5&offset=0")
    print("/shelters?q=...:", r4.status_code)
    j4 = r4.get_json()
    if j4:
        print("filtered count:", j4.get("count"))
        if j4.get("items"):
            pprint(j4["items"][0])

    # BBox test around 足立付近
    bbox = "139.78,35.74,139.82,35.80"
    r5 = client.get(f"/shelters?bbox={bbox}&limit=3")
    print("/shelters?bbox=...:", r5.status_code)
    j5 = r5.get_json()
    if j5:
        print("bbox count:", j5.get("count"))
        if j5.get("items"):
            pprint(j5["items"][0])


if __name__ == "__main__":
    main()

