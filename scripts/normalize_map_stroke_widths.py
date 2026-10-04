#!/usr/bin/env python3
"""Make every Country map's line widths render at the shared standard.

Country maps are shown as <img> at a fraction of their 1200x760 viewBox, so a
stroke of 1.5 viewBox units renders the same everywhere *unless*:

* `vector-effect="non-scaling-stroke"` is set: the width is then fixed in
  rendered pixels and looks about twice as thick on the page as every other map;
* the stroked element sits under a scaling `transform`: the width is multiplied
  by the scale (St Lucia x2.1, Paraguay x1.6, Benin x3.7, South Africa x0.72).

This rewrites those cases so the *effective* width in viewBox units equals the
declared shared value (target 1.5, context 1, lakes .65, …):

1. anisotropic transforms (x and y scaled differently) are baked into the path
   coordinates of the element's descendants and of any clipPath it references;
2. non-scaling-stroke is removed and each stroked path gets an explicit
   `stroke-width = declared / scale` for its remaining (isotropic) transform;
3. the shared drop shadow gets a per-scale copy so its blur also matches.

Geometry is unchanged in rendered position; only stroke widths and shadow size.
"""
from __future__ import annotations

import argparse
import math
import re
from pathlib import Path
from xml.etree import ElementTree as ET

from svgelements import Matrix, Path as SvgPath

NS = "http://www.w3.org/2000/svg"
Q = "{%s}" % NS
ET.register_namespace("", NS)
CANVAS_FRAME = "M 0,0 L 1200,0 L 1200,760 L 0,760 Z "
STROKED = {Q + "path", Q + "polyline", Q + "line", Q + "polygon", Q + "rect", Q + "circle", Q + "ellipse"}


def parse(text: str) -> ET.Element:
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    return ET.fromstring(text, parser=parser)


def matrix_of(transform: str | None) -> Matrix:
    return Matrix(transform) if transform else Matrix()


def scales(m: Matrix) -> tuple[float, float]:
    return math.hypot(m.a, m.b), math.hypot(m.c, m.d)


def fmt(v: float) -> str:
    text = f"{v:.3f}".rstrip("0").rstrip(".")
    return text or "0"


def bake_path(el: ET.Element, m: Matrix) -> None:
    if el.tag != Q + "path":
        raise ValueError(f"Cannot bake anisotropic transform into <{el.tag.split('}')[1]}>")
    d = el.get("d")
    if d:
        p = SvgPath(d) * m
        el.set("d", p.d())


def bake_anisotropic(root: ET.Element) -> int:
    """Push anisotropic transforms down into path data. Returns count baked."""
    clips = {c.get("id"): c for c in root.iter(Q + "clipPath")}
    baked = 0
    for el in list(root.iter()):
        t = el.get("transform")
        if not t:
            continue
        m = matrix_of(t)
        sx, sy = scales(m)
        if abs(sx / sy - 1) <= 0.02:
            continue
        targets = [el] if el.tag == Q + "path" else [d for d in el.iter() if d is not el and d.tag in STROKED | {Q + "path"}]
        for d in targets:
            if d is not el and d.get("transform"):
                raise ValueError("Nested transform under anisotropic transform is not supported")
            bake_path(d, m)
        ref = re.match(r"url\(#([^)]+)\)", el.get("clip-path") or "")
        if ref and ref.group(1) in clips:
            for d in clips[ref.group(1)].iter(Q + "path"):
                # The shared negative clip starts with the full-canvas frame; keep
                # it canonical (it only needs to cover everything) and bake the rest.
                rest = (d.get("d") or "")
                if rest.startswith(CANVAS_FRAME):
                    d.set("d", rest[len(CANVAS_FRAME):])
                    bake_path(d, m)
                    d.set("d", CANVAS_FRAME + d.get("d"))
                else:
                    bake_path(d, m)
        del el.attrib["transform"]
        baked += 1
    return baked


def fix_widths(root: ET.Element) -> tuple[int, set[float]]:
    changed = 0
    shadow_scales: set[float] = set()

    def walk(el: ET.Element, ctm: Matrix, width: str, stroke: str | None, nonscaling: bool):
        nonlocal changed
        m = Matrix(ctm)
        if el.get("transform"):
            m = matrix_of(el.get("transform")) * ctm
        width = el.get("stroke-width", width)
        stroke = el.get("stroke", stroke)
        if el.get("vector-effect") == "non-scaling-stroke":
            nonscaling = True
            del el.attrib["vector-effect"]
            changed += 1
        sx, sy = scales(m)
        s = math.sqrt(sx * sy)
        if el.get("filter") == "url(#shadow)" and abs(s - 1) > 0.01:
            key = round(s, 4)
            shadow_scales.add(key)
            el.set("filter", f"url(#shadow-s{str(key).replace('.', '_')})")
        if el.tag in STROKED and stroke not in (None, "none") and abs(s - 1) > 0.005:
            el.set("stroke-width", fmt(float(width) / s))
            changed += 1
        for child in el:
            walk(child, m, width, stroke, nonscaling)

    walk(root, Matrix(), "1", None, False)
    return changed, shadow_scales


def add_scaled_shadows(root: ET.Element, scales_needed: set[float]) -> None:
    defs = root.find(Q + "defs")
    base = next((f for f in root.iter(Q + "filter") if f.get("id") == "shadow"), None)
    if base is None or defs is None:
        return
    for s in sorted(scales_needed):
        clone = ET.fromstring(ET.tostring(base))
        clone.set("id", f"shadow-s{str(s).replace('.', '_')}")
        for node in clone.iter():
            if node.get("stdDeviation"):
                node.set("stdDeviation", fmt(float(node.get("stdDeviation")) / s))
            if node.get("dy"):
                node.set("dy", fmt(float(node.get("dy")) / s))
        defs.append(clone)


def normalize(text: str) -> tuple[str, dict]:
    root = parse(text)
    baked = bake_anisotropic(root)
    changed, shadow_scales = fix_widths(root)
    add_scaled_shadows(root, shadow_scales)
    out = ET.tostring(root, encoding="unicode")
    return out, {"baked": baked, "widths": changed, "shadows": len(shadow_scales)}


def needs_fix(text: str) -> bool:
    if "non-scaling-stroke" in text:
        return True
    for t in re.findall(r'transform="([^"]+)"', text):
        sx, sy = scales(matrix_of(t))
        if abs(sx - 1) > 0.005 or abs(sy - 1) > 0.005:
            return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    out, report = normalize(args.input.read_text(encoding="utf-8"))
    args.output.write_text(out, encoding="utf-8")
    print(f"{args.output}: {report}")


if __name__ == "__main__":
    main()
