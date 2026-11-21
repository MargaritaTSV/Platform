#!/usr/bin/env python3
"""
StellarTask build script.

Turns `content/` + `site/` + `design/` + `games/` into the static site in
`site-dist/`, ready to be served by GitHub Pages (or locally with --serve).

Scope implemented so far:
  - parse content/taxonomy.yml and content/games.yml
  - discover + validate content/problems/*.yml
  - write data/index.json (areas with counts, problem metadata, search text)
  - render the home page per language (with per-area problem counts)
  - render a topic (area) problem-list page per area, per language
  - render a single-problem page per problem, per language
  - copy static assets (site/static/, design/tokens.css, design/svg/)
  - copy games/ (if present)
  - write site-dist/CNAME and site-dist/.nojekyll

Still deferred to later milestones: real Typst -> SVG compilation (statements
are rendered as text for now), PDF/photo scan processing, content-hash
caching, the MiniSearch index, and the interactive filter/search UI.

Usage:
    python scripts/build.py            # build once, exit 0
    python scripts/build.py --serve    # build, then serve site-dist/ on
                                        # http://localhost:8000

Dependencies: Python 3, jinja2, pyyaml (standard library otherwise).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - friendly error for missing dep
    print(
        "ERROR: the 'pyyaml' package is required. Install it with:\n"
        "    pip install pyyaml",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:  # pragma: no cover - friendly error for missing dep
    print(
        "ERROR: the 'jinja2' package is required. Install it with:\n"
        "    pip install jinja2",
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Paths. Everything is resolved relative to the repository root, which is
# derived from this script's own location so the build works regardless of
# the caller's current working directory.
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent

CONTENT_DIR = REPO_ROOT / "content"
TAXONOMY_FILE = CONTENT_DIR / "taxonomy.yml"
GAMES_FILE = CONTENT_DIR / "games.yml"
PROBLEMS_DIR = CONTENT_DIR / "problems"

SITE_DIR = REPO_ROOT / "site"
TEMPLATES_DIR = SITE_DIR / "templates"
STATIC_DIR = SITE_DIR / "static"
I18N_DIR = SITE_DIR / "i18n"

DESIGN_DIR = REPO_ROOT / "design"
DESIGN_TOKENS_CSS = DESIGN_DIR / "tokens.css"
DESIGN_SVG_DIR = DESIGN_DIR / "svg"

GAMES_DIR = REPO_ROOT / "games"

DIST_DIR = REPO_ROOT / "site-dist"

LANGUAGES = ["en", "ru"]
DEFAULT_LANGUAGE = "en"
CNAME_DOMAIN = "tsvetkovaspace.com"


class BuildError(RuntimeError):
    """Raised for any build-stopping, user-facing error."""


# ---------------------------------------------------------------------------
# Loading content
# ---------------------------------------------------------------------------

def load_yaml(path: Path) -> dict:
    if not path.is_file():
        raise BuildError(f"missing required file: {path.relative_to(REPO_ROOT)}")
    with path.open("r", encoding="utf-8") as fh:
        try:
            data = yaml.safe_load(fh) or {}
        except yaml.YAMLError as exc:
            raise BuildError(
                f"{path.relative_to(REPO_ROOT)}: invalid YAML ({exc})"
            ) from exc
    return data


def load_taxonomy() -> dict:
    """Parse content/taxonomy.yml. Must contain an `areas` list."""
    data = load_yaml(TAXONOMY_FILE)
    if "areas" not in data or not isinstance(data["areas"], list):
        raise BuildError(
            f"{TAXONOMY_FILE.relative_to(REPO_ROOT)}: missing required field 'areas' (list)"
        )
    return data


def load_games() -> list:
    """Parse content/games.yml. Must contain a `games` list."""
    data = load_yaml(GAMES_FILE)
    games = data.get("games")
    if not isinstance(games, list):
        raise BuildError(
            f"{GAMES_FILE.relative_to(REPO_ROOT)}: missing required field 'games' (list)"
        )
    return games


def load_i18n(lang: str) -> dict:
    """Load site/i18n/<lang>.json. Fails clearly if the file is missing."""
    path = I18N_DIR / f"{lang}.json"
    if not path.is_file():
        raise BuildError(
            f"missing required i18n file: {path.relative_to(REPO_ROOT)} "
            f"(expected one JSON file of interface strings per language)"
        )
    with path.open("r", encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except json.JSONDecodeError as exc:
            raise BuildError(
                f"{path.relative_to(REPO_ROOT)}: invalid JSON ({exc})"
            ) from exc


# ---------------------------------------------------------------------------
# Problems: discovery + validation (a broken problem fails the whole build)
# ---------------------------------------------------------------------------

def taxonomy_maps(taxonomy: dict) -> dict:
    """Build lookup maps from the taxonomy for validation and rendering."""
    areas = {a["key"]: a for a in taxonomy["areas"]}
    subtopics = {
        a["key"]: {s["key"]: s for s in a.get("subtopics", [])}
        for a in taxonomy["areas"]
    }
    olympiads = {o["key"]: o for o in taxonomy.get("olympiads") or []}
    return {"areas": areas, "subtopics": subtopics, "olympiads": olympiads}


def discover_problems() -> list[dict]:
    """Read every content/problems/*.yml. The file stem is the permanent id."""
    if not PROBLEMS_DIR.is_dir():
        return []
    problems = []
    for path in sorted(PROBLEMS_DIR.glob("*.yml")):
        data = load_yaml(path)
        if not isinstance(data, dict):
            raise BuildError(f"{path.relative_to(REPO_ROOT)}: expected a YAML mapping")
        data["id"] = path.stem
        data["_path"] = path
        problems.append(data)
    return problems


def validate_problems(problems: list[dict], maps: dict) -> list[dict]:
    """Validate against the data contract; raise BuildError listing all issues.

    Drops drafts. Derives `languages` and `format`. Returns the publishable list.
    """
    errors: list[str] = []
    seen_ids: dict[str, Path] = {}
    published: list[dict] = []

    for p in problems:
        pid = p["id"]
        where = p["_path"].relative_to(REPO_ROOT)

        if pid in seen_ids:
            errors.append(f"duplicate problem id '{pid}' ({where})")
        seen_ids[pid] = where

        if p.get("draft") is True:
            continue

        area = p.get("area")
        subtopic = p.get("subtopic")
        difficulty = p.get("difficulty")

        if not area:
            errors.append(f"{where}: missing required field 'area'")
        elif area not in maps["areas"]:
            errors.append(f"{where}: unknown area '{area}'")
        elif not subtopic:
            errors.append(f"{where}: missing required field 'subtopic'")
        elif subtopic not in maps["subtopics"][area]:
            errors.append(
                f"{where}: subtopic '{subtopic}' is not in area '{area}'"
            )

        if difficulty is None:
            errors.append(f"{where}: missing required field 'difficulty'")
        elif not isinstance(difficulty, int) or not (1 <= difficulty <= 5):
            errors.append(f"{where}: difficulty must be an integer 1..5 (got {difficulty!r})")

        statement = p.get("statement")
        scan = p.get("scan")
        if not statement and not scan:
            errors.append(f"{where}: needs either a 'statement' or a 'scan'")

        olympiad = p.get("olympiad")
        if olympiad and olympiad not in maps["olympiads"]:
            errors.append(f"{where}: unknown olympiad '{olympiad}'")

        # Derive languages + format.
        if isinstance(statement, dict):
            p["languages"] = [l for l in LANGUAGES if statement.get(l)]
            p["format"] = "typst"
        elif scan:
            p["languages"] = [scan.get("lang")] if scan.get("lang") else []
            fmt = "pdf" if str(scan.get("file", "")).lower().endswith(".pdf") else "image"
            p["format"] = fmt
        else:
            p["languages"] = []
            p["format"] = "unknown"

        published.append(p)

    if errors:
        raise BuildError(
            "problem validation failed:\n  - " + "\n  - ".join(errors)
        )
    return published


# ---------------------------------------------------------------------------
# Derived views + index.json
# ---------------------------------------------------------------------------

def source_line(p: dict, maps: dict) -> str:
    """e.g. 'IAO 2023, theory, problem 1' from the available metadata."""
    parts = []
    olympiad = p.get("olympiad")
    if olympiad:
        parts.append(olympiad.upper())
    if p.get("year"):
        parts.append(str(p["year"]))
    head = " ".join(parts)
    tail = []
    if p.get("round"):
        tail.append(str(p["round"]))
    if p.get("number"):
        tail.append(f"problem {p['number']}")
    pieces = [x for x in [head, ", ".join(tail)] if x]
    return ", ".join(pieces)


def statement_text(p: dict, lang: str) -> dict:
    """Return the statement for `lang` with fallback info.

    { 'text': str|None, 'shown_lang': 'en'|'ru'|None, 'fallback': bool }
    """
    st = p.get("statement")
    if isinstance(st, dict):
        if st.get(lang):
            return {"text": st[lang].rstrip(), "shown_lang": lang, "fallback": False}
        for other in LANGUAGES:
            if st.get(other):
                return {"text": st[other].rstrip(), "shown_lang": other, "fallback": True}
    return {"text": None, "shown_lang": None, "fallback": False}


def problem_view(p: dict, maps: dict, lang: str) -> dict:
    """A flat dict of everything a template needs to render one problem."""
    area = maps["areas"][p["area"]]
    sub = maps["subtopics"][p["area"]][p["subtopic"]]
    return {
        "id": p["id"],
        "area_key": p["area"],
        "area_name": area["name"][lang],
        "subtopic_key": p["subtopic"],
        "subtopic_name": sub["name"][lang],
        "difficulty": p["difficulty"],
        "number": p.get("number"),
        "languages": p["languages"],
        "format": p["format"],
        "source": source_line(p, maps),
        "statement": statement_text(p, lang),
    }


def build_index(taxonomy: dict, problems: list[dict], maps: dict) -> dict:
    """Assemble data/index.json: areas with counts + per-problem metadata."""
    area_counts = {k: 0 for k in maps["areas"]}
    sub_counts = {k: {s: 0 for s in maps["subtopics"][k]} for k in maps["areas"]}
    for p in problems:
        area_counts[p["area"]] += 1
        sub_counts[p["area"]][p["subtopic"]] += 1

    areas_out = []
    for a in taxonomy["areas"]:
        areas_out.append({
            "key": a["key"],
            "name": a["name"],
            "description": a.get("description", {}),
            "star": a.get("star", {}),
            "count": area_counts[a["key"]],
            "subtopics": [
                {
                    "key": s["key"],
                    "name": s["name"],
                    "description": s.get("description", {}),
                    "count": sub_counts[a["key"]][s["key"]],
                }
                for s in a.get("subtopics", [])
            ],
        })

    problems_out = []
    for p in problems:
        st = p.get("statement") if isinstance(p.get("statement"), dict) else {}
        search = {
            l: (st.get(l) or "").replace("\n", " ").strip()
            for l in LANGUAGES if st.get(l)
        }
        problems_out.append({
            "id": p["id"],
            "area": p["area"],
            "subtopic": p["subtopic"],
            "difficulty": p["difficulty"],
            "olympiad": p.get("olympiad"),
            "year": p.get("year"),
            "grade": p.get("grade"),
            "round": p.get("round"),
            "number": p.get("number"),
            "languages": p["languages"],
            "format": p["format"],
            "search": search,
        })

    return {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "areas": areas_out,
        "problems": problems_out,
    }


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def clean_dist() -> None:
    """Remove and recreate site-dist/ so every build is reproducible."""
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)


def lang_prefix(lang: str) -> str:
    return "" if lang == DEFAULT_LANGUAGE else f"/{lang}"


def page_urls(suffix: str) -> dict:
    """URL of a page in each language. `suffix` is '' (home) or 'topics/x/' etc."""
    return {l: (lang_prefix(l) + "/" + suffix) for l in LANGUAGES}


def write_page(env: Environment, template_name: str, out_path: Path, **context) -> Path:
    tmpl = env.get_template(template_name)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(tmpl.render(**context), encoding="utf-8")
    return out_path


def render_site(env: Environment, taxonomy: dict, games: list,
                problems: list[dict], maps: dict, index: dict) -> list[Path]:
    """Render home, topic (area) and problem pages for every language."""
    written: list[Path] = []

    area_count = {a["key"]: a["count"] for a in index["areas"]}
    sub_count = {
        a["key"]: {s["key"]: s["count"] for s in a["subtopics"]}
        for a in index["areas"]
    }
    total_problems = len(problems)

    # Group problems by area, preserving a stable order.
    by_area: dict[str, list[dict]] = {a["key"]: [] for a in taxonomy["areas"]}
    for p in problems:
        by_area[p["area"]].append(p)

    for lang in LANGUAGES:
        t = load_i18n(lang)

        def common(suffix: str) -> dict:
            urls = page_urls(suffix)
            return {
                "lang": lang, "t": t,
                "url_en": urls["en"], "url_ru": urls["ru"],
                "lang_prefix": lang_prefix(lang),
            }

        # Home.
        home_ctx = dict(common(""), taxonomy=taxonomy, games=games,
                        area_count=area_count, total_problems=total_problems)
        targets = [DIST_DIR / lang_prefix(lang).lstrip("/") / "index.html"]
        if lang == DEFAULT_LANGUAGE:
            targets = [DIST_DIR / "index.html", DIST_DIR / "en" / "index.html"]
        for target in targets:
            written.append(write_page(env, "home.html", target, **home_ctx))

        # Topic (area) pages.
        for area in taxonomy["areas"]:
            views = [problem_view(p, maps, lang) for p in by_area[area["key"]]]
            ctx = dict(
                common(f"topics/{area['key']}/"),
                area={
                    "key": area["key"],
                    "name": area["name"][lang],
                    "description": (area.get("description") or {}).get(lang, ""),
                    "subtopics": [
                        {"key": s["key"], "name": s["name"][lang],
                         "count": sub_count[area["key"]][s["key"]]}
                        for s in area.get("subtopics", [])
                    ],
                },
                problems=views,
                area_count=area_count[area["key"]],
            )
            out = DIST_DIR / lang_prefix(lang).lstrip("/") / "topics" / area["key"] / "index.html"
            written.append(write_page(env, "area.html", out, **ctx))

        # Single-problem pages (prev/next within the same area).
        for area in taxonomy["areas"]:
            group = by_area[area["key"]]
            for i, p in enumerate(group):
                view = problem_view(p, maps, lang)
                prev_p = group[i - 1] if i > 0 else None
                next_p = group[i + 1] if i < len(group) - 1 else None
                ctx = dict(
                    common(f"problems/{p['id']}/"),
                    problem=view,
                    area_url=lang_prefix(lang) + f"/topics/{area['key']}/",
                    prev_url=(lang_prefix(lang) + f"/problems/{prev_p['id']}/") if prev_p else None,
                    next_url=(lang_prefix(lang) + f"/problems/{next_p['id']}/") if next_p else None,
                )
                out = DIST_DIR / lang_prefix(lang).lstrip("/") / "problems" / p["id"] / "index.html"
                written.append(write_page(env, "problem.html", out, **ctx))

    return written


def copy_static_assets() -> list[str]:
    """Copy site/static/, design/tokens.css and design/svg/ into site-dist/static/."""
    notes = []
    dest_static = DIST_DIR / "static"
    dest_static.mkdir(parents=True, exist_ok=True)

    if STATIC_DIR.is_dir():
        shutil.copytree(STATIC_DIR, dest_static, dirs_exist_ok=True)
        notes.append(f"copied {STATIC_DIR.relative_to(REPO_ROOT)} -> {dest_static.relative_to(REPO_ROOT)}")
    else:
        notes.append(f"note: {STATIC_DIR.relative_to(REPO_ROOT)} not found, skipped")

    if DESIGN_TOKENS_CSS.is_file():
        shutil.copy2(DESIGN_TOKENS_CSS, dest_static / "tokens.css")
        notes.append(f"copied {DESIGN_TOKENS_CSS.relative_to(REPO_ROOT)} -> {(dest_static / 'tokens.css').relative_to(REPO_ROOT)}")
    else:
        raise BuildError(
            f"missing required file: {DESIGN_TOKENS_CSS.relative_to(REPO_ROOT)}"
        )

    dest_svg = dest_static / "svg"
    if DESIGN_SVG_DIR.is_dir():
        dest_svg.mkdir(parents=True, exist_ok=True)
        shutil.copytree(DESIGN_SVG_DIR, dest_svg, dirs_exist_ok=True)
        notes.append(f"copied {DESIGN_SVG_DIR.relative_to(REPO_ROOT)} -> {dest_svg.relative_to(REPO_ROOT)}")
    else:
        raise BuildError(
            f"missing required directory: {DESIGN_SVG_DIR.relative_to(REPO_ROOT)}"
        )

    return notes


def copy_games() -> str:
    """Copy games/ -> site-dist/games/, if the games/ tree exists."""
    if not GAMES_DIR.is_dir():
        return f"note: {GAMES_DIR.relative_to(REPO_ROOT)} not found, skipped (no games built yet)"
    dest = DIST_DIR / "games"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copytree(GAMES_DIR, dest, dirs_exist_ok=True)
    return f"copied {GAMES_DIR.relative_to(REPO_ROOT)} -> {dest.relative_to(REPO_ROOT)}"


def write_index_json(index: dict) -> Path:
    out = DIST_DIR / "data" / "index.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def write_meta_files() -> list[Path]:
    """Write site-dist/CNAME and site-dist/.nojekyll."""
    cname_path = DIST_DIR / "CNAME"
    cname_path.write_text(CNAME_DOMAIN + "\n", encoding="utf-8")

    nojekyll_path = DIST_DIR / ".nojekyll"
    nojekyll_path.write_text("", encoding="utf-8")

    return [cname_path, nojekyll_path]


# ---------------------------------------------------------------------------
# Later milestones plug in here: Typst -> SVG, scan processing, content-hash
# caching, and the MiniSearch per-language index.
# ---------------------------------------------------------------------------


def build() -> None:
    print(f"StellarTask build starting (repo root: {REPO_ROOT})")

    clean_dist()
    print(f"  cleaned {DIST_DIR.relative_to(REPO_ROOT)}/")

    taxonomy = load_taxonomy()
    maps = taxonomy_maps(taxonomy)
    print(f"  loaded {TAXONOMY_FILE.relative_to(REPO_ROOT)} ({len(taxonomy.get('areas', []))} areas)")

    games = load_games()
    print(f"  loaded {GAMES_FILE.relative_to(REPO_ROOT)} ({len(games)} games)")

    problems = validate_problems(discover_problems(), maps)
    print(f"  validated {len(problems)} problem(s)")

    index = build_index(taxonomy, problems, maps)
    print(f"  wrote {write_index_json(index).relative_to(REPO_ROOT)}")

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    written_pages = render_site(env, taxonomy, games, problems, maps, index)
    print(f"  rendered {len(written_pages)} HTML page(s)")

    for note in copy_static_assets():
        print(f"  {note}")

    print(f"  {copy_games()}")

    for meta_path in write_meta_files():
        print(f"  wrote {meta_path.relative_to(REPO_ROOT)}")

    print("Build complete.")


def serve() -> None:
    import functools
    import http.server

    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(DIST_DIR)
    )
    addr = ("localhost", 8000)
    with http.server.HTTPServer(addr, handler) as httpd:
        print(f"Serving {DIST_DIR.relative_to(REPO_ROOT)} at http://{addr[0]}:{addr[1]}/ (Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the StellarTask static site.")
    parser.add_argument(
        "--serve",
        action="store_true",
        help="after building, serve site-dist/ on http://localhost:8000",
    )
    args = parser.parse_args()

    try:
        build()
    except BuildError as exc:
        print(f"BUILD FAILED: {exc}", file=sys.stderr)
        return 1

    if args.serve:
        serve()

    return 0


if __name__ == "__main__":
    sys.exit(main())
