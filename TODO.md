# routingtools — TODO

## High priority

- [ ] **Per-file output mode**
  - The `per_file` flag is parsed from `manifest.yaml` (`manifest.py:35`) but `cmd_build` (`cli.py:68`) always writes a single merged `topology.<fmt>` file and never reads it.
  - Also: the `output.merged` flag is loaded but never checked — both flags should drive output behavior.
  - _Entry point:_ `cli.py:cmd_build`

- [ ] **Cross-env bridge frame-crossing validator**
  - The design requires a warning when a `cross_environment_bridge` (dashed diamond) doesn't cross a frame boundary.
  - The parser doesn't retain per-node frame membership in the `Topology`, so the check can't be written yet — the parser needs to carry that data forward.
  - _Entry point:_ `parser.py:_parse_file` → `validator.py:validate`

## Medium priority

- [x] **Mermaid emitter**
  - `src/routingtools/emit/mermaid_emitter.py` — emits `flowchart LR` for GitHub/Notion rendering.
  - Use: `routingtools build manifest.yaml --format mermaid`

- [ ] **DSL emitter**
  - Drop a new `src/routingtools/emit/dsl_emitter.py` exposing `emit(topology) -> str` once the DSL format is specified.
  - Wire it into `cli.py:_emit` following the existing `yaml` / `json` / `csv` / `mermaid` pattern.
  - _Entry point:_ `cli.py:_emit`

- [ ] **`FileScope.kind` support**
  - The `kind` field (e.g. `"feeds"`) is parsed from the manifest (`manifest.py:73`) but never used by the parser or emitters.
  - Decide what semantic it should carry (e.g. skip outbound-route validation for feed catalog files) and implement it.
  - _Entry point:_ `parser.py:_parse_file`

## Low priority

- [ ] **Excalidraw library file**
  - Generate a `routing.excalidrawlib` with pre-styled shapes for each `NodeType` so users can drag-and-drop instead of styling manually.
  - Likely a standalone script under `fixtures/` or a new `routingtools export-lib` CLI command.
