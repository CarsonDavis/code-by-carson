# Implementation Log

## 2026-02-09 — Project Kickoff
- Created docs folder with initial requirements and architecture docs
- Reviewed znah.net for layout inspiration
- Catalogued existing projects from my-stuff.md

## 2026-02-09 — Full Implementation
### Static Site (`site/`)
- Built `index.html` with hero section, 3 project cards, external links nav, and footer
- Built `style.css` with dark theme, CSS Grid layout, responsive breakpoints
- Project cards: Bass Practice Schedule, Lens Calculator, Goodreads Stats
- External links: Blog, Google Scholar, Cooking Instagram
- Placeholder thumbnails (gray boxes) — ready for real images later

### CDK Infrastructure (`cdk/`)
- Single stack in `portfolio_stack.py` with all resources
- S3 site bucket: BlockPublicAccess.BLOCK_ALL, enforce_ssl, OAC access
- CloudFront distribution: OAC (not OAI), HTTPS redirect, TLS 1.2, security headers, gzip
- ACM certificate: codebycarson.com + www, DNS validation via Route 53
- Route 53: A record aliases for apex + www → CloudFront
- Preview bucket: public-read, static website hosting for PR previews
- GitHub OIDC provider + IAM role (scoped to CarsonDavis/code-by-carson)
- IAM role has: S3 read/write, CloudFront invalidation, CloudFormation deploy perms

### CI/CD (`.github/workflows/`)
- `deploy.yml`: OIDC auth → CDK deploy → S3 sync → CF invalidation (on push to main)
- `preview.yml`: OIDC auth → upload to preview bucket → sticky PR comment with URL → teardown on close

### Verification
- CDK stack imports cleanly (`uv run python -c "from stacks.portfolio_stack import PortfolioStack"`)
- Full `cdk synth` requires AWS credentials (Route53 hosted zone lookup) — will verify on first deploy
- Site HTML/CSS ready for local browser preview

### Bootstrap Note
The CDK stack creates the GitHub OIDC provider and IAM role, but these are needed by GitHub Actions to run CDK deploy. **First deploy must be done manually** from a local machine with AWS credentials:
```bash
cd cdk && uv venv && uv pip install -r requirements.txt
npx cdk bootstrap aws://ACCOUNT_ID/us-east-1
npx cdk deploy
```
After that, set the `AWS_ROLE_ARN` GitHub secret to the output `GitHubActionsRoleArn` value, and CI/CD will handle subsequent deploys.

## 2026-02-09 — Initial Deploy & Bootstrap
### Fixes applied during deploy
- **`app.py`**: Added explicit `account="420665616125"` to `cdk.Environment` — required by `HostedZone.from_lookup`
- **`portfolio_stack.py`**: Moved `response_headers_policy` from `Distribution()` kwargs into `BehaviorOptions()` — it's not a top-level Distribution param
- **`portfolio_stack.py`**: Changed `iam.OpenIdConnectProvider()` (creates new) to `OpenIdConnectProvider.from_open_id_connect_provider_arn()` (imports existing) — the GitHub OIDC provider already existed in the account

### Deploy steps completed
1. CDK bootstrap (`cdk bootstrap aws://420665616125/us-east-1`) — CDKToolkit stack updated
2. CDK deploy — created S3 buckets, CloudFront (E1SYFVZGZC91Z9), ACM cert, Route 53 records, IAM role
3. Uploaded `site/` to S3 via `aws s3 sync`
4. Set `AWS_ROLE_ARN` GitHub secret via `gh secret set`
5. Pushed to master — GitHub Actions deploy workflow passed (run 21849957464)

### Verification
- https://codebycarson.com — HTTP 200, served via CloudFront, security headers present
- https://www.codebycarson.com — HTTP 200, same content
- GitHub Actions deploy workflow: all steps green (OIDC auth, CDK deploy, S3 sync, CF invalidation)

### New files
- `cdk/cdk.context.json` — cached Route 53 hosted zone lookup (committed for CI)
- `.gitignore` — added `cdk/outputs.json`

## 2026-02-09 — Landing Page Redesign
### What changed
Evolved the minimal portfolio page into a full personal landing page.

- **Hero**: Title changed to "Carson Davis", tagline: "Software engineer with too many hobbies and not enough shelf space." Removed nav links (redundant with in-body links).
- **Live Sites**: Renamed from "Projects". Same 3 cards + "Visit my GitHub →" button.
- **Deep Dives** (new): 2x2 image card grid with blog post cover images from S3. Book Cover Design, Shooting Film, Troublesome Translations, Kitchen Knives. "Read more posts →" button.
- **Cooking** (new): Side-by-side layout — Instagram grid image (60%) + description and @carsons_cooking link.
- **Media** (new): No Dumb Questions podcast #199, COVID Face Shields news interview.
- **Research** (new): 7 featured publications list (first-author + NASA-titled, spanning AGU/EGU/IGARSS/SoutheastCon, 2019-2023). "View all on Google Scholar →" button.
- **Footer**: GitHub, Blog, Scholar, Instagram link row + copyright.
- **Open Graph meta tags**: Title, description, and composite OG image for link previews.

### Section order
Hero → Live Sites → Deep Dives → Cooking → Media → Research → Footer

### Files modified
- `site/index.html` — full restructure with 6 content sections + OG meta tags
- `site/style.css` — deep-dives grid, cooking side-by-side layout, publication list, media list, footer links, button-style section-more links, all sections at 960px width

### Files added
- `site/images/instagram-grid.png` — Instagram grid screenshot
- `site/images/kitchen-knives.png` — Japanese knife photo for Deep Dives card
- `site/images/og-image.png` — 1200x630 composite image for link previews (6-panel mosaic)

### Verification
- Local preview via `python3 -m http.server` — all sections render correctly
- All external links verified in HTML
- OG image generated at correct dimensions (1200x630)

## 2026-02-10 — Dark Reader Color Match & Extension Block
### What changed
Adopted Dark Reader's default dark-mode palette as the site's native colors, then blocked Dark Reader from double-transforming the page.

### CSS variable changes (`site/style.css`)
| Variable       | Old         | New         |
|---------------|-------------|-------------|
| `--bg`        | `#0e0e0e`   | `#181a1b`   |
| `--surface`   | `#1a1a1a`   | `#1e2021`   |
| `--border`    | `#2a2a2a`   | `#3c4143`   |
| `--text`      | `#e0e0e0`   | `#e8e6e3`   |
| `--text-muted`| `#888`      | `#a8a095`   |
| `--accent`    | unchanged   | `#8ab4f8`   |
| `--accent-hover`| unchanged | `#aecbfa`   |

### Meta tags added (`site/index.html`)
- `<meta name="darkreader-lock">` — Dark Reader's official opt-out; extension skips the page
- `<meta name="color-scheme" content="dark">` — tells browsers the site is natively dark-themed

### Verification
- Pending: open locally with Dark Reader enabled, confirm it shows as disabled/skipped
