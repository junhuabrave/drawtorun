---
description: Add a new NodeType end-to-end: model, parser classification, validator rules, and a fixture to exercise it.
argument-hint: <node-type-name> --shape <rectangle|diamond|ellipse> --stroke <solid|dashed|dotted> [--is-sink]
---

Add a new `NodeType` to the pipeline following the project's layered conventions. Touches exactly 4 files in order.

## Steps

### 1. Read current state
Read these files before making any changes:
- `src/routingtools/model.py` — to see the current `NodeType` literal
- `src/routingtools/parser.py` — to see `_classify_shape` and understand which shape+stroke combos are taken
- `src/routingtools/validator.py` — to see existing invariant checks
- `fixtures/build_fixture.py` — to understand the fixture API

### 2. Validate the shape+stroke combo
Check `_classify_shape` in `parser.py` to confirm the requested shape+stroke combination is not already claimed by another `NodeType`. If it is, report the conflict and stop.

### 3. `src/routingtools/model.py` — add to the literal
Add `"<node-type-name>"` to the `NodeType` literal. Keep alphabetical order.

### 4. `src/routingtools/parser.py` — teach `_classify_shape`
Add a branch to `_classify_shape` that returns `"<node-type-name>"` for the specified shape+stroke combination.

**Invariant:** `parser.py` must stay pure — no I/O, no manifest reads inside `_classify_shape`.

### 5. `src/routingtools/validator.py` — add invariant checks
Add at least one check specific to the new node type inside `validate()`. Examples:
- If `--is-sink`: check that nodes of this type have no outbound routes (like `FEED_HAS_OUTBOUND`)
- Otherwise: check that nodes have at least one outbound route (like `ISOLATED_NODE`)
- Use a new, stable `code` string: `<NODETYPE_IN_SCREAMING_SNAKE>_<CONDITION>` (e.g. `GATEWAY_NO_ROUTES`)
- Default severity: `"warning"` unless the condition would break the runtime (then `"error"`)

### 6. `fixtures/build_fixture.py` — add a fixture
Add a `build_<node-type-name>_fixture(out_dir: Path) -> None` function that creates at least one node of the new type connected into a minimal topology. Wire it into `main()`.

### 7. Verify
```bash
python fixtures/build_fixture.py
pytest tests/ --basetemp=/tmp/rt_test
```
All existing tests must still pass. If you added a validator check, assert on its code in a new test in `tests/test_pipeline.py`.

## What NOT to do
- Do not add I/O or manifest access inside `parser.py`
- Do not rename existing validator codes — tests assert on them by string
- Do not add the new type to emitters — `yaml_emitter`, `json_emitter`, and `csv_emitter` serialize the `type` field as-is from the model, so they inherit automatically
