# CodeByCarson — Repository Index

## Root Files
- `CLAUDE.md` — AI assistant instructions for this project
- `PROFILE.md` — Author profile synthesized from blog posts at CarsonDavis.github.io
- `my-stuff.md` — Raw list of projects and links to feature
- `INDEX.md` — This file; map of the repository

## site/ — Static Portfolio Site
- `site/index.html` — Landing page: hero, live sites, deep dives, cooking, media, research sections + OG meta tags + Dark Reader lock
- `site/style.css` — Dark minimalist stylesheet (CSS Grid, responsive, all sections at 960px, Dark Reader-matched palette)
- `site/images/` — Project thumbnails, Instagram grid, kitchen knives photo, OG composite image

## cdk/ — AWS CDK Infrastructure (Python)
- `cdk/app.py` — CDK app entry point (account 420665616125, us-east-1)
- `cdk/cdk.json` — CDK configuration (uses `uv run`)
- `cdk/cdk.context.json` — Cached Route 53 hosted zone lookup (needed for CI)
- `cdk/requirements.txt` — Python dependencies (aws-cdk-lib, constructs)
- `cdk/stacks/portfolio_stack.py` — Single stack: S3 + CloudFront (OAC) + ACM + Route 53 + preview bucket + GitHub OIDC role (imported)

## .github/workflows/ — CI/CD
- `.github/workflows/deploy.yml` — Deploy on push to main (CDK deploy + S3 sync + CF invalidation)
- `.github/workflows/preview.yml` — PR preview environments (upload to preview bucket, comment URL)

## docs/
- `docs/REQUIREMENTS.md` — Feature requirements and status
- `docs/IMPLEMENTATION_LOG.md` — Log of what was built and when
