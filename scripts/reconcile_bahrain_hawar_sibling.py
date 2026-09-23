"""Replace *only staged foreign Hawar land* with independently checked sibling QAT ADM0.

Bahrain's approved national map and every other inset region remain untouched.
The sibling source and output were audited as a 1200x760 source-only candidate;
this migration helper does not imply overall Bahrain geographic signoff.
"""
from __future__ import annotations
import base64
import hashlib
import re
import zlib
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SVG='{http://www.w3.org/2000/svg}'
SOURCE_GIT_BLOB='afe2605d77c92e03124c7a5ff5cab8c639fe3060'
OLD_CONTEXT_SHA='d06ca98b93ec8285b0bdfff01c8abfa8f0e7c8aa50e3f429a74225de76c8250f'
PINNED_ASSET_GIT_BLOB='d669e16d210653b3a75b4402f7bfd75d487954a9'
PINNED_PATH_SHA='29144e8c4b8b3d3501136198c5029acbbe6821d937cc92e7aa919218ff6eb3a3'
SOURCE_GEOJSON_SHA='2a14d3068d2fc131ed411d9db187a1579f6d207d4c577bd453920213b8193ee9'
SOURCE_URL=('https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/'
            '9469f09592ced973a3448cf66b6100b741b64c0d/releaseData/gbOpen/'
            'QAT/ADM0/geoBoundaries-QAT-ADM0.geojson')
HAWAR=re.compile(r'(<path\s+data-map-context-legacy="hawar"\s+d=")([^"]+)("[^>]*/>)')


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()


def reconcile(preview: str, source: Path, resolution: str) -> str:
    if resolution!='i' or blob_sha(source.read_bytes())!=SOURCE_GIT_BLOB:
        raise ValueError('Approved Bahrain national source / GSHHG resolution changed')
    original=ET.parse(source).getroot()
    source_land=[dict(p.attrib) for p in original.iter(SVG+'path') if p.get('fill')=='url(#land)']
    candidate=ET.fromstring(preview)
    candidate_land=[dict(p.attrib) for p in candidate.iter(SVG+'path') if p.get('fill')=='url(#land)']
    if candidate.get('viewBox')!='0 0 1200 760' or len(source_land)!=2 or candidate_land!=source_land:
        raise ValueError('Approved Bahrain geometry or map canvas changed')
    matches=list(HAWAR.finditer(preview))
    if len(matches)!=1 or hashlib.sha256(matches[0].group(2).encode()).hexdigest()!=OLD_CONTEXT_SHA:
        raise ValueError('Existing reviewed GSHHG Hawar context changed')
    asset=(ROOT/'assets/images/bahrain/qatar-gbopen-2023-hawar-context.b85').read_bytes()
    if blob_sha(asset)!=PINNED_ASSET_GIT_BLOB:
        raise ValueError('Same-vintage Qatar source path asset changed')
    path=zlib.decompress(base64.b85decode(asset.strip())).decode('utf-8')
    if hashlib.sha256(path.encode()).hexdigest()!=PINNED_PATH_SHA or path.count('M ')!=1:
        raise ValueError('Same-vintage Qatar path invalid')
    result=preview[:matches[0].start(2)]+path+preview[matches[0].end(2):]
    group=re.search(r'<g id="geographic-context"[^>]*>',result)
    if group is None:raise ValueError('Expected geographic context group missing')
    note=('<desc>Hawar inset foreign Qatar land: geoBoundaries gbOpen ADM0 '
          'QAT-ADM0-15585745, 2023-12-12, OSM/Wambacher, ODbL 1.0; '
          'original QAT GeoJSON SHA-256 '+SOURCE_GEOJSON_SHA+'; '
          'source '+SOURCE_URL+'; Bahrain approved land unchanged.</desc>')
    result=result[:group.end()]+note+result[group.end():]
    changed=ET.fromstring(result)
    final_land=[dict(p.attrib) for p in changed.iter(SVG+'path') if p.get('fill')=='url(#land)']
    if final_land!=source_land or changed.get('viewBox')!='0 0 1200 760':
        raise ValueError('Hawar context operation changed approved Bahrain national geometry')
    return result
