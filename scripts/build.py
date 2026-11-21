#!/usr/bin/env python3
"""
StellarTask build script.

Turns `content/` + `site/` + `design/` + `games/` into the static site in
`site-dist/`, ready to be served by GitHub Pages (or locally with --serve).

Milestone 1 ("skeleton live") scope only:
  - parse content/taxonomy.yml and content/games.yml
  - load site/i18n/{en,ru}.json
  - render site/templates/home.html once per language
  - copy static assets (site/static/, design/tokens.css, design/svg/)
  - copy games/ (if present)
  - write site-dist/CNAME and site-dist/.nojekyll

Milestone 2 will add: problem-file validation, Typst -> SVG compilation,
PDF/photo scan processing, content-hash caching, and data/index.json
generation. Those stages are stubbed out below (see the "Milestone 2"
section) so this file stays the single entry point for the whole pipeline.

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
# Output helpers
# ---------------------------------------------------------------------------

def clean_dist() -> None:
    """Remove and recreate site-dist/ so every build is reproducible."""
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)


def render_pages(env: Environment, taxonomy: dict, games: list) -> list[Path]:
    """Render site/templates/home.html once per language.

    EN is written to both site-dist/index.html (site default) and
    site-dist/en/index.html. RU is written to site-dist/ru/index.html.
    """
    template_name = "home.html"
    template_path = TEMPLATES_DIR / template_name
    if not template_path.is_file():
        raise BuildError(
            f"missing required template: {template_path.relative_to(REPO_ROOT)}"
        )

    template = env.get_template(template_name)
    written: list[Path] = []

    for lang in LANGUAGES:
        t = load_i18n(lang)
        html = template.render(lang=lang, t=t, taxonomy=taxonomy, games=games)

        targets = [DIST_DIR / lang / "index.html"]
        if lang == DEFAULT_LANGUAGE:
            targets.append(DIST_DIR / "index.html")

        for target in targets:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(html, encoding="utf-8")
            written.append(target)

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


def write_meta_files() -> list[Path]:
    """Write site-dist/CNAME and site-dist/.nojekyll."""
    cname_path = DIST_DIR / "CNAME"
    cname_path.write_text(CNAME_DOMAIN + "\n", encoding="utf-8")

    nojekyll_path = DIST_DIR / ".nojekyll"
    nojekyll_path.write_text("", encoding="utf-8")

    return [cname_path, nojekyll_path]


# ---------------------------------------------------------------------------
# Milestone 2 (not implemented yet) - stages that will plug in here:
#
#   validate_problems()      - required fields, known area/subtopic,
#                               difficulty 1..5, statement or scan, unique IDs
#   compile_typst_to_svg()   - Typst -> SVG with bundled fonts
#   process_scans()          - pdftoppm + crop + WebP conversion
#   load_content_hash_cache() / save_content_hash_cache()
#   build_search_index()     - MiniSearch index per language
#   write_index_json()       - data/index.json per the documented shape
#   render_problem_pages()   - /topics/<area>/, /problems/<id>/, /notes/<slug>/
#
# They are intentionally not called from main() yet.
# ---------------------------------------------------------------------------


def build() -> None:
    print(f"StellarTask build starting (repo root: {REPO_ROOT})")

    clean_dist()
    print(f"  cleaned {DIST_DIR.relative_to(REPO_ROOT)}/")

    taxonomy = load_taxonomy()
    print(f"  loaded {TAXONOMY_FILE.relative_to(REPO_ROOT)} ({len(taxonomy.get('areas', []))} areas)")

    games = load_games()
    print(f"  loaded {GAMES_FILE.relative_to(REPO_ROOT)} ({len(games)} games)")

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    written_pages = render_pages(env, taxonomy, games)
    for page in written_pages:
        print(f"  wrote {page.relative_to(REPO_ROOT)}")

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
