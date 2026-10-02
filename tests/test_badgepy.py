# Copyright 2018 The pybadge Authors
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
"""Tests for badgepy."""

import base64
import doctest
import json
import os.path
import pathlib
import sys
import tempfile
import unittest
from unittest import mock
from xml.dom import minidom

import xmldiff.main

import badgepy
from tests import image_server

TEST_DIR = os.path.dirname(__file__)

PNG_IMAGE_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAD0lEQVQI12P4zw"
    "AD/xkYAA/+Af8iHnLUAAAAAElFTkSuQmCC"
)
PNG_IMAGE = base64.b64decode(PNG_IMAGE_B64)


class TestbadgepyBadge(unittest.TestCase):
    """Tests for badgepy.badge."""

    def setUp(self):
        super().setUp()
        self._image_server = image_server.ImageServer(PNG_IMAGE)
        self._image_server.start_server()

    def tearDown(self):
        super().tearDown()
        self._image_server.stop_server()

    def test_docs(self):
        doctest.testmod(badgepy, optionflags=doctest.ELLIPSIS)

    def test_whole_link_and_left_link(self):
        with self.assertRaises(ValueError):
            badgepy.badge(
                left_text="foo",
                right_text="bar",
                left_link="http://example.com/",
                whole_link="http://example.com/",
            )

    def test_font_family(self):
        svg = badgepy.badge(
            left_text="font",
            right_text="custom",
            font_family="Open Sans,sans-serif",
        )
        self.assertIn('font-family="Open Sans,sans-serif"', svg)

    def test_logo_width(self):
        svg = badgepy.badge(
            left_text="logo",
            right_text="wide",
            logo="data:image/png;base64," + PNG_IMAGE_B64,
            logo_width=28,
        )
        self.assertIn('width="28"', svg)

    def test_changes(self):
        with open(os.path.join(TEST_DIR, "test-badges.json"), "r") as f:
            examples = json.load(f)

        for example in examples:
            self._image_server.fix_embedded_url_reference(example)
            file_name = example.pop("file_name")
            with self.subTest(example=file_name):
                goldenpath = os.path.join(TEST_DIR, "golden-images", file_name)

                with open(goldenpath, mode="r", encoding="utf-8") as f:
                    golden_image = f.read()
                pybadge_image = badgepy.badge(**example)

                diff = xmldiff.main.diff_texts(golden_image, pybadge_image)
                if diff:
                    with tempfile.NamedTemporaryFile(
                        mode="w+t", encoding="utf-8", delete=False, suffix=".svg"
                    ) as actual:
                        actual.write(pybadge_image)

                    with tempfile.NamedTemporaryFile(
                        mode="w+t", delete=False, suffix=".html"
                    ) as html:
                        html.write(
                            """
                        <html>
                            <body>
                                <img src="file://%s"><br>
                                <img src="file://%s">
                            <body>
                        </html>"""
                            % (goldenpath, actual.name)
                        )
                    self.fail(
                        "images for %s differ:\n%s\nview with:\npython -m webbrowser %s"
                        % (file_name, diff, html.name)
                    )

    def test_quoted_colors_are_normalized(self):
        svg = badgepy.badge(
            left_text="build",
            right_text="passing",
            left_color="'grey'",
            right_color='"green"',
        )

        self.assertIn('fill="#555"', svg)
        self.assertIn('fill="#97CA00"', svg)

    def test_none_colors_use_defaults(self):
        svg = badgepy.badge(
            left_text="build",
            right_text="passing",
            left_color=None,
            right_color=None,
        )

        self.assertIn('fill="#555"', svg)
        self.assertIn('fill="#007ec6"', svg)


