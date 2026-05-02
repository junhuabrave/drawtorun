"""Raw .excalidraw JSON loader.

Pure function from file bytes -> structured RawDiagram. No business logic, no
convention application. Anything that depends on routing semantics belongs in
parser.py.

Excalidraw element shape (subset we use):

    rectangle / diamond / ellipse:
        id, type, x, y, width, height,
        strokeColor, backgroundColor, fillStyle, strokeStyle,
        roundness (None = sharp; truthy = rounded),
        frameId, boundElements: [{id, type}]

    arrow:
        id, type="arrow", strokeColor, strokeStyle,
        startBinding: {elementId, ...} | None,
        endBinding:   {elementId, ...} | None,
        boundElements: [{id, type="text"}]   (the arrow's label)

    text:
        id, type="text", text, containerId

    frame:
        id, type="frame", name, x, y, width, height
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class RawShape:
    id: str
    shape: str                          # "rectangle" | "diamond" | "ellipse"
    x: float
    y: float
    width: float
    height: float
    stroke_color: str
    background_color: str
    fill_style: str
    stroke_style: str                   # "solid" | "dashed" | "dotted"
    rounded: bool                       # rectangle with non-null roundness
    frame_id: Optional[str]
    label: Optional[str]


@dataclass
class RawArrow:
    id: str
    stroke_color: str
    stroke_style: str                   # "solid" | "dashed" | "dotted"
    start_id: Optional[str]
    end_id: Optional[str]
    label: Optional[str]


@dataclass
class RawFrame:
    id: str
    name: str


@dataclass
class RawDiagram:
    file_path: str
    shapes: Dict[str, RawShape] = field(default_factory=dict)
    arrows: Dict[str, RawArrow] = field(default_factory=dict)
    frames: Dict[str, RawFrame] = field(default_factory=dict)


# Element types we accept as "node" shapes
_SHAPE_TYPES = {"rectangle", "diamond", "ellipse"}


def load(path: str | Path) -> RawDiagram:
    """Load a .excalidraw file into a RawDiagram."""
    p = Path(path)
    data = json.loads(p.read_text())
    elements = data.get("elements", [])

    # First pass: index text elements by containerId / element binding for label resolution.
    text_by_container: Dict[str, str] = {}
    text_by_id: Dict[str, str] = {}
    for el in elements:
        if el.get("type") == "text":
            text_by_id[el["id"]] = el.get("text", "")
            container_id = el.get("containerId")
            if container_id:
                text_by_container[container_id] = el.get("text", "")

    diagram = RawDiagram(file_path=str(p))

    # Second pass: build shapes, arrows, frames.
    for el in elements:
        et = el.get("type")
        if et == "frame":
            diagram.frames[el["id"]] = RawFrame(
                id=el["id"],
                name=el.get("name") or "",
            )
        elif et in _SHAPE_TYPES:
            label = text_by_container.get(el["id"])
            # Fallback: walk boundElements for a text child.
            if not label:
                for be in el.get("boundElements") or []:
                    if be.get("type") == "text" and be.get("id") in text_by_id:
                        label = text_by_id[be["id"]]
                        break
            roundness = el.get("roundness")
            diagram.shapes[el["id"]] = RawShape(
                id=el["id"],
                shape=et,
                x=float(el.get("x", 0)),
                y=float(el.get("y", 0)),
                width=float(el.get("width", 0)),
                height=float(el.get("height", 0)),
                stroke_color=el.get("strokeColor", "#000000"),
                background_color=el.get("backgroundColor", "transparent"),
                fill_style=el.get("fillStyle", "hachure"),
                stroke_style=el.get("strokeStyle", "solid"),
                rounded=bool(roundness),
                frame_id=el.get("frameId"),
                label=(label or "").strip() or None,
            )
        elif et == "arrow":
            label = None
            for be in el.get("boundElements") or []:
                if be.get("type") == "text" and be.get("id") in text_by_id:
                    label = text_by_id[be["id"]]
                    break
            sb = el.get("startBinding") or {}
            eb = el.get("endBinding") or {}
            diagram.arrows[el["id"]] = RawArrow(
                id=el["id"],
                stroke_color=el.get("strokeColor", "#000000"),
                stroke_style=el.get("strokeStyle", "solid"),
                start_id=sb.get("elementId"),
                end_id=eb.get("elementId"),
                label=(label or "").strip() or None,
            )
        # Other element types (line, freedraw, image, ...) are ignored.

    return diagram


def shapes_in_frame(diagram: RawDiagram, frame_id: str) -> List[RawShape]:
    return [s for s in diagram.shapes.values() if s.frame_id == frame_id]


def find_frame_for_shape(diagram: RawDiagram, shape: RawShape) -> Optional[RawFrame]:
    if not shape.frame_id:
        return None
    return diagram.frames.get(shape.frame_id)
