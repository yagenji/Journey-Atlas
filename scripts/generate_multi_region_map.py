#!/usr/bin/env python3
"""Generate a multi-region Country map (mainland + inset regions) with the shared generator.

`generate_country_map_with_context.py` only handles single-region maps. For a
Country JSON with `map.regions`, this script:

1. computes, for each region, the lon/lat extent that the whole 1200x760 canvas
   covers under that region's rect-fit projection (latitude symmetric about the
   region mid-latitude, so the runtime marker projection is unchanged);
2. runs the shared single-region generator over that extent;
3. places each result with an exact affine transform so the region's own
   bounds land in its `rect`, exactly as `assets/js/app.js` projects markers.

The primary region (the first, or `--primary`) is drawn across the whole canvas
so its surrounding geography continues past its rect instead of stopping at a
hard edge. Every other region is clipped to its inset frame, which gets an
opaque sea background so it reads as a separate panel over the primary region.

Existing inset frames / explanation labels in the current SVG are carried over
unchanged (`[data-map-inset-frame]`, `[data-map-inset-explanation]`).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import drop_domestic_context  # noqa: E402

WIDTH, HEIGHT = 1200, 760
SCRIPTS = Path(__file__).resolve().parent


def region_fit(bounds: dict, rect: dict):
    lon_scale = math.cos(math.radians((bounds["south"] + bounds["north"]) / 2))
    pw = (bounds["east"] - bounds["west"]) * lon_scale
    ph = bounds["north"] - bounds["south"]
    scale = min(rect["width"] / pw, rect["height"] / ph)
    ox = rect["x"] + (rect["width"] - pw * scale) / 2
    oy = rect["y"] + (rect["height"] - ph * scale) / 2
    return lon_scale, scale, ox, oy


def canvas_extent(bounds: dict, rect: dict) -> dict:
    """Lon/lat extent covered by the full canvas under the region projection."""
    lon_scale, scale, ox, oy = region_fit(bounds, rect)
    west = bounds["west"] - ox / (scale * lon_scale)
    east = bounds["west"] + (WIDTH - ox) / (scale * lon_scale)
    # oy is symmetric only when the rect is vertically centred; keep the same
    # mid-latitude so cos(mid-lat) is identical to the runtime projection.
    mid = (bounds["south"] + bounds["north"]) / 2
    half = HEIGHT / 2 / scale
    north, south = mid + half, mid - half
    return {"west": west, "east": east, "south": south, "north": north}


def placement(bounds: dict, rect: dict, extent: dict) -> tuple[float, float, float]:
    """Affine (scale k, tx, ty) mapping generator canvas coordinates to the final canvas."""
    lon_scale, scale, ox, oy = region_fit(bounds, rect)
    # Generator fit of `extent` onto the full canvas (same cos, by construction).
    _, gscale, gox, goy = region_fit(extent, {"x": 0, "y": 0, "width": WIDTH, "height": HEIGHT})
    k = scale / gscale
    # A lon/lat point: generator x = gox + (lon - ext.west)*lon_scale*gscale
    #                  final x     = ox  + (lon - b.west)  *lon_scale*scale
    tx = ox + (extent["west"] - bounds["west"]) * lon_scale * scale - gox * k
    ty = oy + (bounds["north"] - extent["north"]) * scale - goy * k
    return k, tx, ty


def generate(country: dict, extent: dict, dataset: Path, name: str, resolution: str, simplify: float,
             workdir: Path, tag: str) -> str:
    temp_country = json.loads(json.dumps(country))
    temp_country["map"] = {"bounds": extent, "svg": "unused.svg"}
    country_path = workdir / f"{tag}.json"
    country_path.write_text(json.dumps(temp_country, ensure_ascii=False), encoding="utf-8")
    output = workdir / f"{tag}.svg"
    subprocess.run([
        sys.executable, str(SCRIPTS / "generate_country_map_with_context.py"),
        "--country-json", str(country_path), "--output", str(output),
        "--source", "natural-earth", "--dataset", str(dataset), "--country-name", name, "--map-name", name,
        "--context-resolution", resolution, "--simplify", str(simplify),
    ], check=True)
    return output.read_text(encoding="utf-8")


def inner(svg: str) -> tuple[str, str]:
    """Return (defs inner xml, body xml without the sea background rect)."""
    defs = re.search(r"<defs>(.*?)</defs>", svg, re.S)
    body = svg[svg.index(">", svg.index("<svg")) + 1: svg.rindex("</svg>")]
    body = re.sub(r"<metadata>.*?</metadata>", "", body, flags=re.S)
    body = re.sub(r"<defs>.*?</defs>", "", body, flags=re.S)
    body = re.sub(r'<rect width="1200" height="760" fill="url\(#sea\)"/>', "", body, count=1)
    return (defs.group(1) if defs else ""), body


def scale_strokes(body: str, k: float) -> str:
    return re.sub(r'stroke-width="([0-9.]+)"', lambda m: f'stroke-width="{float(m.group(1)) / k:.3f}"', body)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country-json", required=True, type=Path)
    parser.add_argument("--dataset", required=True, action="append", type=Path,
                        help="Admin-0 GeoJSON per region, in region order (repeat; a single value is reused)")
    parser.add_argument("--country-name", required=True)
    parser.add_argument("--resolution", default="i", choices=("i", "h", "f"))
    parser.add_argument("--simplify", default=0.003, type=float)
    parser.add_argument("--primary", help="Region id drawn across the whole canvas (default: first region)")
    parser.add_argument("--current-svg", type=Path, help="SVG to copy inset frames / explanations from")
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    country = json.loads(args.country_json.read_text(encoding="utf-8"))
    regions = country["map"]["regions"]
    primary = args.primary or regions[0]["id"]
    datasets = args.dataset if len(args.dataset) == len(regions) else [args.dataset[0]] * len(regions)
    defs_out, layers, frames = "", [], ""
    if args.current_svg:
        current = args.current_svg.read_text(encoding="utf-8")
        frames = "\n".join(re.findall(r"<g data-map-inset-frame[^>]*>.*?</g>", current, re.S)
                           + re.findall(r"<g data-map-inset-explanation[^>]*>.*?</g>", current, re.S))
    with tempfile.TemporaryDirectory(prefix="atlas-multiregion-") as tmp:
        for index, (region, dataset) in enumerate(zip(regions, datasets)):
            extent = canvas_extent(region["bounds"], region["rect"])
            svg = generate(country, extent, dataset, args.country_name, args.resolution, args.simplify,
                           Path(tmp), region["id"])
            svg, _ = drop_domestic_context.clean(svg)
            defs, body = inner(svg)
            k, tx, ty = placement(region["bounds"], region["rect"], extent)
            # Keep ids unique per region; the primary region keeps the canonical ids
            # (e.g. #geographic-context) that shared QA looks for.
            suffix = f"-{region['id']}"
            for ident in ([] if region["id"] == primary else set(re.findall(r'id="([^"]+)"', defs + body))):
                if ident in ("sea", "land", "shadow"):
                    continue
                defs = defs.replace(f'id="{ident}"', f'id="{ident}{suffix}"').replace(f"url(#{ident})", f"url(#{ident}{suffix})")
                body = body.replace(f'id="{ident}"', f'id="{ident}{suffix}"').replace(f"url(#{ident})", f"url(#{ident}{suffix})")
            if index == 0:
                defs_out += defs
            else:
                defs_out += re.sub(r'<(linearGradient|filter) id="(sea|land|shadow)".*?</\1>', "", defs, flags=re.S)
            body = scale_strokes(body, k)
            transform = f'transform="matrix({k:.6f} 0 0 {k:.6f} {tx:.3f} {ty:.3f})"'
            if region["id"] == primary:
                layers.insert(0, f'<g data-map-region="{region["id"]}" {transform}>{body}</g>')
            else:
                r = region["rect"]
                clip = f"region-clip{suffix}"
                defs_out += f'<clipPath id="{clip}"><rect x="{r["x"]}" y="{r["y"]}" width="{r["width"]}" height="{r["height"]}"/></clipPath>'
                pad = 10  # covers the dashed inset frame drawn just outside the rect
                background = (
                    f'<rect data-map-inset-background="{region["id"]}" x="{r["x"] - pad}" y="{r["y"] - pad}" '
                    f'width="{r["width"] + 2 * pad}" height="{r["height"] + 2 * pad}" rx="7" fill="url(#sea)"/>'
                ) if frames else ""
                layers.append(
                    background +
                    f'<g clip-path="url(#{clip})"><g data-map-region="{region["id"]}" {transform}>{body}</g></g>'
                )
    name = country.get("map", {}).get("mapName") or args.country_name
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Map of {name}" '
        'data-map-style="journey-atlas-map-v3-clean-background" data-map-projection="multi-region-local-equirectangular-fit-v1">\n'
        f"<metadata>{args.metadata}</metadata>\n<defs>{defs_out}</defs>\n"
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#sea)"/>\n' + "\n".join(layers) + "\n" + frames + "\n</svg>\n"
    )
    args.output.write_text(svg, encoding="utf-8")
    print(f"Wrote {args.output} ({len(svg.encode())} bytes, {len(regions)} regions)")


if __name__ == "__main__":
    main()
