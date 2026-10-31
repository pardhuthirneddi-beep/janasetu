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
