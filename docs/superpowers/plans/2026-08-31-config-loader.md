# v0.1 Config Loader Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Load and validate Sky Weather Outpost YAML configuration and expose validation through `outpost config validate`.

**Architecture:** PyYAML parses external YAML, Pydantic v2 validates it into focused typed models, and a small argparse CLI exposes validation. Configuration stays generic; City Lab values exist only in YAML/examples and tests that exercise the example.

**Tech Stack:** Python >=3.11, Pydantic v2, PyYAML 6, argparse, pytest.

**Spec:** `docs/superpowers/specs/2026-08-31-config-loader-design.md`

## Global Constraints

- Python requires `>=3.11`.
- Keep the core generic and vendor-neutral.
- Do not hardcode `city-lab`, `city-lab-core`, `inFactory-TH`, or device id `166` as validation rules.
- Configuration is external YAML.
- Unknown configuration keys fail validation.
- This slice does not implement replay, SQLite, API, dashboard, live SDR, or retention.

---

### Task 1: Typed configuration loader

**Files:**
- Modify: `pyproject.toml`
- Create: `app/config/__init__.py`
- Create: `app/config/models.py`
- Create: `app/config/loader.py`
- Create: `tests/config/test_loader.py`

**Interfaces:**
- Produces: `load_config(path: str | Path) -> OutpostConfig`
- Produces: typed `OutpostConfig` tree matching the current example YAML.

- [ ] **Step 1: Add pytest/dev and runtime dependency declarations, then write failing loader tests**

Tests must load `config/examples/city-lab.yaml`, assert `site.id == "city-lab"` and `node.id == "city-lab-core"`, load a temporary alternate site successfully, and reject missing/unknown fields with Pydantic validation errors.

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python -m pytest tests/config/test_loader.py -v`

Expected: failure because `app.config.loader` / `OutpostConfig` behavior does not exist yet.

- [ ] **Step 3: Implement minimal Pydantic models and YAML loader**

Use `ConfigDict(extra="forbid")` on configuration models. `load_config` reads UTF-8 YAML with `yaml.safe_load`, requires a mapping at the root, and returns `OutpostConfig.model_validate(data)`.

- [ ] **Step 4: Verify GREEN**

Run: `python -m pytest tests/config/test_loader.py -v`

Expected: all loader tests pass.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml app/config tests/config/test_loader.py
git commit -m "feat: add typed YAML config loader"
```

### Task 2: Config validation CLI

**Files:**
- Create: `app/cli.py`
- Create: `tests/test_cli.py`

**Interfaces:**
- Consumes: `load_config(path) -> OutpostConfig`
- Produces: `main(argv: list[str] | None = None) -> int`
- Command: `outpost config validate <path>`

- [ ] **Step 1: Write failing CLI tests**

Success test calls `main(["config", "validate", "config/examples/city-lab.yaml"])`, expects return code 0, and checks stdout contains `Configuration valid`, `city-lab`, and `city-lab-core`. Failure test validates a temporary invalid YAML file, expects non-zero, and checks stderr contains `Configuration invalid`.

- [ ] **Step 2: Run the CLI tests and verify RED**

Run: `python -m pytest tests/test_cli.py -v`

Expected: failure because `app.cli` does not yet implement the command.

- [ ] **Step 3: Implement the minimal argparse CLI**

Build `config validate` subcommands. On success print a concise validation summary. Catch file errors, `yaml.YAMLError`, and `pydantic.ValidationError`, print a concise error to stderr, and return 2. `if __name__ == "__main__": raise SystemExit(main())` supports direct execution.

- [ ] **Step 4: Verify GREEN and full suite**

Run: `python -m pytest -v`

Expected: all tests pass with no warnings or tracebacks.

- [ ] **Step 5: Manual command smoke test**

Run: `outpost config validate config/examples/city-lab.yaml`

Expected output includes:

```text
Configuration valid
site: city-lab
node: city-lab-core
```

- [ ] **Step 6: Commit**

```bash
git add app/cli.py tests/test_cli.py
git commit -m "feat: add config validation command"
```

### Task 3: Verification

**Files:**
- No production changes expected.

**Interfaces:**
- Verifies the complete slice.

- [ ] **Step 1: Run tests**

Run: `python -m pytest -v`

Expected: all tests pass.

- [ ] **Step 2: Run Ruff**

Run: `python -m ruff check app tests`

Expected: no lint errors.

- [ ] **Step 3: Validate the real example**

Run: `outpost config validate config/examples/city-lab.yaml`

Expected: exit 0 with the City Lab site/node summary.

- [ ] **Step 4: Review the diff against the design**

Confirm no replay, database, FastAPI, SDR, storage-retention, or City Lab-specific validation behavior was added.
