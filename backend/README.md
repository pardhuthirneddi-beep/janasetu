# JanSetu backend

FastAPI for JanSetu's independent public-service guide and local grievance workflow. It does not submit cases to or claim affiliation/integration with government departments. No outbound customer notifications are configured.

## Run and seed

Use Python 3.12. From the repository root, create `backend/.venv`, install `backend/requirements.txt`, then run `pnpm dev` to start FastAPI on loopback port 8000 and Next.js on port 3000. The web container builds its own `/opt/venv` and serves the same API privately. Copy the root `.env.example` to an untracked `.env` only for local credentials; never commit secrets.

`DATABASE_URL` is the managed MySQL-compatible relational database. Apply the additive Alembic migration when intending to prepare that shared development/production database:

```sh
cd backend && .venv/bin/alembic upgrade head
.venv/bin/python -m app.load_catalog
```

Catalog seeding is idempotent and does not overwrite existing claims. The shared database is never truncated or reset by app startup or tests. API tests use isolated in-memory SQLite only.

## Authentication and roles

New accounts are created only after the Manus OAuth authorization-code exchange returns a verified `openId`. `state` binds the callback URL and a single-use, short-lived nonce cookie to the initiating browser. Sessions are opaque, expiring and revocable; only token hashes are stored. The fixed `webdev_app_session` cookie is `SameSite=None; Secure` for HTTPS Preview and published origins. Preview project JWTs are accepted only after HS256 signature, expiry and `MANUS_PROJECT_ID` validation, then mapped to an existing application user/role. There is no simulated demo user or separate password store.

Citizens may access their own grievances, request feedback and appeal eligible JanSetu decisions. Staff manage the case workflow and see internal notes. Reviewers can review appeals independently; self-review and review by the assigned handler are rejected. Staff roles are provisioned by an authorized operator after OAuth sign-in, never by a public endpoint.

```sh
cd backend
.venv/bin/python -c 'from app.main import provision_staff; provision_staff("<verified-openId>", "staff")'
```

Roles: `staff`, `reviewer`, `admin`. Run provisioning only in an operator-controlled environment pointed to the intended `DATABASE_URL`; protect shell history.

## Service catalog and assistant

The shared seed data is `data/service_catalog.json`, copied to `backend/app/data/service_catalog.json`. It contains 22 source-linked records across seven categories. The catalog deliberately marks 21 profiles partially verified and one not verified; none is presented as fully verified. Procedure, eligibility, documents, fees and timelines are displayed only when supported by the cited official source; unsupported details read “Not verified.” This does not meet the 20 fully verified profiles target.

Assistant topic routing is local. Retrieval ranks only public source chunks using keyword overlap and a conservative evidence-sufficiency gate. If configured, the managed model receives the normalized topic, response language and retrieved public source evidence only; it never receives the raw question, grievance narrative or attachments. Its structured response is Pydantic-validated, and only cited IDs from retrieved records are accepted. With no adequate evidence, the assistant abstains. Complaint summaries are deterministic local extracts.

## Private attachments and citizen-facing records

Attachment uploads are validated for authorized ownership, size, MIME and file signature, then transferred using the managed private-storage API. Only random object keys and application metadata are stored in MySQL. Downloads are authorized per owner/staff and served through private signed URLs. Physical object deletion is not exposed by the managed storage service: application access can be removed, but stored bytes may remain; user-facing messaging states this clearly.

Citizens receive their public status history (including actor role labels) and Action Taken public summaries, not staff notes or private report details. Status transitions are validated server-side. References beginning `JS-` are JanSetu-local IDs, never government ticket IDs. Any SLA is internal to JanSetu, not an official government deadline. Jurisdiction/area selections are demonstration values unless backed by verified boundary data.

## Schema and tests

Typed relational models include users/sessions, departments, jurisdictions, services/sources, public knowledge chunks, grievances, attachment metadata, assignments, status history, private notes, action reports, appeals, feedback, SLA policies, notifications, audit events and AI evaluation runs. Migrations are additive; no migration is run automatically on startup.

```sh
cd backend && .venv/bin/pytest -q tests
```

The test suite creates and drops only isolated in-memory SQLite structures. It does not connect to the shared `DATABASE_URL`, migrate, seed or delete managed records.
