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
"""Parse Cobertura XML coverage reports and generate badges.

Supports the Cobertura XML format used by coverage.py, gcov, JaCoCo, and
other coverage tools.

Example Cobertura XML structure::

    <coverage line-rate="0.85" branch-rate="0.75" ...>
      <packages>...</packages>
    </coverage>
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional, Union

from badgepy.presets import coverage_badge


@dataclass
class CoverageResult:
    """Parsed coverage results."""

    line_rate: float
    branch_rate: Optional[float]

    @property
    def line_percentage(self) -> float:
        return self.line_rate * 100

    @property
    def branch_percentage(self) -> Optional[float]:
        if self.branch_rate is not None:
            return self.branch_rate * 100
        return None


def parse_coverage(source: Union[str, "os.PathLike[str]"]) -> CoverageResult:
    """Parse a Cobertura XML coverage file.

    Args:
        source: Path to a Cobertura XML file.

    Returns:
        A CoverageResult with coverage rates.
    """
    import os

    tree = ET.parse(os.fspath(source))
    root = tree.getroot()

    if root.tag != "coverage":
        raise ValueError(f"expected <coverage> root element, got <{root.tag}>")

    line_rate = float(root.get("line-rate", 0))
    branch_rate_str = root.get("branch-rate")
    branch_rate = float(branch_rate_str) if branch_rate_str else None

    return CoverageResult(line_rate=line_rate, branch_rate=branch_rate)


def badges_from_coverage(source: Union[str, "os.PathLike[str]"]) -> dict[str, str]:
    """Parse a Cobertura XML file and generate badge SVGs.

    Args:
        source: Path to a Cobertura XML file.

    Returns:
        A dict mapping badge names to SVG strings.
    """
    result = parse_coverage(source)
    badges = {
        "coverage": coverage_badge(result.line_percentage),
    }
    if result.branch_percentage is not None:
        badges["branch-coverage"] = coverage_badge(
            result.branch_percentage, label="branches"
        )
    return badges
