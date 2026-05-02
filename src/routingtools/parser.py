"""Convention parser: RawDiagram(s) -> Topology.

Applies the visual conventions defined in the design doc:

    Shape + stroke style -> NodeType
        rounded rectangle, solid -> client
        sharp   rectangle, solid -> client_route
        diamond,           solid -> cross_region_bridge
        diamond,           dashed -> cross_environment_bridge
        ellipse,           solid -> feed

    Stroke style on a node:
        dotted -> foreign reference (skip canonical creation)

    Node fill color -> region (via manifest palette)
    Frame membership -> environment (when env_dimension == "frame")

    Arrow stroke style -> route kind
        solid  -> primary  (>=2 from same node with same key = load_balanced)
        dashed -> failover (with optional [pri=N])
        dotted -> multicast

    Arrow label -> match key
        empty | "default" | "*" -> default hop
        otherwise: 4 space-separated tokens; bracket modifiers [pri=N], [w=N], [ttl=N]
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .excalidraw import RawArrow, RawDiagram, RawShape, load as load_excalidraw
from .manifest import Manifest
from .model import (
    Enums, Finding, MatchKey, Node, NodeType, Route, RouteKind, Topology,
)


# ----- Shape/style -> NodeType -----

def _classify_shape(shape: RawShape) -> Optional[NodeType]:
    """Return the NodeType for a canonical (non-foreign-ref) shape, or None."""
    if shape.shape == "rectangle":
        return "client" if shape.rounded else "client_route"
    if shape.shape == "diamond":
        return "cross_environment_bridge" if shape.stroke_style == "dashed" else "cross_region_bridge"
    if shape.shape == "ellipse":
        return "feed"
    return None


def _is_foreign_ref(shape: RawShape) -> bool:
    """Dotted stroke on a node = foreign reference."""
    return shape.stroke_style == "dotted"


# ----- Arrow label -> (match key, kind, modifiers) -----

_MODIFIER_RE = re.compile(r"\[(\w+)=([^\]]+)\]")


@dataclass
class ParsedLabel:
    match: Optional[MatchKey]               # None -> default hop
    priority: Optional[int] = None
    weight: Optional[int] = None
    ttl: Optional[int] = None


def parse_arrow_label(label: Optional[str]) -> ParsedLabel:
    """Parse an arrow label into a match key + modifiers.

    Empty / "default" / "*" -> default hop (match=None).
    Otherwise: 4 space-separated tokens followed by zero or more [k=v] modifiers.
    """
    if not label or label.strip().lower() in ("default", "*"):
        return ParsedLabel(match=None)

    text = label.strip()

    # Pull modifiers off the end.
    modifiers: Dict[str, str] = {}
    while True:
        m = _MODIFIER_RE.search(text)
        if not m:
            break
        modifiers[m.group(1).lower()] = m.group(2)
        text = (text[: m.start()] + text[m.end():]).strip()

    parts = text.split()
    if len(parts) != 4:
        raise ValueError(
            f"Arrow label must be 'default', '*', or 4 space-separated tokens "
            f"(optionally followed by [k=v] modifiers). Got: {label!r}"
        )

    pri = int(modifiers["pri"]) if "pri" in modifiers else None
    weight = int(modifiers["w"]) if "w" in modifiers else None
    ttl = int(modifiers["ttl"]) if "ttl" in modifiers else None

    return ParsedLabel(
        match=(parts[0], parts[1], parts[2], parts[3]),
        priority=pri,
        weight=weight,
        ttl=ttl,
    )


def _arrow_kind(arrow: RawArrow) -> RouteKind:
    if arrow.stroke_style == "dashed":
        return "failover"
    if arrow.stroke_style == "dotted":
        return "multicast"
    return "primary"


# ----- File parser -----

@dataclass
class _FileResult:
    diagram: RawDiagram
    shape_id_to_label: Dict[str, str]
    canonical_nodes: Dict[str, Node]    # nodes whose canonical home is this file
    arrows: List[RawArrow]


def _parse_file(diagram: RawDiagram, manifest: Manifest, file_scope) -> Tuple[_FileResult, List[Finding]]:
    findings: List[Finding] = []
    shape_id_to_label: Dict[str, str] = {}
    canonical: Dict[str, Node] = {}
    color_to_region = manifest.conventions._color_to_region

    for shape in diagram.shapes.values():
        if not shape.label:
            findings.append(Finding(
                severity="warning",
                code="UNLABELED_SHAPE",
                message="Shape has no label; skipping.",
                file=diagram.file_path,
                node_id=shape.id,
            ))
            continue
        shape_id_to_label[shape.id] = shape.label

        if _is_foreign_ref(shape):
            continue   # canonical defined elsewhere

        node_type = _classify_shape(shape)
        if node_type is None:
            findings.append(Finding(
                severity="error",
                code="UNCLASSIFIABLE_SHAPE",
                message=f"Cannot classify shape kind={shape.shape} stroke={shape.stroke_style}.",
                file=diagram.file_path,
                node_id=shape.label,
            ))
            continue

        # Region: from manifest scope first, then from fill color.
        region: Optional[str] = file_scope.region
        if not region:
            region = color_to_region.get((shape.background_color or "").lower())

        # Environment: from manifest scope first, then from frame name.
        environment: Optional[str] = file_scope.environment
        if not environment and shape.frame_id:
            frame = diagram.frames.get(shape.frame_id)
            if frame and frame.name:
                environment = frame.name

        canonical[shape.label] = Node(
            id=shape.label,
            type=node_type,
            region=region,
            environment=environment,
            canonical_file=str(Path(diagram.file_path).name),
        )

    return _FileResult(
        diagram=diagram,
        shape_id_to_label=shape_id_to_label,
        canonical_nodes=canonical,
        arrows=list(diagram.arrows.values()),
    ), findings


# ----- Top-level: build Topology from a Manifest -----

def parse(manifest: Manifest) -> Tuple[Topology, List[Finding]]:
    """Parse all files referenced by the manifest into a single Topology."""
    findings: List[Finding] = []
    file_results: List[_FileResult] = []
    file_scope_by_path: Dict[str, object] = {}

    # Pass 1: load each file, classify canonical nodes per file.
    for fs in manifest.files:
        full_path = manifest.root_dir / fs.path
        try:
            diagram = load_excalidraw(full_path)
        except FileNotFoundError:
            findings.append(Finding(
                severity="error",
                code="FILE_NOT_FOUND",
                message=f"File listed in manifest is missing: {fs.path}",
                file=fs.path,
            ))
            continue
        # Use the relative path (as listed in the manifest) for diagnostics.
        diagram.file_path = fs.path
        file_scope_by_path[fs.path] = fs

        result, file_findings = _parse_file(diagram, manifest, fs)
        findings.extend(file_findings)
        file_results.append(result)

    # Pass 2: merge canonical nodes into global Topology, detecting duplicates.
    topology = Topology(enums=manifest.enums, files=manifest.files)
    for fr in file_results:
        for node_id, node in fr.canonical_nodes.items():
            if node_id in topology.nodes:
                findings.append(Finding(
                    severity="error",
                    code="DUPLICATE_CANONICAL",
                    message=(
                        f"Node {node_id!r} is canonically defined in both "
                        f"{topology.nodes[node_id].canonical_file} and {node.canonical_file}."
                    ),
                    node_id=node_id,
                ))
                continue
            topology.nodes[node_id] = node

    # Pass 3: detect bridge halves (id pattern "<base>.<region>" where two halves exist).
    _link_bridge_halves(topology)

    # Pass 4: walk arrows, build routes.
    for fr in file_results:
        for arrow in fr.arrows:
            if not arrow.start_id or not arrow.end_id:
                findings.append(Finding(
                    severity="error",
                    code="DANGLING_ARROW",
                    message="Arrow is not connected to a shape on both ends.",
                    file=fr.diagram.file_path,
                    arrow_id=arrow.id,
                ))
                continue
            src_label = fr.shape_id_to_label.get(arrow.start_id)
            dst_label = fr.shape_id_to_label.get(arrow.end_id)
            if not src_label or not dst_label:
                findings.append(Finding(
                    severity="error",
                    code="ARROW_MISSING_NODE",
                    message="Arrow references a shape with no label.",
                    file=fr.diagram.file_path,
                    arrow_id=arrow.id,
                ))
                continue

            # Source must be a canonical node *somewhere* (preferably this file).
            src_node = topology.nodes.get(src_label)
            if not src_node:
                findings.append(Finding(
                    severity="error",
                    code="ARROW_SOURCE_NOT_CANONICAL",
                    message=f"Arrow source {src_label!r} is not canonically defined.",
                    file=fr.diagram.file_path,
                    arrow_id=arrow.id,
                ))
                continue

            try:
                parsed = parse_arrow_label(arrow.label)
            except ValueError as e:
                findings.append(Finding(
                    severity="error",
                    code="BAD_ARROW_LABEL",
                    message=str(e),
                    file=fr.diagram.file_path,
                    arrow_id=arrow.id,
                ))
                continue

            src_node.routes.append(Route(
                next_hop=dst_label,
                kind=_arrow_kind(arrow),
                match=parsed.match,
                priority=parsed.priority,
                weight=parsed.weight,
                ttl=parsed.ttl,
                source_file=fr.diagram.file_path,
                arrow_id=arrow.id,
            ))

    # Pass 5: load-balance detection — multiple primary routes from same node with same key.
    _detect_load_balanced(topology)

    return topology, findings


def _link_bridge_halves(topology: Topology) -> None:
    """If two nodes are bridge halves named '<base>.<suffix>', cross-link via .pair."""
    by_base: Dict[str, List[Node]] = {}
    for node in topology.nodes.values():
        if node.type in ("cross_region_bridge", "cross_environment_bridge") and "." in node.id:
            base = node.id.rsplit(".", 1)[0]
            by_base.setdefault(base, []).append(node)
    for base, halves in by_base.items():
        if len(halves) == 2:
            halves[0].pair = halves[1].id
            halves[1].pair = halves[0].id


def _detect_load_balanced(topology: Topology) -> None:
    """Promote groups of >=2 primary routes with identical match keys to load_balanced."""
    for node in topology.nodes.values():
        groups: Dict[Tuple[Optional[MatchKey], RouteKind], List[Route]] = {}
        for r in node.routes:
            if r.kind == "primary":
                groups.setdefault((r.match, r.kind), []).append(r)
        for (_match, _kind), routes in groups.items():
            if len(routes) >= 2:
                for r in routes:
                    r.kind = "load_balanced"


# ----- Validation helpers reused by validator.py -----

def is_canonical(topology: Topology, node_id: str) -> bool:
    return node_id in topology.nodes
