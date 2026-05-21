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
"""Parse local JSON/TOML files and generate badges from selected values."""

import json
import os
import re
from typing import Any, Optional, Union, cast

from badgepy.presets import custom_badge


_PATH_PART_RE = re.compile(r"([^\[\]]+)|\[(\d+)\]")
_TEMPLATE_FIELD_RE = re.compile(r"\{([A-Za-z0-9_.\-\[\]]+)\}")


def _load_toml(content: str) -> dict[str, Any]:
    try:
        import tomllib
    except ImportError:
        return _parse_basic_toml(content)

    return tomllib.loads(content)


def _strip_toml_comment(line: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    for i, char in enumerate(line):
        if char == "\\" and in_double and not escaped:
            escaped = True
            continue
        if char == "'" and not in_double and not escaped:
            in_single = not in_single
        elif char == '"' and not in_single and not escaped:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:i].strip()
        escaped = False
    return line.strip()


def _split_toml_array(value: str) -> list[str]:
    parts = []
    start = 0
    in_single = False
    in_double = False
    escaped = False
    for i, char in enumerate(value):
        if char == "\\" and in_double and not escaped:
            escaped = True
            continue
        if char == "'" and not in_double and not escaped:
            in_single = not in_single
        elif char == '"' and not in_single and not escaped:
            in_double = not in_double
        elif char == "," and not in_single and not in_double:
            parts.append(value[start:i].strip())
            start = i + 1
        escaped = False
    tail = value[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def _parse_toml_value(value: str) -> Any:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return json.loads(value)
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_toml_value(part) for part in _split_toml_array(inner)]
    try:
        if any(char in value for char in ".eE"):
            return float(value)
        return int(value)
    except ValueError:
        return value


def _ensure_toml_table(parent: dict[str, Any], key: str) -> dict[str, Any]:
    """Return a child table, creating it when absent."""
    value = parent.get(key)
    if not isinstance(value, dict):
        value = {}
        parent[key] = value
    return cast(dict[str, Any], value)


def _append_toml_table(parent: dict[str, Any], key: str) -> dict[str, Any]:
    """Append and return a table in a TOML array-of-tables."""
    value = parent.get(key)
    if not isinstance(value, list):
        value = []
        parent[key] = value

    tables = cast(list[dict[str, Any]], value)
    table: dict[str, Any] = {}
    tables.append(table)
    return table


def _parse_basic_toml(content: str) -> dict[str, Any]:
    """Parse a small TOML subset for Python versions without tomllib.

    The fallback supports common badge inputs: sections, dotted section names,
    strings, booleans, numbers, and simple arrays.
    """
    data: dict[str, Any] = {}
    current = data

    for raw_line in content.splitlines():
        line = _strip_toml_comment(raw_line)
        if not line:
            continue
        if line.startswith("[[") and line.endswith("]]"):
            current = data
            parts = line[2:-2].strip().split(".")
            for part in parts[:-1]:
                current = _ensure_toml_table(current, part)
            array_name = parts[-1]
            current = _append_toml_table(current, array_name)
            continue
        if line.startswith("[") and line.endswith("]"):
            current = data
            for part in line[1:-1].strip().split("."):
                current = _ensure_toml_table(current, part)
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        current[key.strip()] = _parse_toml_value(value)

    return data


def load_structured_data(
    source: Union[str, "os.PathLike[str]"],
    input_format: Optional[str] = None,
) -> Any:
    """Load JSON or TOML from a local file."""
    path = os.fspath(source)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    fmt = (input_format or os.path.splitext(path)[1].lstrip(".")).lower()
    if fmt == "json":
        return json.loads(content)
    if fmt == "toml":
        return _load_toml(content)
    raise ValueError(f"unsupported structured data format: {fmt}")


