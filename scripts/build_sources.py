#!/usr/bin/env python3
"""Convert sources.yaml (flat list of funders) to docs/data/sources.json for the website."""
import json, re, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
sources, cur = [], None
for line in (root / "sources.yaml").read_text(encoding="utf-8").splitlines():
    if not line.strip() or line.lstrip().startswith("#"):
        continue
    m = re.match(r"\s*- name:\s*(.*)$", line)
    if m:
        cur = {"name": m.group(1).strip()}
        sources.append(cur)
        continue
    m = re.match(r"\s+(\w+):\s*(.*)$", line)
    if m and cur is not None:
        k, v = m.group(1), m.group(2).strip()
        cur[k] = (v == "true") if v in ("true", "false") else v
(root / "docs/data/sources.json").write_text(json.dumps({"sources": sources}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"{len(sources)} sources")
