# StellarTask: Technical Specification

> Exported from the design artifact (`claude.ai/artifact/X4917SAgKYrmikJGqpACPa`) so the repository is self-contained. Keep `CLAUDE.md` as the short operational rules; this file is the full reference.

## Overview

StellarTask is a free, bilingual (RU/EN) static website of astronomy olympiad problems and theory notes. The home page is a hand-drawn star map: each star is a topic area, and choosing one shows its subtopics right under the map. Each subtopic opens a filterable problem list. The home page also links to two astronomy games hosted on the same site.

**Hard constraints**

- No paid server and no database server. Hosting is GitHub Pages; all build work runs in free GitHub Actions.
- Served on Starsy's own domain via a CNAME record.
- A single author (Starsy) adds content, through a comfortable editor rather than raw Git.
- Must scale from hundreds of problems at launch to a few thousand.

**Users**

- Olympiad students: browse by topic and difficulty, solve.
- Teachers and coaches: find problems by topic for lessons and camps (printable sheets come in phase 2).

**Out of scope for now:** the sheet and PDF of chosen problems (phase 2), user accounts, published solutions, progress tracking, analytics, comments, `.typ` downloads.

## Scope

The MVP is the star map, topic lists, problem lists and game links; the sheet and PDF move to phase 2.

| Feature | MVP | Phase 2 | Later |
|---|---|---|---|
| Star-map home page: 8 topic areas, subtopic list opens under the map | Yes | | |
| Problem list per area with subtopic rail and filters (difficulty, olympiad, year, grade, language) | Yes | | |
| Full-text search | Yes | | |
| RU/EN interface | Yes | | |
| Problems in Typst, photo and PDF sources | Yes | Gradual transcription to Typst | |
| Theory notes | Basic pages | Linked from each subtopic | |
| Two games hosted on the site, shown under the topic list | Yes | | |
| Authoring editor | Yes | Live Typst preview | |
| Sheet of chosen problems and PDF | | Yes | |
| Shareable sheet link, `.typ` download | | Yes | |
| Solutions behind a "Show" button | | | Yes |
| Progress tracking, analytics | | | Maybe |

## Architecture

The Git repository is the database, GitHub Actions is the only place code runs on GitHub's side, and the visitor's browser does the star map, filtering and search.

A save in the editor becomes a commit, the commit triggers a rebuild, and the new static site is live a few minutes later. Nothing runs between visits, so there is nothing to pay for or keep online.

## Content model

Each problem is one YAML file holding its metadata and its statement; photos, PDFs and pictures sit in a shared media folder. The file name is the problem's permanent ID. One file per problem is the shape the editor handles best.

**Repository layout**

```
content/
  taxonomy.yml            # areas (stars) with their subtopics, olympiads, grades; RU/EN names
  games.yml               # game cards for the home page
  problems/
    iao-2024-t03.yml      # one file per problem
  notes/
    keplers-laws.yml      # one file per theory note
  media/                  # photos, PDFs, pictures used in statements
templates/
  problem.typ             # shared look for problem display
fonts/                    # bundled fonts with Cyrillic
games/
  constellation-game/     # built static files of each game
  constellation-finder/
site/                     # the frontend
scripts/build.py          # the build pipeline
.pages.yml                # editor configuration
```

**Example problem file**

```yaml
# content/problems/iao-2024-t03.yml
area: celestial-mechanics
subtopic: keplers-laws
difficulty: 3
olympiad: iao
year: 2024
grade: senior
round: theory
number: "3"
statement:            # Typst source, one field per language
  en: |
    A visual binary has period $P = 20$ yr and angular semi-major axis ...
    #image("/media/iao-2024-t03-orbit.png", width: 60%)
  ru: |
    ...
# for a photo or PDF problem, use scan instead of statement:
# scan:
#   file: /media/iao-2024-t03.pdf
#   page: 2
#   lang: en
# search_text:
#   en: visual binary period mass parallax
```

**Problem fields**

| Field | Type | Required | Example |
|---|---|---|---|
| `id` | string, = file name | Yes | `iao-2024-t03` |
| `area` | key of a star in `taxonomy.yml` | Yes | `celestial-mechanics` |
| `subtopic` | key of a subtopic inside that area | Yes | `keplers-laws` |
| `difficulty` | integer 1 to 5 | Yes | `3` |
| `olympiad` | taxonomy key | No | `iao` |
| `year` | integer | No | `2024` |
| `grade` | string (grade or age group) | No | `"10"`, `"senior"` |
| `round` | string | No | `theory`, `final` |
| `number` | string | No | `"3"` |
| `languages` | list | Derived by the build from the statement fields | `[ru, en]` |
| `format` | `typst` / `image` / `pdf` | Derived | `typst` |
| `scan` | file, page, crop, language | Only for photo and PDF problems | `page: 2` |
| `search_text` | short plain text per language | Recommended for scans | Lets photo problems be found by search |
| `draft` | boolean | No, default false | Drafts are not published |