def select_value(data: Any, query: Optional[str] = None) -> Any:
    """Select a value with a small dot-and-index path syntax.

    Examples: ``project.version``, ``items[0].name``, ``tool.badge.status``.
    """
    if not query:
        return data

    current = data
    for part in query.split("."):
        consumed = False
        for match in _PATH_PART_RE.finditer(part):
            key, index = match.groups()
            if key is not None:
                if not isinstance(current, dict) or key not in current:
                    raise KeyError(f"path component not found: {key}")
                current = current[key]
                consumed = True
            elif index is not None:
                if not isinstance(current, list):
                    raise TypeError(f"path component is not a list: {part}")
                current = current[int(index)]
                consumed = True
        if not consumed:
            raise KeyError(f"invalid path component: {part}")

    return current


def stringify_value(value: Any) -> str:
    """Convert a selected value into badge text."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def render_template(template: Optional[str], data: Any, selected_value: Any) -> str:
    """Render a badge message template.

    ``{value}`` expands to the selected query value. Other fields are treated
    as paths against the full input data, e.g. ``{project.version}``.
    """
    if not template:
        return stringify_value(selected_value)

    def replace(match: re.Match[str]) -> str:
        field = match.group(1)
        if field == "value":
            return stringify_value(selected_value)
        return stringify_value(select_value(data, field))

    return _TEMPLATE_FIELD_RE.sub(replace, template)


def parse_thresholds(spec: Optional[str]) -> Optional[list[tuple[float, str]]]:
    """Parse ``min:color`` threshold specs such as ``90:green,0:red``."""
    if not spec:
        return None

    thresholds = []
    for item in spec.split(","):
        minimum, separator, color = item.partition(":")
        if not separator:
            raise ValueError(f"invalid threshold: {item}")
        thresholds.append((float(minimum.strip()), color.strip()))

    return sorted(thresholds, key=lambda item: item[0], reverse=True)


def color_for_value(
    value: Any, thresholds: Optional[list[tuple[float, str]]]
) -> Optional[str]:
    """Return the threshold color for a selected numeric value."""
    if thresholds is None:
        return None

    numeric_value = float(value)
    for minimum, color in thresholds:
        if numeric_value >= minimum:
            return color
    return thresholds[-1][1]


def badge_from_structured_data(
    source: Union[str, "os.PathLike[str]"],
    label: Optional[str] = None,
    query: Optional[str] = None,
    color: str = "blue",
    template: Optional[str] = None,
    thresholds: Optional[Union[str, list[tuple[float, str]]]] = None,
    input_format: Optional[str] = None,
) -> str:
    """Generate a badge from a JSON or TOML file."""
    data = load_structured_data(source, input_format=input_format)
    selected = select_value(data, query)
    parsed_thresholds = (
        parse_thresholds(thresholds) if isinstance(thresholds, str) else thresholds
    )
    badge_color = color_for_value(selected, parsed_thresholds) or color
    badge_label = label or (
        query.split(".")[-1]
        if query
        else os.path.splitext(os.path.basename(os.fspath(source)))[0]
    )
    return custom_badge(
        label=badge_label,
        message=render_template(template, data, selected),
        color=badge_color,
    )


def package_from_lock(
    source: Union[str, "os.PathLike[str]"],
    package_name: str,
) -> dict[str, Any]:
    """Find a package entry in a uv.lock or poetry.lock TOML file."""
    data = load_structured_data(source, input_format="toml")
    packages = data.get("package")
    if not isinstance(packages, list):
        raise ValueError("lock file does not contain package entries")

    normalized_name = package_name.lower()
    for package in packages:
        if not isinstance(package, dict):
            continue
        if str(package.get("name", "")).lower() == normalized_name:
            return package

    raise KeyError(f"package not found in lock file: {package_name}")


def badge_from_lock(
    source: Union[str, "os.PathLike[str]"],
    package_name: str,
    label: Optional[str] = None,
    color: str = "blue",
    template: Optional[str] = None,
) -> str:
    """Generate a package version badge from a uv.lock or poetry.lock file."""
    package = package_from_lock(source, package_name)
    version = package.get("version")
    if version is None:
        raise KeyError(f"package has no version: {package_name}")

    return custom_badge(
        label=label or package_name,
        message=render_template(template, package, version),
        color=color,
    )
