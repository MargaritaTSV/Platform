# Writing a problem in Overleaf

1. Once: zip this folder, in Overleaf choose New project → Upload project, then set Menu → Compiler → XeLaTeX.
2. Edit `problem.tex`: fill in the header, then write the body. Keys for `topic`, `subtopic` and `source` are in `content/taxonomy.yml`.
3. Compile and check the PDF.
4. Copy the whole file to `content/problems/<source>/<year>/<id>.<lang>.tex`. Put pictures in `content/figures/`.
5. In the repo run `python scripts/figures.py push` (only if you added pictures), then `python scripts/validate.py`.

Rules:

- No preamble, `\newcommand`, `\vspace`, `\label`, `\ref`, footnotes or TikZ.
- Allowed text commands: `\textbf`, `\emph`, `\textit`, `\par`, `\medskip`, `\smallskip`, `\bigskip`, `\noindent`, `\url`, `\href`.
- Allowed environments: `enumerate`, `itemize`, `center`, `tabular` (`l c r |`), `equation*`, `align*`.
- Units and angles go inside math: `$\qty{40}{см}$`, `$\asec{1.5}$`, `$\amin{30}$`, `$\adeg{30}$`.
- Difficulty is 1, 2 or 3.
- If `latex/preamble.tex` or `latex/macros.tex` changes, copy it here and into Overleaf.