**Topic structure (`content/taxonomy.yml`).** Two levels: areas (the stars on the map) contain subtopics. The build rejects a problem whose subtopic is not inside its area. The map position of each star lives here too.

```yaml
areas:
  - key: celestial-mechanics
    name: { en: Celestial mechanics, ru: Небесная механика }
    description: { en: "How bodies move under gravity", ru: "..." }
    star: { x: 110, y: 300, size: 26, filled: true }
    subtopics:
      - key: keplers-laws
        name: { en: "Kepler's laws", ru: "Законы Кеплера" }
        description: { en: "Periods, semi-major axes, areal velocity", ru: "..." }
```

**Statement formats**

- **Typst (preferred).** Compiled to SVG for the site (and reused for PDFs in phase 2). Fully searchable.
- **Photo.** Shown as an image; the build compresses it to WebP. Searchable only through `search_text`.
- **PDF.** The build renders the given page (and crop) to an image, then treats it like a photo.
- Photo and PDF problems carry a "scan" badge, so they can be transcribed to Typst over time without changing their ID.

**Languages.** A problem may exist in RU, EN or both. The site shows the interface language version first and falls back to the other with a language badge. A filter can hide problems not available in the chosen language.

**Theory notes.** Same one-file pattern under `content/notes/`, with `title`, `area`, optional `subtopic` and the Typst body. Each area's topic block links to its notes.

**Solutions (later).** Anything committed to a public repo is readable by anyone, even if the site hides it. Solutions should therefore live in a separate private repo that the build pulls in only once publishing them is decided.

## Build pipeline

One Python script (`scripts/build.py`) turns `content/` into a ready site in under 5 minutes, run by GitHub Actions on every push to `main`.

1. **Validate.** Check every problem file against a schema: required fields, known taxonomy keys, difficulty 1 to 5, at least one statement file, unique IDs. Any error fails the build, so a broken problem never goes live.
2. **Compile Typst problems.** Wrap each statement in `templates/problem.typ` and compile to SVG with the Typst CLI (`#set page(width: 16cm, height: auto)`). Fonts with Cyrillic support are bundled in the repo so output is identical everywhere.
3. **Process scans.** Render PDF pages with `pdftoppm`, apply the crop, convert photos and renders to WebP (max 1600 px wide).
4. **Incremental cache.** Store a hash of each problem file and its media; recompile only changed problems. Keeps builds fast at 2,000+ problems.
5. **Build the index.** Write `data/index.json`: per problem the ID, metadata, languages, format, asset paths and search text. About 300 bytes a problem, so 2,000 problems is roughly 600 KB, or about 100 KB gzipped.
6. **Build the search index.** Pre-build a MiniSearch index per language from Typst plain text and `search_text`.
7. **Copy and deploy.** Copy `site/`, the generated assets and `games/` into one folder and publish it with the official `actions/deploy-pages` action.

The same script runs locally (`python scripts/build.py --serve`) to preview before pushing.

## Pages and UX

The site has five page types, and everything starts from the star map on the home page.

| Page | URL | Contents |
|---|---|---|
| Home | `/` (`/en/`) | StellarTask logo, star map of the 8 areas, the selected area's subtopic list under the map, game cards at the bottom |
| Problem list | `/topics/<area>/` | All problems in one area: subtopic rail on the left, filter sentence on top, one problem per row; `?sub=` preselects subtopics |
| Single problem | `/problems/<id>/` | One problem, metadata, previous/next |
| Note | `/notes/<slug>/` | A theory note |
| Games | `/games/<name>/` | The game itself, full screen |

**Filters** (combine with AND; several values within one filter combine with OR):

