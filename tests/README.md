# tests — cross-cutting integration

Per-service unit tests live next to their service
(`services/radio_ai/tests/`, `services/core_api/tests/`). This
directory is for tests that span more than one service.

- `radio_ai/` and `core_api/` here are for contract-conformance
  checks: validate that each service's real (non-fixture) output still
  matches `contracts/schemas/*.json`, run against JSON Schema directly
  rather than against the Pydantic models used internally.
- `integration/` is for end-to-end checks that exercise the full replay
  -> radio_ai -> core_api -> assessment pipeline using
  `data/incident_manifest.json` fixtures, once real implementations
  exist. Skip these until Workstreams A-C have real (non-fixture) data.
