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
"""CI artifact parsers that extract metrics and generate badges."""

from badgepy.parsers.junit import parse_junit, badges_from_junit
from badgepy.parsers.coverage import parse_coverage, badges_from_coverage
from badgepy.parsers.generic import parse_generic, badges_from_generic

__all__ = [
    "parse_junit",
    "badges_from_junit",
    "parse_coverage",
    "badges_from_coverage",
    "parse_generic",
    "badges_from_generic",
]
