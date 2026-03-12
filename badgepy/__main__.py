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
    )
    _output_badge(badge, args)


def _cmd_preset(args: argparse.Namespace) -> None:
    """Generate a badge from a preset recipe."""
    from badgepy import presets

    preset_type = args.preset_type

    if preset_type == "build":
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
        choices=["build", "coverage", "version", "license", "custom"],
        help="the type of preset badge to generate",
    )
    preset_parser.add_argument(
        "value",
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
        "-o", "--output", default=None,
        help="write the badge to a file",
    )
    junit_parser.add_argument(
        "--output-dir", default=None,
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
        "-o", "--output", default=None,
        help="write the badge to a file",
    )
    cov_parser.add_argument(
        "--output-dir", default=None,
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
        "--output-dir", default=None,
        help="write all badges to a directory",
    )
    generic_parser.add_argument(
        "--color", default=None,
        help="badge color (default: blue)",
    )

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


if __name__ == "__main__":
    main()
