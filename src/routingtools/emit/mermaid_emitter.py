"""Emit a Topology as a Mermaid flowchart.

Useful for embedding in GitHub markdown or Notion to give engineers a
rendered view of the routing topology without leaving their PR/docs workflow.

Shape mapping (NodeType → Mermaid syntax):
    client               → id([label])   stadium/rounded
    client_route         → id[label]     rectangle
    cross_region_bridge  → id{label}     diamond
    cross_environment_bridge → id{{label}}  hexagon
    feed                 → id((label))   circle

Edge style mapping (RouteKind → Mermaid arrow):
    primary       → -->
    load_balanced → -->
    failover      → -.->
    multicast     → ==>
"""
from __future__ import annotations
from typing import Optional

from ..model import Node, Route, Topology


# Mermaid node id characters must be alphanumeric + underscore/hyphen.
# Labels (inside the shape brackets) can be arbitrary text.
def _safe_id(node_id: str) -> str:
    """Return a Mermaid-safe id by replacing non-word characters with underscores."""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in node_id)


def _node_def(node: Node) -> str:
    """Return the Mermaid node definition line, e.g. 'hk_desk_7([hk-desk-7])'."""
    nid = _safe_id(node.id)
    label = node.id
    if node.region:
        label += f"\\n[{node.region}]"
    t = node.type
    if t == "client":
        return f'{nid}(["{label}"])'
    if t == "client_route":
        return f'{nid}["{label}"]'
    if t == "cross_region_bridge":
        return '{nid}{{"{label}"}}'.format(nid=nid, label=label)
    if t == "cross_environment_bridge":
        return '{nid}{{{{"{label}"}}}}'.format(nid=nid, label=label)
    if t == "feed":
        return f'{nid}(("{label}"))'
    # fallback for any future NodeType
    return f'{nid}["{label}"]'


def _edge_arrow(kind: str) -> str:
    if kind == "failover":
        return "-.->"
    if kind == "multicast":
        return "==>"
    return "-->"


def _match_label(route: Route) -> Optional[str]:
    if route.match is None:
        return "default"
    src, typ, ident, exch = route.match
    parts = [src, typ, ident, exch]
    text = " ".join(parts)
    mods = []
    if route.priority is not None:
        mods.append(f"pri={route.priority}")
    if route.weight is not None:
        mods.append(f"w={route.weight}")
    if route.ttl is not None:
        mods.append(f"ttl={route.ttl}")
    if mods:
        text += " [" + ", ".join(mods) + "]"
    return text


def emit(topology: Topology) -> str:
    lines = ["flowchart LR"]

    # Node definitions — sorted for deterministic output.
    for node_id in sorted(topology.nodes):
        node = topology.nodes[node_id]
        lines.append(f"    {_node_def(node)}")

    if any(n.routes for n in topology.nodes.values()):
        lines.append("")

    # Edges — one per Route, grouped by source node.
    for node_id in sorted(topology.nodes):
        node = topology.nodes[node_id]
        for route in node.routes:
            src = _safe_id(node_id)
            dst = _safe_id(route.next_hop)
            arrow = _edge_arrow(route.kind)
            label = _match_label(route)
            lines.append(f'    {src} {arrow}|"{label}"| {dst}')

    return "\n".join(lines) + "\n"
