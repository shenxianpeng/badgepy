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
"""Tests for the badgepy command line interface."""

import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from importlib.metadata import version
from unittest import mock
from xml.dom import minidom

from badgepy import __main__ as cli


class TestBadgepyCli(unittest.TestCase):
    def _run_badgepy(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "badgepy", *args],
            check=False,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def _write_temp(self, content: str, suffix: str) -> str:
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_preset_progress_percentage(self):
        result = self._run_badgepy("preset", "progress", "0.75", "--label", "docs")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("docs", result.stdout)
        self.assertIn("75%", result.stdout)

    def test_preset_progress_fraction(self):
        result = self._run_badgepy(
            "preset",
            "progress",
            "--numerator",
            "3",
            "--denominator",
            "4",
            "--message",
            "documented",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("documented", result.stdout)

    def test_from_json_with_thresholds(self):
        path = self._write_temp(json.dumps({"coverage": 87.5}), ".json")
        try:
            result = self._run_badgepy(
                "from-json",
                path,
                "--query",
                "coverage",
                "--label",
                "coverage",
                "--template",
                "{value}%",
                "--thresholds",
                "90:brightgreen,80:green,0:red",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("coverage", result.stdout)
            self.assertIn("87.5%", result.stdout)
            self.assertIn("#97CA00", result.stdout)
        finally:
            os.unlink(path)

    def test_from_json_error_badge(self):
        path = self._write_temp(json.dumps({"coverage": 87.5}), ".json")
        try:
            result = self._run_badgepy(
                "from-json",
                path,
                "--query",
                "downloads",
                "--label",
                "downloads",
                "--on-error",
                "badge",
                "--error-message",
                "unavailable",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("downloads", result.stdout)
            self.assertIn("unavailable", result.stdout)
        finally:
            os.unlink(path)

    def test_from_json_error_hide(self):
        path = self._write_temp(json.dumps({"coverage": 87.5}), ".json")
        try:
            result = self._run_badgepy(
                "from-json",
                path,
                "--query",
                "downloads",
                "--on-error",
                "hide",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('width="0"', result.stdout)
            self.assertIn('height="0"', result.stdout)
        finally:
            os.unlink(path)

    def test_from_pyproject(self):
        path = self._write_temp('[project]\nname = "badgepy"\n', ".toml")
        try:
            result = self._run_badgepy(
                "from-pyproject",
                path,
                "--query",
                "project.name",
                "--label",
                "package",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("package", result.stdout)
            self.assertIn("badgepy", result.stdout)
        finally:
            os.unlink(path)

    def test_from_lock(self):
        path = self._write_temp(
            '[[package]]\nname = "ruff"\nversion = "0.14.6"\n',
            ".lock",
        )
        try:
            result = self._run_badgepy("from-lock", path, "ruff")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("ruff", result.stdout)
            self.assertIn("0.14.6", result.stdout)
        finally:
            os.unlink(path)

    def test_default_badge_font_family_and_logo_width(self):
        logo = "data:image/png;base64,iVBORw0KGgo="
        result = self._run_badgepy(
            "--left-text",
            "logo",
            "--right-text",
            "wide",
            "--logo",
            logo,
            "--logo-width",
            "28",
            "--font-family",
            "Open Sans,sans-serif",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('font-family="Open Sans,sans-serif"', result.stdout)
        self.assertIn('width="28.0"', result.stdout)


JUNIT_XML = """<?xml version="1.0"?>
<testsuite tests="10" failures="2" errors="0" skipped="1"/>"""

COVERAGE_XML = """<?xml version="1.0"?>
<coverage line-rate="0.853" branch-rate="0.5"><packages/></coverage>"""


class TestCliMain(unittest.TestCase):
    """Run badgepy.__main__.main() in-process for every command."""

    def setUp(self):
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        self.tmpdir = tmpdir.name

    def _write(self, name: str, content: str) -> str:
        path = os.path.join(self.tmpdir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def _main(self, *argv: str) -> tuple[object, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        code: object = 0
        with (
            mock.patch.object(sys, "argv", ["badgepy", *argv]),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            try:
                cli.main()
            except SystemExit as e:
                code = e.code
        return code, stdout.getvalue(), stderr.getvalue()

    def assertSvg(self, text: str) -> None:
        self.assertEqual(minidom.parseString(text).documentElement.tagName, "svg")

    # Default badge command.

    def test_version(self):
        code, stdout, _ = self._main("--version")
        self.assertEqual(code, 0)
        self.assertEqual(stdout.strip(), "badgepy " + version("badgepy"))

    def test_badge_to_stdout(self):
        code, stdout, stderr = self._main(
            "--left-text", "build", "--right-text", "passing", "--right-color", "green"
        )
        self.assertEqual(code, 0, stderr)
        self.assertSvg(stdout)
        self.assertIn(">build<", stdout)
        self.assertIn(">passing<", stdout)
        self.assertIn('fill="#97CA00"', stdout)
        self.assertEqual(stderr, "")

    def test_badge_to_file(self):
        output = os.path.join(self.tmpdir, "nested", "build.svg")
        code, stdout, stderr = self._main(
            "--left-text", "build", "--right-text", "passing", "-o", output
        )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr.strip(), "Badge written to " + output)
        with open(output, encoding="utf-8") as f:
            self.assertSvg(f.read())

    def test_badge_in_browser(self):
        with mock.patch.object(cli.webbrowser, "open_new_tab") as open_new_tab:
            code, stdout, stderr = self._main(
                "--left-text", "build", "--right-text", "passing", "--browser"
            )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(stdout, "")
        ((url,), _) = open_new_tab.call_args
        self.assertTrue(url.startswith("file://"), url)
        path = url[len("file://") :]
        self.addCleanup(os.unlink, path)
        self.assertTrue(path.endswith(".svg"), path)
        with open(path, encoding="utf-8") as f:
            svg = f.read()
        self.assertSvg(svg)
        self.assertIn(">passing<", svg)

    def test_badge_whole_link_conflicts_with_other_links(self):
        for link_flag in ("--left-link", "--right-link", "--center-link"):
            with self.subTest(link_flag=link_flag):
                code, stdout, stderr = self._main(
                    link_flag,
                    "https://a.example/",
                    "--whole-link",
                    "https://b.example/",
                )
                self.assertEqual(code, 1)
                self.assertEqual(stdout, "")
                self.assertIn("cannot be set with", stderr)

    def test_badge_pil_measurer_requires_font_path(self):
        code, stdout, stderr = self._main("--use-pil-text-measurer")
        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("must also set --deja-vu-sans-path", stderr)

    def test_badge_with_pil_measurer(self):
        with mock.patch("badgepy.pil_text_measurer.PilMeasurer") as measurer_class:
            measurer_class.return_value.text_width.return_value = 100.0
            code, stdout, stderr = self._main(
                "--left-text",
                "a",
                "--right-text",
                "b",
                "--use-pil-text-measurer",
                "--deja-vu-sans-path",
                "DejaVuSans.ttf",
            )
        self.assertEqual(code, 0, stderr)
        measurer_class.assert_called_once_with("DejaVuSans.ttf")
        # Each side is 100 / 10 units of text plus 10 units of padding.
        self.assertIn('width="40.0"', stdout)

    def test_badge_options_are_passed_through(self):
        with mock.patch.object(cli.badgepy, "badge", return_value="<svg/>") as badge:
            code, stdout, stderr = self._main(
                "--left-text=l",
                "--right-text=r",
                "--left-link=https://l.example/",
                "--right-link=https://r.example/",
                "--center-link=https://c.example/",
                "--logo=logo.png",
                "--logo-width=20",
                "--font-family=serif",
                "--left-color=red",
                "--right-color=blue",
                "--center-color=green",
                "--left-title=lt",
                "--right-title=rt",
                "--center-title=ct",
                "--whole-title=wt",
                "--right-image=right.png",
                "--center-image=center.png",
                "--embed-logo",
                "--embed-right-image=yes",
                "--embed-center-image=no",
            )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(stdout, "<svg/>")
        badge.assert_called_once_with(
            left_text="l",
            right_text="r",
            left_link="https://l.example/",
            right_link="https://r.example/",
            center_link="https://c.example/",
            whole_link=None,
            logo="logo.png",
            left_color="red",
            right_color="blue",
            center_color="green",
            measurer=None,
            left_title="lt",
            right_title="rt",
            center_title="ct",
            whole_title="wt",
            right_image="right.png",
            center_image="center.png",
            embed_logo=True,
            embed_right_image=True,
            embed_center_image=False,
            logo_width=20.0,
            font_family="serif",
        )

    # preset

    def test_presets(self):
        cases = [
            (["build", "passing"], [">build<", ">passing<", 'fill="#4c1"']),
            (["build", "passing", "--label", "ci"], [">ci<", ">passing<"]),
            (["coverage", "85.3"], [">coverage<", ">85.3%<", 'fill="#97CA00"']),
            (["version", "v1.2.3"], [">version<", ">v1.2.3<", 'fill="#007ec6"']),
            (["license", "MIT"], [">license<", ">MIT<"]),
            (
                ["custom", "linux", "--label", "platform", "--color", "green"],
                [">platform<", ">linux<", 'fill="#97CA00"'],
            ),
            (["custom", "linux"], [">badge<", ">linux<", 'fill="#007ec6"']),
            (["progress", "75"], [">progress<", ">75%<"]),
            (
                ["progress", "--numerator", "1", "--denominator", "4"],
                [">progress<", ">25%<", 'fill="#e05d44"'],
            ),
        ]
        for args, expected in cases:
            with self.subTest(args=args):
                code, stdout, stderr = self._main("preset", *args)
                self.assertEqual(code, 0, stderr)
                self.assertSvg(stdout)
                for text in expected:
                    self.assertIn(text, stdout)

    def test_preset_requires_value(self):
        code, stdout, stderr = self._main("preset", "build")
        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("preset 'build' requires a value", stderr)

    def test_preset_to_file(self):
        output = os.path.join(self.tmpdir, "build.svg")
        code, _, stderr = self._main("preset", "build", "passing", "-o", output)
        self.assertEqual(code, 0, stderr)
        with open(output, encoding="utf-8") as f:
            self.assertIn(">passing<", f.read())

    def test_unknown_preset_type(self):
        # argparse restricts the choices; the function still guards itself.
        args = argparse.Namespace(preset_type="nope", value="x")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                cli._cmd_preset(args)
        self.assertEqual(raised.exception.code, 1)
        self.assertIn("unknown preset type: nope", stderr.getvalue())

    # from-junit / from-coverage

    def test_from_junit(self):
        report = self._write("results.xml", JUNIT_XML)

        code, stdout, stderr = self._main("from-junit", report)
        self.assertEqual(code, 0, stderr)
        self.assertSvg(stdout)
        self.assertIn(">7 passed, 2 failed, 1 skipped<", stdout)

        output = os.path.join(self.tmpdir, "tests.svg")
        code, stdout, stderr = self._main("from-junit", report, "-o", output)
        self.assertEqual(code, 0, stderr)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr.strip(), "Badge written to " + output)
        self.assertTrue(os.path.isfile(output))

        output_dir = os.path.join(self.tmpdir, "badges")
        code, _, stderr = self._main("from-junit", report, "--output-dir", output_dir)
        self.assertEqual(code, 0, stderr)
        self.assertEqual(os.listdir(output_dir), ["tests.svg"])
        self.assertIn(os.path.join(output_dir, "tests.svg"), stderr)

    def test_from_coverage(self):
        report = self._write("coverage.xml", COVERAGE_XML)

        code, stdout, stderr = self._main("from-coverage", report)
        self.assertEqual(code, 0, stderr)
        self.assertSvg(stdout)
        self.assertIn(">85.3%<", stdout)

        output = os.path.join(self.tmpdir, "coverage.svg")
        code, stdout, stderr = self._main("from-coverage", report, "-o", output)
        self.assertEqual(code, 0, stderr)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr.strip(), "Badge written to " + output)
        self.assertTrue(os.path.isfile(output))

        output_dir = os.path.join(self.tmpdir, "badges")
        code, _, stderr = self._main(
            "from-coverage", report, "--output-dir", output_dir
        )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(
            sorted(os.listdir(output_dir)), ["branch-coverage.svg", "coverage.svg"]
        )

    # from-generic

    def test_from_generic_to_stdout(self):
        source = self._write("metrics.txt", "warnings=12\nlint=clean\n")
        code, stdout, stderr = self._main("from-generic", source, "--color", "red")
        self.assertEqual(code, 0, stderr)
        self.assertIn("--- warnings ---\n<svg", stdout)
        self.assertIn("--- lint ---\n<svg", stdout)
        self.assertIn('fill="#e05d44"', stdout)

    def test_from_generic_to_directory(self):
        source = self._write("metrics.json", json.dumps({"warnings": 12}))
        output_dir = os.path.join(self.tmpdir, "badges")
        code, stdout, stderr = self._main(
            "from-generic", source, "--output-dir", output_dir
        )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(stdout, "")
        self.assertEqual(os.listdir(output_dir), ["warnings.svg"])
        with open(os.path.join(output_dir, "warnings.svg"), encoding="utf-8") as f:
            svg = f.read()
        self.assertIn(">12<", svg)
        self.assertIn('fill="#007ec6"', svg)

    # from-json / from-toml / from-pyproject

    def test_from_json(self):
        source = self._write("summary.json", json.dumps({"total": {"pct": 92.5}}))
        code, stdout, stderr = self._main(
            "from-json",
            source,
            "--query",
            "total.pct",
            "--template",
            "{value}%",
            "--thresholds",
            "90:brightgreen,0:red",
        )
        self.assertEqual(code, 0, stderr)
        self.assertIn(">pct<", stdout)
        self.assertIn(">92.5%<", stdout)
        self.assertIn('fill="#4c1"', stdout)

    def test_from_toml_to_file(self):
        source = self._write("data.toml", '[tool.badge]\nstatus = "stable"\n')
        output = os.path.join(self.tmpdir, "status.svg")
        code, _, stderr = self._main(
            "from-toml", source, "--query", "tool.badge.status", "-o", output
        )
        self.assertEqual(code, 0, stderr)
        with open(output, encoding="utf-8") as f:
            svg = f.read()
        self.assertIn(">status<", svg)
        self.assertIn(">stable<", svg)

    def test_from_pyproject_defaults(self):
        source = self._write("pyproject.toml", '[project]\nversion = "1.2.3"\n')
        code, stdout, stderr = self._main("from-pyproject", source)
        self.assertEqual(code, 0, stderr)
        self.assertIn(">version<", stdout)
        self.assertIn(">1.2.3<", stdout)

    def test_structured_errors(self):
        source = self._write("data.json", "{not json")
        cases = [
            # (extra arguments, expected exit code, expected output)
            ([], 1, None),
            (["--on-error", "hide"], 0, ['width="0"']),
            (["--on-error", "badge"], 0, [">badge<", ">unknown<", 'fill="#9f9f9f"']),
            (
                ["--on-error", "badge", "--query", "downloads"],
                0,
                [">downloads<", ">unknown<"],
            ),
            (
                [
                    "--on-error",
                    "badge",
                    "--query",
                    "downloads",
                    "--label",
                    "pypi",
                    "--error-message",
                    "n/a",
                    "--error-color",
                    "red",
                ],
                0,
                [">pypi<", ">n/a<", 'fill="#e05d44"'],
            ),
        ]
        for extra, expected_code, expected in cases:
            with self.subTest(extra=extra):
                code, stdout, stderr = self._main("from-json", source, *extra)
                self.assertEqual(code, expected_code, stderr)
                if expected is None:
                    self.assertEqual(stdout, "")
                    self.assertIn("failed to generate badge:", stderr)
                else:
                    self.assertSvg(stdout)
                    for text in expected:
                        self.assertIn(text, stdout)

    # from-lock

    def test_from_lock(self):
        lock = self._write(
            "uv.lock", '[[package]]\nname = "ruff"\nversion = "0.14.6"\n'
        )
        code, stdout, stderr = self._main(
            "from-lock", lock, "ruff", "--template", "v{value}", "--color", "green"
        )
        self.assertEqual(code, 0, stderr)
        self.assertIn(">ruff<", stdout)
        self.assertIn(">v0.14.6<", stdout)
        self.assertIn('fill="#97CA00"', stdout)

    def test_from_lock_errors(self):
        lock = self._write("uv.lock", '[[package]]\nname = "ruff"\nversion = "1"\n')

        code, stdout, stderr = self._main("from-lock", lock, "jinja2")
        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("failed to generate badge:", stderr)

        code, stdout, stderr = self._main(
            "from-lock", lock, "jinja2", "--on-error", "badge"
        )
        self.assertEqual(code, 0, stderr)
        self.assertIn(">jinja2<", stdout)
        self.assertIn(">unknown<", stdout)

        code, stdout, stderr = self._main(
            "from-lock", lock, "jinja2", "--on-error", "hide"
        )
        self.assertEqual(code, 0, stderr)
        self.assertIn('width="0"', stdout)


if __name__ == "__main__":
    unittest.main()
