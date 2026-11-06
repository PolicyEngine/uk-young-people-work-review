# Wrappers for the README commands. Heavy targets (model, build) take
# /tmp/pe-heavy.lock themselves or must be run inside it.
.PHONY: install install-model test lint format generate generate-mock guard model households build build-mock

MEASURES = $(shell uv run python -c "from young_people_work.reforms import REFORMS; print(' '.join(r.id for r in REFORMS if r.computable))")

install:
	uv sync --locked --extra dev
	cd dashboard && bun install --frozen-lockfile

install-model:
	uv sync --locked --extra model --extra dev

test:
	uv run pytest -q
	cd dashboard && bun run test

lint:
	uv run ruff check .
	uv run ruff format --check .
	cd dashboard && bun run lint

format:
	uv run ruff check --fix .
	uv run ruff format .

generate:
	uv run young-people-work generate

generate-mock:
	uv run young-people-work generate --status mock

guard:
	uv run python scripts/check_public_data.py

# One measure per process, each taking the heavy-run lock in turn; then the
# package, then assembly. Needs the HF login (docs/RUNBOOK.md).
model:
	for m in $(MEASURES); do uv run young-people-work model-run --measure $$m || exit 1; done
	uv run young-people-work model-run --package
	uv run young-people-work generate --mode model $(if $(STATUS),--status $(STATUS),)

households:
	uv run young-people-work households $(FILE) --out $(OUT)

build:
	cd dashboard && bun run data && bun run build

build-mock:
	cd dashboard && bun run data && NEXT_PUBLIC_MOCK=1 bun run build
