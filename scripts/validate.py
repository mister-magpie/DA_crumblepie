#!/usr/bin/env python3
"""Validate docs/data/calls.json. Stdlib only. Exit code 1 on errors."""
import json
import re
import sys
from datetime import date
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "docs" / "data" / "calls.json"
REQUIRED = ["id", "title", "funder", "region", "url", "status", "source", "added"]
DATE_FIELDS = ["opens", "deadline", "added"]
REGIONS = {"SE", "EU"}
STATUSES = {"upcoming", "open", "closed"}
SOURCES = {"manual", "agent", "api"}


def is_date(s):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return False
    try:
        date.fromisoformat(s)
        return True
    except ValueError:
        return False


def main():
    errors = []
    try:
        data = json.loads(PATH.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: cannot parse {PATH}: {e}")
        return 1

    if not is_date(str(data.get("updated", ""))):
        errors.append("top-level 'updated' must be YYYY-MM-DD")
    calls = data.get("calls")
    if not isinstance(calls, list):
        print("ERROR: 'calls' must be a list")
        return 1

    seen = set()
    for i, c in enumerate(calls):
        where = f"calls[{i}] ({c.get('id', '?')})"
        for f in REQUIRED:
            if not c.get(f):
                errors.append(f"{where}: missing '{f}'")
        if c.get("id") in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(c.get("id"))
        if c.get("region") and c["region"] not in REGIONS:
            errors.append(f"{where}: region must be one of {sorted(REGIONS)}")
        if c.get("status") and c["status"] not in STATUSES:
            errors.append(f"{where}: status must be one of {sorted(STATUSES)}")
        if c.get("source") and c["source"] not in SOURCES:
            errors.append(f"{where}: source must be one of {sorted(SOURCES)}")
        if c.get("url") and not str(c["url"]).startswith(("http://", "https://")):
            errors.append(f"{where}: url must start with http(s)://")
        for f in DATE_FIELDS:
            v = c.get(f)
            if v and not is_date(str(v)):
                errors.append(f"{where}: '{f}' must be YYYY-MM-DD, got {v!r}")
        if "topics" in c and not isinstance(c["topics"], list):
            errors.append(f"{where}: 'topics' must be a list")

    for e in errors:
        print("ERROR:", e)
    print(f"{len(calls)} calls checked, {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
