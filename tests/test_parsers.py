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
import sys
import tempfile
import unittest
from unittest import mock
from xml.dom import minidom

from badgepy.parsers.junit import parse_junit, badges_from_junit
from badgepy.parsers.coverage import (
    CoverageResult,
    parse_coverage,
    badges_from_coverage,
)
from badgepy.parsers.generic import parse_generic, badges_from_generic
from badgepy.parsers.structured import (
    _parse_basic_toml,
    _parse_toml_value,
    _split_toml_array,
    _strip_toml_comment,
    badge_from_lock,
    badge_from_structured_data,
    color_for_value,
    load_structured_data,
    package_from_lock,
    parse_thresholds,
    render_template,
    select_value,
    stringify_value,
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

    def test_missing_counts_default_to_zero(self):
        path = self._write_temp('<testsuites><testsuite tests="4"/></testsuites>')
        try:
            result = parse_junit(path)
            self.assertEqual(
                (result.tests, result.failures, result.errors, result.skipped),
                (4, 0, 0, 0),
            )
            self.assertEqual(result.passed, 4)
        finally:
            os.unlink(path)

    def test_errors_count_as_failed_in_badge(self):
        path = self._write_temp('<testsuite tests="5" failures="1" errors="2"/>')
        try:
            svg = badges_from_junit(path)["tests"]
            self.assertIn(">2 passed, 3 failed<", svg)
            self.assertIn('fill="#e05d44"', svg)
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

    def test_badges_without_branch_rate(self):
        path = self._write_temp('<coverage line-rate="0.42"/>')
        try:
            badges = badges_from_coverage(path)
            self.assertEqual(list(badges), ["coverage"])
            self.assertIn(">42%<", badges["coverage"])
        finally:
            os.unlink(path)

    def test_missing_line_rate_defaults_to_zero(self):
        path = self._write_temp('<coverage branch-rate=""/>')
        try:
            result = parse_coverage(path)
            self.assertEqual(result.line_rate, 0.0)
            self.assertIsNone(result.branch_rate)
        finally:
            os.unlink(path)

    def test_percentages(self):
        self.assertIsNone(
            CoverageResult(line_rate=0.5, branch_rate=None).branch_percentage
        )
        result = CoverageResult(line_rate=0.25, branch_rate=0.125)
        self.assertEqual(result.line_percentage, 25.0)
        self.assertEqual(result.branch_percentage, 12.5)


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

    def test_key_value_lines_without_separator_are_ignored(self):
        path = self._write_temp("  key = spaced value  \nno separator here\nempty=\n")
        try:
            self.assertEqual(parse_generic(path), {"key": "spaced value", "empty": ""})
        finally:
            os.unlink(path)

    def test_json_values_are_stringified(self):
        data = {"score": 8.5, "ok": True, "items": [1, 2], "none": None}
        path = self._write_temp(json.dumps(data), suffix=".json")
        try:
            self.assertEqual(
                parse_generic(path),
                {"score": "8.5", "ok": "True", "items": "[1, 2]", "none": "None"},
            )
        finally:
            os.unlink(path)

    def test_badges_from_generic_color(self):
        path = self._write_temp("lint=clean")
        try:
            badges = badges_from_generic(path, color="red")
            self.assertIn('fill="#e05d44"', badges["lint"])
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

    def test_lock_skips_entries_that_are_not_tables(self):
        data = {"package": ["oops", {"name": "Ruff", "version": "0.1.0"}]}
        with mock.patch(
            "badgepy.parsers.structured.load_structured_data", return_value=data
        ) as load:
            self.assertEqual(package_from_lock("uv.lock", "ruff")["version"], "0.1.0")
        load.assert_called_once_with("uv.lock", input_format="toml")

    def test_badge_from_lock_requires_version(self):
        path = self._write_temp('[[package]]\nname = "ruff"\n', ".lock")
        try:
            with self.assertRaisesRegex(KeyError, "has no version"):
                badge_from_lock(path, "ruff")
        finally:
            os.unlink(path)

    def test_badge_from_lock_label_and_template(self):
        path = self._write_temp(
            '[[package]]\nname = "ruff"\nversion = "0.14.6"\n', ".lock"
        )
        try:
            svg = badge_from_lock(
                path, "ruff", label="linter", template="{name}=={value}", color="red"
            )
            self.assertIn(">linter<", svg)
            self.assertIn(">ruff==0.14.6<", svg)
            self.assertIn('fill="#e05d44"', svg)
        finally:
            os.unlink(path)

    def test_toml_without_tomllib_uses_fallback_parser(self):
        content = '[project]\nname = "badgepy"\nversion = "1.2.3"\n'
        path = self._write_temp(content, ".toml")
        try:
            # A None entry in sys.modules makes `import tomllib` fail.
            with mock.patch.dict(sys.modules, {"tomllib": None}):
                result = load_structured_data(path)
            self.assertEqual(
                result, {"project": {"name": "badgepy", "version": "1.2.3"}}
            )
        finally:
            os.unlink(path)

    def test_explicit_input_format(self):
        path = self._write_temp('{"a": 1}', ".txt")
        try:
            self.assertEqual(load_structured_data(path, input_format="JSON"), {"a": 1})
            with self.assertRaisesRegex(ValueError, "unsupported .* format: txt"):
                load_structured_data(path)
        finally:
            os.unlink(path)


class TestBasicTomlParser(unittest.TestCase):
    """Tests for the TOML subset parser used when tomllib is unavailable."""

    def test_strip_comment(self):
        self.assertEqual(_strip_toml_comment("a = 1 # note"), "a = 1")
        self.assertEqual(_strip_toml_comment('a = "x # y" # z'), 'a = "x # y"')
        self.assertEqual(_strip_toml_comment("a = 'x # y' # z"), "a = 'x # y'")
        self.assertEqual(
            _strip_toml_comment('a = "say \\"hi\\" # still" # z'),
            'a = "say \\"hi\\" # still"',
        )
        self.assertEqual(_strip_toml_comment("  # only a comment"), "")
        self.assertEqual(_strip_toml_comment("  a = 1  "), "a = 1")

    def test_split_array(self):
        self.assertEqual(
            _split_toml_array('"a, b", \'c,d\', "e\\",f", 1,'),
            ['"a, b"', "'c,d'", '"e\\",f"', "1"],
        )
        self.assertEqual(_split_toml_array(""), [])

    def test_parse_values(self):
        cases = {
            '"double \\u00e9"': "double é",
            "'single'": "single",
            "true": True,
            "false": False,
            "[]": [],
            '[1, 2.5, "x", [true]]': [1, 2.5, "x", [True]],
            "42": 42,
            "-7": -7,
            "1e3": 1000.0,
            "1.2.3": "1.2.3",
            "bare": "bare",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                value = _parse_toml_value(raw)
                self.assertEqual(value, expected)
                self.assertIs(type(value), type(expected))

    def test_parse_tables(self):
        result = _parse_basic_toml(
            """
            top = 1
            not a key value line
            [tool]
            name = "x"  # comment
            [tool.badge]
            status = 'ok'
            [[tool.items]]
            id = 1
            [[tool.items]]
            id = 2
            [other]
            """
        )
        self.assertEqual(
            result,
            {
                "top": 1,
                "tool": {
                    "name": "x",
                    "badge": {"status": "ok"},
                    "items": [{"id": 1}, {"id": 2}],
                },
                "other": {},
            },
        )


class TestStructuredQueries(unittest.TestCase):
    DATA = {
        "project": {"name": "badgepy", "version": "1.2.3"},
        "items": [{"name": "first"}, {"name": "second", "tags": ["a", "b"]}],
        "matrix": [[1, 2], [3, 4]],
    }

    def test_select_value_without_query(self):
        self.assertIs(select_value(self.DATA, None), self.DATA)
        self.assertIs(select_value(self.DATA, ""), self.DATA)

    def test_select_value_paths(self):
        self.assertEqual(select_value(self.DATA, "items[1].tags[0]"), "a")
        self.assertEqual(select_value(self.DATA, "matrix[1][0]"), 3)

    def test_select_value_errors(self):
        with self.assertRaisesRegex(KeyError, "invalid path component"):
            select_value(self.DATA, "project..name")
        with self.assertRaisesRegex(KeyError, "path component not found: name"):
            select_value(self.DATA, "items.name")
        with self.assertRaises(IndexError):
            select_value(self.DATA, "items[5]")

    def test_stringify_value(self):
        self.assertEqual(stringify_value(True), "true")
        self.assertEqual(stringify_value(False), "false")
        self.assertEqual(stringify_value({"b": 1, "a": "é"}), '{"a": "é", "b": 1}')
        self.assertEqual(stringify_value([1, "x"]), '[1, "x"]')
        self.assertEqual(stringify_value(1.5), "1.5")
        self.assertEqual(stringify_value(None), "None")

    def test_render_template(self):
        self.assertEqual(render_template(None, self.DATA, True), "true")
        self.assertEqual(render_template("", self.DATA, 3), "3")
        self.assertEqual(
            render_template("{project.name}: {items[0].name} {value}", self.DATA, 7),
            "badgepy: first 7",
        )
        self.assertEqual(
            render_template("{ not a field }", self.DATA, 1), "{ not a field }"
        )
        with self.assertRaises(KeyError):
            render_template("{missing}", self.DATA, 1)

    def test_thresholds(self):
        self.assertIsNone(parse_thresholds(None))
        self.assertIsNone(parse_thresholds(""))
        thresholds = parse_thresholds(" 10 : yellow ,90:green")
        self.assertEqual(thresholds, [(90.0, "green"), (10.0, "yellow")])
        self.assertEqual(color_for_value("95", thresholds), "green")
        self.assertEqual(color_for_value(10, thresholds), "yellow")
        # Values below every threshold use the lowest threshold's color.
        self.assertEqual(color_for_value(5, thresholds), "yellow")
        with self.assertRaises(ValueError):
            color_for_value("n/a", thresholds)
        with self.assertRaises(ValueError):
            parse_thresholds("high:green")


class TestBadgeFromStructuredData(unittest.TestCase):
    def setUp(self):
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        self.path = os.path.join(tmpdir.name, "metrics.json")
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"lint": {"score": 7.5}}, f)

    def test_label_defaults_to_last_query_component(self):
        svg = badge_from_structured_data(self.path, query="lint.score")
        self.assertIn(">score<", svg)
        self.assertIn(">7.5<", svg)
        self.assertIn('fill="#007ec6"', svg)

    def test_label_defaults_to_file_name(self):
        svg = badge_from_structured_data(self.path)
        texts = [
            text.firstChild.data
            for text in minidom.parseString(svg).getElementsByTagName("text")
        ]
        self.assertEqual(texts[0], "metrics")
        self.assertEqual(texts[-1], '{"lint": {"score": 7.5}}')

    def test_threshold_list_and_color(self):
        svg = badge_from_structured_data(
            self.path,
            label="lint",
            query="lint.score",
            color="blue",
            thresholds=[(8.0, "green"), (0.0, "orange")],
        )
        self.assertIn(">lint<", svg)
        self.assertIn('fill="#fe7d37"', svg)


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

    def test_write_badges_allows_names_in_subdirectories(self):
        from badgepy.output import write_badges

        with tempfile.TemporaryDirectory() as tmpdir:
            (path,) = write_badges({"lint/errors": "<svg/>"}, tmpdir)
            self.assertEqual(
                path, os.path.join(os.path.abspath(tmpdir), "lint", "errors.svg")
            )
            self.assertTrue(os.path.isfile(path))


if __name__ == "__main__":
    unittest.main()
