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
"""Measure the width, in pixels, of a string rendered using DejaVu Sans 110pt.

Uses a PIL/Pillow to determine the string length.
"""

import unicodedata

from PIL import ImageFont

from badgepy import text_measurer

# The width of one em at the 110pt text is measured at.
_EM_WIDTH = 110.0

# A noncharacter that no font maps, so it always renders as the font's .notdef
# glyph, the box drawn for characters the font lacks.
_UNMAPPED = "\uffff"


class PilMeasurer(text_measurer.TextMeasurer):
    """Measures the width of a string using PIL/Pillow."""

    def __init__(self, deja_vu_sans_path: str):
        """Initializer for PilMeasurer.

        Args:
            deja_vu_sans_path: The path to the DejaVu Sans TrueType (.ttf) font
                file.
        """
        self._font = ImageFont.truetype(deja_vu_sans_path, 110)
        # Without text shaping each character renders as its own glyph, or as
        # .notdef when the font does not map it.
        self._unshaped_font = ImageFont.truetype(
            deja_vu_sans_path, 110, layout_engine=ImageFont.Layout.BASIC
        )
        self._notdef_mask = self._mask(_UNMAPPED)
        self._notdef_width = self._unshaped_font.getlength(_UNMAPPED)
        self._is_missing_wide_cache: dict[str, bool] = {}

    def text_width(self, text: str) -> float:
        """Returns the width, in pixels, of a string in DejaVu Sans 110pt."""
        bbox = self._font.getbbox(text)
        width = bbox[2] - bbox[0]  # Calculate the width from the bounding box
        # The font measures a character it lacks as a .notdef box, but a
        # browser draws it with a fallback font. Wide and fullwidth characters
        # (CJK ideographs, kana, Hangul, fullwidth forms) are one em wide
        # there, so swap each such box for an em.
        for c in text:
            if self._is_missing_wide(c):
                width += _EM_WIDTH - self._notdef_width
        return width

    def _mask(self, c: str) -> tuple[tuple[int, int], bytes]:
        mask = self._unshaped_font.getmask(c)
        return mask.size, bytes(mask)

    def _is_missing_wide(self, c: str) -> bool:
        """Whether `c` is wide or fullwidth and the font has no glyph for it.

        Pillow does not expose the font's character map, so a character
        counts as missing when it renders exactly like .notdef. For DejaVu
        Sans this agrees with the character map on every wide and fullwidth
        code point.
        """
        if unicodedata.east_asian_width(c) not in ("W", "F"):
            return False
        if c not in self._is_missing_wide_cache:
            self._is_missing_wide_cache[c] = self._mask(c) == self._notdef_mask
        return self._is_missing_wide_cache[c]
