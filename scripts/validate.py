"""Validate problem files. Prints `file:line: message` and exits 1 on any error.

    python scripts/validate.py              check the whole bank
    python scripts/validate.py --tex        also compile every problem with XeLaTeX
    python scripts/validate.py --tex a.tex  compile only these files (all are still checked)
    python scripts/validate.py --selftest   run the fixtures in tests/validator/

Unknown *math* macros are caught by --tex (and by KaTeX in the build), not by the static check.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PROBLEMS = ROOT / "content" / "problems"
FIGURES = ROOT / "content" / "figures"
LOCK = ROOT / "content" / "figures.lock.json"
TAXONOMY = ROOT / "content" / "taxonomy.yml"
FIXTURES = ROOT / "tests" / "validator"

LANGS = ("ru", "en")
STATUSES = ("original", "machine-translated-needs-review", "reviewed")
REQUIRED = ("id", "lang", "translation_status", "topic", "subtopic", "difficulty", "source", "year", "grade")
OPTIONAL = ("title", "event", "number", "max_score")
NAME_RE = re.compile(r"^(?P<id>[a-z0-9-]+)(?P<sol>\.sol)?\.(?P<lang>ru|en)\.tex$")

TEXT_COMMANDS = {
    "textbf", "emph", "textit", "par", "medskip", "smallskip", "bigskip", "noindent",
    "item", "multicolumn", "linewidth", "hline",
}
TEXT_SYMBOLS = set("\\%&_#${} ,;\n")
TEXT_ENVS = {"enumerate", "itemize", "center", "tabular"}
MATH_ENVS = {"equation*", "align*"}
# Rejected everywhere, math included.
FORBIDDEN = {
    "documentclass", "usepackage", "newcommand", "renewcommand", "providecommand", "def", "edef",
    "gdef", "let", "input", "include", "write", "immediate", "openin", "openout", "read", "catcode",
    "csname", "special", "vspace", "hspace", "label", "ref", "cite", "footnote",
}
MATH_ONLY = {"qty", "asec", "amin", "adeg"}
LIST_OPTIONS = {r"[label=\alph*)]", r"[label=\arabic*)]"}
FIGURE_RE = re.compile(r"^\[width=(?:0?\.\d+|1(?:\.0+)?)?\\linewidth\]\{figures/([A-Za-z0-9._-]+\.(?:png|jpg))\}$")

TOKEN = re.compile(
    # Only web and mail links: a javascript: link would run on the site.
    r"(?P<link>\\(?:url|href)\{(?:https?://|mailto:)[^{}\\\n]*\})"
    r"|(?P<env>\\(?P<edge>begin|end)\{(?P<envname>[A-Za-z]+\*?)\})"
    r"|(?P<fig>\\includegraphics(?![A-Za-z])(?P<figargs>(?:\[[^\]\n]*\])?(?:\{[^{}\n]*\})?))"
    r"|(?P<cmd>\\(?:[A-Za-z]+\*?|[\s\S]))"
    r"|(?P<comment>%[^\n]*)"
    r"|(?P<dd>\$\$)|(?P<d>\$)|(?P<open>\{)|(?P<close>\})"
    r"|(?P<blank>\n[ \t]*(?=\n))"
)


def load_taxonomy(path=TAXONOMY):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    topics = {t["key"]: {s["key"] for s in t["subtopics"]} for t in data["topics"]}
    return topics, {s["key"] for s in data["sources"]}


def load_lock(path=LOCK):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def split_header(text):
    """Return (header dict, {key: line}, body, first body line). Raises ValueError(line, message)."""
    lines = text.split("\n")
    marks = []
    for i, line in enumerate(lines):
        s = line.strip()
        if s == "% ---":
            marks.append(i)
            if len(marks) == 2:
                break
        elif not marks and s and not s.startswith("%"):
            break
    if len(marks) != 2:
        raise ValueError(1, "missing metadata header (lines between two '% ---' marks at the top)")
    start, end = marks
    key_lines, yaml_lines = {}, []
    for i in range(start + 1, end):
        s = lines[i].strip()
        if not s.startswith("%"):
            raise ValueError(i + 1, "header lines must start with '%'")
        s = s[1:].strip()
        key = s.split(":", 1)[0]
        if key in key_lines:
            raise ValueError(i + 1, f"duplicate header field '{key}'")
        key_lines[key] = i + 1
        yaml_lines.append(s)
    try:
        header = yaml.safe_load("\n".join(yaml_lines)) or {}
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        line = start + 2 + (mark.line if mark else 0)
        raise ValueError(line, "header is not valid YAML (put quotes around values containing ':' or '#')")
    if not isinstance(header, dict):
        raise ValueError(start + 1, "header must be 'key: value' lines")
    return header, key_lines, "\n".join(lines[end + 1:]), end + 2


def check_header(header, where, topics, sources):
    """Yield (field, message) for the header of one file. `where` is the NAME_RE match."""
    solution = where["sol"] is not None
    original = header.get("translation_status") == "original" and not solution
    if solution:
        required, allowed = ("id", "kind", "lang"), ("id", "kind", "lang", "translation_status")
    elif original:
        required, allowed = REQUIRED, REQUIRED + OPTIONAL
    elif header.get("translation_status") in STATUSES:
        required = allowed = ("id", "lang", "translation_status")
    else:
        required, allowed = REQUIRED, REQUIRED + OPTIONAL

    for key in required:
        if header.get(key) in (None, ""):
            yield key, f"missing required field '{key}'"
    for key in header:
        if key not in allowed:
            yield key, f"field '{key}' is not allowed in this file"

    def present(key):
        return key in allowed and header.get(key) not in (None, "")

    if present("id") and header["id"] != where["id"]:
        yield "id", f"id '{header['id']}' does not match the file name '{where['id']}'"
    if present("lang") and header["lang"] != where["lang"]:
        yield "lang", f"lang '{header['lang']}' does not match the file suffix '.{where['lang']}.tex'"
    if solution and present("kind") and header["kind"] != "solution":
        yield "kind", "kind must be 'solution' in a .sol file"
    if present("translation_status") and header["translation_status"] not in STATUSES:
        yield "translation_status", "translation_status must be one of: " + ", ".join(STATUSES)
    if present("topic") and str(header["topic"]) not in topics:
        yield "topic", f"unknown topic '{header['topic']}'"
    elif present("subtopic") and str(header["subtopic"]) not in topics.get(str(header.get("topic")), ()):
        yield "subtopic", f"subtopic '{header['subtopic']}' is not in topic '{header.get('topic')}'"
    if present("difficulty") and (type(header["difficulty"]) is not int or header["difficulty"] not in (1, 2, 3)):
        yield "difficulty", "difficulty must be 1, 2 or 3"
    if present("source") and str(header["source"]) not in sources:
        yield "source", f"unknown source '{header['source']}' (add it to taxonomy.yml)"
    if present("year") and (type(header["year"]) is not int or not 1900 <= header["year"] <= 2100):
        yield "year", "year must be a four-digit number"
    if present("grade"):
        m = re.fullmatch(r"(\d{1,2})(?:-(\d{1,2}))?", str(header["grade"]))
        low, high = (int(m[1]), int(m[2] or m[1])) if m else (0, 0)
        if not (m and 5 <= low <= high <= 11):
            yield "grade", "grade must be 5..11 or a range such as 9-11"


def check_body(body, first_line, lock):
    """Yield (line, message) for the LaTeX body."""
    if not body.strip():
        yield first_line, "the problem body is empty"
        return
    # ^^xx spells any character, so it would slip past the command checks.
    for m in re.finditer(r"\^\^", body):
        yield first_line + body.count("\n", 0, m.start()), "'^^' is not allowed"
    math = None          # the closing delimiter while inside math
    stack = []           # open environments: (name, line)
    braces = []          # lines of open braces
    line, pos = first_line, 0
    for m in TOKEN.finditer(body):
        line += body.count("\n", pos, m.start())
        pos = m.start()
        kind, text = m.lastgroup, m.group()

        if kind == "comment":
            continue
        if kind == "blank":
            if math == "$":
                yield line, "unclosed '$' (paragraph ended inside inline math)"
                math = None
        elif kind == "dd":
            yield line, "use \\[ ... \\] instead of $$"
        elif kind == "d":
            if math is None:
                math = "$"
            elif math == "$":
                math = None
        elif kind == "open":
            braces.append(line)
        elif kind == "close":
            if braces:
                braces.pop()
            else:
                yield line, "unmatched '}'"
        elif kind == "env":
            name = m["envname"]
            if m["edge"] == "begin":
                if math is None:
                    if name in MATH_ENVS:
                        math = name
                    elif name not in TEXT_ENVS:
                        yield line, f"environment '{name}' is not allowed"
                    rest = body[m.end():]
                    if name in ("enumerate", "itemize"):
                        option = re.match(r"[ \t]*(\[[^\]\n]*\])", rest)
                        if option and not (name == "enumerate" and option[1] in LIST_OPTIONS):
                            yield line, f"list option {option[1]} is not allowed"
                    if name == "tabular" and not re.match(r"\{(?:[lcr| ]|@\{\})+\}", rest):
                        yield line, "tabular columns may only use l c r | @{}"
                stack.append((name, line))
            else:
                if not stack or stack[-1][0] != name:
                    yield line, f"\\end{{{name}}} does not match the open environment"
                else:
                    stack.pop()
                if math == name:
                    math = None
        elif kind == "fig":
            if math is not None:
                yield line, "\\includegraphics inside math"
            else:
                figure = FIGURE_RE.match(m["figargs"])
                if not figure:
                    yield line, "write figures as \\includegraphics[width=0.8\\linewidth]{figures/name.png}"
                elif figure[1] not in lock:
                    yield line, f"figure '{figure[1]}' is not in figures.lock.json (run scripts/figures.py push)"
        elif kind == "link":
            if math is not None:
                yield line, "links are not allowed inside math"
        elif kind == "cmd":
            name = text[1:]
            bare = name.rstrip("*")
            if name == "alph*" or name == "arabic*":
                if math is None:
                    before = body[:m.start()]
                    if not before.endswith("\\begin{enumerate}[label="):
                        yield line, f"command \\{name} is not allowed"
            elif bare in FORBIDDEN:
                yield line, f"command \\{bare} is forbidden"
            elif math is None:
                if name == "(":
                    math = "\\)"
                elif name == "[":
                    math = "\\]"
                elif name in (")", "]"):
                    yield line, f"\\{name} without an opening delimiter"
                elif bare in MATH_ONLY:
                    yield line, f"\\{bare} is math-only: write $\\{bare}{{...}}$"
                elif name in ("url", "href"):
                    yield line, "links must start with https://, http:// or mailto:"
                elif name[0].isalpha():
                    if name not in TEXT_COMMANDS:
                        yield line, f"command \\{name} is not allowed in text"
                elif name not in TEXT_SYMBOLS:
                    yield line, f"command \\{name} is not allowed in text"
            elif text == math:
                math = None
    end_line = first_line + body.rstrip().count("\n")
    if math is not None:
        yield end_line, f"math is never closed (expected {math})"
    for name, at in stack:
        yield at, f"\\begin{{{name}}} is never closed"
    for at in braces:
        yield at, "unclosed '{'"


def check_bank(folder, topics, sources, lock):
    """Check every .tex under `folder`. Returns a list of (path, line, message)."""
    errors, variants = [], {}
    for path in sorted(folder.rglob("*.tex")):
        where = NAME_RE.match(path.name)
        if not where:
            errors.append((path, 1, "file name must be <id>.<ru|en>.tex or <id>.sol.<ru|en>.tex (a-z, 0-9, -)"))
            continue
        try:
            text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        except UnicodeDecodeError:
            errors.append((path, 1, "file is not UTF-8"))
            continue
        try:
            header, key_lines, body, first_line = split_header(text)
        except ValueError as e:
            errors.append((path, *e.args))
            continue
        errors += [(path, key_lines.get(key, 1), msg) for key, msg in check_header(header, where, topics, sources)]
        errors += [(path, line, msg) for line, msg in check_body(body, first_line, lock)]
        variants.setdefault(where["id"], []).append((path, where, header))

    for pid, files in variants.items():
        originals = [f for f in files if not f[1]["sol"] and f[2].get("translation_status") == "original"]
        if len(originals) != 1:
            errors.append((files[0][0], 1, f"id '{pid}' needs exactly one 'translation_status: original' file, found {len(originals)}"))
            continue
        path, _, header = originals[0]
        expected = (str(header.get("source")), str(header.get("year")))
        if path.parent.parts[-2:] != expected:
            errors.append((path, 1, f"file must be in {expected[0]}/{expected[1]}/ (from source and year)"))
        seen = set()
        for other, where, _ in files:
            slot = (where["sol"], where["lang"])
            if slot in seen:
                errors.append((other, 1, f"duplicate id '{pid}': this variant exists twice"))
            elif other.parent != path.parent:
                errors.append((other, 1, f"duplicate id '{pid}': variants must sit next to the original"))
            seen.add(slot)
    return errors


def check_figures(lock, folder=FIGURES):
    """Local originals that changed after they were pushed."""
    for name, info in lock.items():
        path = folder / name
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() != info.get("sha256"):
            yield path, 1, "figure changed since it was pushed (run scripts/figures.py push)"


def check_overleaf():
    """The Overleaf starter must use the same preamble and macros as the site."""
    for name in ("preamble.tex", "macros.tex"):
        copy = ROOT / "overleaf" / name
        if not copy.exists() or copy.read_text(encoding="utf-8") != (ROOT / "latex" / name).read_text(encoding="utf-8"):
            yield copy, 1, f"differs from latex/{name} (copy that file here)"


def compile_tex(path):
    """XeLaTeX one problem body. Returns a list of (path, line, message)."""
    if not shutil.which("xelatex"):
        sys.exit("validate: --tex needs xelatex on PATH (it runs in CI)")
    text = path.read_text(encoding="utf-8-sig")
    lang = "english" if path.name.endswith(".en.tex") else "russian"
    # Figures are not in git, so replace them with a box; \tracinglostchars=3 makes "Missing character" fatal.
    wrapper = "\n".join([
        r"\documentclass[12pt]{article}",
        r"\input{preamble}",
        r"\renewcommand{\includegraphics}[2][]{\fbox{figure}}",
        r"\tracinglostchars=3",
        r"\begin{document}",
        rf"\begin{{{lang}}}",
        r"\input{body}",
        rf"\end{{{lang}}}",
        r"\end{document}",
    ])
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "body.tex").write_text(text, encoding="utf-8")
        Path(tmp, "check.tex").write_text(wrapper, encoding="utf-8")
        env = dict(os.environ, TEXINPUTS=f"{ROOT / 'latex'}{os.pathsep}", openin_any="p", openout_any="p")
        run = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error", "-no-shell-escape", "check.tex"],
            cwd=tmp, env=env, capture_output=True, timeout=120,
        )
        log_path = Path(tmp, "check.log")
        log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    bad = re.search(r"^(! .*|Missing character:.*)$", log, re.M)
    if run.returncode == 0 and not bad:
        return []
    at = re.search(r"^l\.(\d+)", log, re.M)
    return [(path, int(at[1]) if at else 1, "XeLaTeX: " + (bad[1] if bad else "compilation failed"))]


def selftest():
    topics, sources = load_taxonomy()
    lock = {"ok.png": {}}
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        def run(files):
            case = Path(tempfile.mkdtemp(dir=tmp))
            for rel, text in files.items():
                (case / rel).parent.mkdir(parents=True, exist_ok=True)
                (case / rel).write_text(text, encoding="utf-8")
            return check_bank(case, topics, sources, lock)

        good = sorted((FIXTURES / "good").glob("*.tex"))
        bad = sorted((FIXTURES / "bad").glob("*.tex"))
        assert good and bad, "no fixtures found"
        # All good fixtures form one bank, so variants link up.
        for path, line, msg in run({f"struve/2023/{p.name}": p.read_text(encoding="utf-8") for p in good}):
            failures.append(f"good/{path.name}:{line}: unexpected: {msg}")
        for p in bad:
            text = p.read_text(encoding="utf-8")
            expect = re.search(r"^% expect: (.+)$", text, re.M)
            assert expect, f"{p.name} has no '% expect:' line"
            found = [msg for _, _, msg in run({f"struve/2023/{p.name}": text})]
            if not any(expect[1] in msg for msg in found):
                failures.append(f"bad/{p.name}: expected '{expect[1]}', got {found}")
        # Bank-level rules need more than one file.
        base = (FIXTURES / "good" / "good-original.ru.tex").read_text(encoding="utf-8")
        for expect, files in {
            "must be in struve/2023": {"camp/2023/good-original.ru.tex": base},
            "variants must sit next to": {"struve/2023/good-original.ru.tex": base,
                                          "x/good-original.en.tex": (FIXTURES / "good" / "good-original.en.tex").read_text(encoding="utf-8")},
            "exactly one": {"struve/2023/good-original.ru.tex": base,
                            "struve/2023/good-original.en.tex": base.replace("lang: ru", "lang: en")},
        }.items():
            found = [msg for _, _, msg in run(files)]
            if not any(expect in msg for msg in found):
                failures.append(f"bank rule: expected '{expect}', got {found}")
    for f in failures:
        print(f)
    print(f"selftest: {len(good)} good, {len(bad)} bad fixtures, {len(failures)} failures")
    return 1 if failures else 0


def check_all():
    """Every static check on the repo. Returns a list of (path, line, message)."""
    topics, sources = load_taxonomy()
    lock = load_lock()
    return check_bank(PROBLEMS, topics, sources, lock) + list(check_figures(lock)) + list(check_overleaf())


def report(errors):
    for path, line, msg in errors:
        rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
        print(f"{rel.as_posix()}:{line}: {msg}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tex", nargs="*", metavar="FILE", help="also compile with XeLaTeX (all files if none given)")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    errors = check_all()
    # Compile only files that pass the static check: it also blocks file-access commands.
    if args.tex is not None and not errors:
        targets = [Path(f).resolve() for f in args.tex] or sorted(PROBLEMS.rglob("*.tex"))
        for path in targets:
            if path.suffix == ".tex" and path.is_relative_to(PROBLEMS) and path.exists():
                errors += compile_tex(path)
    report(errors)
    count = sum(1 for _ in PROBLEMS.rglob("*.tex"))
    print(f"validate: {count} files, {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
