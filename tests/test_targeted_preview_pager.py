import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_country_preview_targeted as preview


class PagerPreviewTests(unittest.TestCase):
    def test_neighbors_follow_chapters_wrap_and_exclude_unpublished(self):
        rows = [
            {"slug": slug, "iso2": iso, "nameEn": name, "atlasPublished": published,
             "href": f"countries/{slug}/"}
            for slug, iso, name, published in [
                ("zulu", "ZZ", "Zulu", True), ("eclair", "EC", "Éclair", True),
                ("echo", "EH", "Echo", True), ("alpha", "AA", "Alpha", True),
                ("hidden", "XX", "Hidden", False),
            ]
        ]
        taxonomy = {"regions": [{"subregions": [{"iso2": ["ZZ", "EH", "EC", "XX"]}]},
                                {"iso2": ["AA"], "subregions": []}]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "data/atlas-destinations.json").write_text(json.dumps({"destinations": rows}))
            (root / "data/region-taxonomy.json").write_text(json.dumps(taxonomy))
            with patch.object(preview, "ROOT", root):
                self.assertEqual(preview.include_pager_neighbors(["echo"]), ["echo", "alpha", "eclair"])
                self.assertEqual(preview.include_pager_neighbors(["alpha"]), ["alpha", "zulu", "echo"])
                self.assertEqual(preview.include_pager_neighbors(["hidden"]), ["hidden"])
                expanded = preview.include_pager_neighbors(["echo", "eclair"])
                self.assertEqual(len(expanded), len(set(expanded)))


if __name__ == "__main__":
    unittest.main()
