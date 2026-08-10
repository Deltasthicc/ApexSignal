# deployment — Workstream D

## Local, full-stack

```bash
docker compose -f deployment/docker-compose.yml up --build
```

Brings up `radio_ai` (8002), `core_api` (8001), and `web` (3000). Set
`ANALYZE_MODE=live` and `EVALUATE_MODE=live` in the respective `.env`
files once the real model/retrieval implementations are ready; both
default to fixture mode.

## Hugging Face Space (optional)

If time allows, package the demo as a Hugging Face Space for judge
accessibility outside the local machine:

- Space SDK: Docker (reuses `deployment/docker-compose.yml` services,
  or a single combined Dockerfile if the Space only supports one
  container).
- Cache models and `data/` assets into the Space image at build time;
  the judged path must not depend on external network calls at runtime.
- Document the Space URL in `../docs/submission/project_links.md` once
  live (see `docs/` — not yet created; add when submission docs are
  written).

Local Docker Compose remains the demo fallback regardless of whether
the Space deployment works.
