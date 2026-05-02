# Claude Code primer for routingtools

This file is a fast on-ramp for any agent (or human) picking up this repo. Read in order.

## What this project is

A pipeline that reads market-data routing topologies authored as Excalidraw diagrams and emits runtime config (YAML / JSON / CSV / DSL). Diagrams are the source of truth. See `README.md` for usage and `../excalidraw-routing-design.md` for the full design rationale.

## Architecture in 30 seconds

```
.excalidraw files  ─────►  excalidraw.load()  ─────►  RawDiagram
                                                          │
manifest.yaml  ──────────►  manifest.load()  ─────►  Manifest
                                                          │
                                              ┌───────────┘
                                              ▼
                                         parser.parse()
                                              │
                                              ▼
                                          Topology  ─────►  validator.validate()
                                              │
                                              ▼
                                       emit/<format>.emit()
                                              │
                                              ▼
                                            text
```

Each module has one job. Don't add cross-module reach-throughs. If a piece of logic doesn't fit, that's usually a sign the layering needs a tweak.

## Where each thing lives

| Concern                               | File                                      |
| ------------------------------------- | ----------------------------------------- |
| Internal data model                   | `src/routingtools/model.py`               |
| .excalidraw JSON loader (raw)         | `src/routingtools/excalidraw.py`          |
| manifest.yaml loader                  | `src/routingtools/manifest.py`            |
| Convention parser (raw → Topology)    | `src/routingtools/parser.py`              |
| Invariant checks                      | `src/routingtools/validator.py`           |
| Emitters                              | `src/routingtools/emit/*.py`              |
| CLI                                   | `src/routingtools/cli.py`                 |
| Fixture generator                     | `fixtures/build_fixture.py`               |
| Tests                                 | `tests/test_pipeline.py`                  |

## Common changes and where to make them

**New node type** — add to `NodeType` literal in `model.py`; teach `_classify_shape` in `parser.py`; add a fixture; add validator rules if needed.

**New route kind** — add to `RouteKind` literal in `model.py`; teach `_arrow_kind` in `parser.py`; emit handling in `emit/yaml_emitter.py`'s `_route_to_dict`; CSV/JSON inherit automatically.

**New label modifier** (e.g. `[region=hk]`) — extend `parse_arrow_label` in `parser.py` and add the field to `Route` in `model.py`.

**New emitter** — drop a new file under `src/routingtools/emit/` exposing `emit(topology) -> str`; add a one-liner to `cli._emit`.

**New invariant** — add a check inside `validator.validate` returning a `Finding`. Default severity is "warning"; reserve "error" for things that would break the runtime.

## Testing

```bash
pytest tests/ --basetemp=/tmp/rt_test     # the basetemp avoids FUSE issues if you're in a sandbox
```

Tests are end-to-end and re-run the CLI against fixtures. To add a test, usually:

1. Extend `fixtures/build_fixture.py` with a new fixture.
2. Add a test in `tests/test_pipeline.py` that runs the CLI and asserts on emitted YAML/CSV.

## What's still TODO

See "Known limitations / future work" at the bottom of `README.md`. The biggest near-term items:

- **Per-file output mode** — emit one config file per input .excalidraw file rather than one merged output. Manifest already has the `per_file` knob; CLI doesn't read it yet.
- **Cross-env bridge frame-crossing validator** — the design calls for warning when a dashed diamond doesn't cross a frame boundary; needs the parser to remember frame-by-env per file.
- **Excalidraw library file** — produce a `routing.excalidrawlib` so users can drag-and-drop pre-styled node shapes.
- **DSL emitter** — once the user specifies their DSL, drop in `emit/dsl_emitter.py`.

## Conventions for diffs / PRs

- The parser must stay pure (input = manifest + file bytes, output = Topology + findings, no side effects). Don't put I/O inside `parser.py` other than via the `excalidraw.load()` call.
- Emitters must be pure functions of `Topology`. No reading the manifest, no walking the filesystem.
- Validator findings get specific `code` strings (e.g. `FEED_HAS_OUTBOUND`, `DANGLING_NEXT_HOP`). Stable codes make grep-based test assertions reliable; don't rename without updating tests.
- Programmatic fixtures preferred over hand-edited `.excalidraw` files — they're easier to diff, regenerate, and parameterize.

## How to think about the 4-part key

The key is matched at every node. The same key reappears at every hop along a route — that's the whole point. There is no "path" object, only per-node `match -> next_hop` rules. Always reason about a single hop at a time; the multi-hop path emerges from following identical keys forward.

## Pointers when stuck

- "What does Excalidraw call X?" — open one of the generated fixtures (e.g. `fixtures/showcase.excalidraw`) and grep for the field. The format is plain JSON.
- "Why is this label not parsing?" — `parse_arrow_label` in `parser.py`; raises `ValueError` with the exact label that failed.
- "Why isn't my node showing up?" — likely missing label, or a stroke style the parser treats as a foreign ref. Run `routingtools summary` and check the warnings.
