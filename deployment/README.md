# deployment — Workstream D

## Local, full-stack

```bash
docker compose -f deployment/docker-compose.yml up --build
```

Brings up `radio_ai` (8002), `core_api` (8001), and `web` (3000). Set
`ANALYZE_MODE=live` and `EVALUATE_MODE=live` in the respective `.env`
files once the real model/retrieval implementations are ready; both
default to fixture mode.

## Hugging Face Space

The repository root is a ready-to-build Hugging Face Docker Space:

- `Dockerfile` exports the Next.js frontend during the image build.
- `mock_server` serves both the exported website and `/v1/*` fixture API on
  port `7860`, so the live inspector works on the Space without Render/Vercel.
- Circuit geometry and fixtures are baked into the image; the judged path has
  no runtime dependency on third-party APIs.

Local Docker Compose remains the full multi-service development path.

### Free-account static fallback

Free Hugging Face accounts may be restricted from creating new Docker Spaces.
`scripts/build_static_fixtures.py` compiles the same contract fixtures into the
browser bundle. Build with `NEXT_PUBLIC_DATA_MODE=embedded` and deploy `out/`
as a Static Space. The UI stays fully interactive and labels the mode as a
fixture demo; it does not claim live model execution.
