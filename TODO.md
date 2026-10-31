# JanSetu delivery outcomes

## Completed implementation outcomes

### Public service discovery and source integrity
- [x] Ship a public Telangana landing page and searchable directory/detail pages with 22 curated service records across seven civic categories. Every record links to official source material and shows its review date, jurisdiction and verification metadata. Preserve the audit count: 21 partially verified and one not verified; do not present any profile as fully verified. Show eligibility, documents, fees, timelines and procedures only when supported by the cited official source; otherwise show “Not verified.” Keep official service navigation, JanSetu’s simulated grievance workflow and external government portal links distinct. Do not imply government affiliation or submission integration.
- [x] Mark jurisdictions as source scope/demonstration unless verified boundaries exist. Do not fabricate service facts, affiliation, government statuses, citizens or live statistics.

### English/Telugu assistant
- [x] Use local topic routing and keyword-overlap retrieval over public source records with a conservative evidence-sufficiency gate. A managed model call receives only the normalized topic, requested response language and retrieved public evidence—not the citizen’s raw question, grievance narrative or attachments. Validate structured output and source IDs; include uncertainty and citations. Complaint summaries are deterministic local extracts that preserve the original narrative and are neither model-generated nor transmitted.

### Citizen identity and private uploads
- [x] Use Manus OAuth, starting from the browser-visible application origin, binding state to a short-lived nonce cookie, exchanging the code server-side and mapping verified `openId` to an application user. Create a citizen only after valid identity. Provision staff roles only by an authorized operator. Do not invent a signed-in citizen or add a password store.
- [x] Validate Preview HS256 project JWT signatures with `MANUS_JWT_SECRET`, `MANUS_PROJECT_ID` and expiry, then resolve through application user permissions. Use `webdev_app_session`; persist only hashes of expiring/revocable opaque app sessions. HTTPS cookies use `SameSite=None; Secure`; plain local HTTP is handled separately. Never bypass real auth in development.
- [x] Provide a logged-out state, citizen dashboard and authenticated case ownership. Store private attachment metadata and random object keys; validate authorization, size, MIME and file signatures; use managed private storage and signed downloads only after owner/staff authorization. Do not claim physical object deletion; disclose that app access can be removed while stored attachment bytes may remain.

### JanSetu grievance and staff operations
- [x] Implement guided grievance creation, JanSetu-local references and tracking. Clearly state that tickets stay inside JanSetu and are not sent to a government department; no external government submission or customer-notification channel exists.
- [x] Provide role-protected staff/admin actions for assignment, validated status transitions, status history, public updates, private notes, Action Taken Reports, resolution, citizen feedback and independent appeal review. Backend authorization and transition validation are authoritative. Staff/private notes and report details are excluded from citizen output. Status history identifies the actor role and change.
- [x] Keep operational analytics honest; do not create fabricated demo cases or present JanSetu counts as government data. Any response-time target is labelled an internal JanSetu goal, not a government deadline.

### Persistence and operations
- [x] Serve a Next.js App Router/TypeScript/Tailwind frontend and separate FastAPI/Pydantic API. Next.js development rewrites `/api/v1/*` to private FastAPI; Docker runs both in one container, exposes only the web listener, and reads managed `DATABASE_URL` at runtime.
- [x] Use the managed MySQL-compatible relational database, normalized tables, foreign keys and indexes. No PostgreSQL, pgvector, PostGIS, embedding or MySQL full-text claims. Keep jurisdiction examples bounded. Provide additive Alembic migration and idempotent catalog seeding. Development/publishing share the database; tests use isolated SQLite and do not reset shared data. Do not invent backup/restore.
- [x] Create typed relational models for users, sessions, departments, jurisdictions, services/sources, knowledge documents/chunks, grievances, attachment metadata, assignments, status history, internal notes, action reports, appeals, feedback, SLA policies, notifications, audit logs and AI evaluation runs. Structured application fields are relational rather than a generic JSON blob.
- [x] Include isolated pytest coverage, `.env.example`, Dockerfile, docker-compose, README, ARCHITECTURE, DEVELOPMENT_LOG, TASKS, safe catalog seed script and a static route manifest matching actual pages.

### Evidence and limitations
- [x] Do not overstate coverage: disclose that 20 fully verified profiles remain an explicit research gap, preserve 21 partially verified/one not verified, and show supported facts only.
- [x] Do not claim government integration/affiliation, customer notifications, PostgreSQL/pgvector/PostGIS, physical object deletion, verified boundaries, official SLA commitments or live government metrics. Keep unavailable capabilities explicit.

## Open research gap

- [ ] Independently verify at least 20 service profiles against current authoritative sources before changing any record’s status to fully verified; current catalog coverage intentionally remains 21 partially verified and one not verified.

## Existing-site rendering, redesign and motion outcomes

### Rendering diagnosis and durable styling
- [x] Preserve the existing project and functionality. Keep the current Next.js App Router structure, Tailwind/PostCSS setup, source-linked catalog, route manifest, components and assets; do not create a separate demo or replace the working application.
- [x] Inspect all existing frontend pages, components, CSS, dependencies, public assets, route manifest and managed Preview. Confirm the root layout imports both global stylesheets, the Tailwind v4 PostCSS plugin is configured, the generated stylesheet returns HTTP 200 and contains the app CSS, all nine declared routes are present, and the inspected live Preview’s browser console is clear. Root causes behind the reported rendering were not a missing global CSS import: the old theme relied on remote Google Fonts, while the global anchor reset removed visible link decoration. Remove both dependencies rather than masking the issue with per-page overrides.
- [x] Make editorial typography reliable in the managed Preview: remove the external Google Fonts CSS dependency and bundle Fraunces, Manrope and DM Mono with the frontend. Keep Tailwind v4’s CSS-first import/PostCSS configuration functioning; do not hide the issue with per-page or temporary overrides.

### Visual system and responsive navigation
- [x] Redesign the existing JanSetu interface in a premium civic-editorial style using deep navy, warm white and subtle teal. Provide responsive editorial typography; a polished navigation/header; a balanced, size-constrained version of the existing hero artwork; and consistent spacing, surfaces, borders, shadows, cards, buttons, forms and section layouts. Keep the supplied bridge illustration and original wordmark; do not discard existing assets.
- [x] Make layouts intentionally responsive across mobile, tablet and desktop. Implement a real accessible mobile navigation control instead of squeezing desktop links into a narrow header. Keep focus states, hit targets and long service titles usable at small widths.

### Motion and interaction
- [x] Use Lenis for restrained smooth scrolling on the public landing page while keeping touch scrolling native. Use GSAP with ScrollTrigger for a small number of meaningful section reveals, Framer Motion for subtle component/page transitions, and deliberate CSS hover/focus feedback. Respect reduced motion, keep controls immediately usable, and avoid excessive effects or animation in forms and operational tables. Add dependencies only because the existing package previously had none of these libraries.

### Existing functionality and browser verification
- [x] Preserve and verify all existing routes and navigation: Home, Explore services, Ask a question, source-backed service details and official links, citizen login/dashboard, grievance create/track, and role-protected staff/appeal areas. Keep existing forms, directory search/category filter and API integrations intact; do not add a fake login, sample citizen or government submission.
- [x] Run the project and inspect the actual managed browser Preview after the redesign. Confirm the served global stylesheet, local fonts, no observed client runtime errors or failed hero/font assets, navigation links and route manifest, all page renders, and mobile/tablet/desktop layouts. Correct defects found, then recapture the Preview; the final redesigned UI is visibly present after the production build and Preview restart.
