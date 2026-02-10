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
Evolved the minimal portfolio page into a full personal landing page with multiple sections:

- **Hero**: Updated tagline to "Engineer, researcher, writer, maker. Building software, collecting cameras, and cooking dinner." Nav links changed to GitHub, Blog, Scholar.
- **Things I've Built**: Renamed from "Projects". Same 3 cards (Bass Practice, Lens Calculator, Goodreads Stats).
- **Writing** (new): 4 featured blog posts as a clean text list — Book Cover Design, Shooting Film, Troublesome Translations, Kitchen Knives. Links to madebycarson.com.
- **Research** (new): NASA/NSSTC blurb, "33 publications and presentations" stat, Google Scholar link. Displayed as a styled card.
- **Cooking** (new): Instagram grid screenshot image + link to @carsons_cooking. Image file (`site/images/instagram-grid.png`) to be provided by user.
- **Media** (new): No Dumb Questions podcast #199, COVID Face Shields news interview. Compact text list.
- **Footer**: Added GitHub, Blog, Scholar, Instagram link row above copyright.

### Files modified
- `site/index.html` — restructured from 1 section to 6 content sections
- `site/style.css` — added writing, research, cooking, media, footer-links styles; added `--section-max` variable for narrower content sections

### Verification
- Local preview via `python3 -m http.server` — all sections render correctly
- Cooking section shows broken image (expected — user needs to provide `instagram-grid.png`)
- All external links verified in HTML (correct URLs for blog posts, Scholar, Instagram, podcast, YouTube)
