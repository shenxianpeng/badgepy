# Copyright 2018 The pybadge Authors
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
"""Output a github-style badge as an SVG image given some text and colors.

For more information, run:
$ python3 -m badgepy --help
"""

import argparse
import sys
import tempfile
import webbrowser
import badgepy
from importlib.metadata import version

from badgepy.output import write_badge


def _output_badge(svg: str, args: argparse.Namespace) -> None:
    """Write badge SVG to the destination specified by args."""
    if getattr(args, "output", None):
        path = write_badge(svg, args.output)
        print(f"Badge written to {path}", file=sys.stderr)
    elif getattr(args, "browser", False):
        _, badge_path = tempfile.mkstemp(suffix=".svg")
        with open(badge_path, "w") as f:
            f.write(svg)
        webbrowser.open_new_tab("file://" + badge_path)
    else:
        print(svg, end="")


def _add_output_args(parser: argparse.ArgumentParser) -> None:
    """Add --output and --browser arguments to a parser."""
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="write the badge to a file instead of stdout",
    )
    parser.add_argument(
        "--browser",
        action="store_true",
        default=False,
        help="display the badge in a browser tab",
    )


def _cmd_badge(args: argparse.Namespace) -> None:
    """Generate a badge from explicit left/right text and colors."""
    if (args.left_link or args.right_link or args.center_link) and args.whole_link:
        print(
            "argument --whole-link: cannot be set with "
            + "--left-link, --right-link, or --center-link",
            file=sys.stderr,
        )
        sys.exit(1)

    measurer = None
    if args.use_pil_text_measurer:
        if args.deja_vu_sans_path is None:
            print(
                "argument --use-pil-text-measurer: must also set "
                + "--deja-vu-sans-path",
                file=sys.stderr,
            )
            sys.exit(1)
        from badgepy import pil_text_measurer

        measurer = pil_text_measurer.PilMeasurer(args.deja_vu_sans_path)

    badge = badgepy.badge(
        left_text=args.left_text,
        right_text=args.right_text,
        left_link=args.left_link,
        right_link=args.right_link,
        center_link=args.center_link,
        whole_link=args.whole_link,
        logo=args.logo,
        left_color=args.left_color,
        right_color=args.right_color,
        center_color=args.center_color,
        measurer=measurer,
        left_title=args.left_title,
        right_title=args.right_title,
        center_title=args.center_title,
        whole_title=args.whole_title,
        right_image=args.right_image,
        center_image=args.center_image,
        embed_logo=args.embed_logo,
        embed_right_image=args.embed_right_image,
        embed_center_image=args.embed_center_image,
        logo_width=args.logo_width,
        font_family=args.font_family,
    )
    _output_badge(badge, args)


def _cmd_preset(args: argparse.Namespace) -> None:
    """Generate a badge from a preset recipe."""
    from badgepy import presets

    preset_type = args.preset_type

    if preset_type == "progress":
        value = float(args.value) if args.value is not None else None
        svg = presets.progress_badge(
            value,
            label=args.label or "progress",
            numerator=args.numerator,
            denominator=args.denominator,
            message=args.message,
        )
    elif args.value is None:
        print(f"preset {preset_type!r} requires a value", file=sys.stderr)
        sys.exit(1)
    elif preset_type == "build":
        svg = presets.build_badge(args.value, label=args.label or "build")
    elif preset_type == "coverage":
        svg = presets.coverage_badge(float(args.value), label=args.label or "coverage")
    elif preset_type == "version":
        svg = presets.version_badge(args.value, label=args.label or "version")
    elif preset_type == "license":
        svg = presets.license_badge(args.value, label=args.label or "license")
    elif preset_type == "custom":
        svg = presets.custom_badge(
            label=args.label or "badge",
            message=args.value,
            color=args.color or "blue",
        )
    else:
        print(f"unknown preset type: {preset_type}", file=sys.stderr)
        sys.exit(1)

    _output_badge(svg, args)


