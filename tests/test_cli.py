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

import json
import os
import subprocess
import sys
import tempfile
import unittest


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


if __name__ == "__main__":
    unittest.main()
