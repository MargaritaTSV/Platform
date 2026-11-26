"""Problem body (LaTeX) -> HTML: pandoc, then KaTeX, cached per problem.

    python scripts/render.py      run the self-test
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MACROS = ROOT / "latex" / "macros.tex"
KATEX_SCRIPT = ROOT / "scripts" / "katex_render.mjs"
KATEX = ROOT / "node_modules" / "katex"
LIST_LABEL = re.compile(r"(\\begin\{enumerate\})[ \t]*\[label=\\(alph|arabic)\*\)\]")
IMAGE = re.compile(r'<img src="figures/([^"]+)"( style="[^"]*")?[^>]*/>')


def need(tool):
    return shutil.which(tool) or sys.exit(f"build: '{tool}' is not installed")


def pandoc_html(body, macros):
    # pandoc ignores enumitem's label=, but understands the enumerate-package form [a)].
    body = LIST_LABEL.sub(lambda m: f"{m[1]}[{'a' if m[2] == 'alph' else '1'})]", body)
    run = subprocess.run(
        [need("pandoc"), "--sandbox", "--fail-if-warnings", "-f", "latex", "-t", "html",
         "--math-method=katex", "--wrap=none"],
        input=f"{macros}\n{body}", capture_output=True, encoding="utf-8",
    )
    if run.returncode:
        raise ValueError(run.stderr.strip())
    return run.stdout


def katex_html(pages):
    run = subprocess.run(
        [need("node"), str(KATEX_SCRIPT)], input=json.dumps(pages), capture_output=True, encoding="utf-8", cwd=ROOT,
    )
    if run.returncode:
        sys.exit(f"build: KaTeX step failed:\n{run.stderr}")
    return json.loads(run.stdout)


def cache_salt(macros):
    """Changes whenever anything that affects the output changes."""
    if not KATEX.exists():
        sys.exit("build: KaTeX is missing, run `npm ci` first")
    pandoc = subprocess.run([need("pandoc"), "--version"], capture_output=True, encoding="utf-8").stdout.split("\n")[0]
    parts = [Path(__file__).read_text(encoding="utf-8"), KATEX_SCRIPT.read_text(encoding="utf-8"),
             (KATEX / "package.json").read_text(encoding="utf-8"), macros, pandoc]
    return "\0".join(parts)


def render_many(bodies, cache):
    """bodies: {key: LaTeX body}. Returns ({key: html}, {key: error}, number rendered)."""
    macros = MACROS.read_text(encoding="utf-8")
    salt = cache_salt(macros)
    cache.mkdir(parents=True, exist_ok=True)
    files = {k: cache / (hashlib.sha256(f"{salt}\0{b}".encode()).hexdigest() + ".html") for k, b in bodies.items()}
    done = {k: f.read_text(encoding="utf-8") for k, f in files.items() if f.exists()}
    todo = [k for k in bodies if k not in done]
    errors, pages = {}, {}

    def one(key):
        try:
            return key, pandoc_html(bodies[key], macros), None
        except ValueError as e:
            return key, None, f"pandoc: {e}"

    with ThreadPoolExecutor(os.cpu_count()) as pool:
        for key, html, error in pool.map(one, todo):
            if error:
                errors[key] = error
            else:
                pages[key] = html
    if pages:
        result = katex_html(pages)
        errors.update({k: f"KaTeX: {message}" for k, message in result["errors"].items()})
        for key, html in result["html"].items():
            files[key].write_text(html, encoding="utf-8")
            done[key] = html
    return done, errors, len(pages)


def rewrite_images(html, lock, media_url, alt):
    """Point figures at R2. Done on every build, so replacing a figure needs no re-render."""
    def image(m):
        info = lock[m[1]]
        # ?v= makes browsers and the CDN fetch a replaced figure.
        src = f"{media_url}/fig/{Path(m[1]).stem}.webp?v={info['sha256'][:8]}"
        return (f'<img src="{src}" width="{info["width"]}" height="{info["height"]}"{m[2] or ""} '
                f'alt="{alt}" loading="lazy">')
    return IMAGE.sub(image, html)


def selftest():
    body = "\n".join([
        r"Скорость $v = \qty{3}{км}$ и $a<b$.",
        r"\begin{enumerate}[label=\alph*)]",
        r"\item раз",
        r"\end{enumerate}",
        r"\includegraphics[width=0.5\linewidth]{figures/a.png}",
        r"\begin{align*} a &= 1 \\ b &= 2 \end{align*}",
    ])
    with tempfile.TemporaryDirectory() as tmp:
        bodies = {"ok": body, "macro": r"$\nosuchmacro$", "cyrillic": "$скорость$"}
        done, errors, count = render_many(bodies, Path(tmp))
        assert set(done) == {"ok"} and set(errors) == {"macro", "cyrillic"}, errors
        html = done["ok"]
        assert 'class="katex"' in html and "katex-display" in html and 'class="math' not in html
        assert '<ol type="a"' in html and "км" in html
        out = rewrite_images(html, {"a.png": {"sha256": "abcdef0123", "width": 10, "height": 5}}, "https://m", "alt")
        assert 'src="https://m/fig/a.webp?v=abcdef01"' in out and 'style="width:50.0%"' in out, out
        again = render_many({"ok": body}, Path(tmp))
        assert again[0]["ok"] == html and again[2] == 0, "second run must come from the cache"
    print("render selftest: ok")


if __name__ == "__main__":
    selftest()
