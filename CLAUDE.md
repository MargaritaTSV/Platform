# StellarTask

Static astronomy problem bank (RU/EN). Only the owner adds content.
**Read `notes/roadmap.md` first**: it says what is done and what is next. Update it when a task ends.
Decisions: `notes/decisions.md`. Adding problems: `notes/routine.md`. `docs/spec.md` is superseded.

## Rules
- Static only, no server, no database. Cloudflare Pages (site) + R2 (figures), deployed by GitHub Actions.
- Python + Jinja build, plain HTML/CSS/JS. No frontend framework. Node only for KaTeX pre-render and wrangler.
- Site name, domain and URLs live only in `site.yml`.
- New content reaches the live site only through a pull request that passes `validate`.
- Never commit other people's PDFs or solutions, figure originals, tool caches (`.wrangler/`) or secrets.
- Roadmap order, one small task at a time; commit after each.

## Folders
`content/taxonomy.yml` topics, subtopics, sources (keys are permanent) · `content/problems/<source>/<year>/` ·
`content/figures/` originals (gitignored) · `content/figures.lock.json` (committed) · `latex/` preamble + macros ·
`overleaf/` starter (copies of `latex/`) · `design/` read-only · `site/` templates · `scripts/` · `tests/`

## Content
- One problem per `<id>.<ru|en>.tex`: `% ---` YAML header, body only. Solutions: `<id>.sol.<lang>.tex` (not shown yet).
- Original file requires id, lang, translation_status, topic, subtopic, difficulty (1-3), source, year, grade;
  optional title, event, number, max_score. Translations: only id, lang, translation_status.
- Claude's translations are `machine-translated-needs-review` until the owner reviews them.
- Allowed LaTeX: see `overleaf/README.md`; `scripts/validate.py` enforces it. Macros are math-only.

## Design
Ink sketchbook from `design/` (tokens in `design/tokens.css`, no new colours), spacious, hand-drawn dividers,
never straight CSS borders or `<hr>`. No all-caps titles or UI text. Desktop only. RU default, RU/EN button;
problems show in their original language.

## Commands
- `python scripts/validate.py` (`--selftest`, `--tex [files]` needs XeLaTeX)
- `python scripts/figures.py push` (`--local` without R2), `python scripts/figures.py selftest`
- Deploy: merging into `main` publishes to Cloudflare Pages (`.github/workflows/deploy.yml`).
- `pip install -r requirements.txt` and `npm ci` once, then `python scripts/build.py --serve` (needs pandoc 3.14 and Node)
- `python scripts/render.py` (self-test of pandoc + KaTeX)
- `python scripts/scale.py` (10k synthetic problems, checks build time, file count, page size; ~10 min)
