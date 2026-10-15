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
"""Tests for PilMeasurer."""

import os
import tempfile
import unittest

import badgepy
from badgepy import pil_text_measurer
from tests import fonts


class TestPilMeasurer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls.font_path = os.path.join(cls._tmpdir.name, "test-font.ttf")
        fonts.build_test_font(cls.font_path)

    @classmethod
    def tearDownClass(cls):
        cls._tmpdir.cleanup()

    def setUp(self):
        self.measurer = pil_text_measurer.PilMeasurer(self.font_path)

    def test_text_width_follows_glyph_widths(self):
        # Text is rendered at 110px and glyphs are 600, 400 and 700 units wide
        # in a 1000 units per em font.
        self.assertAlmostEqual(self.measurer.text_width("A"), 66, delta=1)
        self.assertAlmostEqual(self.measurer.text_width("a"), 44, delta=1)
        self.assertAlmostEqual(self.measurer.text_width("Ж"), 77, delta=1)

    def test_text_width_of_strings(self):
        width = self.measurer.text_width
        self.assertEqual(width(""), 0)
        self.assertAlmostEqual(width("Aa"), width("A") + width("a"), delta=1)
        self.assertAlmostEqual(width("AAA"), 3 * width("A"), delta=1)

    def test_missing_font_file(self):
        with self.assertRaises(OSError):
            pil_text_measurer.PilMeasurer(
                os.path.join(self._tmpdir.name, "missing.ttf")
            )

    def test_badge_uses_measured_widths(self):
        svg = badgepy.badge(left_text="Aa", right_text="Ж", measurer=self.measurer)

        width = self.measurer.text_width
        expected = (width("Aa") / 10.0 + 10) + (width("Ж") / 10.0 + 10)
        self.assertIn('width="{}"'.format(expected), svg)


class TestTextMeasurer(unittest.TestCase):
    def test_text_width_is_abstract(self):
        with self.assertRaises(NotImplementedError):
            badgepy.text_measurer.TextMeasurer().text_width("text")


if __name__ == "__main__":
    unittest.main()
