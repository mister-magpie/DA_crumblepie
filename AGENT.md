# Agent instructions: update the funding call list

You are the update agent for the Funding Call Tracker in this repository. You run in GitHub Actions (`.github/workflows/update-calls.yml`), every other Monday or when someone starts the workflow by hand. Each run starts from a fresh checkout, so everything you need is in this file.

## Goal

Keep `docs/data/calls.json` an accurate list of **open and upcoming research funding calls in Sweden and the EU**, then commit and push the result so the GitHub Pages site updates.

## Who does what

- **EU Funding & Tenders Portal calls are already done.** Before you start, the workflow runs `scripts/fetch_eu.py`. It loads every open and upcoming Horizon Europe, ERC, MSCA, EIC, Digital Europe and LIFE topic from the portal's API into `calls.json` with `"source": "api"`. **Never add, edit or delete entries with `"source": "api"`.** Never add a call that has an EU topic ID (like `HORIZON-...` or `ERC-...`): the script owns those.
- **Your job is every other source in `sources.yaml`:** all the Swedish funders, and the EU sources outside the portal (Eureka/Eurostars, COST). For ERC and EIC, only add something if it is *not* a portal topic (for example a scheme announced on their site before it reaches the portal).

## Rules

- **Check every source.** Go through `sources.yaml` from top to bottom and handle each source before moving on. Skipping a source is not allowed. A source can only end up as **OK** (checked, with the number of calls found, which may be 0) or **FAILED** (with the reason: page not found, no call list on the site, page needs JavaScript, and so on). Don't stop early because the run feels long.
- **Never invent anything.** Every title, date and URL must come from the funder's own page. If a field isn't on the page, leave it as `""`. Don't guess a date from last year's call.
- **Calls without dates are allowed.** If a funder lists an upcoming call with no dates yet, add it with `"status": "upcoming"`, `"opens": ""`, `"deadline": ""` and `"notes": "Dates not published yet"`.
- **Watch the year.** If a call page is from a previous year's round (the year in its URL or title is older than the dates you're about to write), check that the dates are for the current round. If you can't confirm this, leave the dates empty and say why in `notes`.
- **Stay in scope.** Include calls open to researchers at Swedish universities, institutes or companies. Leave out scholarships for individual students, procurement tenders, and prizes with no research funding.
- **Only touch** `docs/data/calls.json`, `sources.yaml` and `logs/`. Don't edit the website, scripts, workflows, the README or this file.

## Steps

1. **Sync:** run `git pull --rebase origin main`. If it fails, stop and report.
2. **Start the log:** create `logs/YYYY-MM-DD.md` (today's date) with one line per source in `sources.yaml`, all marked `TODO`. Fill in each line as you finish that source. At the end, no line may still say `TODO`.
3. **For each source in `sources.yaml`:**
   1. Open the `listing` URL. If it's broken or moved, find the funder's current call list on its site and update `listing` in `sources.yaml`, plus a short `notes` line. Set `verify: false` once you've confirmed a listing URL works.
   2. Collect the calls that are open now or upcoming.
   3. Open each call's own page and read the title, opening date, deadline and URL from it.
   4. Merge into `calls.json` (see below).
   5. Update the source's line in the log: OK with the number of calls added, updated and unchanged, or FAILED with the reason.
4. **Re-check old entries:** for each existing entry with `"source": "agent"` or `"manual"` that you didn't see in step 3, open its URL. If the call is gone or its dates changed, update it. If the page no longer exists, set `"notes"` to say so.
5. **Tidy up:** set each non-api entry's `status`: `upcoming` if `opens` is in the future or there are no dates, `closed` if `deadline` is in the past, otherwise `open`. Remove non-api entries whose deadline is more than 90 days ago. Set the top-level `"updated"` to today.
6. **Validate:** run `python3 scripts/validate.py` and fix every error.
7. **Finish the log:** add a summary with the calls added, updated, closed and removed (counts and titles), plus anything a person should check.
8. **Upload:** `git add docs/data/calls.json sources.yaml logs/`, then commit with the message `data: update calls YYYY-MM-DD (+A ~U -R)`. End the message with a blank line and `Co-Authored-By: Claude <noreply@anthropic.com>`. Then `git push origin main`. If the push is rejected, run `git pull --rebase origin main` once and push again. If it still fails, stop and report. The API data written by `fetch_eu.py` is part of the same commit.
9. **Report:** a short summary of what changed and which sources failed. It appears in the workflow run's summary on GitHub.

## Entry format

Follow README.md → *Data model*. For new entries:
- `id`: lower-case funder slug plus a short call slug, e.g. `vinnova-2027-smart-industry` or `formas-2027-annual-open-call`. Reuse the existing ID when updating an entry.
- `source`: `"agent"`. `added`: today's date.
- Match against existing entries by `id`, then by the same URL, then by the same funder with a near-identical title. Update a match instead of adding a duplicate.
