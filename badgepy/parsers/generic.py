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
"""Parse generic key-value or JSON input and generate badges.

Useful for lint tool output, custom metrics, or any tool that produces
simple key=value pairs or JSON.

Supported input formats:

Key-value text (one per line)::

    warnings=12
    errors=0
    score=8.5

JSON::

    {"warnings": 12, "errors": 0, "score": "8.5/10"}
"""

import json
from typing import Union

from badgepy.presets import custom_badge


def parse_generic(source: Union[str, "os.PathLike[str]"]) -> dict[str, str]:
    """Parse a generic key-value or JSON file.

    Args:
        source: Path to a file containing key=value lines or JSON.

    Returns:
        A dict of parsed key-value pairs (all values as strings).
    """
    import os

    with open(os.fspath(source), "r", encoding="utf-8") as f:
        content = f.read().strip()

    # Try JSON first
    if content.startswith("{"):
        data = json.loads(content)
        return {str(k): str(v) for k, v in data.items()}

    # Fall back to key=value parsing
    result = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()

    return result


def badges_from_generic(
    source: Union[str, "os.PathLike[str]"],
    color: str = "blue",
) -> dict[str, str]:
    """Parse a generic file and generate a badge for each key-value pair.

    Args:
        source: Path to a key-value or JSON file.
        color: Default badge color.

    Returns:
        A dict mapping badge names to SVG strings.
    """
    data = parse_generic(source)
    return {key: custom_badge(label=key, message=value, color=color) for key, value in data.items()}
