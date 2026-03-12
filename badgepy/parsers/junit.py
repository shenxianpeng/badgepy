# Copyright 2024 The badgepy Authors
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
"""Parse JUnit XML test reports and generate badges.

Supports the standard JUnit XML format used by pytest, JUnit, Go test2json,
and many other test frameworks.

Example JUnit XML structure::

    <testsuites>
      <testsuite tests="10" failures="1" errors="0" skipped="2">
        ...
      </testsuite>
    </testsuites>
"""

import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Union

from badgepy.presets import tests_badge


@dataclass
class JUnitResult:
    """Parsed JUnit test results."""

    tests: int
    failures: int
    errors: int
    skipped: int

    @property
    def passed(self) -> int:
        return self.tests - self.failures - self.errors - self.skipped


def parse_junit(source: Union[str, "os.PathLike[str]"]) -> JUnitResult:
    """Parse a JUnit XML file and extract test counts.

    Args:
        source: Path to a JUnit XML file.

    Returns:
        A JUnitResult with aggregated test counts.
    """
    tree = ET.parse(os.fspath(source))
    root = tree.getroot()

    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0

    if root.tag == "testsuites":
        suites = root.findall("testsuite")
    elif root.tag == "testsuite":
        suites = [root]
    else:
        raise ValueError(f"unexpected root element: {root.tag}")

    for suite in suites:
        total_tests += int(suite.get("tests", 0))
        total_failures += int(suite.get("failures", 0))
        total_errors += int(suite.get("errors", 0))
        total_skipped += int(suite.get("skipped", 0))

    return JUnitResult(
        tests=total_tests,
        failures=total_failures,
        errors=total_errors,
        skipped=total_skipped,
    )


def badges_from_junit(source: Union[str, "os.PathLike[str]"]) -> dict[str, str]:
    """Parse a JUnit XML file and generate badge SVGs.

    Args:
        source: Path to a JUnit XML file.

    Returns:
        A dict mapping badge names to SVG strings.
    """
    result = parse_junit(source)
    return {
        "tests": tests_badge(
            passed=result.passed,
            failed=result.failures + result.errors,
            skipped=result.skipped,
        ),
    }
