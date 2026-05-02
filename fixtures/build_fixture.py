"""Programmatically build .excalidraw fixtures for tests, demos, and Excalidraw web.

Run from the routing-tools/ directory:

    python fixtures/build_fixture.py

Writes:
    fixtures/single_file/hk-prod.excalidraw       # one HK file
    fixtures/single_file/manifest.yaml

    fixtures/multi_file/manifest.yaml             # HK + NY with bridge halves
    fixtures/multi_file/prod/hk.excalidraw
    fixtures/multi_file/prod/ny.excalidraw

    fixtures/showcase.excalidraw                  # legend + worked example, for opening in Excalidraw

Each file is structured to load cleanly in https://excalidraw.com.
"""
from __future__ import annotations
import json
import random
import time
from pathlib import Path
from typing import List, Optional


TEAL = "#2dd4bf"
BLUE = "#3b82f6"
PURPLE = "#a855f7"
WHITE = "#ffffff"
TRANSPARENT = "transparent"

FIXTURES_DIR = Path(__file__).parent

_rng = random.Random(20260501)   # deterministic for reproducible builds


def _rand_seed() -> int:
    return _rng.randint(1, 2**31)


def _now_ms() -> int:
    return int(time.time() * 1000)


_BASE_ELEMENT = {
    "angle": 0,
    "strokeWidth": 1,
    "roughness": 1,
    "opacity": 100,
    "groupIds": [],
    "isDeleted": False,
    "version": 1,
    "boundElements": [],
    "link": None,
    "locked": False,
}


def _base(extra: dict) -> dict:
    """Return a fresh element dict with required Excalidraw fields populated."""
    el = dict(_BASE_ELEMENT)
    el["seed"] = _rand_seed()
    el["versionNonce"] = _rand_seed()
    el["updated"] = _now_ms()
    el["frameId"] = None
    el.update(extra)
    return el