class TestBadgeOptions(unittest.TestCase):
    """Tests for badgepy.badge options and argument validation."""

    def test_center_image_requires_right_element(self):
        with self.assertRaisesRegex(ValueError, "without a right element"):
            badgepy.badge(
                left_text="left", center_image="image.png", center_color="red"
            )

    def test_center_image_and_center_color_go_together(self):
        with self.assertRaisesRegex(ValueError, "both a center_image and"):
            badgepy.badge(left_text="left", right_text="right", center_color="red")
        with self.assertRaisesRegex(ValueError, "both a center_image and"):
            badgepy.badge(left_text="left", right_text="right", center_image="a.png")

    def test_center_color_name_is_normalized(self):
        svg = badgepy.badge(
            left_text="left",
            right_text="right",
            center_image="image.png",
            center_color="green",
        )
        self.assertIn('fill="#97CA00"', svg)

    def test_embed_right_and_center_images(self):
        data_url = "data:image/png;base64," + PNG_IMAGE_B64
        with mock.patch.object(badgepy, "_embed_image", return_value=data_url) as embed:
            svg = badgepy.badge(
                left_text="left",
                right_text="right",
                right_image="right.png",
                center_image="center.png",
                center_color="red",
                embed_right_image=True,
                embed_center_image=True,
            )
        embed.assert_has_calls([mock.call("right.png"), mock.call("center.png")])
        self.assertEqual(svg.count('xlink:href="' + data_url + '"'), 2)

    def test_images_are_not_embedded_by_default(self):
        with mock.patch.object(badgepy, "_embed_image") as embed:
            svg = badgepy.badge(
                left_text="left",
                right_text="right",
                logo="logo.png",
                right_image="right.png",
            )
        embed.assert_not_called()
        self.assertIn('xlink:href="logo.png"', svg)
        self.assertIn('xlink:href="right.png"', svg)

    def test_custom_measurer(self):
        class FixedWidthMeasurer(badgepy.text_measurer.TextMeasurer):
            def text_width(self, text):
                return 100.0 * len(text)

        svg = badgepy.badge(
            left_text="ab", right_text="cde", measurer=FixedWidthMeasurer()
        )
        # (20 + 10) + (30 + 10) units wide.
        self.assertTrue(svg.startswith("<svg"), svg)
        self.assertIn('width="70.0"', svg)

    def test_left_text_only(self):
        svg = badgepy.badge(left_text="solo")
        texts = minidom.parseString(svg).getElementsByTagName("text")
        self.assertEqual([t.firstChild.data for t in texts], ["solo", "solo"])


class TestRemoveBlanks(unittest.TestCase):
    def test_strips_text_and_ignores_other_nodes(self):
        doc = minidom.parseString("<a>  x  <!-- note --><b> y </b></a>")
        empty = doc.createTextNode("")
        doc.documentElement.appendChild(empty)

        badgepy._remove_blanks(doc)

        a = doc.documentElement
        self.assertEqual(a.firstChild.data, "x")
        self.assertEqual(a.childNodes[1].nodeType, minidom.Node.COMMENT_NODE)
        self.assertEqual(a.childNodes[1].data, " note ")
        self.assertEqual(a.getElementsByTagName("b")[0].firstChild.data, "y")
        self.assertEqual(empty.data, "")


