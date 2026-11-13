# DA_crumblepie — Funding Call Tracker

A public, automatically updated list of open and upcoming **research funding calls in Sweden and the EU**, published with GitHub Pages.

- **Website:** https://mister-magpie.github.io/DA_crumblepie/
- **Data:** [`docs/data/calls.json`](docs/data/calls.json)
- **How it updates:** a Claude agent runs in GitHub Actions every other Monday at 12:00 (Stockholm time). It follows [`AGENT.md`](AGENT.md): it checks the funders in [`sources.yaml`](sources.yaml), updates `calls.json`, validates it, and pushes to `main`. GitHub Pages then republishes the site.

---

## Status

| Phase | Description | Status |
|---|---|---|
| 0 | Repo set up, README plan, minimal page and data file | ✅ Done |
| 1 | GitHub Pages live, data schema settled | 🚧 In progress (Pages live) |
| 2 | Source list and seed data | 🚧 In progress (draft `sources.yaml`) |
| 3 | Update agent in GitHub Actions, run by hand | 🚧 In progress (first run OK on 2026-11-13: 12 calls; most sources not checked yet) |
| 4 | Scheduled runs, deduplication, run logs | 🚧 In progress (schedule set) |
| 5 | Website polish (filters, calendar/RSS, notifications) | ⬜ Not started |

Last updated: 2026-11-13

---

## Architecture

```
┌───────────────────────────┐ biweekly  ┌──────────────────────────────┐
│ GitHub Actions             │ ────────▶ │ Claude agent                  │
│ update-calls.yml           │           │ (anthropics/claude-code-action)│
│ every other Monday 12:00   │           │  - reads AGENT.md,            │
└───────────────────────────┘           │    sources.yaml               │
                                        │  - checks funder sites / APIs │
                                        │  - merges into calls.json     │
                                        │  - runs scripts/validate.py   │
                                        │  - writes logs/YYYY-MM-DD.md  │
                                        └──────────────┬───────────────┘
                                                       │ git push origin main
                                                       ▼
                                        ┌──────────────────────────────┐
                                        │ GitHub: docs/data/calls.json  │
                                        └──────────────┬───────────────┘
                                                       │ Pages deploy
                                                       ▼
                                        ┌──────────────────────────────┐
                                        │ docs/index.html (static site) │
                                        └──────────────────────────────┘
```

Design choices:
- **The agent runs in GitHub Actions.** Actions minutes are free for public repos, and the agent signs in with a Claude subscription token (`CLAUDE_CODE_OAUTH_TOKEN`) instead of a paid API key. It doesn't depend on anyone's computer being on.
- **Instructions live in the repo.** `AGENT.md` is the agent's whole job description, and the workflow only says "follow AGENT.md". To change what the agent does, edit `AGENT.md` and push. Both of us can do this.
- **Static site, no backend.** `docs/index.html` loads `docs/data/calls.json` and filters it in the browser. Pages serves straight from `/docs` on `main`.
- **Data in git.** Every update is a commit with a log file, so wrong entries are easy to spot and revert.
- **Pushes go straight to `main`.** No review step. `AGENT.md` tells the agent to confirm every call on the official page and never to guess, and `logs/` records what changed. If this lets too many errors through, switch to pushing a branch and opening a PR.
- **Structured sources first.** Where a funder has an API (the EU Funding & Tenders Portal) or a stable listing page, the agent uses that. Open web search is only for finding new sources.

## Repository layout

