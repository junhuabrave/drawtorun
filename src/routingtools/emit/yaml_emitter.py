"""Emit a Topology as YAML, matching the design doc's per-node routing-table form."""
from __future__ import annotations
from typing import Any, Dict, List

import yaml

from ..model import Node, Route, Topology


def emit(topology: Topology) -> str:
    """Return the topology serialized to YAML text."""
    out: Dict[str, Any] = {"nodes": {}}
    for node_id in sorted(topology.nodes):
        out["nodes"][node_id] = _node_to_dict(topology.nodes[node_id])
    return yaml.safe_dump(out, sort_keys=False, default_flow_style=False, width=10_000)


def _node_to_dict(node: Node) -> Dict[str, Any]:
    d: Dict[str, Any] = {"type": node.type}
    if node.region:
        d["region"] = node.region
    if node.environment:
        d["environment"] = node.environment
    if node.pair:
        d["pair"] = node.pair
    if node.routes:
        d["routes"] = [_route_to_dict(r) for r in node.routes]
    elif node.type != "feed":
        d["routes"] = []
    return d


def _route_to_dict(route: Route) -> Dict[str, Any]:
    d: Dict[str, Any] = {}
    if route.match is None:
        d["default"] = True
    else:
        # Emit as a YAML list. Wildcards stay as the string "*".
        d["match"] = list(route.match)
    d["next_hop"] = route.next_hop
    d["kind"] = route.kind
    if route.priority is not None:
        d["priority"] = route.priority
    if route.weight is not None:
        d["weight"] = route.weight
    if route.ttl is not None:
        d["ttl"] = route.ttl
    return d