class DiagramBuilder:
    def __init__(self):
        self.elements: List[dict] = []
        self._counter = 0

    def _next_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}-{self._counter:04d}"

    # ----- frames -----
    def frame(self, name: str, x: float, y: float, w: float, h: float) -> str:
        fid = self._next_id("frame")
        self.elements.append(_base({
            "id": fid,
            "type": "frame",
            "name": name,
            "x": x, "y": y, "width": w, "height": h,
            "strokeColor": "#bbbbbb",
            "backgroundColor": TRANSPARENT,
            "fillStyle": "solid",
            "strokeStyle": "solid",
            "roundness": None,
        }))
        return fid

    # ----- shapes (rectangle / diamond / ellipse) -----
    def shape(
        self,
        kind: str,
        label: str,
        x: float, y: float,
        w: float = 200, h: float = 80,
        rounded: bool = False,
        stroke_style: str = "solid",
        bg_color: str = TEAL,
        fill_style: str = "solid",
        frame_id: Optional[str] = None,
    ) -> str:
        sid = self._next_id("shape")
        tid = self._next_id("text")
        roundness = {"type": 3} if rounded else None
        self.elements.append(_base({
            "id": sid,
            "type": kind,
            "x": x, "y": y, "width": w, "height": h,
            "strokeColor": "#1e1e1e",
            "backgroundColor": bg_color,
            "fillStyle": fill_style,
            "strokeStyle": stroke_style,
            "roundness": roundness,
            "frameId": frame_id,
            "boundElements": [{"type": "text", "id": tid}],
        }))
        # Container-bound text: x/y/width/height are runtime-overridden by Excalidraw,
        # but we set sane initial values anyway.
        line_h = 25
        self.elements.append(_base({
            "id": tid,
            "type": "text",
            "x": x + 8,
            "y": y + h / 2 - line_h / 2,
            "width": w - 16,
            "height": line_h,
            "strokeColor": "#1e1e1e",
            "backgroundColor": TRANSPARENT,
            "fillStyle": "solid",
            "strokeStyle": "solid",
            "roundness": None,
            "fontSize": 18,
            "fontFamily": 1,
            "text": label,
            "textAlign": "center",
            "verticalAlign": "middle",
            "containerId": sid,
            "originalText": label,
            "lineHeight": 1.25,
            "baseline": 18,
            "autoResize": True,
            "frameId": frame_id,
        }))
        return sid

    # ----- arrows -----
    def arrow(
        self,
        src_id: str, dst_id: str,
        label: Optional[str] = None,
        stroke_style: str = "solid",
        stroke_color: str = "#1e1e1e",
        frame_id: Optional[str] = None,
    ) -> str:
        # Resolve source and target geometry to draw a sensible line.
        src = self._find(src_id)
        dst = self._find(dst_id)
        sx = src["x"] + src["width"]            # right edge of source
        sy = src["y"] + src["height"] / 2
        ex = dst["x"]                           # left edge of target
        ey = dst["y"] + dst["height"] / 2

        aid = self._next_id("arrow")
        bound: List[dict] = []
        text_id = None
        if label:
            text_id = self._next_id("text")
            bound.append({"type": "text", "id": text_id})

        # Arrow geometry: we encode as a 2-point line in absolute -> relative form.
        ax, ay = sx, sy
        rel_x = ex - sx
        rel_y = ey - sy

        self.elements.append(_base({
            "id": aid,
            "type": "arrow",
            "x": ax, "y": ay,
            "width": abs(rel_x) or 1,
            "height": abs(rel_y) or 1,
            "strokeColor": stroke_color,
            "backgroundColor": TRANSPARENT,
            "fillStyle": "solid",
            "strokeStyle": stroke_style,
            "roundness": {"type": 2},
            "points": [[0.0, 0.0], [rel_x, rel_y]],
            "lastCommittedPoint": None,
            "startBinding": {"elementId": src_id, "focus": 0, "gap": 4},
            "endBinding":   {"elementId": dst_id, "focus": 0, "gap": 4},
            "startArrowhead": None,
            "endArrowhead": "arrow",
            "elbowed": False,
            "frameId": frame_id,
            "boundElements": bound,
        }))

        if text_id:
            mx = ax + rel_x / 2
            my = ay + rel_y / 2 - 12
            line_h = 22
            self.elements.append(_base({
                "id": text_id,
                "type": "text",
                "x": mx - 80,
                "y": my,
                "width": 160,
                "height": line_h,
                "strokeColor": "#1e1e1e",
                "backgroundColor": TRANSPARENT,
                "fillStyle": "solid",
                "strokeStyle": "solid",
                "roundness": None,
                "fontSize": 16,
                "fontFamily": 1,
                "text": label,
                "textAlign": "center",
                "verticalAlign": "middle",
                "containerId": None,
                "originalText": label,
                "lineHeight": 1.25,
                "baseline": 16,
                "autoResize": True,
                "frameId": frame_id,
            }))
        return aid

    def label_only(self, text: str, x: float, y: float, font_size: int = 16,
                   frame_id: Optional[str] = None) -> str:
        tid = self._next_id("text")
        self.elements.append(_base({
            "id": tid,
            "type": "text",
            "x": x, "y": y,
            "width": max(100, len(text) * font_size * 0.6),
            "height": font_size + 6,
            "strokeColor": "#1e1e1e",
            "backgroundColor": TRANSPARENT,
            "fillStyle": "solid",
            "strokeStyle": "solid",
            "roundness": None,
            "fontSize": font_size,
            "fontFamily": 1,
            "text": text,
            "textAlign": "left",
            "verticalAlign": "top",
            "containerId": None,
            "originalText": text,
            "lineHeight": 1.25,
            "baseline": font_size,
            "autoResize": True,
            "frameId": frame_id,
        }))
        return tid

    def _find(self, eid: str) -> dict:
        for e in self.elements:
            if e["id"] == eid:
                return e
        raise KeyError(eid)

    def to_excalidraw(self) -> dict:
        return {
            "type": "excalidraw",
            "version": 2,
            "source": "https://excalidraw.com",
            "elements": self.elements,
            "appState": {
                "gridSize": None,
                "viewBackgroundColor": WHITE,
            },
            "files": {},
        }


# =============== Single-file fixture =================

