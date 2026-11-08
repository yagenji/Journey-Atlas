"""SEO HTML snapshots must stay factual, safe, and publication-aware."""

import json
import unittest

from scripts.build_site import country_structured_data, render_country_seo_fallback


class CountrySEOTest(unittest.TestCase):
    def setUp(self):
        self.country = {
            "slug": "sample",
            "nameJa": "サンプル国",
            "nameEn": "SAMPLE",
            "hero": {
                "lead": "歩いて知る、大地の風景。",
                "location": "中央の滝",
            },
            "scenes": [
                {
                    "name": "森の滝",
                    "nameLocal": "Forest Falls",
                    "description": "川の流れと森の景色。",
                }
            ],
            "facts": [{"label": "首都", "value": "中央都市"}],
            "taste": {
                "title": "郷土料理",
                "items": [{"name": "郷土スープ", "text": "野菜のスープ。", "image": "food.webp"}],
            },
            "atlasExtras": [{"title": "人々の暮らし", "text": "古い道が残る。"}],
            "seasons": [{"months": "6〜8月", "text": "夏の風景。"}],
            "relatedCountries": [
                {"slug": "published", "nameJa": "公開国"},
                {"slug": "unpublished", "nameJa": "未公開国"},
            ],
        }

    def test_initial_html_contains_real_editorial_and_only_published_links(self):
        snapshot = render_country_seo_fallback(self.country, {"published"})
        for expected in (
            "<h1>SAMPLE</h1>",
            "サンプル国",
            "森の滝",
            "川の流れと森の景色。",
            "中央都市",
            "郷土スープ",
            "人々の暮らし",
            "6〜8月",
            'href="countries/published/"',
        ):
            self.assertIn(expected, snapshot)
        self.assertNotIn("未公開国", snapshot)
        self.assertNotIn("countries/unpublished/", snapshot)

    def test_editorial_strings_are_html_escaped(self):
        self.country["hero"]["lead"] = "<script>alert('x')</script>"
        self.country["scenes"][0]["name"] = "Rock & Sea"
        snapshot = render_country_seo_fallback(self.country, set())
        self.assertNotIn("<script>", snapshot)
        self.assertIn("&lt;script&gt;", snapshot)
        self.assertIn("Rock &amp; Sea", snapshot)

    def test_json_ld_is_valid_and_script_safe(self):
        self.country["nameJa"] = '</script><script>alert("x")</script>'
        canonical = "https://atlas.yagenji.com/countries/sample/"
        payload = country_structured_data(
            self.country,
            canonical=canonical,
            title="Sample — JOURNEY ATLAS",
            description="An interesting place",
            og_image="https://atlas.yagenji.com/hero.webp",
        )
        self.assertNotIn("</script>", payload)
        graph = json.loads(payload)["@graph"]
        self.assertEqual(graph[0]["url"], canonical)
        self.assertEqual(graph[1]["itemListElement"][0]["position"], 1)
        self.assertEqual(graph[1]["itemListElement"][1]["item"], canonical)


if __name__ == "__main__":
    unittest.main()
