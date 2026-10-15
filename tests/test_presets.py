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
"""Tests for badgepy.presets."""

import doctest
import unittest

from badgepy import presets
from badgepy.presets import (
    build_badge,
    coverage_badge,
    version_badge,
    license_badge,
    custom_badge,
    progress_badge,
    _color_for_coverage,
)


class TestDocs(unittest.TestCase):
    def test_docs(self):
        failed, attempted = doctest.testmod(presets, optionflags=doctest.ELLIPSIS)
        self.assertGreater(attempted, 0)
        self.assertEqual(failed, 0)


class TestBuildBadge(unittest.TestCase):
    def test_status_colors(self):
        cases = {
            "passing": "#4c1",
            "PASSING": "#4c1",
            "failing": "#e05d44",
            "error": "#e05d44",
            "pending": "#dfb317",
            "cancelled": "#9f9f9f",
            "weird": "#9f9f9f",
        }
        for status, color in cases.items():
            with self.subTest(status=status):
                svg = build_badge(status)
                self.assertIn(">%s<" % status, svg)
                self.assertIn('fill="%s"' % color, svg)

    def test_passing(self):
        svg = build_badge("passing")
        self.assertIn("passing", svg)
        self.assertIn("<svg", svg)

    def test_failing(self):
        svg = build_badge("failing")
        self.assertIn("failing", svg)

    def test_custom_label(self):
        svg = build_badge("passing", label="ci")
        self.assertIn("ci", svg)

    def test_unknown_status(self):
        svg = build_badge("weird")
        self.assertIn("weird", svg)


class TestCoverageBadge(unittest.TestCase):
    def test_high_coverage(self):
        svg = coverage_badge(95.0)
        self.assertIn("95%", svg)

    def test_low_coverage(self):
        svg = coverage_badge(30.0)
        self.assertIn("30%", svg)

    def test_decimal_coverage(self):
        svg = coverage_badge(85.3)
        self.assertIn("85.3%", svg)

    def test_integer_coverage(self):
        svg = coverage_badge(80.0)
        self.assertIn("80%", svg)

    def test_custom_thresholds_and_label(self):
        thresholds = [(50, "blue"), (10, "orange")]
        svg = coverage_badge(55, label="lines", thresholds=thresholds)
        self.assertIn(">lines<", svg)
        self.assertIn('fill="#007ec6"', svg)
        # Below every custom threshold falls back to red.
        self.assertIn('fill="#e05d44"', coverage_badge(5, thresholds=thresholds))


class TestProgressBadge(unittest.TestCase):
    def test_percentage(self):
        svg = progress_badge(75)
        self.assertIn("75%", svg)
        self.assertIn("progress", svg)

    def test_fraction_percentage(self):
        svg = progress_badge(0.5)
        self.assertIn("50%", svg)

    def test_numerator_denominator(self):
        svg = progress_badge(numerator=3, denominator=4)
        self.assertIn("75%", svg)

    def test_message_override(self):
        svg = progress_badge(75, message="documented")
        self.assertIn("documented", svg)

    def test_requires_value(self):
        with self.assertRaises(ValueError):
            progress_badge()

    def test_rejects_mixed_percentage_and_fraction(self):
        with self.assertRaises(ValueError):
            progress_badge(75, numerator=3, denominator=4)

    def test_rejects_zero_denominator(self):
        with self.assertRaises(ValueError):
            progress_badge(numerator=3, denominator=0)

    def test_rejects_out_of_range_percentage(self):
        with self.assertRaises(ValueError):
            progress_badge(101)

    def test_rejects_negative_percentage(self):
        with self.assertRaises(ValueError):
            progress_badge(-1)
        with self.assertRaises(ValueError):
            progress_badge(numerator=-1, denominator=4)

    def test_rejects_only_numerator_or_denominator(self):
        with self.assertRaises(ValueError):
            progress_badge(numerator=3)
        with self.assertRaises(ValueError):
            progress_badge(denominator=3)
        with self.assertRaises(ValueError):
            progress_badge(0.5, denominator=3)

    def test_boundaries_and_rounding(self):
        self.assertIn(">0%<", progress_badge(0))
        self.assertIn(">100%<", progress_badge(1))
        self.assertIn(">100%<", progress_badge(100))
        self.assertIn(">33.3%<", progress_badge(numerator=1, denominator=3))

    def test_custom_label_and_thresholds(self):
        svg = progress_badge(30, label="docs", thresholds=[(25, "blue")])
        self.assertIn(">docs<", svg)
        self.assertIn('fill="#007ec6"', svg)


