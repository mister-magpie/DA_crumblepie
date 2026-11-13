#!/usr/bin/env python3
"""Fetch open and forthcoming EU calls from the Funding & Tenders Portal search API
and merge them into docs/data/calls.json. Stdlib only.

Entries this script writes have "source": "api". Each run replaces all of them with
fresh data, so calls that are gone or past their deadline drop out. Entries with
source "manual" or "agent" are kept, unless an "agent" entry has the same ID as an
API call, in which case the API version wins.

Usage: python3 scripts/fetch_eu.py [--dry-run]
"""
import json
import sys
import urllib.request
import uuid
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CALLS = ROOT / "docs" / "data" / "calls.json"
API = "https://api.tech.ec.europa.eu/search-api/prod/rest/search?apiKey=SEDIA&text=***"
PAGE_SIZE = 100
TOPIC_URL = "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/"

# Programmes to keep, by identifier prefix. Research-relevant only: no defence (EDF),
# culture (CREA), transport infrastructure (CEF), etc. Edit to widen or narrow.
PROGRAMMES = {
    "HORIZON": "Horizon Europe",
    "ERC": "ERC",
    "EURATOM": "Euratom",
    "DIGITAL": "Digital Europe",
    "LIFE": "LIFE",
    "EU4H": "EU4Health",
    "RFCS": "Research Fund for Coal and Steel",
    "I3": "Interregional Innovation Investments",
}
# Second part of Horizon Europe IDs, e.g. HORIZON-CL5-2027-...
HORIZON_PARTS = {
    "CL1": "Cluster 1: Health",
    "CL2": "Cluster 2: Culture, Creativity and Inclusive Society",
    "CL3": "Cluster 3: Civil Security for Society",
    "CL4": "Cluster 4: Digital, Industry and Space",
    "CL5": "Cluster 5: Climate, Energy and Mobility",
    "CL6": "Cluster 6: Food, Bioeconomy, Natural Resources, Agriculture and Environment",
    "MSCA": "Marie Skłodowska-Curie Actions",
    "ERC": "ERC",
    "EIC": "European Innovation Council",
    "EIE": "European Innovation Ecosystems",
    "WIDERA": "Widening Participation and Strengthening the ERA",
    "INFRA": "Research Infrastructures",
    "MISS": "Missions",
    "JU": "Joint Undertakings",
    "EUSPA": "EU Space Programme Agency",
    "HLTH": "Cluster 1: Health",
}


def post(page):
    """One page of grant topics (type 1/2) that are open or forthcoming."""
    query = {"bool": {"must": [
        {"terms": {"type": ["1", "2"]}},
        {"terms": {"status": ["31094501", "31094502"]}},  # open, forthcoming
    ]}}
    boundary = uuid.uuid4().hex
    # Sorting by identifier keeps paging stable. Without it, pages overlap and
    # different runs miss different calls.
    parts = [("query", json.dumps(query)), ("languages", json.dumps(["en"])),
             ("sort", json.dumps({"field": "identifier", "order": "ASC"}))]
    body = b"".join(
        f'--{boundary}\r\nContent-Disposition: form-data; name="{n}"\r\n'
        f"Content-Type: application/json\r\n\r\n{v}\r\n".encode()
        for n, v in parts
    ) + f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{API}&pageSize={PAGE_SIZE}&pageNumber={page}", data=body, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
                 "User-Agent": "funding-call-tracker"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def first(m, key):
    v = m.get(key)
    return (v[0] if isinstance(v, list) and v else v) or ""


def day(s):
    return s[:10] if s else ""


def programme(ident):
    parts = ident.split("-")
    name = PROGRAMMES[parts[0]]
    if parts[0] == "HORIZON" and len(parts) > 1:
        sub = HORIZON_PARTS.get(parts[1])
        if sub:
            return f"{name}, {sub}"
    return name


def fetch(today):
    calls, page, total = {}, 1, None
    while total is None or (page - 1) * PAGE_SIZE < total:
        d = post(page)
        total = d.get("totalResults", 0)
        results = d.get("results", [])
        if not results:
            break
        for r in results:
            m = r.get("metadata", {})
            ident = first(m, "identifier")
            if not ident or ident.split("-")[0] not in PROGRAMMES:
                continue
            # Deadlines: some topics have several cut-offs. Keep the next one.
            deadlines = sorted({day(x) for x in (m.get("deadlineDate") or []) if x})
            future = [x for x in deadlines if x >= today]
            if not future:
                continue  # status says open/forthcoming but all deadlines passed
            opens = day(first(m, "startDate"))
            notes = []
            if len(future) > 1:
                notes.append("Later cut-offs: " + ", ".join(future[1:]))
            model = first(m, "deadlineModel")
            if model and model != "single-stage":
                notes.append(model)
            call_title = first(m, "callTitle")
            calls[ident] = {
                "id": ident,
                "title": first(m, "title") or ident,
                "funder": "European Commission",
                "region": "EU",
                "programme": programme(ident),
                "url": TOPIC_URL + ident,
                "opens": opens,
                "deadline": future[0],
                "budget": "",
                "topics": [t for t in [ident.split("-")[1] if "-" in ident else "", call_title] if t],
                "status": "upcoming" if opens and opens > today else "open",
                "source": "api",
                "added": today,
                **({"notes": "; ".join(notes)} if notes else {}),
            }
        page += 1
    return calls


def main():
    dry = "--dry-run" in sys.argv
    today = date.today().isoformat()
    try:
        fresh = fetch(today)
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: EU API request failed: {e}")
        return 1
    if not fresh:
        print("ERROR: EU API returned no calls; leaving calls.json unchanged")
        return 1

    data = json.loads(CALLS.read_text(encoding="utf-8"))
    old = data.get("calls", [])
    old_api = {c["id"]: c for c in old if c.get("source") == "api"}
    kept = [c for c in old if c.get("source") != "api" and c["id"] not in fresh]
    replaced_agent = [c["id"] for c in old if c.get("source") == "agent" and c["id"] in fresh]

    for ident, c in fresh.items():  # keep the original "added" date
        if ident in old_api:
            c["added"] = old_api[ident].get("added", today)

    added = sorted(set(fresh) - set(old_api) - set(replaced_agent))
    removed = sorted(set(old_api) - set(fresh))
    updated = sorted(i for i in set(fresh) & set(old_api) if fresh[i] != old_api[i])

    data["calls"] = kept + sorted(fresh.values(), key=lambda c: (c["deadline"], c["id"]))
    data["updated"] = today
    print(f"EU API: {len(fresh)} calls kept "
          f"(+{len(added)} new, ~{len(updated)} changed, -{len(removed)} gone, "
          f"{len(replaced_agent)} agent entries replaced by API data)")
    by_prog = {}
    for c in fresh.values():
        by_prog[c["programme"].split(",")[0]] = by_prog.get(c["programme"].split(",")[0], 0) + 1
    print("By programme:", ", ".join(f"{k} {v}" for k, v in sorted(by_prog.items())))
    if not dry:
        CALLS.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