def build_single_file_fixture(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    b = DiagramBuilder()
    prod = b.frame("prod", 0, 0, 1100, 380)

    desk = b.shape("rectangle", "hk-desk-7",       60,  80, rounded=True, frame_id=prod)
    rt   = b.shape("rectangle", "hk-route-1",     360,  80, frame_id=prod)
    bbg  = b.shape("ellipse",   "hk-bbg-feed",    760,  20, frame_id=prod)
    dft  = b.shape("ellipse",   "hk-default-feed",760, 180, frame_id=prod)

    b.arrow(desk, rt, frame_id=prod)
    b.arrow(rt, bbg, label="bloomberg trade * *", frame_id=prod)
    b.arrow(rt, dft, label="default", frame_id=prod)

    (out_dir / "hk-prod.excalidraw").write_text(json.dumps(b.to_excalidraw(), indent=2))
    (out_dir / "manifest.yaml").write_text(_single_file_manifest())


def _single_file_manifest() -> str:
    return """\
version: 1

files:
  - path: hk-prod.excalidraw
    scope: { region: hk, environment: prod }

enums:
  sources:      [bloomberg, refinitiv, ice, direct]
  types:        [trade, orderbook, greeks, nbbo]
  exchanges:    [nyse, nasdaq, hkex, sehk]
  environments: [prod, uat]
  regions:      [hk, ny]

conventions:
  region_dimension: fill_color
  env_dimension: frame
  modifiers_in_label: true

output:
  formats: [yaml, json, csv]
  per_file: false
  merged: true
  output_dir: generated
"""


# =============== Multi-file fixture =================

def build_multi_file_fixture(out_dir: Path) -> None:
    (out_dir / "prod").mkdir(parents=True, exist_ok=True)

    # ----- HK side -----
    hk = DiagramBuilder()
    prod_hk = hk.frame("prod", 0, 0, 1300, 420)

    desk      = hk.shape("rectangle", "hk-desk-7",        60,  80, rounded=True, frame_id=prod_hk)
    route     = hk.shape("rectangle", "hk-route-1",      360,  80, frame_id=prod_hk)
    bridge_hk = hk.shape("diamond",   "hkny-bridge.hk",  720,  40, frame_id=prod_hk)
    bridge_ny = hk.shape("diamond",   "hkny-bridge.ny", 1020,  40,
                         stroke_style="dotted", frame_id=prod_hk)            # foreign ref
    feed_hkex = hk.shape("ellipse",   "hk-hkex-trades",  720, 220, frame_id=prod_hk)

    hk.arrow(desk, route, frame_id=prod_hk)                                    # default
    hk.arrow(route, bridge_hk, label="bloomberg trade * *", frame_id=prod_hk)
    hk.arrow(route, feed_hkex, label="* * * hkex", frame_id=prod_hk)
    hk.arrow(bridge_hk, bridge_ny, frame_id=prod_hk)                           # default to NY half

    (out_dir / "prod" / "hk.excalidraw").write_text(json.dumps(hk.to_excalidraw(), indent=2))

    # ----- NY side -----
    ny = DiagramBuilder()
    prod_ny = ny.frame("prod", 0, 0, 1100, 380)

    bridge_ny = ny.shape("diamond",   "hkny-bridge.ny",  60,  80, bg_color=BLUE, frame_id=prod_ny)
    bridge_hk = ny.shape("diamond",   "hkny-bridge.hk",  60, 240,
                         stroke_style="dotted", bg_color=BLUE, frame_id=prod_ny)   # foreign ref
    route_ny  = ny.shape("rectangle", "ny-route-1",     400,  80, bg_color=BLUE, frame_id=prod_ny)
    feed_bbg  = ny.shape("ellipse",   "ny-bloomberg-trades", 800, 80, bg_color=BLUE, frame_id=prod_ny)

    ny.arrow(bridge_ny, route_ny, frame_id=prod_ny)                            # default
    ny.arrow(route_ny, feed_bbg, label="bloomberg trade * nyse", frame_id=prod_ny)

    (out_dir / "prod" / "ny.excalidraw").write_text(json.dumps(ny.to_excalidraw(), indent=2))

    (out_dir / "manifest.yaml").write_text(_multi_file_manifest())


def _multi_file_manifest() -> str:
    return """\
version: 1

files:
  - path: prod/hk.excalidraw
    scope: { region: hk, environment: prod }
  - path: prod/ny.excalidraw
    scope: { region: ny, environment: prod }

enums:
  sources:      [bloomberg, refinitiv, ice, direct]
  types:        [trade, orderbook, greeks, nbbo]
  exchanges:    [nyse, nasdaq, hkex, sehk]
  environments: [prod, uat]
  regions:      [hk, ny]

conventions:
  region_dimension: fill_color
  env_dimension: frame
  modifiers_in_label: true

output:
  formats: [yaml, json, csv]
  per_file: false
  merged: true
  output_dir: generated
"""


# =============== Showcase (single file with legend + worked example) ==========

def build_showcase(out_path: Path) -> None:
    """A single .excalidraw file with a legend block and the worked HK example.

    Designed to drag-and-drop into https://excalidraw.com to inspect the
    conventions visually.
    """
    b = DiagramBuilder()

    # ----- Legend frame -----
    legend = b.frame("legend", 0, 0, 1300, 400)
    b.label_only("Node types", 30, 20, 22, frame_id=legend)
    b.shape("rectangle", "client", 30, 70, rounded=True, frame_id=legend)
    b.shape("rectangle", "client_route", 250, 70, frame_id=legend)
    b.shape("diamond",   "x-region bridge", 470, 70, frame_id=legend)
    b.shape("diamond",   "x-env bridge",    690, 70, stroke_style="dashed", frame_id=legend)
    b.shape("ellipse",   "feed",            910, 70, frame_id=legend)
    b.shape("rectangle", "foreign ref",    1120, 70, stroke_style="dotted", frame_id=legend)

    b.label_only("Region (fill color): HK=teal, NY=blue, LDN=purple",
                 30, 180, 16, frame_id=legend)
    # Color swatches
    b.shape("rectangle", "hk", 30, 220, w=80, h=40, frame_id=legend)
    b.shape("rectangle", "ny", 130, 220, w=80, h=40, bg_color=BLUE, frame_id=legend)
    b.shape("rectangle", "ldn", 230, 220, w=80, h=40, bg_color=PURPLE, frame_id=legend)

    b.label_only("Arrow styles: solid=primary, dashed=failover, dotted=multicast.  "
                 "Empty / 'default' / '*' = default hop.",
                 30, 290, 16, frame_id=legend)
    b.label_only("Key format: 'source type id exchange'  (e.g. bloomberg trade AAPL nyse).  "
                 "Modifiers in brackets: [pri=N] [w=N] [ttl=N].",
                 30, 320, 16, frame_id=legend)

    # ----- Worked example frame -----
    prod = b.frame("prod", 0, 460, 1300, 420)

    desk      = b.shape("rectangle", "hk-desk-7",        60, 540, rounded=True, frame_id=prod)
    route     = b.shape("rectangle", "hk-route-1",      360, 540, frame_id=prod)
    bridge_hk = b.shape("diamond",   "hkny-bridge.hk",  720, 500, frame_id=prod)
    feed_hkex = b.shape("ellipse",   "hk-hkex-trades",  720, 680, frame_id=prod)
    bridge_ny = b.shape("diamond",   "hkny-bridge.ny", 1020, 500,
                        stroke_style="dotted", frame_id=prod)            # foreign ref

    b.arrow(desk, route, frame_id=prod)                                    # default
    b.arrow(route, bridge_hk, label="bloomberg trade * *", frame_id=prod)
    b.arrow(route, feed_hkex, label="* * * hkex", frame_id=prod)
    b.arrow(bridge_hk, bridge_ny, frame_id=prod)                           # default

    out_path.write_text(json.dumps(b.to_excalidraw(), indent=2))


def main():
    build_single_file_fixture(FIXTURES_DIR / "single_file")
    build_multi_file_fixture(FIXTURES_DIR / "multi_file")
    build_showcase(FIXTURES_DIR / "showcase.excalidraw")
    print("Fixtures written under", FIXTURES_DIR)


if __name__ == "__main__":
    main()
