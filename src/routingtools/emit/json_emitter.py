"""Emit a Topology as JSON. Mirrors yaml_emitter shape."""
from __future__ import annotations
import json

from .yaml_emitter import _node_to_dict
from ..model import Topology


def emit(topology: Topology) -> str:
    out = {"nodes": {nid: _node_to_dict(topology.nodes[nid]) for nid in sorted(topology.nodes)}}
    return json.dumps(out, indent=2)
