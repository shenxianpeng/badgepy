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
from badgepy.parsers.structured import (
    _parse_basic_toml,
    badge_from_lock,
    badge_from_structured_data,
    color_for_value,
    load_structured_data,
    package_from_lock,
    parse_thresholds,
    render_template,
    select_value,
)


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


class TestStructuredParser(unittest.TestCase):
    def _write_temp(self, content: str, suffix: str) -> str:
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_json_query(self):
        data = {"project": {"version": "1.2.3"}, "items": [{"name": "first"}]}
        path = self._write_temp(json.dumps(data), ".json")
        try:
            result = load_structured_data(path)
            self.assertEqual(select_value(result, "project.version"), "1.2.3")
            self.assertEqual(select_value(result, "items[0].name"), "first")
        finally:
            os.unlink(path)

    def test_toml_query(self):
        path = self._write_temp(
            '[project]\nname = "badgepy"\nversion = "1.2.3"\n',
            ".toml",
        )
        try:
            result = load_structured_data(path)
            self.assertEqual(select_value(result, "project.name"), "badgepy")
            self.assertEqual(select_value(result, "project.version"), "1.2.3")
        finally:
            os.unlink(path)

    def test_basic_toml_fallback_sections_and_arrays(self):
        result = _parse_basic_toml(
            """
            [project]
            name = "badgepy"
            classifiers = ["Framework :: Pytest", "Typing :: Typed"]

            [[package]]
            name = "jinja2"
            version = "3.1.6"

            [[package]]
            name = "ruff"
            version = "0.14.6"
            """
        )
        self.assertEqual(result["project"]["name"], "badgepy")
        self.assertEqual(result["project"]["classifiers"][1], "Typing :: Typed")
        self.assertEqual(result["package"][0]["name"], "jinja2")
        self.assertEqual(result["package"][1]["version"], "0.14.6")

    def test_template(self):
        data = {"project": {"name": "badgepy", "version": "1.2.3"}}
        message = render_template(
            "{project.name} {value}",
            data,
            select_value(data, "project.version"),
        )
        self.assertEqual(message, "badgepy 1.2.3")

    def test_thresholds(self):
        self.assertEqual(
            parse_thresholds("90:brightgreen,60:yellow,0:red"),
            [(90.0, "brightgreen"), (60.0, "yellow"), (0.0, "red")],
        )

    def test_invalid_threshold(self):
        with self.assertRaises(ValueError):
            parse_thresholds("90-green")

    def test_color_for_value(self):
        thresholds = parse_thresholds("90:brightgreen,80:green,0:red")
        self.assertEqual(color_for_value(85, thresholds), "green")
        self.assertIsNone(color_for_value(85, None))

    def test_badge_from_structured_data(self):
        path = self._write_temp('{"coverage": 87.5}', ".json")
        try:
            svg = badge_from_structured_data(
                path,
                label="coverage",
                query="coverage",
                template="{value}%",
                thresholds="90:brightgreen,80:green,0:red",
            )
            self.assertIn("coverage", svg)
            self.assertIn("87.5%", svg)
            self.assertIn("#97CA00", svg)
        finally:
            os.unlink(path)

    def test_unsupported_structured_format(self):
        path = self._write_temp("coverage: 87.5", ".yaml")
        try:
            with self.assertRaises(ValueError):
                load_structured_data(path)
        finally:
            os.unlink(path)

    def test_missing_query_component(self):
        with self.assertRaises(KeyError):
            select_value({"project": {"name": "badgepy"}}, "project.version")

    def test_index_query_requires_list(self):
        with self.assertRaises(TypeError):
            select_value({"project": {"name": "badgepy"}}, "project[0].name")

    def test_lock_package(self):
        path = self._write_temp(
            '[[package]]\nname = "jinja2"\nversion = "3.1.6"\n',
            ".lock",
        )
        try:
            package = package_from_lock(path, "Jinja2")
            self.assertEqual(package["version"], "3.1.6")
        finally:
            os.unlink(path)

    def test_badge_from_lock(self):
        path = self._write_temp(
            '[[package]]\nname = "ruff"\nversion = "0.14.6"\n',
            ".lock",
        )
        try:
            svg = badge_from_lock(path, "ruff")
            self.assertIn("ruff", svg)
            self.assertIn("0.14.6", svg)
        finally:
            os.unlink(path)

    def test_lock_package_missing(self):
        path = self._write_temp(
            '[[package]]\nname = "ruff"\nversion = "0.14.6"\n',
            ".lock",
        )
        try:
            with self.assertRaises(KeyError):
                package_from_lock(path, "jinja2")
        finally:
            os.unlink(path)

    def test_lock_without_package_entries(self):
        path = self._write_temp("[project]\nname = 'badgepy'\n", ".lock")
        try:
            with self.assertRaises(ValueError):
                package_from_lock(path, "jinja2")
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


class TestPyPIParser(unittest.TestCase):
    def _fake_get(self, data):
        from unittest import mock

        response = mock.Mock()
        response.raise_for_status = mock.Mock()
        response.json = mock.Mock(return_value={"data": data, "package": "pkg"})
        return mock.Mock(return_value=response)

    def test_humanize_count(self):
        from badgepy.parsers.pypi import humanize_count

        self.assertEqual(humanize_count(0), "0")
        self.assertEqual(humanize_count(999), "999")
        self.assertEqual(humanize_count(1234), "1.2k")
        self.assertEqual(humanize_count(12345), "12k")
        self.assertEqual(humanize_count(123456), "123k")
        self.assertEqual(humanize_count(1234567), "1.2M")
        self.assertEqual(humanize_count(999999), "1M")

    def test_fetch_recent_downloads(self):
        from unittest import mock
        from badgepy.parsers import pypi

        fake = self._fake_get({"last_day": 100, "last_week": 700, "last_month": 3000})
        with mock.patch.object(pypi.requests, "get", fake):
            data = pypi.fetch_recent_downloads("python-multipart")
        self.assertEqual(data["last_month"], 3000)
        called_url = fake.call_args[0][0]
        self.assertIn("python-multipart", called_url)

    def test_download_count_metric(self):
        from unittest import mock
        from badgepy.parsers import pypi

        fake = self._fake_get({"last_day": 100, "last_week": 700, "last_month": 3000})
        with mock.patch.object(pypi.requests, "get", fake):
            self.assertEqual(pypi.download_count("pkg", "dm"), 3000)
            self.assertEqual(pypi.download_count("pkg", "dw"), 700)
            self.assertEqual(pypi.download_count("pkg", "dd"), 100)

    def test_download_count_bad_metric(self):
        from badgepy.parsers import pypi

        with self.assertRaises(ValueError):
            pypi.download_count("pkg", "bogus")

    def test_badge_from_pypi(self):
        from unittest import mock
        from badgepy.parsers import pypi

        fake = self._fake_get(
            {"last_day": 100, "last_week": 700, "last_month": 1234567}
        )
        with mock.patch.object(pypi.requests, "get", fake):
            svg = pypi.badge_from_pypi("python-multipart", metric="dm")
        self.assertIn("downloads", svg)
        self.assertIn("1.2M/month", svg)

    def test_badge_from_pypi_template(self):
        from unittest import mock
        from badgepy.parsers import pypi

        fake = self._fake_get({"last_day": 100, "last_week": 700, "last_month": 3000})
        with mock.patch.object(pypi.requests, "get", fake):
            svg = pypi.badge_from_pypi(
                "pkg", metric="dm", label="pypi", template="{value} ({count})"
            )
        self.assertIn("pypi", svg)
        self.assertIn("3k (3000)", svg)


if __name__ == "__main__":
    unittest.main()
