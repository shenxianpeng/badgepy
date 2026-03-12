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
"""Tests for badgepy.parsers."""

import json
import os
import tempfile
import unittest

from badgepy.parsers.junit import parse_junit, badges_from_junit
from badgepy.parsers.coverage import parse_coverage, badges_from_coverage
from badgepy.parsers.generic import parse_generic, badges_from_generic


class TestJUnitParser(unittest.TestCase):
    def _write_temp(self, content: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".xml")
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path

    def test_testsuites_root(self):
        xml = """<?xml version="1.0"?>
        <testsuites>
          <testsuite tests="10" failures="1" errors="0" skipped="2">
          </testsuite>
        </testsuites>"""
        path = self._write_temp(xml)
        try:
            result = parse_junit(path)
            self.assertEqual(result.tests, 10)
            self.assertEqual(result.failures, 1)
            self.assertEqual(result.errors, 0)
            self.assertEqual(result.skipped, 2)
            self.assertEqual(result.passed, 7)
        finally:
            os.unlink(path)

    def test_single_testsuite_root(self):
        xml = """<?xml version="1.0"?>
        <testsuite tests="5" failures="0" errors="0" skipped="0">
        </testsuite>"""
        path = self._write_temp(xml)
        try:
            result = parse_junit(path)
            self.assertEqual(result.tests, 5)
            self.assertEqual(result.passed, 5)
        finally:
            os.unlink(path)

    def test_multiple_suites(self):
        xml = """<?xml version="1.0"?>
        <testsuites>
          <testsuite tests="3" failures="1" errors="0" skipped="0"/>
          <testsuite tests="7" failures="0" errors="1" skipped="2"/>
        </testsuites>"""
        path = self._write_temp(xml)
        try:
            result = parse_junit(path)
            self.assertEqual(result.tests, 10)
            self.assertEqual(result.failures, 1)
            self.assertEqual(result.errors, 1)
            self.assertEqual(result.skipped, 2)
            self.assertEqual(result.passed, 6)
        finally:
            os.unlink(path)

    def test_invalid_root(self):
        xml = """<?xml version="1.0"?><foo/>"""
        path = self._write_temp(xml)
        try:
            with self.assertRaises(ValueError):
                parse_junit(path)
        finally:
            os.unlink(path)

    def test_badges_from_junit(self):
        xml = """<?xml version="1.0"?>
        <testsuite tests="10" failures="2" errors="0" skipped="1"/>"""
        path = self._write_temp(xml)
        try:
            badges = badges_from_junit(path)
            self.assertIn("tests", badges)
            self.assertIn("<svg", badges["tests"])
            self.assertIn("7 passed", badges["tests"])
        finally:
            os.unlink(path)


class TestCoverageParser(unittest.TestCase):
    def _write_temp(self, content: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".xml")
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path

    def test_line_rate(self):
        xml = """<?xml version="1.0"?>
        <coverage line-rate="0.85" branch-rate="0.75">
          <packages/>
        </coverage>"""
        path = self._write_temp(xml)
        try:
            result = parse_coverage(path)
            self.assertAlmostEqual(result.line_rate, 0.85)
            self.assertAlmostEqual(result.branch_rate, 0.75)
            self.assertAlmostEqual(result.line_percentage, 85.0)
            self.assertAlmostEqual(result.branch_percentage, 75.0)
        finally:
            os.unlink(path)

    def test_no_branch_rate(self):
        xml = """<?xml version="1.0"?>
        <coverage line-rate="0.90">
          <packages/>
        </coverage>"""
        path = self._write_temp(xml)
        try:
            result = parse_coverage(path)
            self.assertAlmostEqual(result.line_rate, 0.90)
            self.assertIsNone(result.branch_rate)
        finally:
            os.unlink(path)

    def test_invalid_root(self):
        xml = """<?xml version="1.0"?><foo/>"""
        path = self._write_temp(xml)
        try:
            with self.assertRaises(ValueError):
                parse_coverage(path)
        finally:
            os.unlink(path)

    def test_badges_from_coverage(self):
        xml = """<?xml version="1.0"?>
        <coverage line-rate="0.85" branch-rate="0.70">
          <packages/>
        </coverage>"""
        path = self._write_temp(xml)
        try:
            badges = badges_from_coverage(path)
            self.assertIn("coverage", badges)
            self.assertIn("branch-coverage", badges)
            self.assertIn("<svg", badges["coverage"])
        finally:
            os.unlink(path)


class TestGenericParser(unittest.TestCase):
    def _write_temp(self, content: str, suffix: str = ".txt") -> str:
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path

    def test_key_value(self):
        path = self._write_temp("warnings=12\nerrors=0\nscore=8.5")
        try:
            result = parse_generic(path)
            self.assertEqual(result["warnings"], "12")
            self.assertEqual(result["errors"], "0")
            self.assertEqual(result["score"], "8.5")
        finally:
            os.unlink(path)

    def test_json(self):
        data = {"warnings": 12, "errors": 0}
        path = self._write_temp(json.dumps(data), suffix=".json")
        try:
            result = parse_generic(path)
            self.assertEqual(result["warnings"], "12")
            self.assertEqual(result["errors"], "0")
        finally:
            os.unlink(path)

    def test_comments_and_blank_lines(self):
        path = self._write_temp("# header\nkey=value\n\n# comment\nfoo=bar")
        try:
            result = parse_generic(path)
            self.assertEqual(result["key"], "value")
            self.assertEqual(result["foo"], "bar")
            self.assertEqual(len(result), 2)
        finally:
            os.unlink(path)

    def test_badges_from_generic(self):
        path = self._write_temp("lint=clean\nwarnings=0")
        try:
            badges = badges_from_generic(path)
            self.assertIn("lint", badges)
            self.assertIn("warnings", badges)
            self.assertIn("<svg", badges["lint"])
        finally:
            os.unlink(path)


class TestOutput(unittest.TestCase):
    def test_write_badge(self):
        from badgepy.output import write_badge

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sub", "badge.svg")
            result = write_badge("<svg>test</svg>", path)
            self.assertTrue(os.path.exists(result))
            with open(result) as f:
                self.assertEqual(f.read(), "<svg>test</svg>")

    def test_write_badges(self):
        from badgepy.output import write_badges

        with tempfile.TemporaryDirectory() as tmpdir:
            badges = {"build": "<svg>b</svg>", "test.svg": "<svg>t</svg>"}
            paths = write_badges(badges, tmpdir)
            self.assertEqual(len(paths), 2)
            for p in paths:
                self.assertTrue(os.path.exists(p))


if __name__ == "__main__":
    unittest.main()
