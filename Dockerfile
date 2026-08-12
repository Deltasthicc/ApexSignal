# Hugging Face Docker Space: static Next.js frontend + fixture-backed FastAPI.
# One origin means every live inspector request works without a second host.

FROM node:20-slim AS web-builder

WORKDIR /build/apps/web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web/ ./

ENV NEXT_OUTPUT=export
ENV NEXT_PUBLIC_CORE_API_BASE_URL=""
ENV NEXT_PUBLIC_RADIO_AI_BASE_URL=""
RUN npm run build

FROM python:3.11-slim

WORKDIR /srv
COPY mock_server/requirements.txt ./mock_server/requirements.txt
RUN pip install --no-cache-dir -r ./mock_server/requirements.txt

COPY mock_server/ ./mock_server/
COPY contracts/ ./contracts/
COPY --from=web-builder /build/apps/web/out ./frontend/

ENV STATIC_SITE_DIR=/srv/frontend
ENV PORT=7860
EXPOSE 7860

CMD ["uvicorn", "mock_server.server:app", "--host", "0.0.0.0", "--port", "7860"]
