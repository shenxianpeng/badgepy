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
"""Utilities for writing badge SVG files to disk."""

import os
from typing import Optional


def write_badge(svg: str, output_path: str) -> str:
    """Write a badge SVG string to a file, creating parent directories as needed.

    Args:
        svg: The SVG string to write.
        output_path: The file path to write to.

    Returns:
        The absolute path of the written file.
    """
    output_path = os.path.abspath(output_path)
    parent_dir = os.path.dirname(output_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    return output_path


def write_badges(badges: dict[str, str], output_dir: str = ".") -> list[str]:
    """Write multiple badge SVGs to a directory.

    Args:
        badges: A dict mapping filenames (without extension) to SVG strings.
        output_dir: The directory to write badge files into.

    Returns:
        A list of absolute paths of the written files.
    """
    paths = []
    for name, svg in badges.items():
        filename = name if name.endswith(".svg") else f"{name}.svg"
        path = write_badge(svg, os.path.join(output_dir, filename))
        paths.append(path)
    return paths
