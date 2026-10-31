# Development log

## 2026-10-31 — project initialization

- Initialized a managed Web project with server and database capability; no application tables or code were supplied.
- Chose the requested Next.js + TypeScript + Tailwind frontend and separate FastAPI backend. The intended single-container runtime exposes only Next.js and keeps FastAPI loopback/private.
- Confirmed the managed relational service is MySQL-compatible. No PostgreSQL, pgvector or PostGIS capability is available; use normalized relational tables and conservative keyword retrieval without claiming embeddings or full-text search.
- Kept source certainty bounded: the catalog target remains 21 partially verified profiles and one not verified, with no fully verified profile.
- Preserved privacy boundary: do not send raw assistant questions, grievance text or attachments to the managed model. Summary drafts are local and extractive.
- Implementing real Manus OAuth, app-owned opaque DB sessions and server-side role authorization. No demo citizen/password login.
- Store only attachment keys and ownership metadata in MySQL; physical object deletion is unavailable and will not be promised.
- Government submission, outbound customer notifications, official SLA commitments and fabricated analytics are out of scope.

## 2026-10-31 — implementation and validation

- Implemented the Next.js citizen-facing directory, assistant, OAuth entry, dashboard, grievance submission/tracking, and role-sensitive staff/appeal workspace; added a generated editorial bridge image through managed storage.
- Added 22 source-linked catalog rows across seven categories (21 partially verified; one not verified; none fully verified) and idempotently loaded them into the managed database.
- Applied the additive Alembic schema revision to the managed MySQL database. Database TLS options are normalized to PyMySQL with CA and hostname verification enabled; no destructive reset was performed.
- Added private managed-storage upload/download handlers, actor-labelled public status history, citizen-visible public Action Taken summaries, and staff-private internal data separation.
- Backend tests pass against isolated in-memory SQLite (10 tests). The optimized Next.js build and TypeScript check pass. The Preview health, nine-route manifest and source-backed service API return successfully. No Preview login was simulated; actual OAuth remains browser-mediated.
- Full verification of 20 service profiles, verified geographic boundaries, government complaint APIs, outbound citizen notification and physical object deletion remain explicitly unavailable/open.


## 2026-10-31 — existing Preview rendering repair and civic redesign

- Audited the full existing frontend route/component tree, Tailwind v4/PostCSS setup, CSS imports, dependencies, assets and route manifest. The live app stylesheet and both global stylesheets were already loading; the reported default appearance came from an external-only Google Fonts import and a global anchor reset that made text links look unstyled. Preserved the app structure and API flows; removed those fragile presentation dependencies rather than creating a separate demo.
- Bundled Fraunces, Manrope and DM Mono locally; refreshed the existing CSS system to warm white, deep navy and subtle teal; preserved and recolored the original bridge wordmark; constrained the existing bridge illustration and fixed tablet/phone layout proportions. Added an accessible mobile disclosure navigation and disabled the supported Next.js dev badge.
- Added home-only Lenis smooth scrolling, GSAP/ScrollTrigger section reveals, reduced-motion-aware Framer Motion route entrances and CSS hover/focus treatment. The browser confirmed local fonts are available, the bridge image loads, Lenis activates, scroll reveals become visible, and the test captured no client runtime errors.
- Verified the directory’s existing search and category filter in-browser (a “birth” query returned the relevant two records; the Health filter returned its three records; all 22 cards restored). Browser navigation from Services to the Birth certificate detail worked and showed the official source link. All nine page routes and `/manus-routes.json` returned HTTP 200; the manifest matches App Router source.
- Captured final Preview layouts at desktop (1280×1000), tablet (768×1024) and phone (390×844). Frontend TypeScript and the production `next build` passed, including Next lint/type checks. The isolated backend suite remains 10/10 passing; its only output was upstream/Pydantic deprecation warnings. No grievance was submitted and no synthetic cases were added.
- Preview was restarted successfully after the production build. Public publication was not requested and was not triggered.
