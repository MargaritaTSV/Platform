# Roadmap (MVP target: mid-December 2026)

Status: `[x]` done, `[~]` partly, `[ ]` open. Big sessions until Sun Nov 29, then one task per short session.
Work branch: `latex-mvp` (pushed to GitHub; `main` still serves the maintenance page). Domain: astroolymp.com.

| Status | # | Task | Needs from owner | Latest |
|---|---|---|---|---|
| [x] | T0 | CLAUDE.md, roadmap, site.yml, validator + fixtures | | Nov 27 |
| [x] | T1 | Cleanup of old content, games, subagents; .gitignore | | Nov 28 |
| [x] | T2 | Cloudflare: nameservers, R2 bucket `astroolymp` at files.astroolymp.com, Pages project `stellartask` | | Nov 29 |
| [~] | T3 | Real taxonomy.yml + sources | check names and subtopics; grades need no list | Nov 30 |
| [~] | T4 | figures.py + lock; samples migrated; 4 figures live on R2 | confirm topics/difficulties | Dec 1 |
| [~] | T5 | Overleaf starter | upload and compile once | Dec 2 |
| [~] | T6 | CI: `validate.yml` written (never run yet); `deploy.yml`, coming-soon page, remove GH Pages/CNAME open | token + account id as repo secrets | Dec 3 |
| [x] | T7 | build.py: pandoc fragments, cache, KaTeX pre-render (`throwOnError`), R2 image URLs, `\alph*)` sub-lists | | Dec 5 |
| [ ] | T8 | Layout: header, footer, RU/EN button, name from site.yml, tabs (Задачи / Теория / Игры) | | Dec 6 |
| [ ] | T9 | Home: star map (design/map.json, `star` in taxonomy), subtopic panel, counts | | Dec 8 |
| [ ] | T10 | Problems page per subtopic: rail, rows, filters (difficulty, source, year, grade), URL state | | Dec 10 |
| [ ] | T11 | Pagefind search (home + problems page), results link to `#<id>` | | Dec 11 |
| [ ] | T12 | Theory placeholder, games link | | Dec 11 |
| [ ] | T13 | Scale test with 10k synthetic problems (build < 20 min, < 20k files, page < 1.5 MB) | | Dec 12 |
| [ ] | T14 | Branch protection + required `validate` check; `notes/routine.md` | enable in GitHub | Dec 13 |
| [ ] | T15 | Design pass, launch checklist, go live | final look | Dec 15 |

## Open notes
- `--tex` has not run anywhere yet (no XeLaTeX locally); the first CI run tests it.
- T7 pages are temporary (`site/templates/plain_*.html`); T8-T10 replace them and the old templates.
- T13: math HTML averages ~9 KB per problem, so a 500-row page is ~4 MB raw (~0.8 MB gzipped), over the
  1.5 MB raw target. Options then: split the page, or drop KaTeX MathML output (worse for screen readers).
- The T6 deploy must fail on any `"uploaded": false` entry in `figures.lock.json`.
- T6 must also attach astroolymp.com to the Pages project.
- Old PDFs stay in earlier git history (the repo appears private; owner to confirm).
- Local `content/figures/` is the only original copy besides R2: back it up.

## After the MVP
Games on their own subdomain, theory notes, study order, RU→EN translations, solutions, whole-bank filters.
