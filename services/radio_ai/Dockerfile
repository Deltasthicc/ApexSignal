# Build context must be the REPOSITORY ROOT, not this directory:
#
#     docker build -f services/radio_ai/Dockerfile -t apexsignal-radio-ai .
#
# radio_ai reads contracts/fixtures/ (ANALYZE_MODE=fixture) and writes
# each RadioAnalysisOutput to data/radio_analysis/{incident_id}.json,
# which core_api reads directly from disk rather than over HTTP -- see
# contracts/api_contract.md, "Output location." Neither is reachable
# from a build context rooted in this directory.
#
# Workstream D: deployment/ compose files need `context: .` with this
# dockerfile path, not `context: services/radio_ai`. Same bug class
# Tanish fixed on core_api's side -- see services/core_api/Dockerfile.

FROM python:3.11-slim

WORKDIR /srv

COPY services/radio_ai/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/radio_ai/ ./services/radio_ai/
COPY contracts/ ./contracts/

WORKDIR /srv/services/radio_ai

ENV RADIO_AI_PORT=8002
EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
