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
"""Tests for badgepy.precalculate_text."""

import contextlib
import io
import json
import lzma
import os
import statistics
import sys
import tempfile
import unittest
from unittest import mock

from badgepy import pil_text_measurer
from badgepy import precalculate_text
from badgepy import precalculated_text_measurer
from badgepy import text_measurer
from tests import fonts

CP1252_CHARACTERS = {"A", "V", "a"}


class FakeMeasurer(text_measurer.TextMeasurer):
    def __init__(self, widths):
        self._widths = widths

    def text_width(self, text):
        return self._widths[text]


class FontTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls.tmpdir = cls._tmpdir.name
        cls.font_path = os.path.join(cls.tmpdir, "test-font.ttf")
        fonts.build_test_font(cls.font_path)

    @classmethod
    def tearDownClass(cls):
        cls._tmpdir.cleanup()


class TestCharacterSelection(FontTestCase):
    def test_generate_supported_characters(self):
        characters = list(
            precalculate_text.generate_supported_characters(self.font_path)
        )
        self.assertEqual(set(characters), set(fonts.CHARACTERS))
        # The Mac Roman cmap subtable is not a Unicode mapping.
        self.assertNotIn(chr(fonts.MAC_ONLY_CODE), characters)

    def test_generate_encodeable_characters(self):
        generate = precalculate_text.generate_encodeable_characters
        text = "aЖ€"  # "a", CYRILLIC ZHE, EURO SIGN

        self.assertEqual(list(generate(text, ["cp1252"])), ["a", "€"])
        self.assertEqual(list(generate(text, ["iso-8859-5"])), ["a", "Ж"])
        self.assertEqual(set(generate(text, ["cp1252", "iso-8859-5"])), set(text))
        self.assertEqual(list(generate(text, [])), [])


class TestMeasurements(unittest.TestCase):
    def test_calculate_character_to_length_mapping(self):
        measurer = FakeMeasurer({"a": 10.5, "b": 20})
        self.assertEqual(
            precalculate_text.calculate_character_to_length_mapping(measurer, "ab"),
            {"a": 10.5, "b": 20},
        )

    def test_calculate_pair_to_kern_mapping(self):
        measurer = FakeMeasurer(
            {
                "AV": 109.12345,  # Drawn closer together: positive, rounded.
                "VA": 119.97,  # Within the 0.05 tolerance: dropped.
                "Aa": 100,
                "aA": 100,
                "Va": 100.5,  # Drawn further apart: negative.
                "aV": 100.04,  # Within the 0.05 tolerance: dropped.
            }
        )
        pairs = precalculate_text.calculate_pair_to_kern_mapping(
            measurer, {"A": 60, "V": 60, "a": 40}, "AVa"
        )
        self.assertEqual(pairs, {"AV": 10.877, "Va": -0.5})


class TestWriteJson(FontTestCase):
    def test_write_json(self):
        measurer = pil_text_measurer.PilMeasurer(self.font_path)
        output = io.StringIO()

        precalculate_text.write_json(output, self.font_path, measurer, ["cp1252"])

        data = json.loads(output.getvalue())
        lengths = {c: measurer.text_width(c) for c in fonts.CHARACTERS}
        self.assertEqual(data["character-lengths"], lengths)
        self.assertEqual(
            data["mean-character-length"], statistics.mean(lengths.values())
        )
        self.assertEqual(set(data["kerning-characters"]), CP1252_CHARACTERS)
        for pair in data["kerning-pairs"]:
            self.assertEqual(len(pair), 2)
            self.assertLessEqual(set(pair), CP1252_CHARACTERS)

        loaded = precalculated_text_measurer.PrecalculatedTextMeasurer.from_json(
            io.StringIO(output.getvalue())
        )
        self.assertEqual(loaded.text_width("Ж"), lengths["Ж"])


class TestMain(FontTestCase):
    def _main(self, *args):
        argv = ["precalculate_text", "--deja-vu-sans-path", self.font_path, *args]
        with mock.patch.object(sys, "argv", argv):
            precalculate_text.main()

    def test_writes_json_file(self):
        output = os.path.join(self.tmpdir, "widths.json")
        self._main("--output-json-file", output)

        with open(output, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(set(data["character-lengths"]), set(fonts.CHARACTERS))
        self.assertEqual(set(data["kerning-characters"]), CP1252_CHARACTERS)

    def test_writes_xz_file_with_extra_encodings(self):
        output = os.path.join(self.tmpdir, "widths.json.xz")
        self._main(
            "--output-json-file", output, "--kerning-pair-encodings", "iso-8859-5"
        )

        with lzma.open(output, "rt", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(set(data["character-lengths"]), set(fonts.CHARACTERS))
        self.assertEqual(set(data["kerning-characters"]), set(fonts.CHARACTERS))

    def test_font_path_is_required(self):
        with (
            mock.patch.object(sys, "argv", ["precalculate_text"]),
            contextlib.redirect_stderr(io.StringIO()) as stderr,
        ):
            with self.assertRaises(SystemExit) as raised:
                precalculate_text.main()
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("--deja-vu-sans-path", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
