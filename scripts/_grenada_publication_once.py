#!/usr/bin/env python3
"""One-time user-authorized Grenada publication handoff, run on an isolated ops branch."""
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from PIL import Image

ROOT = Path.cwd()
SLUG = "grenada"
URL = "https://atlas.yagenji.com/countries/grenada/"
STATE = ROOT / "ops/country-production/grenada.json"
COUNTRY = ROOT / "data/countries/grenada.json"
REGISTRY = ROOT / "data/atlas-destinations.json"
STATUS = ROOT / "data/country-renewal-status.json"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def write(path, data, compact=False):
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":") if compact else None,
                               indent=None if compact else 2) + "\n", encoding="utf-8")

def run(*args):
    subprocess.run(args, check=True)

run("git", "fetch", "--no-tags", "origin", "+refs/heads/main:refs/remotes/origin/main")
run("git", "merge-base", "--is-ancestor", "origin/main", "HEAD")
state, country, registry = read(STATE), read(COUNTRY), read(REGISTRY)
assert state.get("slug") == SLUG and country.get("slug") == SLUG
assert country.get("publicationPipelineVersion") == 2
assert state.get("phase") == "REVIEW" and state.get("stateRevision") == 15
assert state.get("contentRef") == "main" and state.get("stateRef") == "main"
assert state.get("finalApproval", {}).get("state") == "PENDING"
assert state.get("publication", {}).get("atlasPublished") is False
assert state.get("qa", {}).get("state") == "PASS"
review = state.get("reviewDeployment", {})
assert (review.get("state"), review.get("url"), review.get("productionVerification")) == ("DONE", URL, "LIVE_BROWSER_QA_PASS")
assert review.get("verifiedAt") and review.get("verificationBasis")
assert state.get("assetHandoff", {}).get("verifiedRasterCount") == 13
assert state.get("sceneBatchReview", {}).get("approval") == "APPROVED"
assert state.get("tasteBatchReview", {}).get("approval") == "APPROVED"
rows = [r for r in registry.get("destinations", []) if r.get("slug") == SLUG]
assert len(rows) == 1 and rows[0].get("atlasPublished") is False
assets = [state["hero"]["asset"]] + [x["asset"] for x in state["scenes"]] + [x["asset"] for x in state["taste"]]
assert len(state["scenes"]) == 8 and len(state["taste"]) == 4 and len(assets) == 13
assert all(x.get("state") == "APPROVED" for x in [state["hero"], *state["scenes"], *state["taste"]])
country_assets = [country["hero"]["image"]] + [x["image"] for x in country["scenes"]] + [x["image"] for x in country["taste"]["items"]]
assert assets == country_assets, "Approved State / Country image paths mismatch"
assert len(set(assets)) == 13
hashes = set()
for rel in assets:
    p = ROOT / rel
    assert p.is_file() and p.stat().st_size > 4096, rel
    with Image.open(p) as im:
        assert im.format == "WEBP" and im.width >= 1000 and im.height >= 700, rel
        im.load()
    hashes.add(hashlib.sha256(p.read_bytes()).hexdigest())
assert len(hashes) == 13, "duplicate image bytes"
svg = ROOT / country["map"]["svg"]
assert svg.is_file() and ET.parse(svg).getroot().get("viewBox") == "0 0 1200 760"
print("Grenada 13 approved images full-decode, unique bytes, source paths and 1200x760 Map: PASS")

stamp = datetime.now(timezone(timedelta(hours=9))).replace(microsecond=0).isoformat()
state["finalApproval"] = {
    "state": "APPROVED",
    "approvedAt": stamp,
    "basis": "User requested QA and publication of Grenada in this conversation on 2026-09-19; verified canonical unpublished Desktop/Tablet/Mobile QA passed before approval.",
}
state["stateRevision"] += 1
state["updatedAt"] = stamp
write(STATE, state)
run("python3", "scripts/publication_pipeline_v2.py", "assert-publish-ready", SLUG)
run("python3", "scripts/publication_pipeline_v2.py", "finalize", SLUG)
state = read(STATE)
assert state["publication"]["atlasPublished"] is True
assert state["reviewDeployment"]["prePublicationReviewVerification"] == "LIVE_BROWSER_QA_PASS"
assert read(REGISTRY)["destinations"][[r.get("slug") for r in read(REGISTRY)["destinations"]].index(SLUG)]["atlasPublished"] is True

status = read(STATUS)
rows = status.setdefault("countries", [])
row = next((r for r in rows if r.get("slug") == SLUG), None)
base = {"slug":SLUG,"nameJa":country.get("nameJa") or "グレナダ","wave":9,"published":True,
        "auditState":"AUDITED","renewalClass":"UNCLASSIFIED","content":"DONE","visual":"DONE",
        "map":"DONE","sources":"DONE","qa":"PASS","production":"CI_GATED",
        "hardImageGate":True,"automatedAudit":"DONE",
        "notes":["Publication Pipeline v2; canonical noindex Desktop/Tablet/Mobile Browser QA verified before explicit user publication approval; live verification after merge required."]}
if row is None:
    rows.append(base)
else:
    row.update(base)
status["updatedAt"] = stamp[:10]
write(STATUS, status, compact=True)
run("python3", "scripts/validate_production_state_routed.py")
run("python3", "scripts/audit_published_countries.py")
run("python3", "scripts/validate_country.py", "--strict", str(COUNTRY.relative_to(ROOT)))
changed = subprocess.check_output(["git", "diff", "--name-only"], text=True).splitlines()
expected = {"ops/country-production/grenada.json", "data/atlas-destinations.json", "data/country-renewal-status.json"}
assert set(changed) == expected, f"unexpected changes: {changed}"
run("git", "config", "user.name", "github-actions[bot]")
run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
run("git", "add", *sorted(expected))
run("git", "commit", "-m", "Stage explicitly approved Grenada publication on latest main")
run("git", "push", "origin", "HEAD:country/grenada-renewal")
print("Grenada publication PR content staged; production remains unmodified until checked PR merge and live verification")
