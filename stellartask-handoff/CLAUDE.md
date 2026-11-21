# StellarTask

A free, bilingual (RU/EN) static website of astronomy olympiad problems. The home page is a hand-drawn star map: each star is a topic area; choosing one shows its subtopics under the map; each subtopic opens a filterable problem list. Two astronomy games are hosted on the same site.

Full spec: `docs/spec.md`. Visual reference: `design/` (see "Design" below).

## Hard constraints

- No server, no database server. Hosting is GitHub Pages; all build work runs in GitHub Actions.
- Plain HTML, CSS and JavaScript. No frontend framework, no npm build step for the site.
- One Python build script (`scripts/build.py`) turns `content/` into the site.
- Must stay fast with up to ~2,000 problems.
- Every interface string exists in RU and EN.

## MVP scope

In: star-map home page with the topic block, area problem pages with subtopic rail and filters, search, RU/EN switch, problems from Typst / photo / PDF sources, basic theory note pages, two hosted games, Pages CMS editing.

Out (phase 2 or later): sheet of chosen problems, PDF output, `.typ` download, shareable sheet links, solutions, accounts, analytics, dark theme. Do not build these.

## Repository layout

```
content/
  taxonomy.yml        # areas (stars) -> subtopics; olympiads. RU/EN names. DRAFT, owner will replace.
  games.yml           # game cards
  problems/<id>.yml   # one file per problem
  notes/<slug>.yml    # theory notes
  media/              # photos, PDFs, pictures used in statements
templates/problem.typ # Typst wrapper for one problem
fonts/                # bundled fonts (Cyrillic)
games/<name>/         # built static files of each game
site/                 # HTML templates (Jinja2), CSS, JS
scripts/build.py      # the build
design/               # design reference, tokens, SVG drawings, map data (read-only input)
docs/spec.md          # full specification
.pages.yml            # Pages CMS config
```

## Data contracts (do not change without updating this file)

### Problem file `content/problems/<id>.yml`

```yaml
area: celestial-mechanics        # required, area key from taxonomy.yml
subtopic: keplers-laws           # required, must belong to that area
difficulty: 3                    # required, 1..5
olympiad: iao                    # optional, taxonomy key
year: 2024                       # optional
grade: senior                    # optional string
round: theory                    # optional
number: "3"                      # optional string
statement:                       # Typst source per language (one or both)
  en: |
    ...
  ru: |
    ...
# OR, for photo / PDF problems instead of `statement`:
scan: { file: /media/x.pdf, page: 2, crop: [x, y, w, h], lang: ru }
search_text: { ru: "...", en: "..." }   # recommended for scans
draft: false
```

The file name (without `.yml`) is the permanent problem ID.

### Build output `site-dist/data/index.json`

```json
{
  "generated": "ISO timestamp",
  "areas": [
    { "key": "celestial-mechanics", "name": {"en": "", "ru": ""}, "description": {"en": "", "ru": ""},
      "star": {"x": 110, "y": 300, "size": 26, "filled": true}, "count": 0,
      "subtopics": [ { "key": "keplers-laws", "name": {"en": "", "ru": ""}, "description": {"en": "", "ru": ""}, "count": 0 } ] }
  ],
  "problems": [
    { "id": "iao-2024-t03", "area": "celestial-mechanics", "subtopic": "keplers-laws", "difficulty": 3,
      "olympiad": "iao", "year": 2024, "grade": "senior", "round": "theory", "number": "3",
      "languages": ["ru", "en"], "format": "typst",
      "assets": { "en": "/p/iao-2024-t03.en.svg", "ru": "/p/iao-2024-t03.ru.svg" },
      "search": { "en": "plain text", "ru": "plain text" } }
  ]
}
```

The build writes this file; the frontend only reads it. Builders working in parallel must both follow this shape.

## Build pipeline (`scripts/build.py`)

1. Validate every problem file (required fields, known area, subtopic inside its area, difficulty 1..5, statement or scan present, unique IDs). Any error fails the build with a clear message.
2. Compile Typst statements to SVG (`#set page(width: 16cm, height: auto)`), using bundled fonts.
3. Render PDF scans with `pdftoppm`, crop, convert photos and renders to WebP (max 1600 px wide).
4. Cache by content hash; rebuild only changed problems.
5. Write `data/index.json` and a MiniSearch index per language.
6. Render static HTML pages from `site/` templates; copy `games/`.
7. Deploy with `actions/deploy-pages`.

`python scripts/build.py --serve` builds and serves locally.

## Pages

| Page | URL | Content |
|---|---|---|
| Home | `/` (`/en/`) | Logo, star map of 8 areas, topic block for the selected area under the map, games, footer |
| Area problem list | `/topics/<area>/` | Subtopic rail (left), filter sentence, search, one problem per row. `?sub=` preselects subtopics |
| Single problem | `/problems/<id>/` | One problem, metadata, previous/next |
| Note | `/notes/<slug>/` | Theory note |
| Game | `/games/<name>/` | The game, full screen |

Home behaviour: the first area is selected on load; clicking a star circles it (drawn ring, italic label) and swaps the topic block (area name, description, subtopic rows with counts). Every subtopic row and "All problems in this topic" link to the area page. Filter state lives in the URL query.

## Design (must follow)

Reference: `design/reference/home.dc.html` and `design/reference/problems.dc.html`. They are written for a design canvas runtime and will not run as-is: read them for layout, sizes and spacing, then rebuild cleanly. Live view: https://claude.ai/artifact/U4McF4YZ1TiM1YMGkM7qYC (page "StellarTask flow", version 1).

- Ink on white, minimal and spacious. Tokens in `design/tokens.css` / `design/tokens.json`; use them, do not invent new colours.
- Colours: bg `#FDFCFA`, text `#161616`, secondary `#6F6B64`, rules `#BDB7AB`, hover `#3B6E99`. Nothing else.
- Fonts: Cormorant Garamond (titles, area/subtopic names, problem statements), Onest (interface), JetBrains Mono (labels, counts, sources). No handwritten fonts.
- **No straight lines.** Every divider, border, rule and connector is a drawn SVG path (see `design/svg/`). Never CSS borders, `<hr>` or straight `<line>`s for decoration.
- One problem per row, full width. Large serif number on the left, difficulty stars under it.
- Map: positions and line paths in `design/map.json`; drawn stars in `design/svg/`.
- Phones: the map becomes a vertical list of stars; the subtopic rail folds above the list.
- Accessibility: real `<button>`/`<a>`, visible focus, contrast WCAG AA, `aria-pressed` on toggles.

## Milestones

1. Skeleton live: repo, Actions deploy, domain + HTTPS, header/footer, both games under `/games/`.
2. Content pipeline: taxonomy, problem format, build with validation, Typst to SVG, scans, `index.json`, 20 sample problems in 2+ areas.
3. Home page: star map, switching topic block, games.
4. Problem lists: area pages, subtopic rail, filters, search, URL state, RU/EN.
5. Authoring and launch: Pages CMS, bulk import script, notes, real content.

Work one milestone at a time. Finish with a short report of what is done and what is open.

## Working rules for agents

- Plan each milestone in plan mode first; split work between `pipeline-builder` and `frontend-builder`; run `design-reviewer` after UI changes and `content-checker` after content changes.
- Never change the data contracts above silently; propose the change first.
- Keep `content/taxonomy.yml` keys stable once problems use them.
- Do not commit secrets, solutions or private material; the repo is public.
