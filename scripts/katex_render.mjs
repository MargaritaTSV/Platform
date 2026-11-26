// stdin: {key: html from pandoc}. stdout: {html: {key: html}, errors: {key: message}}.
// All math is rendered here, so the browser needs only KaTeX's CSS and fonts.
import { readFileSync } from "node:fs";
import katex from "katex";

const entities = { "&lt;": "<", "&gt;": ">", "&quot;": '"', "&#39;": "'", "&amp;": "&" };
const unescape = (s) => s.replace(/&(lt|gt|quot|#39|amp);/g, (m) => entities[m]);

const pages = JSON.parse(readFileSync(0, "utf8"));
const out = { html: {}, errors: {} };

for (const [key, html] of Object.entries(pages)) {
  try {
    out.html[key] = html.replace(/<span class="math (inline|display)">([\s\S]*?)<\/span>/g, (_, kind, tex) =>
      katex.renderToString(unescape(tex), {
        displayMode: kind === "display",
        throwOnError: true,
        // Anything TeX would complain about (such as Cyrillic outside \text) fails the build.
        strict: (code) => (code === "newLineInDisplayMode" ? "ignore" : "error"),
      }),
    );
  } catch (e) {
    out.errors[key] = e.message;
  }
}
process.stdout.write(JSON.stringify(out));
