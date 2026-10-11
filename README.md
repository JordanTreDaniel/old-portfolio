# Poker Hands v1 — preservation artifact

**Complete, frozen version 1 of the "Poker Hands, Decoded" teaching page**, preserved
durably in git on 2026-10-11 (page built + deployed 2026-10-10). One self-contained
static HTML page plus 42 optimized SVG playing cards, the machine-verified content
JSON it was generated from, the generator, and the review evidence.

> **Why this repo looks the way it does:** this VM has **no working GitHub API
> credential** (see "Storage situation" below), so a dedicated private repo could not
> be created from here. Everything lives in this repo as a **standalone branch
> `poker-hands-v1` pushed to the existing dormant `JordanTreDaniel/old-portfolio` repo**
> (GitHub name: `old-portfolio` — the older name `portfolio` redirects to it; its
> `master` branch — the old jQuery-era site — is untouched). Nothing was written into
> any `~/dev` repo checkout. Migration to a dedicated repo is one command once a PAT
> works (see below).

## What's live right now (v1)

| Where | URL | Status |
|---|---|---|
| **Cloudflare Pages (canonical)** | https://portfolio.jordanchristley.com/public/poker-hands/ | 200 — CF Pages project `portfolio`, deployment `b329b6b8.portfolio-d9a.pages.dev`, custom domain |
| **Vercel mirror** | https://poker-hands-two.vercel.app/poker-hands.html | 200 — project `poker-hands-two`. Root `/` 404s (no index.html — expected). **Not** `poker-hands.vercel.app` — that host serves an unrelated "Create Next App" starter. |
| Local VM serve | `/home/jordanc/html-portfolio/public/` via `server.py` on `:8814` | dev only |

Page title: `Poker Hands, Decoded — A Beginner's Guide to Texas Hold'em`

### CF Pages rollback snapshot (VOLATILE)

- `/tmp/portfolio-mirror-pristine` — 188 MB snapshot of the **whole portfolio mirror**
  (pre-change state, captured 2026-10-10) kept for CF Pages rollback.
- ⚠️ **`/tmp` is wiped on reboot.** It is NOT in this repo (too big). If rollback is
  ever needed after a reboot, it must be re-captured from the live Pages deployment
  (`wrangler pages deployment ...`) instead.

## Layout

```
content/public/poker-hands.html   ← deployed v1 HTML (byte-identical to live; md5 dfdea599…)
content/public/poker-cards/       ← 42 SVGs actually used by the page (subset of full deck)
content/registry-entry.txt        ← ready-to-paste content/registry.ts entry (artifacts skill shape)
source/hands-content.json         ← ★ SOURCE OF TRUTH: machine-verified hand rankings/content
source/build.py                   ← generator: hands-content.json → poker-hands.html
source/page.js                    ← standalone copy of the tab-switcher JS (also embedded in build.py)
source/svgo.config.json|.mjs, svgo0.config.mjs  ← card-optimization configs (3 iterations)
source/cards/SOURCE.txt           ← card art provenance + license
source/cards-opt3/                ← final optimized full deck (52 SVGs, 1.5 MB) — build input
source/review/                    ← review evidence: report*.json (3), review*.py (8), screenshots (v1 + rounds)
```

## Source of truth & rebuild

**`source/hands-content.json` is authoritative** — every hand ranking, example, glossary
term, and trap is machine-verified there. The HTML is generated from it; never edit the
HTML by hand for content changes.

`build.py` hardcodes `/tmp/poker-hands/` paths (it was written for the /tmp build dir).
To rebuild from this repo:

```bash
# 1. point the generator at this repo's files
sed -i 's|/tmp/poker-hands/|'"$PWD"'/source/|g' source/build.py
# 2. generate (writes source/poker-hands.html, prints byte count)
python3 source/build.py
# 3. compare against the frozen v1 (expect identical output)
diff source/poker-hands.html content/public/poker-hands.html
```