def _cmd_from_junit(args: argparse.Namespace) -> None:
    """Generate badges from a JUnit XML report."""
    from badgepy.parsers.junit import badges_from_junit
    from badgepy.output import write_badges

    badges = badges_from_junit(args.file)

    if args.output_dir:
        paths = write_badges(badges, args.output_dir)
        for p in paths:
            print(f"Badge written to {p}", file=sys.stderr)
    elif args.output:
        # Write just the tests badge to --output
        write_badge(badges["tests"], args.output)
        print(f"Badge written to {args.output}", file=sys.stderr)
    else:
        print(badges["tests"], end="")


def _cmd_from_coverage(args: argparse.Namespace) -> None:
    """Generate badges from a Cobertura XML coverage report."""
    from badgepy.parsers.coverage import badges_from_coverage
    from badgepy.output import write_badges

    badges = badges_from_coverage(args.file)

    if args.output_dir:
        paths = write_badges(badges, args.output_dir)
        for p in paths:
            print(f"Badge written to {p}", file=sys.stderr)
    elif args.output:
        write_badge(badges["coverage"], args.output)
        print(f"Badge written to {args.output}", file=sys.stderr)
    else:
        print(badges["coverage"], end="")


def _cmd_from_generic(args: argparse.Namespace) -> None:
    """Generate badges from a generic key-value or JSON file."""
    from badgepy.parsers.generic import badges_from_generic
    from badgepy.output import write_badges

    badges = badges_from_generic(args.file, color=args.color or "blue")

    if args.output_dir:
        paths = write_badges(badges, args.output_dir)
        for p in paths:
            print(f"Badge written to {p}", file=sys.stderr)
    else:
        for name, svg in badges.items():
            print(f"--- {name} ---")
            print(svg)


def _fallback_badge(args: argparse.Namespace) -> str:
    """Generate the configured fallback badge for structured data errors."""
    from badgepy.presets import empty_badge, error_badge

    if args.on_error == "hide":
        return empty_badge()
    label = args.label or args.query or "badge"
    return error_badge(label=label, message=args.error_message, color=args.error_color)


def _cmd_from_structured(args: argparse.Namespace, input_format: str) -> None:
    """Generate a badge from JSON or TOML data."""
    from badgepy.parsers.structured import badge_from_structured_data

    try:
        svg = badge_from_structured_data(
            args.file,
            label=args.label,
            query=args.query,
            color=args.color or "blue",
            template=args.template,
            thresholds=args.thresholds,
            input_format=input_format,
        )
    except Exception as exc:
        if args.on_error == "raise":
            print(f"failed to generate badge: {exc}", file=sys.stderr)
            sys.exit(1)
        svg = _fallback_badge(args)

    _output_badge(svg, args)


def _cmd_from_pypi(args: argparse.Namespace) -> None:
    """Generate a PyPI download-count badge from pypistats.org."""
    from badgepy.parsers.pypi import badge_from_pypi

    try:
        svg = badge_from_pypi(
            args.package,
            metric=args.metric,
            label=args.label,
            color=args.color or "blue",
            template=args.template,
            timeout=args.timeout,
        )
    except Exception as exc:
        if args.on_error == "raise":
            print(f"failed to generate badge: {exc}", file=sys.stderr)
            sys.exit(1)
        args.query = args.label or "downloads"
        svg = _fallback_badge(args)

    _output_badge(svg, args)


def _cmd_from_lock(args: argparse.Namespace) -> None:
    """Generate a package badge from a uv.lock or poetry.lock file."""
    from badgepy.parsers.structured import badge_from_lock

    try:
        svg = badge_from_lock(
            args.file,
            args.package,
            label=args.label,
            color=args.color or "blue",
            template=args.template,
        )
    except Exception as exc:
        if args.on_error == "raise":
            print(f"failed to generate badge: {exc}", file=sys.stderr)
            sys.exit(1)
        args.query = args.package
        svg = _fallback_badge(args)

    _output_badge(svg, args)


