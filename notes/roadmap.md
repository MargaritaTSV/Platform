# Roadmap (MVP target: mid-December 2026)

Status: `[x]` done, `[~]` partly, `[ ]` open. Big sessions until Sun Nov 29, then one task per short session.
Each task: a branch from `main`, then a pull request. Domain: astroolymp.com (live).

| Status | # | Task | Needs from owner | Latest |
|---|---|---|---|---|
| [x] | T0 | CLAUDE.md, roadmap, site.yml, validator + fixtures | | Nov 27 |
| [x] | T1 | Cleanup of old content, games, subagents; .gitignore | | Nov 28 |
| [x] | T2 | Cloudflare: nameservers, R2 bucket `astroolymp` at files.astroolymp.com, Pages project `stellartask` | | Nov 29 |
| [x] | T3 | Real taxonomy.yml + sources (from `notes/topicslist.txt`) | review Russian names | Nov 30 |
| [x] | T4 | figures.py + lock; samples migrated; 4 figures live on R2 |  | Dec 1 |
| [x] | T5 | Overleaf starter |  | Dec 2 |
| [x] | T6 | `validate.yml` + `deploy.yml` (publish on merge to main); live at astroolymp.com since Nov 27 | | Dec 3 |
| [x] | T7 | build.py: pandoc fragments, cache, KaTeX pre-render (`throwOnError`), R2 image URLs, `\alph*)` sub-lists | | Dec 5 |
| [x] | T8 | Layout: header, footer, RU/EN button, name from site.yml, tabs (Задачи / Теория / Игры) | | Dec 6 |
| [x] | T9 | Home: star map (design/map.json, `star` in taxonomy), subtopic panel, counts | | Dec 8 |
| [x] | T10 | Problems page per subtopic: rail, rows, filters (difficulty, source, year, grade), URL state | | Dec 10 |
| [x] | T11 | Pagefind search (home + problems page), results link to `#<id>` | | Dec 11 |
| [x] | T12 | Theory placeholder, games link | | Dec 11 |
| [x] | T13 | Scale test with 10k synthetic problems (build < 20 min, < 20k files, page < 1.5 MB) | | Dec 12 |
| [x] | T14 | Branch protection + required `validate` check; `notes/routine.md` | | Dec 13 |
| [~] | T15 | Design pass, launch checklist, go live | owner items in `notes/launch.md` | Dec 15 |

## Open notes
- Big question bank: classify into `notes/intake/<bank>.csv`, owner approves, then write (`notes/routine.md`).
  Waiting for the owner's files.
- "Games" shows without a link until `games_url` in site.yml is set.
- Back up of source PDFs: `../Platform-source-backup/` (pulling `main` can delete `content/_source/`).
- `design/svg/logo_star.svg` comes from a Vecteezy stock file (250 KB): check its licence before launch.
- T13 (`python scripts/scale.py`, Nov 27, 10k problems): cold build 343 s, cached 183 s, 10,704 files,
  largest page 0.62 MB (20 rows). All pass.
- Subtopic lists have numbered pages of 20; the filters cover the whole subtopic (`site/static/js/filters.js`).
  A rare filter combination can fetch up to 20 pages for one view: check the speed once there are many problems.
- Not measured: the full XeLaTeX check (weekly, and any PR touching `latex/` or the validator) compiles one file
  at a time, so at 10k it may take hours and pass GitHub's 6-hour job limit.
- The old GitHub Pages maintenance page stays published until Pages is switched off in repo settings.
- Old PDFs stay in earlier git history (the repo is private).
- Search (`scripts/search.py`): one Pagefind record per problem, so 10k problems = ~10k fragment files.
  With the list pages, the free Pages limit of
  20,000 files is reached at roughly 18,500 problems.
- Map lines are hand-written in `site/templates/home.html` and match `star` in taxonomy.yml.
- Short subtopic names, all Russian text and the descriptions of the last three topics in taxonomy.yml were written by
  Claude: owner to review.
- Local `content/figures/` is the only original copy besides R2: back it up.

## After the MVP
Games on their own subdomain, theory notes, study order, RU→EN translations, solutions, whole-bank filters.
