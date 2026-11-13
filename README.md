# DA_crumblepie — Funding Call Tracker

A public, automatically updated list of open and upcoming **research funding calls in Sweden and the EU**, published with GitHub Pages.

- **Website:** https://mister-magpie.github.io/DA_crumblepie/ (live once Pages is enabled, see Phase 1)
- **Data:** [`docs/data/calls.json`](docs/data/calls.json)
- **How it updates:** a scheduled agentic workflow (GitHub Actions + an LLM agent) searches funder websites, pulls out new calls and opens a pull request with the changes.

---

## Status

| Phase | Description | Status |
|---|---|---|
| 0 | Repo set up, README plan, minimal page and data file | ✅ Done |
| 1 | GitHub Pages live, data schema settled | ⏳ Next |
| 2 | Source list and manual seed data | ⬜ Not started |
| 3 | Agentic scraping workflow (manual trigger) | ⬜ Not started |
| 4 | Scheduled runs, review flow, deduplication | ⬜ Not started |
| 5 | Website polish (filters, calendar/RSS, notifications) | ⬜ Not started |

Last updated: 2026-11-13

---

## Architecture

```
┌──────────────────────┐   cron (weekly)   ┌──────────────────────────┐
│ GitHub Actions        │ ────────────────▶ │ Agent (Claude Code       │
│ .github/workflows/    │                   │ action / Agent SDK)      │
│ update-calls.yml      │                   │  - reads sources.yaml    │
└──────────────────────┘                   │  - fetches/searches web  │
                                           │  - extracts calls        │
                                           │  - merges into JSON      │
                                           └────────────┬─────────────┘
                                                        │ opens PR
                                                        ▼
                                           ┌──────────────────────────┐
                                           │ docs/data/calls.json      │
                                           │ (human review + merge)    │
                                           └────────────┬─────────────┘
                                                        │ Pages deploy
                                                        ▼
                                           ┌──────────────────────────┐
                                           │ docs/index.html (static)  │
                                           └──────────────────────────┘
```

Design choices:
- **Static site, no backend.** `docs/index.html` loads `docs/data/calls.json` and filters it in the browser. Pages serves straight from `/docs` on `main`.
- **Data in git.** Every change to the list is a commit, so we get history, diffs and review for free.
- **Agent writes through PRs, not to `main`.** A person merges each update. This catches hallucinated or wrong calls before they go live.
- **Structured sources first, open web search second.** Where a funder has an API or a stable listing page, use that. Free-form web search is only for finding new sources.

## Repository layout

```
docs/                  # GitHub Pages root
  index.html           # the tracker page
  data/calls.json      # the list of calls (single source of truth)
sources.yaml           # (Phase 2) funders and URLs the agent checks
schema/call.schema.json# (Phase 1) JSON Schema for one call
scripts/validate.py    # (Phase 3) schema + dedup + link check
.github/workflows/
  update-calls.yml     # (Phase 3) agentic update job
  validate.yml         # (Phase 3) CI check on PRs touching data
```

## Data model (draft)

Each entry in `calls[]`:

| Field | Type | Notes |
|---|---|---|
| `id` | string | Stable ID: funder slug + call identifier, e.g. `vr-2027-project-grant` or the EU topic ID `HORIZON-CL4-2027-...` |
| `title` | string | Official call title |
| `funder` | string | e.g. Vetenskapsrådet, Vinnova, European Commission |
| `region` | `SE` \| `EU` | |
| `programme` | string | e.g. Horizon Europe Cluster 4, ERC Starting Grant |
| `url` | string | Official call page |
| `opens` | date (YYYY-MM-DD) | Optional |
| `deadline` | date (YYYY-MM-DD) | First or only deadline; multi-stage calls note others in `notes` |
| `budget` | string | Free text: total or per-project |
| `topics` | string[] | Free tags |
| `status` | `upcoming` \| `open` \| `closed` | |
| `source` | `manual` \| `agent` | Who added it |
| `added` | date | When it was added to the tracker |
| `notes` | string | Optional |

## Sources to cover (Phase 2)

**Sweden**
- Vetenskapsrådet (VR)
- Vinnova
- Formas
- Forte
- Energimyndigheten (Swedish Energy Agency)
- Rymdstyrelsen (Swedish National Space Agency)
- Stiftelsen för strategisk forskning (SSF)
- Knut och Alice Wallenbergs Stiftelse (KAW)
- Riksbankens Jubileumsfond (RJ)
- KK-stiftelsen
- Mistra
- Wallenberg AI, Autonomous Systems and Software Program (WASP)

**EU**
- EU Funding & Tenders Portal (Horizon Europe, Digital Europe, LIFE, etc.). Has a public search API, so this should be the main EU source.
- European Research Council (ERC)
- European Innovation Council (EIC)
- Eureka / Eurostars
- Interreg programmes relevant to Sweden
- COST Actions

## Plan

### Phase 1: Pages and schema
- [ ] Enable GitHub Pages: *Settings → Pages → Deploy from branch → `main` / `docs`*
- [ ] Add collaborator: *Settings → Collaborators → Add people*
- [ ] Write `schema/call.schema.json` from the data model above
- [ ] Agree on the ID convention and the status rules

### Phase 2: Sources and seed data
- [ ] Create `sources.yaml` (name, region, listing URL, API if any, notes)
- [ ] Add 10–20 real calls by hand to test the page and the schema
- [ ] Remove the placeholder entry

### Phase 3: Agentic workflow (manual trigger)
- [ ] `scripts/validate.py`: schema validation, duplicate IDs, dates parse, URLs return 200
- [ ] `.github/workflows/validate.yml`: run the validator on every PR
- [ ] `.github/workflows/update-calls.yml` with `workflow_dispatch`:
  - run the agent (e.g. `anthropics/claude-code-action`) with a prompt that reads `sources.yaml`, checks each source, and adds or updates entries in `calls.json`
  - for the EU portal, call the API from a script instead of having the agent browse
  - mark calls past their deadline as `closed`
  - open a PR with a summary: added / updated / closed
- [ ] Store the `ANTHROPIC_API_KEY` repository secret
- [ ] Do a few manual runs and tune the prompt

### Phase 4: Scheduling and quality
- [ ] Add a `schedule:` cron trigger (e.g. weekly on Monday morning)
- [ ] Deduplicate by ID and fuzzy title match
- [ ] Keep a run log (`data/runs/YYYY-MM-DD.md`) of what the agent checked
- [ ] Watch cost and runtime, and cap pages per run

### Phase 5: Website polish
- [ ] Filter by funder, topic and deadline range
- [ ] "Closing soon" highlight
- [ ] iCal feed of deadlines and/or RSS of new calls
- [ ] Optional: email/Slack notification for new calls

## Collaborating

- Work on branches and open PRs into `main`. Don't push data changes straight to `main`.
- Update the **Status** table and tick the plan checkboxes in the same PR as the work.
- Open questions and ideas go in GitHub Issues.

## Local preview

```bash
cd docs && python3 -m http.server 8000
```
Then open http://localhost:8000.

## Open questions

- Which research fields should we focus on, or should we track everything?
- Track only calls open to Swedish applicants, or all EU calls?
- Which LLM and budget should the agent use, and who owns the API key?
