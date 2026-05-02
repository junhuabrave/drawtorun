---
description: Validate a manifest and explain every finding with actionable fix hints. Stricter than build — warnings are also explained.
argument-hint: <manifest.yaml> [--lint]
---

Validate the routing topology from the given manifest and give actionable feedback on every finding.

## Steps

1. Parse the argument string:
   - A path to `manifest.yaml` (required)
   - Optional `--lint` flag — if present, run `routingtools lint` (warnings treated as errors); otherwise run `routingtools validate`

2. Run:
   ```
   routingtools validate <manifest>
   # or with --lint:
   routingtools lint <manifest>
   ```

3. For each finding, print a structured explanation:
   - **Code** + severity
   - What it means in plain English
   - Exactly where in the diagram to look (node label, arrow, frame)
   - How to fix it — specific shape/stroke/label change needed

## Finding reference

| Code | Meaning | Fix |
|------|---------|-----|
| `UNLABELED_SHAPE` | Shape has no text label | Add a label to the shape in Excalidraw |
| `UNCLASSIFIABLE_SHAPE` | Shape kind+stroke combo not in conventions | Check shape is rectangle/diamond/ellipse with solid or dashed stroke |
| `DANGLING_ARROW` | Arrow not connected on both ends | Re-attach the arrow in Excalidraw |
| `ARROW_MISSING_NODE` | Arrow touches an unlabeled shape | Label the shape the arrow connects to |
| `ARROW_SOURCE_NOT_CANONICAL` | Arrow source is a dotted (foreign ref) shape — foreign refs can't have routes | Move the arrow to the canonical (non-dotted) version of the node |
| `BAD_ARROW_LABEL` | Label isn't `default`/`*` and doesn't have exactly 4 tokens | Fix to `source type id exchange` (e.g. `bloomberg trade AAPL nyse`) |
| `DUPLICATE_CANONICAL` | Same node label appears (non-dotted) in two files | One copy must be dotted (foreign ref) |
| `FEED_HAS_OUTBOUND` | Ellipse (feed) has an outbound arrow — feeds are sinks | Remove the arrow or change the shape to a rectangle/diamond |
| `DANGLING_NEXT_HOP` | Route points at a node not defined anywhere | Add the missing node (non-dotted) to one of the manifest files |
| `UNKNOWN_ENUM_VALUE` | Match key uses a source/type/exchange not in `manifest.yaml` enums | Add the value to the manifest enum list or fix the label typo |
| `ISOLATED_NODE` | Non-feed node has no outbound routes | Add an arrow or confirm the node is intentionally terminal |
| `FAILOVER_NO_PRIORITY` | Dashed arrow has no `[pri=N]` modifier | Add e.g. `[pri=1]` to the arrow label |
| `MISSING_BRIDGE_HALF` | Bridge node id has a `.` but no paired half found | Add the other half (e.g. `bridge.ny` if `bridge.hk` exists) or rename to remove the `.` |
| `CLIENT_HAS_KEYED_ROUTES` | Client node has keyed routes in addition to a default | Usually clients just forward to a `client_route`; confirm this is intentional |
| `FILE_NOT_FOUND` | A file listed in the manifest doesn't exist on disk | Fix the path in `manifest.yaml` or run `python fixtures/build_fixture.py` to regenerate |

## After explaining findings

- Summarise: X errors, Y warnings
- If clean: confirm topology is valid and mention node + route counts
