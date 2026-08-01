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
"""Generate PyPI download-count badges from pypistats.org.

Shields.io's ``pypi/dm`` endpoint frequently returns "rate limited by
upstream service" because every README on the internet shares the same
upstream quota. This module lets you query pypistats.org directly from your
own CI, so you control retries and caching and render a static badge that
never hits a shared rate limit at display time.

>>> badge_from_pypi('badgepy')             # doctest: +SKIP
'<svg...</svg>'
"""

from urllib.parse import quote

import requests

from badgepy.presets import custom_badge

# pypistats.org exposes recent download totals (last day/week/month) for a
# single package at this endpoint. It is a different, dedicated upstream from
# the one shields.io shares across all badge requests.
PYPISTATS_RECENT_URL = "https://pypistats.org/api/packages/{package}/recent"

# Metric aliases mirror shields.io: dd=downloads/day, dw=downloads/week,
# dm=downloads/month. Each maps to (pypistats key, human-readable period).
_METRICS: dict[str, tuple[str, str]] = {
    "dd": ("last_day", "day"),
    "dw": ("last_week", "week"),
    "dm": ("last_month", "month"),
}

_SUFFIXES = ["", "k", "M", "G", "T"]


def humanize_count(count: int) -> str:
    """Format a download count with a metric suffix, shields.io style.

    Examples: ``999`` -> ``"999"``, ``1234`` -> ``"1.2k"``,
    ``12345`` -> ``"12k"``, ``1234567`` -> ``"1.2M"``.
    """
    number = int(count)
    value = float(abs(number))
    magnitude = 0
    while value >= 1000 and magnitude < len(_SUFFIXES) - 1:
        value /= 1000
        magnitude += 1

    if magnitude == 0:
        return str(number)

    # Guard against rounding a value like 999.9 up to "1000k"; promote it to
    # the next suffix so the text stays at three characters.
    if value >= 999.5 and magnitude < len(_SUFFIXES) - 1:
        value /= 1000
        magnitude += 1

    if value >= 10:
        text = f"{value:.0f}"
    else:
        text = f"{value:.1f}".rstrip("0").rstrip(".")

    sign = "-" if number < 0 else ""
    return f"{sign}{text}{_SUFFIXES[magnitude]}"


def fetch_recent_downloads(
    package: str,
    *,
    timeout: float = 10.0,
    session: requests.Session | None = None,
) -> dict[str, int]:
    """Fetch recent download counts for a package from pypistats.org.

    Args:
        package: The PyPI project name (e.g. ``python-multipart``).
        timeout: Per-request timeout in seconds.
        session: Optional pre-configured ``requests.Session`` (useful for
            retries or custom headers in CI).

    Returns:
        A dict with ``last_day``, ``last_week`` and ``last_month`` keys.
    """
    url = PYPISTATS_RECENT_URL.format(package=quote(package, safe=""))
    getter = session.get if session is not None else requests.get
    response = getter(url, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError(f"unexpected pypistats response for {package!r}")
    return {str(key): int(value) for key, value in data.items()}


def download_count(
    package: str,
    metric: str = "dm",
    *,
    timeout: float = 10.0,
    session: requests.Session | None = None,
) -> int:
    """Return the download count for the given package and metric."""
    if metric not in _METRICS:
        raise ValueError(
            f"unknown metric {metric!r}; choose from {', '.join(_METRICS)}"
        )
    key, _period = _METRICS[metric]
    data = fetch_recent_downloads(package, timeout=timeout, session=session)
    if key not in data:
        raise KeyError(f"pypistats response missing {key!r} for {package!r}")
    return data[key]


def badge_from_pypi(
    package: str,
    metric: str = "dm",
    label: str | None = None,
    color: str = "blue",
    template: str | None = None,
    *,
    timeout: float = 10.0,
    session: requests.Session | None = None,
) -> str:
    """Generate a download-count badge for a PyPI package.

    Args:
        package: The PyPI project name.
        metric: One of ``dd`` (day), ``dw`` (week), ``dm`` (month).
        label: Left-hand label (defaults to ``downloads``).
        color: Badge color (defaults to ``blue``).
        template: Optional right-hand template. ``{value}`` expands to the
            humanized count, ``{count}`` to the raw integer, and ``{period}``
            to ``day``/``week``/``month``. Defaults to ``{value}/{period}``.

    Returns:
        SVG string of the badge.
    """
    if metric not in _METRICS:
        raise ValueError(
            f"unknown metric {metric!r}; choose from {', '.join(_METRICS)}"
        )
    _key, period = _METRICS[metric]
    count = download_count(package, metric, timeout=timeout, session=session)
    humanized = humanize_count(count)
    message = (template or "{value}/{period}").format(
        value=humanized, count=count, period=period
    )
    return custom_badge(label=label or "downloads", message=message, color=color)
