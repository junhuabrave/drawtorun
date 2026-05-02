"""Validate a Topology against the parser invariants from the design doc."""
from __future__ import annotations
from typing import List

from .model import Finding, MatchKey, Node, Topology


def validate(topology: Topology) -> List[Finding]:
    findings: List[Finding] = []

    enums = topology.enums

    for node in topology.nodes.values():
        # Feed has no outbound.
        if node.type == "feed" and node.routes:
            findings.append(Finding(
                severity="error",
                code="FEED_HAS_OUTBOUND",
                message=f"Feed {node.id!r} has {len(node.routes)} outbound arrow(s); feeds must be sinks.",
                node_id=node.id,
            ))

        # Isolated non-feed nodes (zero outbound) -> warning.
        if node.type != "feed" and not node.routes:
            findings.append(Finding(
                severity="warning",
                code="ISOLATED_NODE",
                message=f"Node {node.id!r} ({node.type}) has no outbound routes.",
                node_id=node.id,
            ))

        # Validate routes.
        for r in node.routes:
            # next_hop must resolve to a canonical node.
            if r.next_hop not in topology.nodes:
                findings.append(Finding(
                    severity="error",
                    code="DANGLING_NEXT_HOP",
                    message=f"Route on {node.id!r} points at undefined node {r.next_hop!r}.",
                    file=r.source_file,
                    node_id=node.id,
                    arrow_id=r.arrow_id,
                ))

            # Enum validation for keyed routes.
            if r.match is not None:
                _validate_match(r.match, enums, node, r, findings)

            # Failover routes should have priority.
            if r.kind == "failover" and r.priority is None:
                findings.append(Finding(
                    severity="warning",
                    code="FAILOVER_NO_PRIORITY",
                    message=f"Failover route on {node.id!r} has no [pri=N] modifier.",
                    file=r.source_file,
                    node_id=node.id,
                    arrow_id=r.arrow_id,
                ))

        # Client default-hop idiom check (informational, surfaced only when keyed routes exist too).
        if node.type == "client":
            keyed = [r for r in node.routes if r.match is not None]
            if keyed:
                findings.append(Finding(
                    severity="warning",
                    code="CLIENT_HAS_KEYED_ROUTES",
                    message=(
                        f"Client {node.id!r} has {len(keyed)} keyed route(s) in addition to its default. "
                        f"Confirm this is intentional (clients usually only forward to a client_route node)."
                    ),
                    node_id=node.id,
                ))

        # Bridge half pairing.
        if node.type in ("cross_region_bridge", "cross_environment_bridge") and "." in node.id:
            base, _, _ = node.id.rpartition(".")
            if not node.pair:
                findings.append(Finding(
                    severity="warning",
                    code="MISSING_BRIDGE_HALF",
                    message=(
                        f"Bridge {node.id!r} appears to be a half (id contains '.') but has no paired half. "
                        f"Add the matching node or use a non-dotted id."
                    ),
                    node_id=node.id,
                ))

    return findings


def _validate_match(match: MatchKey, enums, node: Node, route, findings: List[Finding]) -> None:
    src, typ, ident, exch = match
    enum_checks = [
        ("source",   src,  enums.sources),
        ("type",     typ,  enums.types),
        ("exchange", exch, enums.exchanges),
    ]
    for label, value, allowed in enum_checks:
        if value == "*":
            continue
        if allowed and value not in allowed:
            findings.append(Finding(
                severity="error",
                code="UNKNOWN_ENUM_VALUE",
                message=(
                    f"Route on {node.id!r} uses unknown {label}={value!r}. "
                    f"Allowed: {allowed}"
                ),
                file=route.source_file,
                node_id=node.id,
                arrow_id=route.arrow_id,
            ))
    # `id` is free-form; require non-empty.
    if not ident:
        findings.append(Finding(
            severity="error",
            code="EMPTY_ID_TOKEN",
            message=f"Route on {node.id!r} has an empty id token.",
            file=route.source_file,
            node_id=node.id,
            arrow_id=route.arrow_id,
        ))


def has_errors(findings: List[Finding]) -> bool:
    return any(f.severity == "error" for f in findings)
