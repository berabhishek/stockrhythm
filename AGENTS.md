# Repository Guidelines

## Project Structure & Module Organization
- `apps/backend/`: FastAPI backend engine, providers, risk engine, and data orchestration.
- `apps/mock_exchange/`: Simulator used for local testing.
- `apps/dashboard/`: Frontend UI.
- `packages/stockrhythm-sdk/`: Python SDK (src layout in `packages/stockrhythm-sdk/src`).
- `packages/stockrhythm-cli/`: CLI scaffolding tool (src layout in `packages/stockrhythm-cli/src`).
- `strategies/`: Sample and user strategies.
- `tests/`: `tests/unit`, `tests/integration`, `tests/e2e`.

## Build, Test, and Development Commands
```bash
uv sync
```
Installs workspace dependencies using uv (preferred over pip).

```bash
docker-compose up -d backend redis
```
Starts backend and infrastructure services locally.

```bash
uv run uvicorn apps.backend.src.main:app --port 8000
```
Runs the backend directly for development.

```bash
uv tool install packages/stockrhythm-cli --editable
```
Installs the CLI in editable mode for local iteration.

## Coding Style & Naming Conventions
- Python: 4-space indentation, `snake_case` for functions/vars, `PascalCase` for classes.
- Prefer the existing `src` layout and keep imports within workspace packages explicit.
- No formatter/linter is configured; keep style consistent with surrounding files.

## Testing Guidelines
- Framework: `pytest` with `pytest-asyncio` (asyncio mode is strict).
- Naming: tests live in `tests/` and use `test_*.py`.
- Always add unit tests for new features.
- Run the relevant tests and ensure they pass before reporting completion.
- Run locally:
```bash
uv run pytest
```

## Commit & Pull Request Guidelines
- Commits follow Conventional Commits (e.g., `feat: ...`, `chore: ...`).
- PRs should include a clear description, linked issues, and screenshots for UI changes.

## Security & Configuration Notes
- Do not read or modify `.env`; credentials are managed manually by maintainers.
- Do not delete or truncate database files (e.g., `paper_trades.db`).
- Do not start or stop background services on behalf of users; provide commands instead.
