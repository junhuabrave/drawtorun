---
description: Build routing topology config from a manifest. Runs parse + validate + emit and reports output files written.
argument-hint: <manifest.yaml> [--format yaml,json,csv] [--out <dir>]
---

Build the routing topology from the given manifest.

## Steps

1. Parse the argument string. Expect:
   - A path to a `manifest.yaml` (required)
   - Optional `--format` flag with comma-separated values from `yaml`, `json`, `csv`
   - Optional `--out` flag to override the output directory

2. Run the build:
   ```
   routingtools build <manifest> [--format <fmt>] [--out <dir>]
   ```
   Run from the manifest's parent directory so relative paths inside the manifest resolve correctly.

3. Report results clearly:
   - List every file written (path + format)
   - Print any ERROR or WARNING findings, each on its own line with the finding code
   - If there are errors, explain what they mean and where in the diagram to fix them (reference `parser.py` conventions: shape type, stroke style, label format)
   - If clean, print a one-line success summary: node count, route count, formats written

4. If the build fails due to missing `routingtools` CLI, suggest:
   ```
   pip install -e .
   ```
   from the `routing-tools/` directory.

## Conventions to keep in mind
- Feeds are sinks — `FEED_HAS_OUTBOUND` means an ellipse has an outbound arrow
- `DANGLING_NEXT_HOP` means an arrow points at a dotted (foreign ref) shape with no canonical definition elsewhere
- `BAD_ARROW_LABEL` means the label isn't empty/`default`/`*` and doesn't have exactly 4 space-separated tokens