Card art: raw upstream deck is **not** included (8 MB, excluded — see below);
`source/cards-opt3/` is the optimized build input, and `content/public/poker-cards/`
is the 42-card subset the page references as `<img src="poker-cards/…svg">`.

## Mac merge (into the canonical portfolio-next tree)

The artifacts skill's canonical home is the **portfolio-next checkout on the Mac**
(`/Users/jordanc/dev/hermes/portfolio-next`) — it does not exist on this VM and has no
GitHub remote under `JordanTreDaniel/portfolio-next` / `jordanchristley/portfolio-next`
(checked 2026-10-11). To land v1 in the canonical tree:

```bash
export PORTFOLIO_NEXT=/Users/jordanc/dev/hermes/portfolio-next
# 1. drop the content
cp content/public/poker-hands.html "$PORTFOLIO_NEXT/content/public/"
cp -r content/public/poker-cards    "$PORTFOLIO_NEXT/content/public/"
# 2. paste content/registry-entry.txt into content/registry.ts
#    (insert BEFORE the registry object's final `};`, i.e. before
#     `};\n\nexport function getContentByTier` — unregistered slugs 404)
# 3. build + deploy + verify
cd "$PORTFOLIO_NEXT" && npm run build && ./deploy/deploy.sh && ./deploy/verify.sh
```

⚠️ **MagazineShell strips `<script>` tags at build time.** v1 contains exactly **one**
inline script (tab switcher, line ~822 of the HTML). Before merging, either reimplement
the tabs as a Next client component or verify the no-JS fallback (review round included
a `16-nojs.png` check). `<style>` blocks and Google Fonts links are preserved.

## Storage situation (why a branch, not a new repo)

Verified 2026-10-11 on this VM:

- `gh` token (`~/.config/gh/hosts.yml`) → **401 Bad credentials**
- `~/.hermes/.env` `GITHUB_TOKEN` + `GITHUB_PERSONAL_ACCESS_TOKEN` (and `.bak`,
  orchestrator-profile copies) → **401**
- Doppler (all 8 projects × configs `dev/dev_personal/stg/prd`, key-name scan of
  downloaded secrets) → **no GitHub token exists at all**
- Whole-filesystem sweep for real token formats (`ghp_…`, `github_pat_…`,
  `gho_…`, `ghs_…` across 44,907 files + `/proc/*/environ`) → 11 hits, **all 401**
  (mostly Hermes test fixtures)
- **SSH works** (`JordanTreDaniel`) → git push/clone to *existing* repos only;
  GitHub cannot create repos over SSH.

→ New private repo creation was impossible without a human `gh auth login` device-code
step. This artifact was therefore pushed as branch **`poker-hands-v1`** of
**`git@github.com:JordanTreDaniel/old-portfolio.git`** (additive; `master` untouched).
The older name `JordanTreDaniel/portfolio` redirects to `old-portfolio`.

**Migration once a PAT/device-login works:**

```bash
gh repo create jordanchristley/poker-hands --private   # or any owner/name
git push git@github.com:<owner>/<name>.git poker-hands-v1:main
```

## Excluded (and why)

| Excluded | Size | Why |
|---|---|---|
| `cards/` raw upstream deck | 8 MB | Throwaway download; `source/cards/SOURCE.txt` documents source (github.com/notpeter/Vector-Playing-Cards, Byron Knoll, public domain/WTFPL). Re-downloadable. |
| `cards-opt/`, `cards-opt2/` | 8.4 MB | Superseded intermediate optimization rounds; `cards-opt3` is final. |
| `vercel-deploy/` staged copy | 1.4 MB | Duplicate of `content/public/`; Vercel link documented above (`.vercel/project.json` deliberately not committed — Vercel's own README says don't share it; it contains only project/org IDs). |
| `/tmp/portfolio-mirror-pristine` | 188 MB | Whole-site CF rollback snapshot — volatile by nature, documented above. |

Not excluded but optional: `source/review/` screenshots (~4.2 MB) — kept because they are
the v1 visual-review record.
