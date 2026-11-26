"""Pagefind search index: one record per problem, so a result is a problem, not a page."""
import asyncio
from html.parser import HTMLParser

import pagefind.service
from pagefind.index import IndexConfig, PagefindIndex


class _NoDelay:
    """pagefind 1.6.0 sleeps 0.1 s before reading each reply: over 16 minutes for 10k problems."""

    def __getattr__(self, name):
        return getattr(asyncio, name)

    async def sleep(self, _):
        await asyncio.sleep(0)  # still yields, so the waiting request can continue


pagefind.service.asyncio = _NoDelay()

VOID = {"br", "img", "hr", "col", "input", "meta", "link", "source", "wbr"}
BLOCKS = {"p", "li", "tr", "td", "th", "div", "br", "table", "ol", "ul"}


class _Text(HTMLParser):
    """Text of a rendered statement without the formulas (KaTeX output reads as noise)."""

    def __init__(self):
        super().__init__()
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        classes = (dict(attrs).get("class") or "").split()
        if not self.skip and ("katex" in classes or "katex-display" in classes):
            self.parts.append("…")  # keeps excerpts readable where a formula was
        if tag not in VOID and (self.skip or "katex" in classes or "katex-display" in classes):
            self.skip += 1
        elif tag in BLOCKS:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag not in VOID and self.skip:
            self.skip -= 1
        elif tag in BLOCKS:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def plain_text(html):
    parser = _Text()
    parser.feed(html)
    parser.close()
    return " ".join("".join(parser.parts).split())


def records(problems, topics, sources):
    subtopics = {(t["key"], s["key"]): (t, s) for t in topics for s in t["subtopics"]}
    for p in problems:
        topic, sub = subtopics[p["topic"], p["subtopic"]]
        source = sources[p["source"]]
        title = p.get("title") or f"{source[p['lang']]}, {p['year']}"
        # Names in both languages, so "Struve 2023" and "Струве 2023" both find the problem.
        extra = [title, source["ru"], source["en"], p.get("event"), p["year"],
                 topic["name"]["ru"], topic["name"]["en"], sub["name"]["ru"], sub["name"]["en"]]
        yield {
            "url": f"/problems/{p['topic']}/{p['subtopic']}/#{p['id']}",
            # The statement comes first, so excerpts are taken from it.
            "content": " · ".join([plain_text(p["html"]), *(str(x) for x in extra if x)]),
            # One index for the whole bank, whatever the interface language is.
            "language": "ru",
            "meta": {
                "title": str(title),
                "ru": f"{sub['name']['ru']} · {source['ru']} · {p['year']}",
                "en": f"{sub['name']['en']} · {source['en']} · {p['year']}",
            },
        }


def write_index(problems, topics, sources, folder):
    async def run():
        # Leaving the block writes the files. Without output_path they also land in ./pagefind.
        async with PagefindIndex(config=IndexConfig(output_path=str(folder))) as index:
            for record in records(problems, topics, sources):
                await index.add_custom_record(**record)

    asyncio.run(run())


if __name__ == "__main__":
    assert plain_text('<p>a <span class="katex"><span><math><mi>x</mi></math></span><br></span> b</p><p>c &lt;d</p>') == "a … b c <d"
    print("search selftest: ok")
