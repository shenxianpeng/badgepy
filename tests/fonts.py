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
"""Build a tiny TrueType font for tests that need a real font file."""

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

# Characters supported by the test font, mapped to (glyph name, advance width
# in font units). Every glyph is a filled rectangle as wide as its advance.
CHARACTERS = {
    "A": ("A", 600),
    "V": ("V", 600),
    "a": ("a", 400),
    "Ж": ("Zhe", 700),  # CYRILLIC CAPITAL LETTER ZHE, not in cp1252.
}

# A character that is only mapped by the non-Unicode (Mac Roman) cmap.
MAC_ONLY_CODE = 0xC0


def _rectangle(width):
    pen = TTGlyphPen(None)
    pen.moveTo((0, 0))
    pen.lineTo((0, 700))
    pen.lineTo((width, 700))
    pen.lineTo((width, 0))
    pen.closePath()
    return pen.glyph()


def build_test_font(path):
    """Write a TrueType font supporting CHARACTERS to `path`."""
    widths = {".notdef": 500}
    widths.update(dict(CHARACTERS.values()))

    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder(list(widths))
    builder.setupCharacterMap({ord(c): name for c, (name, _) in CHARACTERS.items()})
    builder.setupGlyf({name: _rectangle(width) for name, width in widths.items()})
    builder.setupHorizontalMetrics({name: (width, 0) for name, width in widths.items()})
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable({"familyName": "Badgepy Test", "styleName": "Regular"})
    builder.setupOS2(sTypoAscender=800, usWinAscent=800, usWinDescent=200)
    builder.setupPost()

    mac_roman = CmapSubtable.newSubtable(0)
    mac_roman.platformID = 1
    mac_roman.platEncID = 0
    mac_roman.language = 0
    mac_roman.cmap = {MAC_ONLY_CODE: "A"}
    builder.font["cmap"].tables.append(mac_roman)

    builder.save(path)
