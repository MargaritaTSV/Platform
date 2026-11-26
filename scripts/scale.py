"""Scale test: build a copy of the site with synthetic problems and check the limits.

    python scripts/scale.py                 10000 problems
    python scripts/scale.py --count 200     quick run

Works in .build-cache/scale/ (gitignored), so content/ is never touched. Exits 1 if a limit is broken.
"""
import argparse
import itertools
import re
import shutil
import subprocess
import sys
import time

import validate
from validate import ROOT

WORK = ROOT / ".build-cache" / "scale"
MAX_SECONDS = 20 * 60
MAX_FILES = 20_000          # Cloudflare Pages free plan
MAX_PAGE = 1_500_000        # bytes, uncompressed
BIG_PAGE = 500              # rows in the fullest subtopic; the rest share the others evenly


def copy_repo():
    shutil.rmtree(WORK, ignore_errors=True)
    for folder in ("scripts", "site", "design", "latex", "overleaf", "node_modules/katex"):
        shutil.copytree(ROOT / folder, WORK / folder, ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "content").mkdir()
    for name in ("site.yml", "content/taxonomy.yml", "content/figures.lock.json"):
        shutil.copy(ROOT / name, WORK / name)


def write_problems(count):
    """Variants of the real problems, each with unique text so nothing comes from the cache."""
    templates = []
    for path in sorted(validate.PROBLEMS.rglob("*.tex")):
        header, _, body, _ = validate.split_header(path.read_text(encoding="utf-8-sig").replace("\r\n", "\n"))
        if header.get("translation_status") == "original":
            templates.append((header, body.strip()))
    topics, _ = validate.load_taxonomy()
    subtopics = [(topic, sub) for topic, subs in topics.items() for sub in sorted(subs)]
    big = min(BIG_PAGE, count)
    places = itertools.chain([subtopics[0]] * big, itertools.cycle(subtopics[1:]))
    for i, (header, body), (topic, sub) in zip(range(count), itertools.cycle(templates), places):
        pid = f"scale-{i:05}"
        new = dict(header, id=pid, topic=topic, subtopic=sub, difficulty=i % 3 + 1, year=2000 + i % 27)
        # A quoted title survives ':' and '#'.
        if "title" in new:
            new["title"] = f"'Задача {i}'"
        if "event" in new:
            new["event"] = f"'Этап {i % 5}'"
        lines = "".join(f"% {key}: {value}\n" for key, value in new.items())
        folder = WORK / "content" / "problems" / new["source"] / str(new["year"])
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{pid}.{new['lang']}.tex").write_text(
            f"% ---\n{lines}% ---\n{body}\n\n$N = {i}$\n", encoding="utf-8")


def build():
    start = time.perf_counter()
    run = subprocess.run([sys.executable, str(WORK / "scripts" / "build.py")])
    if run.returncode:
        sys.exit("scale: the build failed")
    return time.perf_counter() - start


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--count", type=int, default=10_000)
    args = parser.parse_args()
    copy_repo()
    write_problems(args.count)
    cold, warm = build(), build()

    dist = WORK / "site-dist"
    files = sum(1 for p in dist.rglob("*") if p.is_file())
    page = max(dist.rglob("*.html"), key=lambda p: p.stat().st_size)
    data = page.read_bytes()
    rows = len(re.findall(rb'class="problem-item"', data))
    print(f"\ncold build {cold:.0f} s, cached build {warm:.0f} s")
    # No gzip figure: the synthetic text repeats, so it would compress far better than real problems.
    print(f"largest page {page.parent.relative_to(dist).as_posix()}: {rows} rows, {len(data) / 1e6:.2f} MB "
          f"({len(data) // max(rows, 1)} bytes per row)")
    broken = 0
    for name, value, limit in (("build seconds", round(cold), MAX_SECONDS), ("files", files, MAX_FILES),
                               ("largest page, bytes", len(data), MAX_PAGE)):
        broken += value >= limit
        print(f"{'ok  ' if value < limit else 'OVER'} {name}: {value} (limit {limit})")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
