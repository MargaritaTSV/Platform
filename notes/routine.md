# Routine: adding problems

One session adds one small set (about 5–15 problems) in one pull request.

## Owner
1. Put the material in `content/_source/` (PDF, photos) or paste finished LaTeX (`overleaf/README.md`).
2. Ask Claude: "Follow notes/routine.md for <material>", with the source, year and grade if the material omits them.
3. Review the pull request: statements, topic, subtopic, difficulty, figures. Merge when `validate` is green.
   Merging publishes to astroolymp.com within a few minutes; look at one new problem there.

## Claude
Work in the main checkout: `content/_source/` and `content/figures/` are gitignored, so worktrees lack them.

1. Start a branch from the latest `origin/main`: `content/<source>-<year>-<short-name>`.
2. Check that each problem is not in `content/problems/` already.
3. Write `content/problems/<source>/<year>/<id>.<lang>.tex` in the original language. Rules: `overleaf/README.md`.
   The id follows the neighbouring files and never changes once published.
4. Copy the statement faithfully. List anything unreadable or doubtful in the pull request; never guess numbers.
5. Keys come from `content/taxonomy.yml`. Ask before adding a source or subtopic: keys are permanent.
6. Statements only: no solutions, no source PDFs, no figure originals in Git.
7. Figures: put them in `content/figures/` under new names, run `python scripts/figures.py push`, commit
   `content/figures.lock.json`.
8. Run `python scripts/validate.py` (`--tex <files>` if XeLaTeX is installed; CI runs it too) and
   `python scripts/build.py`.
9. Run the `content-checker` agent on the new files and fix what it finds.
10. Commit, push, open the pull request. List the added ids and the doubts. Do not merge.

Translations are a separate task: `translation_status: machine-translated-needs-review` until the owner reviews.

## When something fails
- `validate` is red: open the run, fix the `file:line` it names, push to the same branch.
- Deploy is red: the live site keeps the previous version. Fix through a new pull request.
- A bad problem is live: revert its pull request in GitHub, then merge the revert.

## Protection of `main`
The ruleset `main` (GitHub → Settings → Rules → Rulesets, active since 2026-11-27, no bypass) blocks deletion
and force pushes, and requires a pull request (0 approvals) with a passing `validate` check.
