# v0.1 Config Loader Design

## Goal

Create the first executable slice of Sky Weather Outpost: load and validate an external YAML configuration without hardcoding City Lab behavior in Python.

## Scope

This slice implements configuration loading and validation only. It does not implement JSONL replay, SDR collection, SQLite, FastAPI, dashboard rendering, systemd, or storage retention.

The existing `config/examples/city-lab.yaml` is the first real configuration and remains data, not application logic.

## Approach

Use PyYAML for YAML parsing and Pydantic v2 models for typed validation. Keep the public interface small: `load_config(path) -> OutpostConfig` in `app/config/loader.py`. Pydantic models live in `app/config/models.py` and represent the existing YAML structure closely enough to validate v0.1 without inventing future configuration fields.

The CLI entry point declared by `pyproject.toml` will gain `outpost config validate <path>`. Successful validation prints a concise site/node summary and exits 0. Missing files, invalid YAML, or invalid configuration print a useful error to stderr and exit non-zero.

## Configuration model

The root `OutpostConfig` contains:

- `site`: id, name, type, timezone
- `node`: id, role
- `modules`: `rtl433` and `system_metrics`
- `storage`: SQLite path
- `logging`: level and mode
- `api`: host, port and public/internal toggles
- `devices`: configured devices with match rules and metric names
- `dashboard`: card names

Validation is intentionally structural for this slice. Required fields must exist and basic scalar types must be correct. The loader must not enforce City Lab-specific IDs, the `inFactory-TH` model, or device id 166.

Unknown fields are rejected so configuration typos fail early rather than being silently ignored.

## Error handling

`load_config` distinguishes filesystem/YAML parsing from schema validation through clear exceptions. The CLI converts those failures into human-readable messages and a non-zero exit status rather than a traceback during normal validation use.

## Testing

Use pytest and temporary YAML files. Tests cover:

1. loading the existing City Lab example into typed models;
2. proving a different valid site/node is accepted, preventing accidental City Lab hardcoding;
3. rejecting a missing required field;
4. rejecting an unknown field;
5. CLI success and CLI failure exit codes/output.

Implementation follows red-green-refactor: tests are introduced before production behavior.

## Dependencies

Add runtime dependencies `pydantic>=2,<3` and `PyYAML>=6,<7`. Add pytest as a development dependency so a clean development checkout can execute the test suite.

## Success criterion

From an installed development checkout:

```bash
outpost config validate config/examples/city-lab.yaml
```

returns exit code 0 and identifies `city-lab` / `city-lab-core`. A malformed or structurally invalid YAML file returns non-zero with an actionable validation error.
