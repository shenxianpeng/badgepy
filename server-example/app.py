# Copyright 2020 The pybadge Authors
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
"""Example Flask server that serves badges."""

import flask
import badgepy

app = flask.Flask(__name__)


def _build_cli_cmd(b):
    """Build the CLI command string for a badge dict."""
    parts = ["badgepy"]
    parts.append(f'--left-text="{b["left_text"]}"')
    parts.append(f'--right-text="{b["right_text"]}"')
    if b.get("left_color"):
        parts.append(f'--left-color="{b["left_color"]}"')
    if b.get("right_color"):
        parts.append(f'--right-color="{b["right_color"]}"')
    if b.get("logo") and not b["logo"].startswith("data:"):
        parts.append(f'--logo="{b["logo"]}"')
    parts.append("--browser")
    return " \\\n    ".join(parts)


def _build_python_snippet(b):
    """Build the Python API snippet for a badge dict."""
    lines = ["from badgepy import badge", "", "badge("]
    lines.append(f'    left_text="{b["left_text"]}",')
    lines.append(f'    right_text="{b["right_text"]}",')
    if b.get("left_color"):
        lines.append(f'    left_color="{b["left_color"]}",')
    if b.get("right_color"):
        lines.append(f'    right_color="{b["right_color"]}",')
    if b.get("logo"):
        logo_display = b["logo"] if not b["logo"].startswith("data:") else "data:image/png;base64,..."
        lines.append(f'    logo="{logo_display}",')
    lines.append(")")
    return "\n".join(lines)


@app.route("/")
@app.route("/index")
def index():
    """Serve an HTML page containing badge images."""
    badges = [
        {
            "left_text": "Build",
            "right_text": "passing",
            "left_color": "#555",
            "right_color": "#008000",
        },
        {
            "left_text": "Build",
            "right_text": "fail",
            "left_color": "#555",
            "right_color": "#800000",
        },
        {
            "left_text": "complete",
            "right_text": "example",
            "left_color": "green",
            "right_color": "yellow",
            "logo": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAD0lEQVQI12P4zwAD/xkYAA/+Af8iHnLUAAAAAElFTkSuQmCC",
        },
    ]
    for b in badges:
        b["url"] = flask.url_for(".serve_badge", **b)
        b["python_snippet"] = _build_python_snippet(b)
        b["cli_cmd"] = _build_cli_cmd(b)
    return flask.render_template("index.html", badges=badges)


@app.route("/img")
def serve_badge():
    """Serve a badge image based on the request query string."""
    badge = badgepy.badge(
        left_text=flask.request.args.get("left_text"),
        right_text=flask.request.args.get("right_text"),
        left_color=flask.request.args.get("left_color"),
        right_color=flask.request.args.get("right_color"),
        logo=flask.request.args.get("logo"),
    )

    response = flask.make_response(badge)
    response.content_type = "image/svg+xml"
    return response


@app.route("/badge/<path:spec>")
def shields_compatible(spec):
    """Serve a badge using a shields.io-compatible URL format.

    URL format: /badge/label-message-color
    Examples:
        /badge/build-passing-brightgreen
        /badge/coverage-85%25-green
        /badge/license-MIT-blue
    """
    parts = spec.rsplit("-", 2)
    if len(parts) == 3:
        label, message, color = parts
    elif len(parts) == 2:
        label, message = parts
        color = "blue"
    else:
        label = parts[0]
        message = ""
        color = "blue"

    badge_svg = badgepy.badge(
        left_text=label,
        right_text=message,
        right_color=color,
    )
    response = flask.make_response(badge_svg)
    response.content_type = "image/svg+xml"
    return response


if __name__ == "__main__":
    app.run()
