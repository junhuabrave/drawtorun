"""Internal model produced by the convention parser and consumed by emitters/validators."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Literal


NodeType = Literal[
    "client",
    "client_route",
    "cross_region_bridge",
    "cross_environment_bridge",
    "feed",
]

RouteKind = Literal["primary", "failover", "multicast", "load_balanced"]

# A 4-part match key: source, type, id, exchange. Each part is a string or "*".
MatchKey = Tuple[str, str, str, str]


@dataclass
class Route:
    """One row in a node's routing table — one outbound arrow in the diagram."""
    next_hop: str
    kind: RouteKind = "primary"
    match: Optional[MatchKey] = None       # None -> default hop
    priority: Optional[int] = None         # [pri=N] modifier
    weight: Optional[int] = None           # [w=N] modifier
    ttl: Optional[int] = None              # [ttl=N] modifier
    source_file: str = ""                  # for diagnostics
    arrow_id: str = ""                     # for diagnostics

    @property
    def is_default(self) -> bool:
        return self.match is None


@dataclass
class Node:
    """One shape in the diagram."""
    id: str
    type: NodeType
    region: Optional[str] = None
    environment: Optional[str] = None
    pair: Optional[str] = None             # for bridge halves: id of paired half
    canonical_file: str = ""
    routes: List[Route] = field(default_factory=list)


@dataclass
class Enums:
    sources: List[str] = field(default_factory=list)
    types: List[str] = field(default_factory=list)
    exchanges: List[str] = field(default_factory=list)
    environments: List[str] = field(default_factory=list)
    regions: List[str] = field(default_factory=list)


@dataclass
class FileScope:
    path: str
    region: Optional[str] = None
    environment: Optional[str] = None
    kind: Optional[str] = None             # e.g. "feeds" for shared catalogs


@dataclass
class Topology:
    nodes: Dict[str, Node] = field(default_factory=dict)
    enums: Enums = field(default_factory=Enums)
    files: List[FileScope] = field(default_factory=list)


@dataclass
class Finding:
    """A validation finding — error or warning — emitted by the validator."""
    severity: Literal["error", "warning"]
    code: str
    message: str
    file: Optional[str] = None
    node_id: Optional[str] = None
    arrow_id: Optional[str] = None

    def format(self) -> str:
        loc = []
        if self.file:
            loc.append(self.file)
        if self.node_id:
            loc.append(f"node={self.node_id}")
        if self.arrow_id:
            loc.append(f"arrow={self.arrow_id}")
        loc_str = f" [{', '.join(loc)}]" if loc else ""
        return f"{self.severity.upper()} {self.code}: {self.message}{loc_str}"
