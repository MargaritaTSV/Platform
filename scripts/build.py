"""Build the static site into site-dist/.

    python scripts/build.py            build
    python scripts/build.py --serve    build, then serve on http://localhost:8000

Needs Python (jinja2, pyyaml), pandoc, Node and `npm ci` (KaTeX).
"""
import argparse
import functools
import shutil
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import yaml
from jinja2 import Environment, FileSystemLoader

import render
import validate
from validate import PROBLEMS, ROOT

DIST = ROOT / "site-dist"
CACHE = ROOT / ".build-cache" / "html"
ALT = {"ru": "Рисунок к задаче", "en": "Figure for the problem"}


def load_yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_problems():
    """The original-language variant of every problem (MVP shows no translations or solutions)."""
    problems = []
    for path in sorted(PROBLEMS.rglob("*.tex")):
        text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        header, _, body, _ = validate.split_header(text)
        if header.get("translation_status") != "original" or header.get("kind") == "solution":
            continue
        low, _, high = str(header["grade"]).partition("-")
        problems.append(dict(header, grade_low=int(low), grade_high=int(high or low), path=path, body=body))
    problems.sort(key=lambda p: (-p["year"], p["source"], p["id"]))
    return problems


def build():
    errors = validate.check_all()
    if errors:
        validate.report(errors)
        sys.exit(1)
    site = load_yaml(ROOT / "site.yml")
    taxonomy = load_yaml(ROOT / "content" / "taxonomy.yml")
    lock = validate.load_lock()
    problems = load_problems()

    html, failed, rendered = render.render_many({p["id"]: p["body"] for p in problems}, CACHE)
    if failed:
        paths = {p["id"]: p["path"] for p in problems}
        validate.report([(paths[pid], 1, message) for pid, message in sorted(failed.items())])
        sys.exit(1)
    for p in problems:
        p["html"] = render.rewrite_images(html[p["id"]], lock, site["media_url"], ALT[p["lang"]])

    shutil.rmtree(DIST, ignore_errors=True)
    (DIST / "static").mkdir(parents=True)
    shutil.copy(ROOT / "design" / "tokens.css", DIST / "static")
    shutil.copy(ROOT / "site" / "static" / "statement.css", DIST / "static")
    shutil.copy(render.KATEX / "dist" / "katex.min.css", DIST / "static")
    shutil.copytree(render.KATEX / "dist" / "fonts", DIST / "static" / "fonts")

    env = Environment(loader=FileSystemLoader(ROOT / "site" / "templates"), autoescape=True)
    sources = {s["key"]: s["name"] for s in taxonomy["sources"]}

    def page(url, template, **data):
        target = DIST / url / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(env.get_template(template).render(site=site, **data), encoding="utf-8")

    counts = {}
    for topic in taxonomy["topics"]:
        for sub in topic["subtopics"]:
            rows = [p for p in problems if (p["topic"], p["subtopic"]) == (topic["key"], sub["key"])]
            counts[topic["key"], sub["key"]] = len(rows)
            page(f"problems/{topic['key']}/{sub['key']}", "plain_subtopic.html",
                 topic=topic, subtopic=sub, problems=rows, sources=sources)
    page("", "plain_home.html", topics=taxonomy["topics"], counts=counts)
    print(f"build: {len(problems)} problems ({rendered} rendered, {len(problems) - rendered} cached) -> {DIST.name}/")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    build()
    if args.serve:
        handler = functools.partial(SimpleHTTPRequestHandler, directory=DIST)
        print(f"serving http://localhost:{args.port} (Ctrl+C to stop)")
        ThreadingHTTPServer(("127.0.0.1", args.port), handler).serve_forever()


if __name__ == "__main__":
    main()
