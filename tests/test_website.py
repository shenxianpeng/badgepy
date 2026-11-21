# Copyright 2026 The badgepy Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Keep the playground page in website/ in step with the library.

The page runs badgepy in the visitor's browser, so nothing here loads it in
one. These tests cover what the page states statically: the badge shown before
Python has loaded, the choices its form offers, and its examples.
"""

import html.parser
import json
import os
import os.path
import re
import unittest

import badgepy

WEBSITE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "website")


class _Page(html.parser.HTMLParser):
    """Collects the form's initial values, its choices and the examples."""

    def __init__(self):
        super().__init__()
        self.inputs = {}
        self.options = {}
        self.examples = None
        self._options_of = None
        self._in_examples = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input":
            self.inputs[attrs["id"]] = attrs.get("value", "")
        elif tag in ("select", "datalist"):
            self._options_of = attrs["id"]
            self.options[self._options_of] = []
        elif tag == "option":
            self.options[self._options_of].append(attrs["value"])
        elif tag == "script" and attrs.get("id") == "examples":
            self._in_examples = True

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_examples = False

    def handle_data(self, data):
        if self._in_examples:
            self.examples = json.loads(data)


class TestWebsite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = _Page()
        with open(os.path.join(WEBSITE_DIR, "index.html"), encoding="utf-8") as f:
            cls.page.feed(f.read())

    def test_static_preview_is_what_the_form_renders(self):
        """default.svg is shown until Python has loaded, next to a form that
        already holds its initial values, so the two must agree."""
        args = {name: value for name, value in self.page.inputs.items() if value}
        args["style"] = self.page.options["style"][0]
        with open(os.path.join(WEBSITE_DIR, "default.svg"), encoding="utf-8") as f:
            self.assertEqual(f.read(), badgepy.badge(**args))

    def test_style_choices_are_the_supported_styles(self):
        self.assertEqual(tuple(self.page.options["style"]), badgepy.STYLES)

    def test_suggested_colors_are_named_colors(self):
        for color in self.page.options["colors"]:
            with self.subTest(color=color):
                self.assertIn(color, badgepy._NAME_TO_COLOR)

    def test_examples_render_and_fit_the_form(self):
        fields = set(self.page.inputs) | {"style"}
        self.assertTrue(self.page.examples)
        for example in self.page.examples:
            with self.subTest(example=example):
                self.assertLessEqual(set(example), fields)
                self.assertTrue(badgepy.badge(**example).startswith("<svg"))


SITE_URL = "https://shenxianpeng.dev/badgepy/"


class _Head(html.parser.HTMLParser):
    """Collects a page's canonical URL, its og:image and its relative links."""

    def __init__(self):
        super().__init__()
        self.canonical = None
        self.og_image = None
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical = attrs["href"]
        elif tag == "meta" and attrs.get("property") == "og:image":
            self.og_image = attrs["content"]
        elif tag == "a" and "://" not in attrs.get("href", "://"):
            self.links.append(attrs["href"])


class TestSiteFiles(unittest.TestCase):
    """The pages, the sitemap and llms.txt name each other by URL; a renamed or
    deleted file would leave a dead link that nothing else notices."""

    def _local_file(self, url):
        self.assertTrue(url.startswith(SITE_URL), url)
        name = url[len(SITE_URL) :].split("#")[0] or "index.html"
        path = os.path.join(WEBSITE_DIR, name)
        self.assertTrue(os.path.isfile(path), f"{url} has no file {name}")
        return name

    def test_sitemap_lists_every_page_at_its_canonical_url(self):
        with open(os.path.join(WEBSITE_DIR, "sitemap.xml"), encoding="utf-8") as f:
            locs = re.findall(r"<loc>(.*?)</loc>", f.read())
        pages = sorted(n for n in os.listdir(WEBSITE_DIR) if n.endswith(".html"))
        self.assertEqual(sorted(self._local_file(loc) for loc in locs), pages)
        for name in pages:
            with self.subTest(page=name):
                head = _Head()
                with open(os.path.join(WEBSITE_DIR, name), encoding="utf-8") as f:
                    head.feed(f.read())
                self.assertIn(head.canonical, locs)
                self.assertEqual(self._local_file(head.canonical), name)
                self._local_file(head.og_image)
                for link in head.links:
                    # "./" is the directory's index page; "#section" is this page.
                    target = link.split("#")[0]
                    if target in ("", "./"):
                        target = "index.html" if target else name
                    self.assertTrue(
                        os.path.isfile(os.path.join(WEBSITE_DIR, target)), link
                    )

    def test_llms_txt_links_to_site_pages_that_exist(self):
        with open(os.path.join(WEBSITE_DIR, "llms.txt"), encoding="utf-8") as f:
            urls = re.findall(r"\]\((https?://[^)]+)\)", f.read())
        site_urls = [url for url in urls if url.startswith(SITE_URL)]
        self.assertTrue(site_urls)
        for url in site_urls:
            with self.subTest(url=url):
                self._local_file(url)


if __name__ == "__main__":
    unittest.main()
