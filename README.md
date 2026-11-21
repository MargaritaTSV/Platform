# StellarTask — handoff for Claude Code

Everything needed to start building the StellarTask MVP in Claude Code.

## What's inside

| Path | What it is |
|---|---|
| `CLAUDE.md` | Instructions Claude Code reads automatically: scope, stack, data formats, design rules, milestones |
| `.claude/agents/` | Four helper agents: `pipeline-builder`, `frontend-builder`, `design-reviewer`, `content-checker` |
| `design/reference/` | The chosen design (home page and problems page) as source files. They need the design canvas to run, so use them as a reference; the live version is on the canvas, page "StellarTask flow", version 1: https://claude.ai/artifact/U4McF4YZ1TiM1YMGkM7qYC |
| `design/tokens.css`, `design/tokens.json` | Colours, fonts, type sizes, spacing |
| `design/svg/` | The drawn elements: logo star, stars, ring, dividers, rules, rail line, game drawings, full map |
| `design/map.json` | Star positions and the hand-drawn line paths of the map |
| `content/taxonomy.yml` | DRAFT list of the 8 areas and their subtopics, EN + RU names. Replace with your real list |
| `content/games.yml` | Game cards (ConstellationFinder description still TODO) |
| `docs/` | Put the full spec here (see step 2) |

## How to start

1. Create a new GitHub repository (for example `stellartask`) and copy this whole folder into it, including the hidden `.claude` folder.
2. Open the spec, https://claude.ai/artifact/X4917SAgKYrmikJGqpACPa, export it as Markdown from the doc's Export menu and save it as `docs/spec.md`.
3. Replace `content/taxonomy.yml` with your real areas and subtopics (or keep the draft for now and edit later).
4. Open Claude Code in the repository and start with:

   > Read CLAUDE.md and docs/spec.md. Plan milestone 1 in plan mode, then build it using the pipeline-builder and frontend-builder agents. Run design-reviewer at the end.

5. After each milestone, check the result yourself before starting the next one.

## Still needed from you

- The real list of areas and subtopics (with RU and EN names)
- 5–10 real problems to test with: some Typst, one photo, one PDF
- The built files of ConstellationGame and ConstellationFinder, and a one-line description of ConstellationFinder
- The domain name, and GitHub Pages turned on for the repository
