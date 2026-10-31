# JanSetu task status

## Delivered in this build

- Next.js civic-editorial frontend, searchable source-linked 22-record directory, English/Telugu assistant, OAuth entry, citizen dashboard and grievance tracking.
- FastAPI/MySQL-compatible schema, additive Alembic migration, idempotent catalog loader, privacy-bounded evidence retrieval, grievance workflow, private attachment routes, staff workspace and independent appeal API.
- Docker/Compose runtime, API health, route manifest, source documentation and isolated SQLite API tests.

## Open follow-ups

- Verify 20 service profiles fully against authoritative current sources before changing any profile to fully verified. Current inventory remains 21 partially verified and one not verified.
- Add authenticated department integrations only after explicit authorization and real API contracts exist; until then preserve JanSetu-only references.
- Add verified geospatial boundary data before claiming area or jurisdiction precision.
- Add physical attachment deletion only if the managed storage platform exposes an authorized runtime deletion operation.
- Keep any response-time targets internal to JanSetu and separately distinguish them from government timelines.

## Operating constraints

The managed MySQL database is shared across development, tests and production; never use destructive test resets. Pytest uses isolated in-memory SQLite. No synthetic citizen cases, government ticket numbers or official-affiliation claims are seeded.