```
AGENT.md               # instructions the update agent follows on every run
sources.yaml           # funders and URLs the agent checks
docs/                  # GitHub Pages root
  index.html           # the tracker page
  data/calls.json      # the list of calls (single source of truth)
scripts/validate.py    # checks calls.json: required fields, dates, duplicate IDs
logs/                  # one file per agent run: what was checked and changed
.github/workflows/
  update-calls.yml     # runs the agent every other Monday, or on demand
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

## Sources

The full list, with URLs, is in [`sources.yaml`](sources.yaml). Most URLs are starting points marked `verify: true`. The agent confirms or corrects them on its first run.

- **Sweden:** VR, Vinnova, Formas, Forte, Energimyndigheten, Rymdstyrelsen, SSF, KAW, RJ, KK-stiftelsen, Mistra, WASP
- **EU:** Funding & Tenders Portal (via its public search API), ERC, EIC, Eureka/Eurostars, COST

## Plan

### Phase 1: Pages and schema
- [x] Enable GitHub Pages: *Settings → Pages → Deploy from branch → `main` / `docs`*
- [ ] Add collaborator: *Settings → Collaborators → Add people*
- [ ] Agree on the ID convention and the status rules (draft in `AGENT.md`)

### Phase 2: Sources and seed data
- [x] Draft `sources.yaml`
- [ ] Review the source list together: add or remove funders
- [ ] Remove the placeholder entry (the agent does this on its first real run)

### Phase 3: Update agent in GitHub Actions, run by hand
- [x] `AGENT.md`: the instructions for each run
- [x] `scripts/validate.py`: required fields, date format, duplicate IDs
- [x] `.github/workflows/update-calls.yml`
- [x] Add the `CLAUDE_CODE_OAUTH_TOKEN` repository secret (see *Running the agent* below)
- [ ] Do 2–3 runs by hand (1 done) ("Run workflow"), read the logs, and tune `AGENT.md`
- [x] Check that a push by the workflow triggers a Pages rebuild
- [ ] Add a URL check (HTTP 200) to the validator

### Phase 4: Scheduled runs and quality
- [x] Turn on the schedule: every other Monday at 12:00
- [ ] Better deduplication (fuzzy title matching)
- [ ] Decide whether to keep pushing to `main` or switch to PRs

### Phase 5: Website polish
- [ ] Filter by funder, topic and deadline range
- [ ] "Closing soon" highlight
- [ ] iCal feed of deadlines and/or RSS of new calls
- [ ] Optional: email/Slack notification for new calls

## Running the agent

The agent is the **"Update funding calls"** workflow ([`.github/workflows/update-calls.yml`](.github/workflows/update-calls.yml)).

- **Schedule:** every other Monday at 12:00 Stockholm time, in odd ISO weeks. The first run is Monday 2026-11-16 (week 47). GitHub cron uses UTC and has no "every 2 weeks", so the workflow fires every Monday at 10:00 and 11:00 UTC. A small `gate` job then keeps only the run that is 12:00 in Stockholm (summer or winter time) in an odd week. All the other runs show as skipped. GitHub often starts scheduled runs a few minutes late.
- **Run by hand:** *Actions → Update funding calls → Run workflow*. This always runs, whatever the week.
- **Results:** the agent's summary is on the run's page. Its commit and `logs/YYYY-MM-DD.md` land on `main`.

**One-time setup (needs a Claude Pro/Max subscription):**

1. On a computer with Claude Code installed, create a long-lived token:
   ```bash
   claude setup-token
   ```
2. Save it as a repository secret named `CLAUDE_CODE_OAUTH_TOKEN`, either in *Settings → Secrets and variables → Actions → New repository secret*, or:
   ```bash
   gh secret set CLAUDE_CODE_OAUTH_TOKEN --repo mister-magpie/DA_crumblepie
   ```
   (paste the token when asked).

Runs use the subscription's usage limits. Actions minutes are free because the repo is public.

## Collaborating

- The agent pushes to `main`, so **pull before you edit** (`git pull --rebase`) to avoid conflicts.
- For bigger changes (the website, `AGENT.md`, new data fields), use a branch and a PR.
- Update the **Status** table and tick the plan checkboxes in the same commit as the work.
- Open questions and ideas go in GitHub Issues.

## Local preview

```bash
cd docs && python3 -m http.server 8000
```
Then open http://localhost:8000.

## Open questions

- Which research fields should we focus on, or should we track everything?
- Track only calls open to Swedish applicants, or all EU calls?
