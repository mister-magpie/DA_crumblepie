# Agent instructions: update the funding call list

You are the update agent for the Funding Call Tracker in this repository. You run on a schedule on the maintainer's machine. Each run starts fresh, so everything you need is in this file.

## Goal

Keep `docs/data/calls.json` an accurate list of **open and upcoming research funding calls in Sweden and the EU**, then commit and push the result so the GitHub Pages site updates.

## Steps

1. **Sync.** In the repo root run `git pull --rebase origin main`. If that fails (conflicts, a dirty tree), stop and report. Never force-push or reset someone else's work.
2. **Read** `sources.yaml` and `docs/data/calls.json`.
3. **Check each source** in `sources.yaml`:
   - If it has an `api`, use that (for example the EU Funding & Tenders search API). Otherwise open its `listing` page.
   - Collect calls that are open now or open in the future. Open the official call page for each one and confirm the title, deadline and URL there. **Never invent or guess a call, date or URL.** If you can't confirm a field, leave it empty (`""`) and say so in `notes`.
   - If a listing URL is broken or has moved, find the new one on the funder's site and update `sources.yaml`.
4. **Merge into `calls.json`:**
   - Match existing entries by `id`, then by the same URL or the same funder plus a near-identical title. Update a matched entry instead of adding a duplicate.
   - New entries get `"source": "agent"` and `"added": "<today>"`.
   - Set `status`: `upcoming` if `opens` is in the future, `closed` if `deadline` is in the past, otherwise `open`.
   - Remove entries whose deadline is more than 90 days in the past.
   - Delete the `example-001` placeholder once there is at least one real call.
   - Set the top-level `"updated"` to today (YYYY-MM-DD).
   - Follow the field rules in README.md → *Data model*. IDs: lower-case funder slug plus call identifier (`vinnova-2027-xyz`), or the official EU topic ID as is.
5. **Validate:** `python3 scripts/validate.py`. Fix every error before continuing.
6. **Log:** write `logs/YYYY-MM-DD.md` with: the sources checked (OK or failed, with the reason), and the calls added, updated, closed and removed (counts and titles).
7. **Upload:** if anything changed, `git add docs/data/calls.json sources.yaml logs/` and commit with the message `data: update calls YYYY-MM-DD (+A ~U -R)`, ending in a blank line and `Co-Authored-By: Claude <noreply@anthropic.com>`. Then `git push origin main`. If the push is rejected, pull with rebase once and try again. If it still fails, stop and report.
8. **Report** a short summary: what changed, which sources failed, and anything a person should check.

## Scope

- **In:** calls open to researchers at Swedish universities, institutes or companies. That means Swedish national funders, Swedish private foundations, and EU programmes Sweden takes part in.
- **Out:** calls for individual students (scholarships), procurement tenders, and prizes with no research funding.
- Only touch `docs/data/calls.json`, `sources.yaml` and `logs/`. Don't edit the website, the README or this file.
