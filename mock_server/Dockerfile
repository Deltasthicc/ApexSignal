# Build context must be the REPOSITORY ROOT (same convention as
# services/core_api/Dockerfile and services/radio_ai/Dockerfile):
#
#     docker build -f mock_server/Dockerfile -t apexsignal-mock-server .
#
# mock_server reads contracts/fixtures/, which lives outside this
# directory.

FROM python:3.11-slim

WORKDIR /srv

COPY mock_server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mock_server/ ./mock_server/
COPY contracts/ ./contracts/

WORKDIR /srv/mock_server

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
