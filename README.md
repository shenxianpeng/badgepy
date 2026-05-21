# badgepy

[![CI](https://github.com/shenxianpeng/badgepy/actions/workflows/ci.yml/badge.svg)](https://github.com/shenxianpeng/badgepy/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/shenxianpeng/badgepy/branch/main/graph/badge.svg)](https://codecov.io/gh/shenxianpeng/badgepy)
[![pypi](https://img.shields.io/pypi/v/badgepy.svg)](https://pypi.org/project/badgepy/)
![versions](https://img.shields.io/pypi/pyversions/badgepy.svg)

> **badgepy** is a fork of [google/pybadges](https://github.com/google/pybadges) with fixes including added support for Python 3.13 and 3.14, dropped Python 3.7/3.8 support, removal of deprecated `imghdr`, and replacement of `pkg_resources` — see [all changes](https://github.com/shenxianpeng/badgepy/pulls?q=is%3Apr+is%3Aclosed). This project is actively maintained.

badgepy is a Python library and command-line tool for generating GitHub-style badges as SVG images — no external service required. Badges are rendered locally, offline, and fully under your control.

The visual design follows the [Shields specification](https://github.com/badges/shields/blob/master/spec/SPECIFICATION.md) and is compatible with [Shields.io](https://shields.io).

## Shields.io vs badgepy

Both tools produce identical-looking badges, but they work very differently. Here's how to choose:

| | [Shields.io](https://shields.io) | badgepy |
|---|---|---|
| **How it works** | HTTP service — you request a badge URL and get back an SVG | Python library/CLI — generates SVGs locally |
| **Internet required** | Yes (or [self-host](https://github.com/badges/shields#self-hosting)) | No — works fully offline |
| **Setup** | Zero — just use a URL in your README | `pip install badgepy` |
| **Customization** | URL query parameters only | Full programmatic control in Python |
| **CI integration** | Via shields.io endpoint JSON | Native parsers for JUnit, Cobertura, generic JSON |
| **Rate limits** | Yes on shields.io (no limits if self-hosted) | None |
| **Preset badges** | Static badge only | build, coverage, version, license, custom |
| **Output** | Rendered in browser from URL | SVG string, file, or served from your own app |

**Choose Shields.io if:**
- You just need a few badges in a README and don't want to install anything
- Your badge data is already exposed via a public API
- You're comfortable with the hosted service's availability and rate limits

**Choose badgepy if:**
- You're generating badges in a CI/CD pipeline and want offline reliability
- You need programmatic control over badge generation from Python
- You're parsing local test/coverage reports (JUnit, Cobertura) into badges
- You want to serve badges from your own application
- You need zero network dependencies at badge generation time

> 💡 **Already using Shields.io static badges?** See the [Shields.io Migration Guide](docs/shields-migration.md) for a drop-in replacement path.

## Getting Started

### Installing

```sh
pip install badgepy
```

Verify the installation:

```sh
python -m badgepy --left-text=build --right-text=failure --right-color='#c00' --browser
```

You should see a badge like this in your browser:

![pip installation](tests/golden-images/build-failure.svg)

## Usage

badgepy can be used from the command line and as a Python library.

Prefer to start with the CLI? It's a great way to experiment before writing code.
Prefer to see a running server? Check out the [example Flask server](server-example).

### Command Line

Full documentation of all command-line arguments:

```sh
badgepy --help
```

A complete example demonstrating every option:

```sh
badgepy \
    --left-text=complete \
    --right-text=example \
    --left-color=green \
    --right-color='#fb3' \
    --left-link=http://www.complete.com/ \
    --right-link=http://www.example.com \
    --logo='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAD0lEQVQI12P4zwAD/xkYAA/+Af8iHnLUAAAAAElFTkSuQmCC' \
    --embed-logo \
    --whole-title="Badge Title" \
    --left-title="Left Title" \
    --right-title="Right Title" \
    --browser
```

![complete](tests/golden-images/complete.svg)

#### Logos

The `--logo` option accepts a URL:

```sh
badgepy \
    --left-text="python" \
    --right-text="3.9, 3.10, 3.11, 3.12, 3.13, 3.14" \
    --whole-link="https://www.python.org/" \
    --browser \
    --logo='https://dev.w3.org/SVG/tools/svgweb/samples/svg-files/python.svg'
```

![python](tests/golden-images/python.svg)

Use `--embed-logo` to inline the logo data directly into the SVG, saving an HTTP request at render time. This is especially useful offline or in browsers that block external image references.

![--embed-logo=yes](tests/golden-images/embedded-logo.svg)
![--embed-logo=no](tests/golden-images/no-embedded-logo.svg)

#### Titles

The `title` element is shown as a [tooltip by browsers](https://developer.mozilla.org/en-US/docs/Web/SVG/Element/title) but is currently [filtered by GitHub](https://github.com/github/markup/issues/1267).

### Library

```python
from badgepy import badge

s = badge(left_text='coverage', right_text='23%', right_color='red')
# s is a string containing the badge as an SVG image.
print(s[:40])  # => <svg height="20" width="191.0" xmlns="ht
```

Keyword arguments mirror the CLI flags, with underscores instead of hyphens (e.g. `--left-text` → `left_text=`).

#### Serving Badges from a Web App

badgepy works well behind a web server. See the [Flask example](server-example) for a minimal setup.

### Preset Badges

Common badge types with automatic color coding, no manual color picking needed:

```sh
# Build status (auto-colored: passing=brightgreen, failing=red)
badgepy preset build passing -o badges/build.svg

# Coverage (auto-colored by percentage thresholds)
badgepy preset coverage 85.3 -o badges/coverage.svg

# Version and license
badgepy preset version v1.2.3 -o badges/version.svg
badgepy preset license MIT -o badges/license.svg

# Custom badge (compatible with shields.io static badge format)
badgepy preset custom "linux" --label platform --color green -o badges/platform.svg
```

From Python:

```python
from badgepy.presets import build_badge, coverage_badge, custom_badge

svg = build_badge('passing')
svg = coverage_badge(85.3)
svg = custom_badge(label='platform', message='linux', color='green')
```

### CI Report Badges

Generate badges directly from test and coverage report files — no external API needed:

```sh
# From JUnit XML (pytest, JUnit, Go, etc.)
badgepy from-junit test-results.xml -o badges/tests.svg

# From Cobertura XML (coverage.py, gcov, JaCoCo, etc.)
badgepy from-coverage coverage.xml -o badges/coverage.svg

# From generic key-value or JSON files
badgepy from-generic metrics.json --output-dir badges/
```

From Python:

```python
from badgepy.parsers import badges_from_junit, badges_from_coverage

badges = badges_from_junit('test-results.xml')   # {'tests': '<svg...>'}
badges = badges_from_coverage('coverage.xml')    # {'coverage': '<svg...>', 'branch-coverage': '<svg...>'}
```

See the [CI Integration Guide](docs/ci-integration.md) for GitHub Actions, GitLab CI, and Jenkins examples.

### Output to File

Use `-o` / `--output` to write badges to a file instead of stdout:

```sh
badgepy --left-text=build --right-text=passing --right-color=green -o badges/build.svg
```

## Caveats

- **Text measurement**: badgepy uses a pre-calculated table of text widths and [kerning](https://en.wikipedia.org/wiki/Kerning) distances for western glyphs. Eastern European languages may not render as accurately:

  ![saying-russian](tests/golden-images/saying-russian.svg)

  Glyphs not present in Deja Vu Sans (the default font) may render poorly:

  ![saying-chinese](tests/golden-images/saying-chinese.svg)

- **Right-to-left languages**: Arabic, Hebrew, and other RTL scripts are not explicitly supported; the text direction may be incorrect:

  ![saying-arabic](tests/golden-images/saying-arabic.svg)

## Development

```sh
git clone https://github.com/shenxianpeng/badgepy.git
cd badgepy
python -m venv venv
source venv/bin/activate
pip install -e .[dev]
nox
```

Contributions are welcome! Please read the [contributor guide](CONTRIBUTING.md) before submitting a PR.

## Versioning

This project follows [SemVer](http://semver.org/).

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
