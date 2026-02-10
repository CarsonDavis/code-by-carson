# CodeByCarson Portfolio - Requirements

## Overview
A minimalist portfolio website showcasing Carson's coding projects. Inspired by
[znah.net](https://znah.net/) — clean, simple, project-focused.

## Core Requirements

### R1 - Project Grid
- [x] Display projects in a responsive card grid
- [x] Each card shows: thumbnail image, title, short description
- [x] Cards link to the live project and/or GitHub repo
- [x] Grid adapts gracefully from desktop to mobile

### R2 - Hero / Header
- [x] Site title: "CodeByCarson"
- [x] Short tagline / bio
- [x] Minimal navigation (external links in hero nav)

### R3 - Visual Style
- [x] Clean, minimalist aesthetic (znah.net-inspired)
- [x] Typography-focused, not cluttered
- [x] Dark-only modern design

### R4 - Projects to Feature (initial set)
- [x] Bass Practice Schedule — https://bass-practice.codebycarson.com/
- [x] Lens Calculator — https://lens-calc.codebycarson.com
- [x] Goodreads Stats — https://goodreads-stats.codebycarson.com/

### R5 - External Links
- [x] Link to blog: madebycarson.com
- [x] Link to Google Scholar profile
- [x] Link to cooking Instagram

### R6 - Infrastructure
- [x] S3 + CloudFront hosting with OAC (not OAI) — deployed, CloudFront dist E1SYFVZGZC91Z9
- [x] ACM certificate with DNS validation — issued, covers apex + www
- [x] Route 53 A records (apex + www) — live, both resolve
- [x] GitHub OIDC for Actions auth (no long-lived keys) — imports existing provider
- [x] Preview bucket for PR previews — created (not yet tested with a real PR)

### R7 - CI/CD
- [x] Deploy on push to master (CDK deploy + S3 sync + CF invalidation) — verified, run 21849957464
- [x] PR preview environments with comment links — workflow exists (not yet tested)
- [x] OIDC-based AWS authentication — working

### R8 - Landing Page Sections
- [x] Writing section — 4 featured blog posts with "More on the blog" link
- [x] Research section — NASA/NSSTC blurb, publication count, Google Scholar link
- [x] Cooking section — Instagram grid image + @carsons_cooking link
- [ ] Cooking section image — user needs to provide `site/images/instagram-grid.png`
- [x] Media section — No Dumb Questions podcast, COVID Face Shields interview
- [x] Updated hero tagline and nav links
- [x] Footer link row (GitHub, Blog, Scholar, Instagram)

## Non-Goals (for now)
- No tutorials section
- No blog integration (just link out)
- No CMS — project data lives in HTML

## Decided
- **Theme**: Dark-only
- **Domain**: codebycarson.com (registered in AWS/Route 53)
- **Hosting**: AWS (S3 + CloudFront) via CDK
- **IaC**: AWS CDK (Python)
- **CI/CD**: GitHub Actions with OIDC — deploy on merge, PR preview environments
- **Complexity**: Simple static landing page, no interactive app
- **Auth**: GitHub OIDC (no long-lived AWS access keys)

## Open Questions
- Thumbnail images for project cards (currently placeholder)
- Instagram grid screenshot needed for cooking section
