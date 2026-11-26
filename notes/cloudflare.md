# T2: Cloudflare setup

Menu names in the dashboard may differ slightly.

1. **Domain** (start first, it can take up to 24 h). Dashboard → Add a domain → `astroolymp.com` → Free plan.
   Check that the imported DNS records match what your current DNS provider shows, then replace the nameservers
   at your registrar with the two Cloudflare gives you. Wait until the domain shows "Active".
2. **R2.** Dashboard → R2. Activating it asks for a payment method even on the free tier.
   Create bucket `astroolymp`.
3. **Media address** (after step 1 is active). Bucket → Settings → Custom domains → add `files.astroolymp.com`.
4. **Pages project**, in a terminal: `npx wrangler login`, then
   `npx wrangler pages project create stellartask --production-branch main`.
5. **Upload figures:** `python scripts/figures.py push`, then commit `content/figures.lock.json`.
6. **For CI (T6):** My Profile → API Tokens → Create custom token → Account · Cloudflare Pages · Edit.
   In GitHub → repo Settings → Secrets and variables → Actions, add `CLOUDFLARE_API_TOKEN` and
   `CLOUDFLARE_ACCOUNT_ID`. Never paste the token into a file or a chat.
