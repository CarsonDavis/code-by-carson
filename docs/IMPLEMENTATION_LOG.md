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
