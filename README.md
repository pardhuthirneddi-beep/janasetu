# JanSetu

An independent, evidence-led Telangana public-service directory and transparent JanSetu-only grievance workflow. It is not an official government site; JanSetu grievance references are not government submissions.

## Stack and local development

- `frontend/`: Next.js App Router, TypeScript and Tailwind.
- `backend/`: FastAPI, Pydantic, SQLAlchemy, Alembic and pytest.
- Managed runtime data: MySQL-compatible `DATABASE_URL`; verified public-source metadata is maintained with the service catalog.

Use Node 22, pnpm 11 (pinned in the root `package.json`) and Python 3.12. Copy `.env.example` to an untracked `.env`, install root Node and backend Python dependencies, then run `pnpm dev`. Next.js listens on port 3000 and proxies `/api/v1/*` to the private FastAPI process on port 8000.

Apply the additive Alembic revision with `cd backend && .venv/bin/alembic upgrade head`, then seed the catalog idempotently with `cd backend && .venv/bin/python -m app.load_catalog`. Both development and published environments share the managed database: migrations add schema, seeding does not overwrite existing claims, and tests use isolated SQLite only. Never reset, truncate or use destructive test fixtures against the managed database.

Run isolated API tests with `backend/.venv/bin/pytest -q backend/tests`. Run the UI production check with `pnpm --dir frontend build`.

## Deployment

Docker builds one container: the optimized Next.js app is public on `PORT` (3000 by default); FastAPI listens only on loopback port 8000. Readiness is checked at the unauthenticated `/api/v1/health` endpoint. The Dockerfile installs frontend and backend dependencies itself; sandbox-installed packages are not required at runtime.

## Integrity and privacy

The directory has 22 curated entries across seven categories: 21 are marked **partially verified** and one **not verified**; none is represented as a fully verified profile. Unsupported details read “Not verified.” The current evidence does not meet the 20 fully verified profiles target.

The assistant uses local topic routing and keyword overlap over public source chunks. It sends only the normalized topic and retrieved public evidence—not the raw citizen question, grievance narrative or attachments—to the configured model. Complaint summaries are deterministic local extracts, not model-generated. JanSetu has no department-submission integration or outbound citizen-notification service. Internal notes remain private. Physical removal of stored attachment objects is unavailable, and account-removal messaging must disclose that limitation. Any SLA shown is a JanSetu-only service target, never a government deadline; area/jurisdiction values must be labelled as demonstrations unless authoritative boundaries are verified.
