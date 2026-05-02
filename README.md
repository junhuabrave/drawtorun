# routingtools

Author market-data routing topology as Excalidraw diagrams. Generate runtime config (YAML / JSON / CSV / Mermaid).

The diagrams are the source of truth. Each shape is a routing node, each arrow is one row in the source node's routing table. A 4-part key (`source type id exchange`) plus optional default hop encodes how messages flow through the network.

See `excalidraw-routing-design.md` (one level up, in the parent directory) for the full design rationale, conventions, and the multi-file architecture for 10k-node scale.

## Install

```bash
pip install -e .                       # editable install
pip install -e ".[dev]"                # with pytest
```

## Quick start

```bash
# Generate the example fixtures (single-file and multi-file topologies plus a
# showcase file with a legend).
python fixtures/build_fixture.py

# Inspect a topology summary.
routingtools summary fixtures/single_file/manifest.yaml

# Validate (errors + warnings).
routingtools validate fixtures/single_file/manifest.yaml

# Lint (treats warnings as errors).
routingtools lint fixtures/single_file/manifest.yaml

# Build all configured output formats.
routingtools build fixtures/multi_file/manifest.yaml --out /tmp/topology
ls /tmp/topology
#   topology.yaml  topology.json  topology.csv

# Build a Mermaid diagram (paste into GitHub markdown or https://mermaid.live).
routingtools build fixtures/single_file/manifest.yaml --format mermaid --out /tmp/topology
```

## Diagram conventions (one-page summary)

| Shape                                | Stroke   | Node type                  |
| ------------------------------------ | -------- | -------------------------- |
| Rounded rectangle                    | solid    | `client`                   |
| Sharp rectangle                      | solid    | `client_route`             |
| Diamond                              | solid    | `cross_region_bridge`      |
| Diamond                              | dashed   | `cross_environment_bridge` |
| Ellipse                              | solid    | `feed` (zero outbound)     |
| Any of the above                     | dotted   | foreign reference          |

Region: encoded as **fill color** (manifest provides the palette).
Environment: encoded as **frame membership** (frame name = env name).
Arrow style: solid = primary, dashed = failover, dotted = multicast.
Arrow label: `source type id exchange` with optional `[pri=N]`, `[w=N]`, `[ttl=N]` modifiers. Empty / `default` / `*` = default hop.

## Repository layout

```
routing-tools/
  pyproject.toml
  README.md
  CLAUDE.md                            # primer for agents picking up this repo
  src/routingtools/
    __init__.py
    model.py                           # Node, Route, Topology dataclasses
    excalidraw.py                      # raw .excalidraw JSON loader
    manifest.py                        # manifest.yaml loader
    parser.py                          # raw -> Topology (applies conventions)
    validator.py                       # invariant checks
    cli.py                             # build / validate / lint / summary
    emit/
      yaml_emitter.py
      json_emitter.py
      csv_emitter.py
      mermaid_emitter.py
  fixtures/
    build_fixture.py                   # programmatically writes valid .excalidraw files
    showcase.excalidraw                # legend + worked example, drag-and-drop into Excalidraw
    single_file/
      hk-prod.excalidraw
      manifest.yaml
      generated/                       # gitignored — run build_fixture.py then routingtools build
    multi_file/
      manifest.yaml
      prod/
        hk.excalidraw
        ny.excalidraw
      generated/                       # gitignored — run build_fixture.py then routingtools build
  tests/
    test_pipeline.py                   # end-to-end tests
```

## Architecture

The pipeline is a function from `Manifest` to `Topology` to emitted text:

```
manifest.yaml
     │
     ▼
manifest.load()                ── Manifest
     │
     ▼
parser.parse()                 ── Topology, [Finding]
     │
     ▼
validator.validate()           ── [Finding]
     │
     ▼
emit/{yaml,json,csv,mermaid}_emitter   ── str
```

`parser.py` is the only place that knows about conventions. `excalidraw.py` is a pure JSON loader with no semantic interpretation. `validator.py` operates on `Topology` and never on raw shapes. Emitters consume `Topology` and have no opinions about validity. This separation makes it easy to add new emitters, swap parsing conventions, or run validators independently.

## Adding a new emitter

```python
# src/routingtools/emit/dsl_emitter.py
from ..model import Topology

def emit(topology: Topology) -> str:
    out = []
    for nid in sorted(topology.nodes):
        node = topology.nodes[nid]
        for r in node.routes:
            key = "default" if r.match is None else " ".join(r.match)
            out.append(f"{nid}: {key} -> {r.next_hop}  ({r.kind})")
    return "\n".join(out) + "\n"
```

Then wire it into `cli._emit()` (single line). Done.

## Adding a new node type or route kind

1. Add the literal to `NodeType` / `RouteKind` in `model.py`.
2. Update `_classify_shape` in `parser.py` (or `_arrow_kind`).
3. Update `validator.py` if there are new invariants.
4. Add a fixture exercising the new type.

## Testing

```bash
pytest tests/
```

Tests are end-to-end: they run the CLI against fixtures and assert on the emitted YAML/CSV. Adding a new test usually means adding a new fixture (programmatically in `build_fixture.py`) plus assertions on the emitted output.

## Contributing

```bash
pip install -e ".[dev]"
python fixtures/build_fixture.py          # regenerate fixtures
pytest tests/ --basetemp=/tmp/rt_test     # run end-to-end tests
```

See `CLAUDE.md` for the architecture primer, common change patterns, and invariants every PR must preserve. See `TODO.md` for the prioritised backlog.

## Known limitations / future work

- **No proper hot-reload** — emitter writes complete files, no diff stream.
- **DSL emitter not yet shipped.** Once the DSL format is specified, implement `src/routingtools/emit/dsl_emitter.py` and wire it into `cli._emit()` — see `TODO.md` for details.
- **Per-file output** option in the manifest is wired but not yet implemented in the CLI.
- **Performance** is fine for the current scale but un-tuned for 10k nodes — should be straightforward (the parser is single-pass and uses dicts everywhere).
- **Validator** doesn't yet check cross-env bridge frame-crossing — the design calls for it but the parser would need to track frames-by-env across files.
- **Excalidraw library file** (`.excalidrawlib`) for shape templates not yet shipped.
