"""Emit a Topology as CSV — one row per edge (route).

Useful for diff review and audit. Wildcards stay as the literal token "*".
"""
from __future__ import annotations
import csv
import io

from ..model import Route, Topology


HEADER = [
    "from", "env_from", "source", "type", "id", "exchange",
    "is_default", "kind", "priority", "weight", "to", "env_to",
]


def emit(topology: Topology) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(HEADER)
    for nid in sorted(topology.nodes):
        node = topology.nodes[nid]
        for r in node.routes:
            target = topology.nodes.get(r.next_hop)
            env_to = target.environment if target else ""
            w.writerow(_row(node, r, env_to))
    return buf.getvalue()


def _row(node, route: Route, env_to: str):
    if route.match is None:
        src = typ = ident = exch = ""
        is_default = "true"
    else:
        src, typ, ident, exch = route.match
        is_default = "false"
    return [
        node.id,
        node.environment or "",
        src, typ, ident, exch,
        is_default,
        route.kind,
        "" if route.priority is None else route.priority,
        "" if route.weight is None else route.weight,
        route.next_hop,
        env_to,
    ]
