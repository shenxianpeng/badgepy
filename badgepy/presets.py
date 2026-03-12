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
"""Pre-configured badge recipes for common use cases.

These functions provide shields.io-compatible badge generation with
sensible defaults for colors and labels.

>>> build_badge('passing')
'<svg...</svg>'
>>> coverage_badge(85.3)
'<svg...</svg>'
"""

from typing import Optional

import badgepy

# Status-to-color mappings for build badges
_BUILD_STATUS_COLORS = {
    "passing": "brightgreen",
    "failing": "red",
    "error": "red",
    "unknown": "lightgrey",
    "pending": "yellow",
    "cancelled": "lightgrey",
}

# Default coverage thresholds: (min_percentage, color)
_DEFAULT_COVERAGE_THRESHOLDS = [
    (90, "brightgreen"),
    (80, "green"),
    (70, "yellowgreen"),
    (60, "yellow"),
    (40, "orange"),
    (0, "red"),
]


def _color_for_coverage(
    percentage: float,
    thresholds: Optional[list[tuple[float, str]]] = None,
) -> str:
    """Determine the badge color based on coverage percentage."""
    if thresholds is None:
        thresholds = _DEFAULT_COVERAGE_THRESHOLDS
    for min_pct, color in thresholds:
        if percentage >= min_pct:
            return color
    return "red"


def build_badge(status: str, label: str = "build") -> str:
    """Generate a build status badge.

    Args:
        status: Build status string (e.g. 'passing', 'failing', 'error').
        label: Left-hand label text.

    Returns:
        SVG string of the badge.

    >>> build_badge('passing')
    '<svg...</svg>'
    """
    color = _BUILD_STATUS_COLORS.get(status.lower(), "lightgrey")
    return badgepy.badge(left_text=label, right_text=status, right_color=color)


def coverage_badge(
    percentage: float,
    label: str = "coverage",
    thresholds: Optional[list[tuple[float, str]]] = None,
) -> str:
    """Generate a coverage badge with automatic color based on percentage.

    Args:
        percentage: Coverage percentage (0-100).
        label: Left-hand label text.
        thresholds: Optional list of (min_percentage, color) tuples,
            ordered from highest to lowest. Defaults to a standard
            green/yellow/red gradient.

    Returns:
        SVG string of the badge.

    >>> coverage_badge(85.3)
    '<svg...</svg>'
    """
    color = _color_for_coverage(percentage, thresholds)
    right_text = f"{percentage:.1f}%" if percentage != int(percentage) else f"{int(percentage)}%"
    return badgepy.badge(left_text=label, right_text=right_text, right_color=color)


def version_badge(ver: str, label: str = "version") -> str:
    """Generate a version badge.

    Args:
        ver: Version string (e.g. '1.2.3', 'v2.0.0').
        label: Left-hand label text.

    Returns:
        SVG string of the badge.
    """
    return badgepy.badge(left_text=label, right_text=ver, right_color="blue")


def license_badge(license_type: str, label: str = "license") -> str:
    """Generate a license badge.

    Args:
        license_type: License name (e.g. 'MIT', 'Apache-2.0', 'GPL-3.0').
        label: Left-hand label text.

    Returns:
        SVG string of the badge.
    """
    return badgepy.badge(left_text=label, right_text=license_type, right_color="blue")


def custom_badge(
    label: str,
    message: str,
    color: str = "blue",
    label_color: str = "#555",
) -> str:
    """Generate a custom badge (shields.io static badge compatible).

    This mirrors the shields.io static badge API:
    https://shields.io/badges/static-badge

    Args:
        label: Left-hand text.
        message: Right-hand text.
        color: Right-hand background color.
        label_color: Left-hand background color.

    Returns:
        SVG string of the badge.
    """
    return badgepy.badge(
        left_text=label,
        right_text=message,
        right_color=color,
        left_color=label_color,
    )


def tests_badge(passed: int, failed: int, skipped: int = 0) -> str:
    """Generate a test results summary badge.

    Args:
        passed: Number of passing tests.
        failed: Number of failing tests.
        skipped: Number of skipped tests.

    Returns:
        SVG string of the badge.
    """
    parts = [f"{passed} passed"]
    if failed:
        parts.append(f"{failed} failed")
    if skipped:
        parts.append(f"{skipped} skipped")
    right_text = ", ".join(parts)

    if failed > 0:
        color = "red"
    elif skipped > 0:
        color = "yellow"
    else:
        color = "brightgreen"

    return badgepy.badge(left_text="tests", right_text=right_text, right_color=color)