def main():
    parser = argparse.ArgumentParser(
        "badgepy",
        description="generate github-style badges from text, CI reports, or presets",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=version("badgepy")),
    )

    subparsers = parser.add_subparsers(dest="command")

    # ── Default badge generation (backward-compatible) ──
    # When no subcommand is given, use the original flag-based interface.
    # The arguments below are added directly to the main parser for
    # backward compatibility.
    parser.add_argument(
        "--left-text",
        default="license",
        help="the text to show on the left-hand-side of the badge",
    )
    parser.add_argument(
        "--right-text",
        default=None,
        help="the text to show on the right-hand-side of the badge",
    )
    parser.add_argument(
        "--left-link",
        default=None,
        help="the url to redirect to when the left-hand of the badge is clicked",
    )
    parser.add_argument(
        "--right-link",
        default=None,
        help="the url to redirect to when the right-hand of the badge is clicked",
    )
    parser.add_argument(
        "--center-link",
        default=None,
        help="the url to redirect to when the center of the badge is clicked",
    )
    parser.add_argument(
        "--whole-link",
        default=None,
        help="the url to redirect to when the badge is clicked",
    )
    parser.add_argument(
        "--logo", default=None, help="a URI reference to a logo to display in the badge"
    )
    parser.add_argument(
        "--logo-width",
        type=float,
        default=14,
        help="the SVG width to use for the logo image",
    )
    parser.add_argument(
        "--font-family",
        default="DejaVu Sans,Verdana,Geneva,sans-serif",
        help="the SVG font-family value for badge text",
    )
    parser.add_argument(
        "--left-color",
        default="#555",
        help="the background color of the left-hand-side of the badge",
    )
    parser.add_argument(
        "--right-color",
        default="#007ec6",
        help="the background color of the right-hand-side of the badge",
    )
    parser.add_argument(
        "--center-color",
        default=None,
        help="the background color of the center of the badge",
    )
    parser.add_argument(
        "--use-pil-text-measurer",
        action="store_true",
        default=False,
        help="use the PilMeasurer to measure the length of text (kerning may "
        "be more precise for non-Western languages. "
        + "--deja-vu-sans-path must also be set.",
    )
    parser.add_argument(
        "--deja-vu-sans-path",
        default=None,
        help="the path to the ttf font file containing DejaVu Sans. If not "
        + "present on your system, you can download it from "
        + "https://www.fontsquirrel.com/fonts/dejavu-sans",
    )
    parser.add_argument(
        "--left-title",
        default=None,
        help="the title to associate with the left part of the badge",
    )
    parser.add_argument(
        "--right-title",
        default=None,
        help="the title to associate with the right part of the badge",
    )
    parser.add_argument(
        "--center-title",
        default=None,
        help="the title to associate with the center part of the badge",
    )
    parser.add_argument(
        "--whole-title",
        default=None,
        help="the title to associate with the entire badge",
    )
    parser.add_argument(
        "--right-image",
        default=None,
        help="the image to associate with the right-hand side of the badge",
    )
    parser.add_argument(
        "--center-image",
        default=None,
        help="the image to associate with the center of the badge",
    )
    parser.add_argument(
        "--embed-logo",
        nargs="?",
        type=lambda x: x.lower() in ["y", "yes", "t", "true", "1", ""],
        const="yes",
        default="no",
        help="embed the logo image directly in the badge SVG",
    )
    parser.add_argument(
        "--embed-right-image",
        nargs="?",
        type=lambda x: x.lower() in ["y", "yes", "t", "true", "1", ""],
        const="yes",
        default="no",
        help="embed the right image directly in the badge SVG",
    )
    parser.add_argument(
        "--embed-center-image",
        nargs="?",
        type=lambda x: x.lower() in ["y", "yes", "t", "true", "1", ""],
        const="yes",
        default="no",
        help="embed the center image directly in the badge SVG",
    )
    _add_output_args(parser)

    # ── preset subcommand ──
    preset_parser = subparsers.add_parser(
        "preset",
        help="generate a badge from a preset recipe",
        description="Generate badges using preset recipes like build, coverage, version, etc.",
    )
    preset_parser.add_argument(
        "preset_type",
        choices=["build", "coverage", "version", "license", "custom", "progress"],
        help="the type of preset badge to generate",
    )
    preset_parser.add_argument(
        "value",
        nargs="?",
        help="the value for the badge (e.g. 'passing', '85.3', 'v1.0.0')",
    )
    preset_parser.add_argument(
        "--label",
        default=None,
        help="override the default left-hand label text",
    )
    preset_parser.add_argument(
        "--color",
        default=None,
        help="override the badge color (for custom preset)",
    )
    preset_parser.add_argument(
        "--numerator",
        type=float,
        default=None,
        help="numerator for progress badges",
    )
    preset_parser.add_argument(
        "--denominator",
        type=float,
        default=None,
        help="denominator for progress badges",
    )
    preset_parser.add_argument(
        "--message",
        default=None,
        help="override the right-hand text for progress badges",
    )
    _add_output_args(preset_parser)

    # ── from-junit subcommand ──
    junit_parser = subparsers.add_parser(
        "from-junit",
        help="generate badges from a JUnit XML report",
        description="Parse a JUnit XML test report and generate test result badges.",
    )
    junit_parser.add_argument(
        "file",
        help="path to the JUnit XML file",
    )
    junit_parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="write the badge to a file",
    )
    junit_parser.add_argument(
        "--output-dir",
        default=None,
        help="write all badges to a directory",
    )

    # ── from-coverage subcommand ──
    cov_parser = subparsers.add_parser(
        "from-coverage",
        help="generate badges from a Cobertura XML coverage report",
        description="Parse a Cobertura XML coverage report and generate coverage badges.",
    )
    cov_parser.add_argument(
        "file",
        help="path to the Cobertura XML file",
    )
    cov_parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="write the badge to a file",
    )
    cov_parser.add_argument(
        "--output-dir",
        default=None,
        help="write all badges to a directory",
    )

    # ── from-generic subcommand ──
    generic_parser = subparsers.add_parser(
        "from-generic",
        help="generate badges from a key-value or JSON file",
        description="Parse a generic key=value or JSON file and generate a badge per entry.",
    )
    generic_parser.add_argument(
        "file",
        help="path to the key-value or JSON file",
    )
    generic_parser.add_argument(
        "--output-dir",
        default=None,
        help="write all badges to a directory",
    )
    generic_parser.add_argument(
        "--color",
        default=None,
        help="badge color (default: blue)",
    )

    def add_structured_parser(name: str, fmt: str) -> None:
        structured_parser = subparsers.add_parser(
            name,
            help=f"generate a badge from a {fmt.upper()} file",
            description=f"Select data from a local {fmt.upper()} file and render a badge.",
        )
        structured_parser.add_argument(
            "file",
            help=f"path to the {fmt.upper()} file",
        )
        structured_parser.add_argument(
            "--query",
            default=None,
            help="dot path to select, e.g. project.version or items[0].name",
        )
        structured_parser.add_argument(
            "--label",
            default=None,
            help="left-hand badge label",
        )
        structured_parser.add_argument(
            "--template",
            default=None,
            help="right-hand template using {value} or input paths",
        )
        structured_parser.add_argument(
            "--thresholds",
            default=None,
            help="numeric color thresholds, e.g. 90:brightgreen,60:yellow,0:red",
        )
        structured_parser.add_argument(
            "--color",
            default=None,
            help="badge color when thresholds do not apply (default: blue)",
        )
        structured_parser.add_argument(
            "--on-error",
            choices=["raise", "badge", "hide"],
            default="raise",
            help="how to handle parse/query errors",
        )
        structured_parser.add_argument(
            "--error-message",
            default="unknown",
            help="fallback badge message for --on-error=badge",
        )
        structured_parser.add_argument(
            "--error-color",
            default="lightgrey",
            help="fallback badge color for --on-error=badge",
        )
        _add_output_args(structured_parser)

    add_structured_parser("from-json", "json")
    add_structured_parser("from-toml", "toml")

    pyproject_parser = subparsers.add_parser(
        "from-pyproject",
        help="generate a badge from pyproject.toml",
        description="Select data from pyproject.toml and render a badge.",
    )
    pyproject_parser.add_argument(
        "file",
        nargs="?",
        default="pyproject.toml",
        help="path to pyproject.toml (default: pyproject.toml)",
    )
    pyproject_parser.add_argument(
        "--query",
        default="project.version",
        help="dot path to select (default: project.version)",
    )
    pyproject_parser.add_argument(
        "--label",
        default="version",
        help="left-hand badge label (default: version)",
    )
    pyproject_parser.add_argument(
        "--template",
        default=None,
        help="right-hand template using {value} or input paths",
    )
    pyproject_parser.add_argument(
        "--thresholds",
        default=None,
        help="numeric color thresholds, e.g. 90:brightgreen,60:yellow,0:red",
    )
    pyproject_parser.add_argument(
        "--color",
        default=None,
        help="badge color when thresholds do not apply (default: blue)",
    )
    pyproject_parser.add_argument(
        "--on-error",
        choices=["raise", "badge", "hide"],
        default="raise",
        help="how to handle parse/query errors",
    )
    pyproject_parser.add_argument(
        "--error-message",
        default="unknown",
        help="fallback badge message for --on-error=badge",
    )
    pyproject_parser.add_argument(
        "--error-color",
        default="lightgrey",
        help="fallback badge color for --on-error=badge",
    )
    _add_output_args(pyproject_parser)

    lock_parser = subparsers.add_parser(
        "from-lock",
        help="generate a package version badge from uv.lock or poetry.lock",
        description="Find a package in a local uv.lock or poetry.lock file.",
    )
    lock_parser.add_argument(
        "file",
        help="path to uv.lock or poetry.lock",
    )
    lock_parser.add_argument(
        "package",
        help="package name to read from the lock file",
    )
    lock_parser.add_argument(
        "--label",
        default=None,
        help="left-hand badge label (default: package name)",
    )
    lock_parser.add_argument(
        "--template",
        default=None,
        help="right-hand template using {value} or package fields",
    )
    lock_parser.add_argument(
        "--color",
        default=None,
        help="badge color (default: blue)",
    )
    lock_parser.add_argument(
        "--on-error",
        choices=["raise", "badge", "hide"],
        default="raise",
        help="how to handle missing package or parse errors",
    )
    lock_parser.add_argument(
        "--error-message",
        default="unknown",
        help="fallback badge message for --on-error=badge",
    )
    lock_parser.add_argument(
        "--error-color",
        default="lightgrey",
        help="fallback badge color for --on-error=badge",
    )
    _add_output_args(lock_parser)

    # ── from-pypi subcommand ──
    pypi_parser = subparsers.add_parser(
        "from-pypi",
        help="generate a PyPI download-count badge from pypistats.org",
        description=(
            "Fetch download counts from pypistats.org and render a static "
            "badge. Run this in CI to avoid shields.io's shared upstream "
            "rate limits at display time."
        ),
    )
    pypi_parser.add_argument(
        "package",
        help="the PyPI project name, e.g. python-multipart",
    )
    pypi_parser.add_argument(
        "--metric",
        choices=["dd", "dw", "dm"],
        default="dm",
        help="downloads per day (dd), week (dw), or month (dm); default: dm",
    )
    pypi_parser.add_argument(
        "--label",
        default=None,
        help="left-hand badge label (default: downloads)",
    )
    pypi_parser.add_argument(
        "--template",
        default=None,
        help="right-hand template using {value}, {count}, or {period}",
    )
    pypi_parser.add_argument(
        "--color",
        default=None,
        help="badge color (default: blue)",
    )
    pypi_parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP request timeout in seconds (default: 10)",
    )
    pypi_parser.add_argument(
        "--on-error",
        choices=["raise", "badge", "hide"],
        default="raise",
        help="how to handle fetch or parse errors",
    )
    pypi_parser.add_argument(
        "--error-message",
        default="unknown",
        help="fallback badge message for --on-error=badge",
    )
    pypi_parser.add_argument(
        "--error-color",
        default="lightgrey",
        help="fallback badge color for --on-error=badge",
    )
    _add_output_args(pypi_parser)

    args = parser.parse_args()

    if args.command is None:
        # No subcommand: use the original badge generation
        _cmd_badge(args)
    elif args.command == "preset":
        _cmd_preset(args)
    elif args.command == "from-junit":
        _cmd_from_junit(args)
    elif args.command == "from-coverage":
        _cmd_from_coverage(args)
    elif args.command == "from-generic":
        _cmd_from_generic(args)
    elif args.command == "from-json":
        _cmd_from_structured(args, "json")
    elif args.command == "from-toml":
        _cmd_from_structured(args, "toml")
    elif args.command == "from-pyproject":
        _cmd_from_structured(args, "toml")
    elif args.command == "from-lock":
        _cmd_from_lock(args)
    elif args.command == "from-pypi":
        _cmd_from_pypi(args)


if __name__ == "__main__":
    main()
