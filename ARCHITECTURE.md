# JanSetu architecture

## Request path

Browser pages are served by Next.js App Router on port 3000. Relative `/api/v1/*` requests are rewritten to FastAPI on loopback port 8000. Development starts both with `scripts/dev.sh`; Docker builds both applications in one image and starts FastAPI privately with `scripts/start.sh`. The unauthenticated health endpoint is `/api/v1/health`.

## Persistence and evidence

SQLAlchemy uses runtime `DATABASE_URL` with the managed MySQL-compatible database. The Alembic schema migration is additive; catalog seeding is idempotent and does not overwrite existing claims. Tests use isolated in-memory SQLite fixtures, never the shared database. Typed relational tables cover accounts, services and sources, jurisdictions/departments, grievance lifecycles, files, staff activity, feedback, appeals, internal policy and audit/evaluation events.

The catalog contains 22 public-source-linked records across seven categories: 21 partially verified and one not verified. None is a fully verified profile. Unsupported facts read “Not verified.” Jurisdiction/area selections are demonstration values unless a boundary source is verified. JanSetu is not an official government service and has no authorized government intake, notification channel, verified boundary dataset or government SLA.

## Identity and authorization

Manus OAuth verifies an identity before creating a citizen account. The browser-visible origin forms the callback, and the callback validates its single-use nonce cookie before exchanging authorization code. Opaque app sessions are expiring/revocable and only their token hashes are stored. Preview project JWTs require valid HS256, expiry and project ID and resolve through existing application users. Authorization and status transitions are enforced by the API, not the frontend.

## AI privacy

Topic routing runs locally. Retrieval ranks only public evidence by keyword overlap and a conservative sufficiency threshold. The configured model receives the normalized topic, requested language and retrieved public passages only; the citizen’s raw question, complaint narrative and attachments are excluded. Output is Pydantic-validated, source IDs must refer to retrieved evidence, and responses state uncertainty. Complaint summaries are local extractive drafts.

## Private files and case details

The app validates citizen authorization, upload size, MIME and signature before transferring bytes to managed private storage. MySQL stores a random object key plus owner and grievance metadata; signed downloads are issued only after authorization. Private staff notes and report details are excluded from citizen output. Citizens see public status updates with actor-role labels and public Action Taken summaries. Physical object deletion is unavailable; the interface states that removal of app access cannot guarantee physical erasure.

## Honest operations

Staff overview counts represent real JanSetu records and explicitly are not synthetic or government statistics; the queue does not seed fabricated citizen cases. Any response-time target is an internal JanSetu goal, not a government deadline. No government service details, affiliations, official case statuses, live statistics or capabilities absent from the platform are fabricated.
