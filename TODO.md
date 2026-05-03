# routingtools — TODO

## Done

- [x] **Mermaid emitter** — `emit/mermaid_emitter.py` emits `flowchart LR` for GitHub/Notion rendering.
  Use: `routingtools build manifest.yaml --format mermaid`
- [x] **Project skills** — five `/rt-*` Claude Code slash commands in `.claude/commands/` covering build, validate, new fixture, new node type, and new emitter workflows.
- [x] **GitHub upload cleanup** — `.gitignore`, `LICENSE` (MIT), `pyproject.toml` metadata, stale artifacts removed, generated outputs gitignored.

---

## High priority

- [ ] **Per-file output mode**
  - `manifest.yaml` supports `output.per_file` and `output.merged` flags but `cmd_build` ignores both and always writes one merged file.
  - Expected behaviour: when `per_file: true`, emit one `<stem>.<fmt>` per input `.excalidraw` file alongside the merged output.
  - _Touch:_ `cli.py:cmd_build`, possibly a new `emit/` dispatch helper.

- [ ] **Cross-env bridge frame-crossing validator**
  - Design calls for a warning when a `cross_environment_bridge` (dashed diamond) doesn't actually cross a frame boundary.
  - Blocker: `parser.py` discards frame membership after building `Node`; it needs to be carried forward (e.g. as `Node.frame_id: Optional[str]`) so `validator.py` can check it.
  - _Touch:_ `parser.py:_parse_file` → `model.py:Node` → `validator.py:validate` (new code `BRIDGE_SAME_FRAME`).

---

## Medium priority

- [ ] **`FileScope.kind` semantics**
  - The `kind` field (e.g. `"feeds"`) is loaded from the manifest (`manifest.py:73`) but never consumed.
  - Decision needed: should `kind: feeds` suppress `ISOLATED_NODE` warnings for feed-only files? Or drive a different validation profile?
  - _Touch:_ `parser.py:_parse_file`, `validator.py:validate`.

- [ ] **DSL emitter**
  - Blocked on DSL format specification. Once defined, drop `emit/dsl_emitter.py` exposing `emit(topology) -> str` and add one line to `cli.py:_emit`.
  - Use the `/rt-new-emitter` skill to scaffold it.

---

## Low priority

- [ ] **Excalidraw library file**
  - Generate a `routing.excalidrawlib` with one pre-styled shape per `NodeType` so users can drag-and-drop instead of hand-styling.
  - Options: standalone script under `fixtures/`, or a new `routingtools export-lib` CLI subcommand.
