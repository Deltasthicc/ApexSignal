# Build context must be the REPOSITORY ROOT, not this directory:
#
#     docker build -f services/core_api/Dockerfile -t apexsignal-core-api .
#
# core_api reads three things that live outside services/core_api/ and
# cannot be reached from a build context rooted here:
#   - services/evidence_memory/   the retrieval/telemetry library it imports
#   - storage/schema.sql          applied verbatim at runtime by app/db.py
#   - contracts/fixtures/         served by EVALUATE_MODE=fixture
#
# Workstream D: deployment/ compose files need `context: .` with this
# dockerfile path, not `context: services/core_api`.

FROM python:3.11-slim

WORKDIR /srv

COPY services/core_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/core_api/ ./services/core_api/
COPY services/evidence_memory/ ./services/evidence_memory/
COPY storage/schema.sql ./storage/schema.sql
COPY contracts/ ./contracts/

WORKDIR /srv/services/core_api

ENV CORE_API_PORT=8001
ENV CORE_API_DB_PATH=/srv/storage/incidents.db
EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
