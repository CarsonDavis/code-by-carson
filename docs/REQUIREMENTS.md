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
- [x] Site title: "Carson Davis"
- [x] Tagline: "Software engineer with too many hobbies and not enough shelf space."
- [x] No nav links in hero (links are in-body and footer)

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
- [x] Live Sites section — 3 project cards + "Visit my GitHub →" button
- [x] Deep Dives section — 2x2 image card grid with blog cover images + "Read more posts →" button
- [x] Cooking section — side-by-side layout (image + text) + "Follow @carsons_cooking →" button
- [x] Media section — No Dumb Questions podcast, COVID Face Shields interview
- [x] Research section — 7 featured publications list + "View all on Google Scholar →" button
- [x] Footer link row (GitHub, Blog, Scholar, Instagram)

### R9 - Open Graph / Link Previews
- [x] OG meta tags (title, description, image, url)
- [x] Twitter card meta tags
- [x] Composite OG image (1200x630, 6-panel mosaic)

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
- Favicon for browser tab
