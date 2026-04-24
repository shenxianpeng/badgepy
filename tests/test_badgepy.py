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


class TestEmbedImage(unittest.TestCase):
    """Tests for badgepy._embed_image."""

    def test_data_url(self):
        url = "data:image/png;base64," + PNG_IMAGE_B64
        self.assertEqual(url, badgepy._embed_image(url))

    def test_http_url(self):
        url = "https://dev.w3.org/SVG/tools/svgweb/samples/svg-files/python.svg"
        self.assertRegex(badgepy._embed_image(url), r"^data:image/svg(\+xml)?;base64,")

    def test_not_image_url(self):
        with self.assertRaisesRegex(ValueError, 'expected an image, got "text"'):
            badgepy._embed_image("http://www.google.com/")

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


if __name__ == "__main__":
    unittest.main()
