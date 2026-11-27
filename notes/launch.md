# Launch checklist (astroolymp.com)

## Checked on 2026-11-27
- [x] HTTPS works, `http://` redirects to it, an unknown address returns the 404 page with status 404.
- [x] Merging into `main` deploys; `main` needs a pull request with a passing `validate` check.
- [x] All 4 figures load from files.astroolymp.com. Cloudflare Web Analytics is on every page.
- [x] No PDF, `.env` or `.wrangler` file is tracked in Git, and a pattern search found no keys.
- [x] The 6 problem pages with content and the theory page: no horizontal scroll, no KaTeX error (1280 px).
- [x] 10,000 problems fit the build time, file count and page size limits (T13, before the topic list grew).
- [x] Page description and tab icon; "Games" has no link while `games_url` in `site.yml` is empty (live after merge).
- [x] The star map shows all 13 topics (live after merge).

## Owner, before announcing the site
- [ ] **Logo licence.** The header uses `design/svg/logo_star.svg`, made from a Vecteezy stock file (250 KB).
      Confirm the licence, or switch to `design/svg/logo-star.svg` (the design reference's star, already the tab icon).
- [ ] **www.** `www.astroolymp.com` does not open. Cloudflare → Pages `stellartask` → Custom domains, or a redirect rule.
- [ ] **Figure originals.** Copy `content/figures/` somewhere outside this PC.
- [ ] **Russian text.** Review the names and descriptions in `content/taxonomy.yml`.
- [ ] **Old site.** GitHub → Settings → Pages: switch it off (it still redirects to the old domain).
- [ ] **Content.** The bank has 6 problems: add a first batch (`notes/routine.md`) or launch as it is.
- [ ] **Final look** at the home page, one problem list and the search, in both languages.

## After launch
- Set `games_url` when the games are live.
- The weekly XeLaTeX check compiles one file at a time: split it before the bank reaches a few thousand problems.
- With many problems, check how fast a rare filter combination loads.