class TestColorForCoverage(unittest.TestCase):
    def test_thresholds(self):
        self.assertEqual(_color_for_coverage(95), "brightgreen")
        self.assertEqual(_color_for_coverage(85), "green")
        self.assertEqual(_color_for_coverage(75), "yellowgreen")
        self.assertEqual(_color_for_coverage(65), "yellow")
        self.assertEqual(_color_for_coverage(45), "orange")
        self.assertEqual(_color_for_coverage(20), "red")

    def test_threshold_boundaries(self):
        self.assertEqual(_color_for_coverage(90), "brightgreen")
        self.assertEqual(_color_for_coverage(89.99), "green")
        self.assertEqual(_color_for_coverage(0), "red")
        self.assertEqual(_color_for_coverage(-5), "red")

    def test_custom_thresholds(self):
        thresholds = [(75, "green"), (50, "yellow")]
        self.assertEqual(_color_for_coverage(80, thresholds), "green")
        self.assertEqual(_color_for_coverage(50, thresholds), "yellow")
        self.assertEqual(_color_for_coverage(49, thresholds), "red")


class TestVersionBadge(unittest.TestCase):
    def test_version(self):
        svg = version_badge("1.2.3")
        self.assertIn("1.2.3", svg)
        self.assertIn("version", svg)


class TestLicenseBadge(unittest.TestCase):
    def test_license(self):
        svg = license_badge("MIT")
        self.assertIn("MIT", svg)
        self.assertIn("license", svg)


class TestCustomBadge(unittest.TestCase):
    def test_custom(self):
        svg = custom_badge("platform", "linux", color="green")
        self.assertIn("platform", svg)
        self.assertIn("linux", svg)

    def test_label_color(self):
        svg = custom_badge("platform", "linux", label_color="#123456")
        self.assertIn('fill="#123456"', svg)
        self.assertIn('fill="#007ec6"', svg)


class TestTestsBadge(unittest.TestCase):
    def test_all_passing(self):
        svg = presets.tests_badge(10, 0)
        self.assertIn("10 passed", svg)

    def test_with_failures(self):
        svg = presets.tests_badge(8, 2)
        self.assertIn("8 passed", svg)
        self.assertIn("2 failed", svg)

    def test_with_skipped(self):
        svg = presets.tests_badge(7, 0, 3)
        self.assertIn("7 passed", svg)
        self.assertIn("3 skipped", svg)

    def test_colors(self):
        self.assertIn('fill="#4c1"', presets.tests_badge(10, 0))
        self.assertIn('fill="#dfb317"', presets.tests_badge(7, 0, 3))
        svg = presets.tests_badge(5, 1, 2)
        self.assertIn(">5 passed, 1 failed, 2 skipped<", svg)
        self.assertIn('fill="#e05d44"', svg)


class TestFallbackBadges(unittest.TestCase):
    def test_error_badge(self):
        svg = presets.error_badge("downloads", message="unknown")
        self.assertIn("downloads", svg)
        self.assertIn("unknown", svg)

    def test_empty_badge(self):
        self.assertEqual(
            presets.empty_badge(),
            '<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0"/>',
        )


if __name__ == "__main__":
    unittest.main()
