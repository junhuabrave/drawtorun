---
description: Scaffold a new output format emitter and wire it into the CLI.
argument-hint: <format-name>
---

Add a new emitter for the given format name (e.g. `dsl`, `protobuf`, `toml`).

## Steps

### 1. Read existing emitters for reference
Read `src/routingtools/emit/yaml_emitter.py` and `src/routingtools/emit/csv_emitter.py` to understand the pattern before writing anything.

### 2. Create `src/routingtools/emit/<format-name>_emitter.py`
The file must expose exactly one public function:
```python
def emit(topology: Topology) -> str:
    ...
```

**Invariants — do not break these:**
- The function must be a pure function of `Topology`. No filesystem access, no manifest reads, no external calls.
- Import only from `..model` (never from `..manifest`, `..parser`, `..excalidraw`).
- Iterate `sorted(topology.nodes)` to produce deterministic output.
- Handle all five `NodeType` values: `client`, `client_route`, `cross_region_bridge`, `cross_environment_bridge`, `feed`.
- Handle all four `RouteKind` values: `primary`, `failover`, `multicast`, `load_balanced`.
- Emit `route.match` as `None` (default hop) vs a 4-tuple `(source, type, id, exchange)`.
- Include optional route fields only when set: `priority`, `weight`, `ttl`.

### 3. Wire into `src/routingtools/cli.py`
In `_emit()` (`cli.py:90`), add:
```python
from .emit import <format-name>_emitter
# ...
if fmt == "<format-name>":
    return <format-name>_emitter.emit(topology)
```

### 4. Update `src/routingtools/emit/__init__.py` if needed
If the `__init__.py` imports emitters explicitly, add the new one. Read the file first.

### 5. Add to manifest output formats (optional)
If the new format should be a default, update `manifest.py:OutputPrefs.formats`. Usually leave this alone and let users opt in via `manifest.yaml`.

### 6. Verify
```bash
routingtools build fixtures/single_file/manifest.yaml --format <format-name>
pytest tests/ --basetemp=/tmp/rt_test
```

Consider adding a test in `tests/test_pipeline.py` that runs the CLI with the new format and does a basic sanity check on the output (non-empty, contains expected node IDs).
