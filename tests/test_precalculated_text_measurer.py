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
"""Tests for PrecalculatedTextMeasurer."""

import io
import json
import lzma
import unittest
from unittest import mock

from badgepy import precalculated_text_measurer

PrecalculatedTextMeasurer = precalculated_text_measurer.PrecalculatedTextMeasurer

WIDTHS = {
    "mean-character-length": 5,
    "character-lengths": {"a": 3},
    "kerning-characters": "ab",
    "kerning-pairs": {"ab": 1},
}


class TestPrecalculatedTextMeasurer(unittest.TestCase):
    def test_some_known_widths(self):
        measurer = precalculated_text_measurer.PrecalculatedTextMeasurer(
            default_character_width=5.1,
            char_to_width={"H": 1.2, "l": 1.3},
            pair_to_kern={},
        )

        text_width = measurer.text_width("Hello")
        self.assertAlmostEqual(text_width, 1.2 + 5.1 + 1.3 + 1.3 + 5.1)

    def test_kern_in_middle(self):
        measurer = precalculated_text_measurer.PrecalculatedTextMeasurer(
            default_character_width=5,
            char_to_width={},
            pair_to_kern={"el": 3.3, "ll": 4.4, "no": 5.5},
        )

        text_width = measurer.text_width("Hello")
        self.assertAlmostEqual(text_width, 5 * 5 - 3.3 - 4.4)

    def test_kern_at_start(self):
        measurer = precalculated_text_measurer.PrecalculatedTextMeasurer(
            default_character_width=5,
            char_to_width={},
            pair_to_kern={"He": 3.3, "no": 4.4},
        )

        text_width = measurer.text_width("Hello")
        self.assertAlmostEqual(text_width, 5 * 5 - 3.3)

    def test_kern_at_end(self):
        measurer = precalculated_text_measurer.PrecalculatedTextMeasurer(
            default_character_width=5,
            char_to_width={},
            pair_to_kern={"lo": 3.3, "no": 4.4},
        )

        text_width = measurer.text_width("Hello")
        self.assertAlmostEqual(text_width, 5 * 5 - 3.3)

    def test_default_usable(self):
        measurer = precalculated_text_measurer.PrecalculatedTextMeasurer.default()
        measurer.text_width("This is a long string of text")

    def test_empty_text(self):
        measurer = PrecalculatedTextMeasurer(5, {}, {})
        self.assertEqual(measurer.text_width(""), 0)

    def test_from_json(self):
        measurer = PrecalculatedTextMeasurer.from_json(io.StringIO(json.dumps(WIDTHS)))
        # "a" is 3 wide, "b" uses the mean width of 5 and "ab" kerns by 1.
        self.assertEqual(measurer.text_width("ab"), 7)


class TestMissingCharacters(unittest.TestCase):
    """Characters the tables lack are drawn by a fallback font in the browser."""

    def setUp(self):
        self.measurer = PrecalculatedTextMeasurer(
            default_character_width=5, char_to_width={"a": 3, "中": 7}, pair_to_kern={}
        )

    def test_wide_and_fullwidth_characters_are_one_em(self):
        # Chinese, Japanese kana, Korean Hangul, and a fullwidth Latin letter.
        for c in ("构", "テ", "빌", "Ａ"):
            with self.subTest(character=c):
                self.assertEqual(self.measurer.text_width(c), 110)

    def test_other_missing_characters_use_the_mean_width(self):
        # Not wide: Thai, and a halfwidth katakana.
        for c in ("ก", "ｱ"):
            with self.subTest(character=c):
                self.assertEqual(self.measurer.text_width(c), 5)

    def test_a_tabled_width_wins_over_the_em(self):
        self.assertEqual(self.measurer.text_width("中"), 7)

    def test_mixed_text_adds_up(self):
        self.assertEqual(self.measurer.text_width("a构ก"), 3 + 110 + 5)


class TestDefaultMeasurerWidths(unittest.TestCase):
    """The packaged tables, against widths measured in Chromium.

    The text was rendered in a <span> at 110px with the badge template's font
    stack (DejaVu Sans,Verdana,Geneva,sans-serif); CJK fell back to
    WenQuanYi Zen Hei.
    """

    RENDERED = {
        "build": 271,
        "passing": 422,
        "构建": 220,
        "构建 v2.0": 495,
        "빌드": 220,
        "ＡＢＣ": 330,
    }

    def test_within_two_percent_of_the_rendered_width(self):
        measurer = PrecalculatedTextMeasurer.default()
        for text, rendered in self.RENDERED.items():
            with self.subTest(text=text):
                self.assertAlmostEqual(
                    measurer.text_width(text), rendered, delta=rendered * 0.02
                )


class TestDefaultMeasurer(unittest.TestCase):
    """Tests for loading the packaged widths in PrecalculatedTextMeasurer.default."""

    def setUp(self):
        cache = mock.patch.object(PrecalculatedTextMeasurer, "_default_cache", None)
        cache.start()
        self.addCleanup(cache.stop)
        # Package resources served by the patched importlib.resources functions.
        self.resources = {}

    def _default(self):
        def is_resource(package, name):
            self.assertEqual(package, "badgepy")
            return name in self.resources

        def open_binary(package, name):
            return io.BytesIO(self.resources[name])

        def open_text(package, name, encoding):
            return io.StringIO(self.resources[name].decode(encoding))

        resources = precalculated_text_measurer.importlib.resources
        with (
            mock.patch.object(resources, "is_resource", side_effect=is_resource),
            mock.patch.object(resources, "open_binary", side_effect=open_binary),
            mock.patch.object(resources, "open_text", side_effect=open_text),
        ):
            return PrecalculatedTextMeasurer.default()

    def test_prefers_compressed_widths(self):
        self.resources["default-widths.json.xz"] = lzma.compress(
            json.dumps(WIDTHS).encode()
        )
        self.resources["default-widths.json"] = b"not json"

        self.assertEqual(self._default().text_width("ab"), 7)

    def test_uncompressed_widths(self):
        self.resources["default-widths.json"] = json.dumps(WIDTHS).encode()

        self.assertEqual(self._default().text_width("ab"), 7)

    def test_result_is_cached(self):
        self.resources["default-widths.json"] = json.dumps(WIDTHS).encode()
        measurer = self._default()
        self.resources.clear()

        self.assertIs(self._default(), measurer)

    def test_missing_widths(self):
        with self.assertRaisesRegex(ValueError, "could not load default-widths.json"):
            self._default()

    def test_invalid_widths(self):
        self.resources["default-widths.json"] = b"{"
        with self.assertRaisesRegex(ValueError, "Error loading default-widths.json"):
            self._default()


if __name__ == "__main__":
    unittest.main()