class TestEmbedImage(unittest.TestCase):
    """Tests for badgepy._embed_image."""

    def _serve(self, data, content_type):
        server = image_server.ImageServer(data, content_type=content_type)
        server.start_server()
        self.addCleanup(server.stop_server)
        return server.logo_url

    def test_data_url(self):
        url = "data:image/png;base64," + PNG_IMAGE_B64
        self.assertEqual(url, badgepy._embed_image(url))

    def test_http_url(self):
        url = "https://dev.w3.org/SVG/tools/svgweb/samples/svg-files/python.svg"
        self.assertRegex(badgepy._embed_image(url), r"^data:image/svg(\+xml)?;base64,")

    def test_http_png_url(self):
        url = self._serve(PNG_IMAGE, "image/png")
        self.assertEqual(
            badgepy._embed_image(url), "data:image/png;base64," + PNG_IMAGE_B64
        )

    def test_not_image_url(self):
        with self.assertRaisesRegex(ValueError, 'expected an image, got "text"'):
            badgepy._embed_image("http://www.google.com/")

    def test_http_url_without_content_type(self):
        url = self._serve(PNG_IMAGE, None)
        with self.assertRaisesRegex(ValueError, 'no "Content-Type" header'):
            badgepy._embed_image(url)

    @unittest.skipIf(sys.platform.startswith("win"), "requires Unix filesystem")
    def test_svg_file_path(self):
        image_path = os.path.abspath(
            os.path.join(TEST_DIR, "golden-images", "build-failure.svg")
        )
        self.assertRegex(
            badgepy._embed_image(image_path), r"^data:image/svg(\+xml)?;base64,"
        )

    @unittest.skipIf(sys.platform.startswith("win"), "requires Unix filesystem")
    def test_png_file_path(self):
        with tempfile.NamedTemporaryFile() as png:
            png.write(PNG_IMAGE)
            png.flush()
            self.assertEqual(
                badgepy._embed_image(png.name), "data:image/png;base64," + PNG_IMAGE_B64
            )

    @unittest.skipIf(sys.platform.startswith("win"), "requires Unix filesystem")
    def test_unknown_type_file_path(self):
        with tempfile.NamedTemporaryFile() as non_image:
            non_image.write(b"Hello")
            non_image.flush()
            with self.assertRaisesRegex(ValueError, "not able to determine file type"):
                badgepy._embed_image(non_image.name)

    @unittest.skipIf(sys.platform.startswith("win"), "requires Unix filesystem")
    def test_text_file_path(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as non_image:
            non_image.write(b"Hello")
            non_image.flush()
            with self.assertRaisesRegex(ValueError, 'expected an image, got "text"'):
                badgepy._embed_image(non_image.name)

    def test_file_url(self):
        image_path = os.path.abspath(
            os.path.join(TEST_DIR, "golden-images", "build-failure.svg")
        )

        with self.assertRaisesRegex(ValueError, 'unsupported scheme "file"'):
            badgepy._embed_image(pathlib.Path(image_path).as_uri())


SCRIPT_TEXT = "</text><script>alert(1)</script><text>"
SCRIPT_ATTRIBUTE = '" onload="alert(1)'


class TestBadgeEscaping(unittest.TestCase):
    """User supplied values must not change the structure of the SVG."""

    def assertNoInjectedMarkup(self, svg):
        elements = minidom.parseString(svg).getElementsByTagName("*")
        self.assertNotIn("script", {element.tagName for element in elements})
        for element in elements:
            self.assertFalse(element.hasAttribute("onload"), element.toxml())

    def test_text_values_are_escaped(self):
        center = {"center_image": "image.png", "center_color": "red"}
        cases = {
            "left_text": {},
            "right_text": {},
            "left_title": {},
            "right_title": {},
            "whole_title": {},
            "center_title": center,
        }
        for field, extra in cases.items():
            with self.subTest(field=field):
                kwargs = {"left_text": "label", "right_text": "message", **extra}
                kwargs[field] = SCRIPT_TEXT
                svg = badgepy.badge(**kwargs)

                self.assertNoInjectedMarkup(svg)
                texts = [
                    node.data
                    for element in minidom.parseString(svg).getElementsByTagName("*")
                    for node in element.childNodes
                    if node.nodeType == node.TEXT_NODE
                ]
                self.assertIn(SCRIPT_TEXT, texts)

    def test_attribute_values_are_escaped(self):
        center = {"center_image": "image.png", "center_color": "red"}
        cases = {
            "left_color": {},
            "right_color": {},
            "font_family": {},
            "id_suffix": {},
            "logo": {},
            "right_image": {},
            "left_link": {},
            "right_link": {},
            "whole_link": {},
            "center_image": {"center_color": "red"},
            "center_color": {"center_image": "image.png"},
            "center_link": center,
        }
        for field, extra in cases.items():
            with self.subTest(field=field):
                kwargs = {"left_text": "label", "right_text": "message", **extra}
                kwargs[field] = SCRIPT_ATTRIBUTE
                svg = badgepy.badge(**kwargs)

                self.assertNoInjectedMarkup(svg)
                values = [
                    value
                    for element in minidom.parseString(svg).getElementsByTagName("*")
                    for _, value in element.attributes.items()
                ]
                self.assertTrue(
                    any('onload="alert(1)' in value for value in values), values
                )


class TestLinks(unittest.TestCase):
    LINKS = [
        "https://example.com/",
        "http://example.com/?next=/docs",
        "mailto:badges@example.com",
        "/docs/intro",
        "#status",
        "relative.html",
    ]

    def test_whole_link_is_rendered_on_both_sides(self):
        for link in self.LINKS:
            with self.subTest(link=link):
                svg = badgepy.badge(left_text="label", right_text="ok", whole_link=link)
                anchors = minidom.parseString(svg).getElementsByTagName("a")
                self.assertEqual(
                    [anchor.getAttribute("xlink:href") for anchor in anchors],
                    [link, link],
                )


if __name__ == "__main__":
    unittest.main()
