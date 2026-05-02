---
description: Scaffold a new programmatic fixture in fixtures/build_fixture.py following project conventions.
argument-hint: <fixture-name> [--region <hk|ny|ldn|...>] [--env <prod|uat|...>] [--multi-file]
---

Add a new programmatic fixture to `fixtures/build_fixture.py` and wire it into `main()`.

## Steps

1. Parse the argument string:
   - `<fixture-name>` (required) — used as the function name and output directory, e.g. `failover_demo`
   - `--region` — default region for the fixture (e.g. `hk`). Defaults to `hk` if omitted.
   - `--env` — default environment frame name (e.g. `prod`). Defaults to `prod` if omitted.
   - `--multi-file` — if present, scaffold two region files + manifest; otherwise single file.

2. Read `fixtures/build_fixture.py` to understand the existing `DiagramBuilder` API and fixture patterns.

3. Add a new `build_<fixture-name>_fixture(out_dir: Path) -> None` function to `fixtures/build_fixture.py`:
   - Use `DiagramBuilder` — never hand-write raw Excalidraw JSON
   - Include at least one node of each relevant type to exercise the feature being demonstrated
   - Follow the layout convention: frames first, then shapes (left → right: client → client_route → bridge/feed), then arrows
   - For multi-file: create separate `DiagramBuilder` instances per region; use dotted stroke for foreign refs

4. Add a helper `_<fixture-name>_manifest() -> str` returning a YAML string with:
   - Correct `files:` entries pointing at the `.excalidraw` file(s) produced
   - Reasonable enum values (copy from an existing manifest if unsure)
   - `output.formats: [yaml, json, csv]`

5. Wire the new fixture into `main()`:
   ```python
   build_<fixture-name>_fixture(FIXTURES_DIR / "<fixture-name>")
   ```

6. Run the fixture generator to verify it produces valid files:
   ```
   python fixtures/build_fixture.py
   ```

7. Run the full test suite to confirm no regressions:
   ```
   pytest tests/ --basetemp=/tmp/rt_test
   ```

## DiagramBuilder quick reference

```python
b = DiagramBuilder()
fid  = b.frame("prod", x, y, w, h)                          # frame
sid  = b.shape("rectangle", "label", x, y, rounded=True,    # client
               bg_color=TEAL, frame_id=fid)
sid  = b.shape("rectangle", "label", x, y, frame_id=fid)    # client_route
sid  = b.shape("diamond",   "label", x, y, frame_id=fid)    # cross_region_bridge
sid  = b.shape("diamond",   "label", x, y,                  # cross_env_bridge
               stroke_style="dashed", frame_id=fid)
sid  = b.shape("ellipse",   "label", x, y, frame_id=fid)    # feed
sid  = b.shape("rectangle", "label", x, y,                  # foreign ref
               stroke_style="dotted", frame_id=fid)
b.arrow(src_id, dst_id, label="bloomberg trade * nyse",      # keyed primary
        frame_id=fid)
b.arrow(src_id, dst_id, label="default", frame_id=fid)       # default hop
b.arrow(src_id, dst_id, stroke_style="dashed",               # failover
        label="bloomberg trade * nyse [pri=1]", frame_id=fid)
b.arrow(src_id, dst_id, stroke_style="dotted", frame_id=fid) # multicast
```

Color constants already imported: `TEAL`, `BLUE`, `PURPLE`, `WHITE`, `TRANSPARENT`.
