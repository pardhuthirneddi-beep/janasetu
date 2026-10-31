# JanSetu — implementation plan

## Product implementation

Build a responsive Telangana civic-services application using Next.js App Router, TypeScript and Tailwind for the frontend, plus a separate FastAPI/Pydantic API using SQLAlchemy, Alembic and pytest. During development, the Next server on port 3000 proxies `/api/v1/*` to FastAPI on private port 8000. A root Dockerfile runs both processes in one published container and exposes only the frontend listener. The API reads the managed `DATABASE_URL` at runtime; its MySQL-compatible dialect uses normalized relational tables, foreign keys, indexes and additive migrations. Catalog seeds are repeatable and additive; tests must not reset or delete shared database rows.

Provide a public landing page, service directory and source-labelled details, English/Telugu topic assistant, Manus OAuth sign-in, logged-out citizen dashboard, guided grievance creation and reference tracking, and role-protected staff/admin workspace. Backend identity, roles and status-transition validation are authoritative. Service navigation and government links are distinct from JanSetu's simulated grievance workflow. Every relevant grievance view states that a JanSetu ticket is not a government submission. Staff notes are private; public updates and status history are separately exposed. Demo analytics and any seeded/demo case records are clearly synthetic. Staff access is provisioned, not granted by self-registration.

The catalog targets 22 source-linked records in seven civic categories. Every record has an official-source URL, review date, jurisdiction metadata and an honest verification status: 21 partially verified and one not verified; none fully verified. Facts about eligibility, required documents, fees, timelines or procedures are shown only when supported by the cited source, otherwise “Not verified.” Area and jurisdiction selectors are clearly marked as demonstration values unless authoritative boundaries are verified. The assistant locally routes a normalized topic and retrieves public evidence using conservative keyword overlap and a detail-sufficiency gate. Only the normalized topic and retrieved public evidence may reach the configured managed model; raw questions, grievance narratives and attachments do not. Parse and validate structured replies, source IDs and uncertainty. Complaint-summary drafts are deterministic local extracts, preserve the original complaint, and are never sent to the model.

Use Manus OAuth: bind state to a single-use nonce cookie, exchange codes server-side, map verified `openId` identities to users and create citizen accounts only after successful identity resolution. Validate Preview project JWTs (HS256 signature, project ID and expiry) against the platform secret and resolve their openId against app users. Use the exact `webdev_app_session` cookie; normal app sessions are opaque, hashed in storage, expiring and revocable. Staff roles are provisioned by an authorized operator. Cookie behavior must support cross-site HTTPS Preview (`SameSite=None; Secure`) and keep plain HTTP local handling separate. No password store, test citizen, development login bypass, or fabricated signed-in user.

Private attachment metadata and random storage object keys are stored in the relational DB. Enforce ownership/staff authorization, size, MIME and file-signature checks; use the managed storage presign API and only issue authorized signed downloads. Physical object deletion is unavailable; account-removal copy must explain that access can be removed while stored objects may remain. Do not claim an attachment has been physically erased.

Implement the relational schema for users, sessions, departments, jurisdictions, services, service sources, knowledge documents/chunks, grievances, attachment metadata, assignments, status history, internal notes, action reports, appeals, feedback, SLA policies, notifications, audit logs and AI evaluation runs. Keep structured records in typed relational columns rather than a generic JSON blob. Provide safe seed/migration scripts, Docker, `.env.example`, README, architecture and development-log documentation.

## Project structure

- `frontend/app/`: landing, service list/detail, assistant, login, dashboard, grievance submit/track and staff routes.
- `frontend/components/`: accessible navigation, service discovery, citations, forms, timelines, staff actions and shared UI.
- `frontend/lib/`: typed API client, validation, formatting and role/session helpers.
- `frontend/public/manus-routes.json`: actual App Router route manifest.
- `backend/app/main.py`: FastAPI health, auth, public directory/assistant and protected grievance/staff endpoints.
- `backend/app/core/`: runtime settings, DB/session handling, security and errors.
- `backend/app/models/`, `backend/app/schemas/`: relational models and validated contracts.
- `backend/app/services/`, `backend/app/ai/`: lifecycle logic, authorization, local retrieval, model boundary and deterministic summaries.
- `backend/alembic/`, `backend/tests/`: additive migrations and safe pytest coverage.
- Root: Dockerfile, compose file, pnpm workspace/config, `.env.example`, README, architecture and operating notes.

## Design

**Design Movement:** Civic Editorial: a contemporary public-service editorial aesthetic with institutional restraint and modern product clarity.

**Core Principles:** legibility before decoration; evidence and process stay visible; a warm, humane tone without false authority; operations favor predictable actions.

**Color Philosophy:** warm ivory `#F4F3EC` makes the experience approachable; deep forest `#173D37` anchors trust; signal lime `#C7ED75` marks primary actions; civic coral `#D96E50` signals attention; quiet borders and secondary surfaces use `#D8D9CE` and `#E8E9DE`.

**Layout Paradigm:** asymmetric editorial landing with left-aligned narrative, compact civic illustration and full-width discovery. Citizen/staff screens use a compact operational shell, thin rules, generous whitespace and responsive columns rather than repetitive dashboard cards.

**Signature Elements:** original bridge/linked-path mark; monospaced case references and source metadata; numbered status timeline that clarifies what happens next.

**Interaction Philosophy:** direct controls, plain-language errors, nearby source links, explicit explanations for status changes, and motion that never obscures controls.

**Animation:** subtle 150–400 ms entrances/focus/dialog/timeline motion; respect reduced-motion; no complex form or staff-table motion. Smooth scrolling is restricted to the public landing page and must retain native touch behavior.

**Typography System:** Fraunces display headlines, Manrope interface/body, Geist Mono references/timestamps, and a local Telugu-capable fallback. Use a responsive scale and efficient loading.

**Brand Essence:** an evidence-led route through Telangana public services and transparent local grievance workflow; trustworthy, humane and precise.

**Brand Voice:** citizen-centred headings and explicit next-step actions distinguish official information from JanSetu guidance. Example: “Government services shouldn't feel complicated.” “Your request is recorded here—not sent to a government department.”

**Wordmark & Logo:** original bridge/linked-path symbol with a carefully typeset JanSetu wordmark; never use a government seal or imitate a government logo.

**Signature Brand Color:** deep forest `#173D37`, balanced with signal lime.

## Material constraints

The managed database is MySQL-compatible; do not claim PostgreSQL, pgvector, PostGIS, embeddings or full-text search. Use keyword overlap and relational area labels. The platform does not supply government submission integrations, customer-notification delivery, verified service coverage, physically deletable object storage or authoritative geographic boundary data. SLA values are JanSetu policies, not official government deadlines. Never fabricate official affiliation, service facts, case statuses, citizens or live statistics. Evidence gaps remain explicit.