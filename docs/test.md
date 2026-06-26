# Test Strategy

## Goals

The test suite protects three contracts:

1. Device adapters return stable results under mocked conditions.
2. FastAPI routes expose callable, OpenAPI-documented endpoints for agents.
3. The frontend store and production build keep working against the backend API.

## Commands

Backend unit tests:

```bash
source .venv/bin/activate
python -m pytest test/ -q --ignore=test/test_integration_real.py
```

Frontend tests and build:

```bash
cd frontend
npm test -- --run
npm run build
```

Startup script syntax:

```bash
bash -n start_server.sh
```

Privacy scan for public files:

```bash
git grep -n -E '<real-lan-subnet>|<real-email>|<secret-reference>|<device-id>' -- . ':!*.lock' || true
```

The final command should print nothing for tracked public files.

## Coverage Map

| Area | Tests |
|---|---|
| API routes | `test/test_api.py` |
| Hue service | `test/test_hue_service.py` |
| Wemo service | `test/test_wemo_service.py` |
| Meross local HTTP | `test/test_meross_service.py` |
| Garage notifications | `test/test_notification_service.py` |
| Database/history | `test/test_database.py` |
| Dynamic scheduler | `test/test_dynamic_scheduler.py`, `test/test_action_executor.py` |
| Frontend store | `frontend/src/stores/deviceStore.test.ts` |

## OpenAPI Assertions

`test/test_api.py` should keep explicit checks for `/openapi.json`:

1. The schema returns 200.
2. Core endpoints are present.
3. Garage toggle is POST-only.
4. The SPA catch-all route is not included in OpenAPI.

These tests make OpenAPI-first agent usage safer because they catch accidental schema regressions.

## Live Integration Tests

`test/test_integration_real.py` is intentionally excluded from default test runs. It may touch real devices and should only run with explicit local intent.

## CI

GitHub Actions currently runs backend pytest and frontend Vitest on PRs. Local verification should also run `npm run build` because build errors can pass unit tests.
