"""Build the static site into site-dist/.

    python scripts/build.py            build
    python scripts/build.py --serve    build, then serve on http://localhost:8000

Needs Python (requirements.txt), pandoc, Node and `npm ci` (KaTeX).
"""
import argparse
import functools
import json
import shutil
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

import render
import search
import validate
from validate import PROBLEMS, ROOT

DIST = ROOT / "site-dist"
CACHE = ROOT / ".build-cache" / "html"
ALT = {"ru": "Рисунок к задаче", "en": "Figure for the problem"}


def load_yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_ui():
    """Interface strings as {key: {ru, en}}. Both languages must have the same keys."""
    ru, en = (json.loads((ROOT / "site" / "i18n" / f"{lang}.json").read_text(encoding="utf-8")) for lang in ("ru", "en"))
    if ru.keys() != en.keys():
        sys.exit(f"build: site/i18n keys differ between ru and en: {', '.join(sorted(ru.keys() ^ en.keys()))}")
    return {key: {"ru": ru[key], "en": en[key]} for key in ru}


def check_names(taxonomy):
    """Everything shown in the interface needs both languages."""
    missing = []
    for topic in taxonomy["topics"]:
        for item in [topic, *topic["subtopics"]]:
            for field in ("name", "description"):
                if not all(item.get(field, {}).get(lang) for lang in ("ru", "en")):
                    missing.append(f"{item['key']}.{field}")
    if missing:
        sys.exit(f"build: taxonomy.yml needs ru and en text for: {', '.join(missing)}")


def filter_choices(rows, ui, sources):
    """The filters of one page, offering only values that occur on it."""
    def same(values):
        return [(v, {"ru": v, "en": v}) for v in values]

    grades = sorted({g for p in rows for g in range(p["grade_low"], p["grade_high"] + 1)})
    return [
        {"name": "difficulty", "label": ui["difficulty"], "any": ui["any_f"],
         "options": same(sorted({p["difficulty"] for p in rows}))},
        {"name": "source", "label": ui["source"], "any": ui["any_m"],
         "options": [(key, name) for key, name in sources.items() if any(p["source"] == key for p in rows)]},
        {"name": "year", "label": ui["year"], "any": ui["any_m"],
         "options": same(sorted({p["year"] for p in rows}, reverse=True))},
        {"name": "grade", "label": ui["grade"], "any": ui["any_m"], "options": same(grades)},
    ]


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


def build(deploy=False):
    errors = validate.check_all()
    if errors:
        validate.report(errors)
        sys.exit(1)
    site = load_yaml(ROOT / "site.yml")
    taxonomy = load_yaml(ROOT / "content" / "taxonomy.yml")
    lock = validate.load_lock()
    waiting = [name for name, info in lock.items() if not info.get("uploaded")]
    if deploy and waiting:
        sys.exit(f"build: figures not uploaded to R2 (run scripts/figures.py push): {', '.join(waiting)}")
    problems = load_problems()

    html, failed, rendered = render.render_many({p["id"]: p["body"] for p in problems}, CACHE)
    if failed:
        paths = {p["id"]: p["path"] for p in problems}
        validate.report([(paths[pid], 1, message) for pid, message in sorted(failed.items())])
        sys.exit(1)
    for p in problems:
        p["html"] = render.rewrite_images(html[p["id"]], lock, site["media_url"], ALT[p["lang"]])

    shutil.rmtree(DIST, ignore_errors=True)
    static = DIST / "static"
    (static / "js").mkdir(parents=True)
    (static / "svg").mkdir()
    for source, folder in (
        ("design/tokens.css", ""), ("site/static/app.css", ""), ("site/static/statement.css", ""),
        ("site/static/js/ui.js", "js"), ("site/static/js/map.js", "js"), ("site/static/js/filters.js", "js"),
        ("site/static/js/search.js", "js"),
        ("design/svg/logo_star.svg", "svg"),
    ):
        shutil.copy(ROOT / source, static / folder)
    shutil.copy(render.KATEX / "dist" / "katex.min.css", static)
    shutil.copytree(render.KATEX / "dist" / "fonts", static / "fonts")

    env = Environment(loader=FileSystemLoader(ROOT / "site" / "templates"), autoescape=True,
                      undefined=StrictUndefined)
    sources = {s["key"]: s["name"] for s in taxonomy["sources"]}
    ui = load_ui()

    def page(url, template, title, tab="problems", **data):
        target = DIST / url if url.endswith(".html") else DIST / url / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        html = env.get_template(template).render(site=site, ui=ui, title=title, tab=tab, **data)
        target.write_text(html, encoding="utf-8")

    check_names(taxonomy)
    def rows_of(topic, sub):
        return [p for p in problems if (p["topic"], p["subtopic"]) == (topic["key"], sub["key"])]

    topics = taxonomy["topics"]
    counts = {(t["key"], s["key"]): len(rows_of(t, s)) for t in topics for s in t["subtopics"]}
    topic_counts = {t["key"]: sum(counts[t["key"], s["key"]] for s in t["subtopics"]) for t in topics}
    # "Other topics" opens the first subtopic that has problems.
    first_subtopic = {t["key"]: next((s["key"] for s in t["subtopics"] if counts[t["key"], s["key"]]),
                                     t["subtopics"][0]["key"]) for t in topics}
    for topic in topics:
        for sub in topic["subtopics"]:
            rows = rows_of(topic, sub)
            page(f"problems/{topic['key']}/{sub['key']}", "subtopic.html", sub["name"],
                 topics=topics, topic=topic, subtopic=sub, problems=rows, sources=sources, counts=counts,
                 first_subtopic=first_subtopic, filters=filter_choices(rows, ui, sources))
    page("", "home.html", ui["tagline"], topics=taxonomy["topics"], counts=counts, topic_counts=topic_counts)
    page("notes", "notes.html", ui["notes_heading"], tab="notes")
    # Without a 404 page, Cloudflare Pages answers every unknown address with the home page.
    page("404.html", "404.html", ui["not_found"])
    search.write_index(problems, topics, sources, DIST / "pagefind")
    print(f"build: {len(problems)} problems ({rendered} rendered, {len(problems) - rendered} cached) -> {DIST.name}/")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--deploy", action="store_true", help="also require every figure to be on R2")
    args = parser.parse_args()
    build(args.deploy)
    if args.serve:
        handler = functools.partial(SimpleHTTPRequestHandler, directory=DIST)
        print(f"serving http://localhost:{args.port} (Ctrl+C to stop)")
        ThreadingHTTPServer(("127.0.0.1", args.port), handler).serve_forever()


if __name__ == "__main__":
    main()
