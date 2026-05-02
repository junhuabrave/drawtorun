"""Load and validate manifest.yaml.

The manifest declares:
  - The set of .excalidraw files to parse and their scopes.
  - Enums for source/type/exchange/environment/region.
  - Convention knobs (region dimension = color or frame, env dimension = frame or id_prefix).
  - Output preferences.

This loader is intentionally permissive: missing fields default to sensible values.
A separate `validate_manifest` step (in cli.py) prints a summary so users can
sanity-check what was parsed.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from .model import Enums, FileScope


@dataclass
class Conventions:
    region_dimension: str = "fill_color"   # "fill_color" or "frame"
    env_dimension: str = "frame"           # "frame" or "id_prefix"
    modifiers_in_label: bool = True
    region_palette: Dict[str, str] = field(default_factory=dict)
    # Color -> region name (reverse of region_palette, built post-load)
    _color_to_region: Dict[str, str] = field(default_factory=dict, init=False, repr=False)


@dataclass
class OutputPrefs:
    formats: List[str] = field(default_factory=lambda: ["yaml"])
    per_file: bool = True
    merged: bool = True
    output_dir: str = "generated"


@dataclass
class Manifest:
    version: int = 1
    root_dir: Path = field(default_factory=lambda: Path("."))
    files: List[FileScope] = field(default_factory=list)
    enums: Enums = field(default_factory=Enums)
    conventions: Conventions = field(default_factory=Conventions)
    output: OutputPrefs = field(default_factory=OutputPrefs)


# Reasonable default region palette — overridden by manifest if specified.
DEFAULT_REGION_PALETTE: Dict[str, str] = {
    "hk":  "#2dd4bf",   # teal
    "ny":  "#3b82f6",   # blue
    "ldn": "#a855f7",   # purple
    "tky": "#ec4899",   # pink
    "sgp": "#f59e0b",   # orange
    "syd": "#22c55e",   # green
}


def load(path: str | Path) -> Manifest:
    p = Path(path)
    raw = yaml.safe_load(p.read_text()) or {}

    files = []
    for f in raw.get("files", []):
        scope = f.get("scope") or {}
        files.append(FileScope(
            path=f["path"],
            region=scope.get("region"),
            environment=scope.get("environment"),
            kind=scope.get("kind"),
        ))

    enums_raw = raw.get("enums") or {}
    enums = Enums(
        sources=list(enums_raw.get("sources") or []),
        types=list(enums_raw.get("types") or []),
        exchanges=list(enums_raw.get("exchanges") or []),
        environments=list(enums_raw.get("environments") or []),
        regions=list(enums_raw.get("regions") or []),
    )

    conv_raw = raw.get("conventions") or {}
    palette = dict(DEFAULT_REGION_PALETTE)
    palette.update({k.lower(): v.lower() for k, v in (conv_raw.get("region_palette") or {}).items()})
    conv = Conventions(
        region_dimension=conv_raw.get("region_dimension", "fill_color"),
        env_dimension=conv_raw.get("env_dimension", "frame"),
        modifiers_in_label=bool(conv_raw.get("modifiers_in_label", True)),
        region_palette=palette,
    )
    conv._color_to_region = {v.lower(): k for k, v in palette.items()}

    out_raw = raw.get("output") or {}
    output = OutputPrefs(
        formats=list(out_raw.get("formats") or ["yaml"]),
        per_file=bool(out_raw.get("per_file", True)),
        merged=bool(out_raw.get("merged", True)),
        output_dir=out_raw.get("output_dir", "generated"),
    )

    return Manifest(
        version=int(raw.get("version", 1)),
        root_dir=p.parent,
        files=files,
        enums=enums,
        conventions=conv,
        output=output,
    )
