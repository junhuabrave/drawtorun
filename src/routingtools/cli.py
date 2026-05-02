"""routingtools command-line interface.

    routingtools build    <manifest.yaml> [--out DIR]
    routingtools validate <manifest.yaml>
    routingtools lint     <manifest.yaml>          # warnings as errors
    routingtools summary  <manifest.yaml>          # human-readable topology summary
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

from . import manifest as manifest_mod
from . import parser as parser_mod
from . import validator as validator_mod
from .emit import yaml_emitter, json_emitter, csv_emitter, mermaid_emitter


def _load(manifest_path: str):
    mf = manifest_mod.load(manifest_path)
    topology, parse_findings = parser_mod.parse(mf)
    validate_findings = validator_mod.validate(topology)
    return mf, topology, parse_findings + validate_findings


def _print_findings(findings, *, lint_mode: bool = False) -> int:
    """Print findings; return non-zero exit code if errors (or warnings in lint mode) present."""
    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]
    for f in findings:
        print(f.format(), file=sys.stderr)
    if errors:
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s).", file=sys.stderr)
        return 1
    if warnings:
        print(f"\n0 errors, {len(warnings)} warning(s).", file=sys.stderr)
        return 1 if lint_mode else 0
    print("clean.", file=sys.stderr)
    return 0


def cmd_validate(args) -> int:
    _, _, findings = _load(args.manifest)
    return _print_findings(findings, lint_mode=False)


def cmd_lint(args) -> int:
    _, _, findings = _load(args.manifest)
    return _print_findings(findings, lint_mode=True)


def cmd_summary(args) -> int:
    mf, topology, findings = _load(args.manifest)
    print(f"Manifest: {args.manifest}")
    print(f"Files: {len(mf.files)}")
    print(f"Nodes: {len(topology.nodes)}")
    by_type: dict = {}
    for n in topology.nodes.values():
        by_type[n.type] = by_type.get(n.type, 0) + 1
    for t, c in sorted(by_type.items()):
        print(f"  {t:>26}: {c}")
    edges = sum(len(n.routes) for n in topology.nodes.values())
    print(f"Routes (edges): {edges}")
    return _print_findings(findings, lint_mode=False)


def cmd_build(args) -> int:
    mf, topology, findings = _load(args.manifest)
    rc = _print_findings(findings, lint_mode=False)
    if rc != 0:
        return rc

    if args.out:
        out_dir = Path(args.out)                       # CLI override: relative to CWD
    else:
        out_dir = Path(mf.output.output_dir)
        if not out_dir.is_absolute():
            out_dir = mf.root_dir / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    formats = args.format.split(",") if args.format else mf.output.formats
    for fmt in formats:
        text = _emit(topology, fmt)
        (out_dir / f"topology.{fmt}").write_text(text)
        print(f"wrote {out_dir / f'topology.{fmt}'}")
    return 0


def _emit(topology, fmt: str) -> str:
    if fmt == "yaml":
        return yaml_emitter.emit(topology)
    if fmt == "json":
        return json_emitter.emit(topology)
    if fmt == "csv":
        return csv_emitter.emit(topology)
    if fmt == "mermaid":
        return mermaid_emitter.emit(topology)
    raise SystemExit(f"unknown format: {fmt}")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="routingtools")
    sub = p.add_subparsers(dest="cmd", required=True)

    for cmd in ("validate", "lint", "summary"):
        sp = sub.add_parser(cmd)
        sp.add_argument("manifest")

    sp = sub.add_parser("build")
    sp.add_argument("manifest")
    sp.add_argument("--out", help="output directory (overrides manifest)")
    sp.add_argument("--format", help="comma-separated: yaml,json,csv,mermaid (default: from manifest)")

    args = p.parse_args(argv)
    return {
        "validate": cmd_validate,
        "lint":     cmd_lint,
        "summary":  cmd_summary,
        "build":    cmd_build,
    }[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