- Subtopic (the area's subtopics in a rail on the left, each toggled on or off)
- Difficulty (range 1 to 5)
- Olympiad, year range, grade
- Language (RU, EN, any)
- Format (Typst only / include scans)
- Free-text search

Filter state lives in the URL query (`?sub=keplers-laws&diff=1-3`), so any filtered view can be bookmarked or sent. Results load 30 at a time as the user scrolls.

**Problem row:** large number, difficulty stars, subtopic label, typeset statement (SVG or image), source line ("IAO 2024, theory, problem 3"), language and scan badges. One problem per row, full width.

**Home page behaviour**

- The map shows 8 stars joined by hand-drawn lines; star size and fill vary for rhythm.
- Clicking a star circles it with a drawn ring and swaps the topic block under the map: area name, one-line description, subtopic rows with problem counts.
- The first area is open on load, so the block is never empty.
- Each subtopic row and "All problems in this topic" open the area's problem list.
- Games sit under the topic block, then the footer.

**Language switch:** RU/EN toggle in the header. Interface strings live in `site/i18n/ru.json` and `en.json`. The choice is remembered; the first visit follows the browser language.

## PDF generation (phase 2)

The MVP has no sheet, so PDF output moves to phase 2. When the sheet returns, the plan below applies.

**First step: print page**

- "Make PDF" opens `/sheet/`, which lays out the chosen problems with a print stylesheet: A4, title, numbered problems, optional source lines, page breaks between problems if chosen.
- Typst problems print as their SVG (vector, sharp at any zoom); scans print as images.
- The page calls `window.print()`; the user picks "Save as PDF". Works in all current browsers and needs no extra download.
- Downside: layout is close to, not identical to, Typst output, and the user sees the print dialog.

**Next step: real Typst PDF in the browser**

- Use [typst.ts](https://myriad-dreamin.github.io/typst.ts/cookery/get-started.html), the official Typst compiler built for the browser. It assembles `sheet.typ` from the selected problem sources and compiles it locally.
- Cost: the compiler is about 7.6 MB and the text fonts about 4.4 MB (gzipped). It loads only when "Make PDF" is first pressed, then stays cached.
- Scans are included as images in the Typst document.
- The same assembled `sheet.typ` (plus images, zipped) becomes the `.typ` download.

**Alternative considered:** pre-building a PDF for every fixed list in GitHub Actions. Rejected because sheets are built from dynamic filters, so there are no fixed lists to pre-build.

## Authoring tool

The MVP uses [Pages CMS](https://pagescms.org/docs/), a free, open-source editor for content stored in GitHub. It gives Starsy forms instead of Git. Phase 2 adds a custom editor page with live Typst preview.

**How Pages CMS fits.** A `.pages.yml` file in the repo describes the content types. Starsy signs in at app.pagescms.org with GitHub, fills in a form, and each save becomes a commit to the repo, which triggers the build. There is no separate CMS database for content.

**Problem form (configured in `.pages.yml`):**

- Dropdowns for area, subtopic, olympiad, grade, round (from the taxonomy); a number field for difficulty and year.
- Code fields for the Typst statement in RU and EN.
- File upload for a photo or PDF scan, plus page number and language.
- Image upload for pictures used inside a statement; the editor puts them in `content/media/`.
- A "draft" switch.
- The list view shows ID, area, subtopic, difficulty and year, and can be searched.

**Gaps and how they are covered:**

- No Typst preview in the form: the build's SVG output appears on the site 2 to 4 minutes after saving. For heavy editing, work locally in VS Code with the Tinymist Typst extension, which previews as you type.
- Bulk import: a script `scripts/import.py` turns a folder of photos or a multi-page PDF into draft problem files (one per page or crop), which Starsy then tags in the editor.

**Phase 2: custom editor at `/admin/`.** A page of the site itself that edits the repo through the GitHub API using a personal access token kept in the browser. It adds a side-by-side live Typst preview (typst.ts), a crop tool for scans and quick tagging of imported drafts. Still no server.

## Games hosting

ConstellationGame and ConstellationFinder are served from the same site at `/games/constellation-game/` and `/games/constellation-finder/`, linked from cards on the home page.

- Each game's **built** static files (HTML, JS, CSS, assets) go into `games/<name>/`. If a game has its own repo, a workflow step can build it and copy the output instead.
- Games must work with relative paths under their subfolder and need no server. Anything that needs one (a backend AI opponent, multiplayer, saved scores) must first move into the browser or be cut.
- Card data lives in `content/games.yml`: name and blurb in RU/EN, cover image, URL, optional "new" or "beta" tag. Adding a third game later means one more folder and one more entry.
- Games open full-screen with a small "back to platform" link and share the site's RU/EN choice where they support it.

## Frontend, design and non-functional requirements

The frontend is plain HTML, CSS and JavaScript with no framework. `build.py` renders a static HTML page for every problem, topic and note from Jinja2 templates, and small JS modules add the star map, filtering and search.

**Why static pages per problem:** each problem has a real URL that loads fast, can be shared, and is indexed by search engines. The site still works for reading if JavaScript fails.

**JS modules:** `map.js` (star map and topic block), `filters.js` (subtopic rail, filters, URL state), `search.js` (MiniSearch), `i18n.js`. No build tool beyond `build.py`.

**Design**

- **Direction: ink on white.** Minimal and spacious, with hand-drawn elements. Reference: version 1 on the StellarTask flow page of the [design canvas](https://claude.ai/artifact/U4McF4YZ1TiM1YMGkM7qYC).
- **No straight lines.** Every divider, border and connector is a drawn SVG path with a slight wobble; the selected star gets a drawn ring.
- **Colours:** background `#FDFCFA`, text `#161616`, secondary text `#6F6B64`, divider lines `#BDB7AB`, hover `#3B6E99`. No other colours in the MVP.
- **Fonts:** Cormorant Garamond (headings, area and subtopic names, problem statements), Onest (interface text), JetBrains Mono (labels, counts, sources). All three cover Cyrillic. No handwritten fonts.
- **Logo:** a drawn star (three overlapping outlines) with "StellarTask" in Cormorant italic, top-left.
- **Spacing:** generous; sections 72 to 96 px apart, content about 1100 px wide.
- **Dark theme:** not in the MVP.
- **Phones:** the map becomes a vertical list of stars; the subtopic rail folds above the problem list.
- **Domain:** a CNAME file in the published folder plus DNS records at Starsy's registrar (an A/AAAA set for an apex domain or a CNAME for a subdomain). Enforce HTTPS in the Pages settings.

**Non-functional requirements**

| Area | Requirement |
|---|---|
| Cost | 0 per month: GitHub Pages, Actions and Pages CMS free tiers; only the domain is paid |
| Performance | Catalogue interactive within 2 s on 4G; filtering 2,000 problems under 100 ms |
| Size | Published site under 1 GB, the GitHub Pages hard limit; scans compressed to WebP |
| Traffic | Under the 100 GB/month soft bandwidth limit; a CDN can be added later if exceeded |
| Build | Full build under 10 min (Pages deploys time out after 10 min); incremental builds under 3 min |
| Accessibility | Keyboard navigation, alt text for scans (from `search_text`), contrast WCAG AA |
| SEO | Static pages, `sitemap.xml`, hreflang RU/EN links, Open Graph previews |
| Repo | Public; no solutions or private material committed |

## Milestones

Five milestones take the project to a public MVP; each ends with something visible on the live site.

1. **Skeleton live.** Repo, GitHub Actions deploy, domain with HTTPS, StellarTask header and footer, both games playable under `/games/`. *Done when: the domain loads and both games run.*
2. **Content pipeline.** `taxonomy.yml` (areas and subtopics), the problem format, `build.py` with validation, Typst-to-SVG, scan processing and `index.json`. 20 sample problems across at least two areas. *Done when: a pushed problem appears in its area; a problem with a wrong subtopic fails the build.*
3. **Home page.** Star map, topic block that switches on click, game cards. *Done when: all 8 stars switch the block and every subtopic link opens the right list.*
4. **Problem lists.** Area pages with subtopic rail, filters, search, URL state, RU/EN switch. *Done when: any filter combination works on phone and desktop.*
5. **Authoring and launch.** Pages CMS configured, bulk import script, theory notes, the first few hundred problems, final design check. *Done when: Starsy adds a problem from the editor without touching Git, and it is live within 5 minutes.*

Phase 2 then adds the sheet with PDF output (Typst in the browser), `.typ` download, shareable sheet links and the custom `/admin/` editor.

## Open questions

These need Starsy's answer before or during milestone 1; each has a default the build can start with.

- **Areas and subtopics.** Replace the draft list in `content/taxonomy.yml` with the real one, with RU and EN names.
- **Games' tech.** Do both games run fully in the browser (including ConstellationGame's AI opponent)? What framework, and is there a build step? *Default: assume static builds.*
- **ConstellationFinder description** for its game card.
- **Domain.** Which domain, and the whole domain or a subdomain?
- **Difficulty scale.** What 1 to 5 means, e.g. 1 = regional junior, 5 = hardest international. Written on the site so ratings stay consistent.
- **Problem IDs.** Source-based (`iao-2024-t03`) or sequential (`A0412`)? Source-based reads better but problems without a source need a fallback.
- **Rights to republish.** Check terms for each olympiad's problems and for any book scans; always show the source line.
- **Default interface language** for visitors whose browser is neither RU nor EN. *Default: EN.*
- **Doodles.** The design uses simple drawn stars and lines; decide whether to keep them or redraw them by hand.
