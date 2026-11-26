# Samples for the Platform

Real material from the camp sheets (Праки, Оптика I, Небмех I) and the Struve 2023
regional booklet, converted to the planned LaTeX format. Compile the test sheet from
this folder: `xelatex camp-sheet.tex` (twice). Fonts: needs a font with Cyrillic
(DejaVu Serif is set in preamble.tex).

## Conventions (the schema Claude Code should start from)
- One problem = one `.tex` file in `problems/`: body only, no preamble, with a `% ---` metadata header.
- Same `id` links variants: `.ru.tex`, `.en.tex` (language) and `.sol.tex` (solution + criteria, `kind: solution`).
- Macros live only in `macros.tex` and are math-only: write `$\qty{40}{см}$`, `$\asec{1.0}$`.
- Figures: `figures/`, referenced from the root as `figures/name.png`; build everything from this folder.
- Problems without text source get a sidecar `.yml` with the same fields (`photo/`, `pdf/`).
- Difficulty values and topic names are placeholders guessed by Claude; fix them.

## What each sample tests
| File | Tests |
|---|---|
| problems/praki-2026-001-space-oddity.tex | two photographic figures inside a problem |
| problems/praki-2026-002-black-hole-sun.tex | figures plus a 4th-root formula, text between figures |
| problems/optics-2026-001-simple-1.tex | numbered sub-questions, units, arc seconds |
| problems/optics-2026-003-jupiter.tex | long multi-part problem with a) b) c) d), many units |
| problems/optics-2026-004-goto.tex | formula-heavy problem (SNR typed as math, not an image) |
| problems/struve-2023-7-1-crescent.{ru,en,sol}.tex | RU/EN pair and a solution with a grading table |
| photo/nebmeh-2026-002-scan.png + .yml | problem that exists only as an image |
| pdf/praki-2026-02-12.pdf + .yml | PDF-only camp set (5 problems, photos inside) |
| pdf/struve-2023-regional-with-solutions.pdf + .yml | large official booklet (26 pages) |
| old-typst/*.pdf | output of the old Typst template (sources are template.typ / units.typ) |

## Known gaps
- The scan in photo/ is a crop of a PDF page, not a real photo. Add a real one.
- pandoc ignores enumitem's `label=\alph*)`; check how sub-lists render on the web.
- English text in `.en.tex` needs `otherlanguage{english}` in PDF builds (not yet in the sheet).
