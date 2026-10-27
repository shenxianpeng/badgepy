# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Releases up to and including 1.3.0 are listed on the
[GitHub releases page](https://github.com/shenxianpeng/badgepy/releases).

## [Unreleased]

## [2.0.1] - 2026-10-27

Adds Python 3.15. There are no API or output changes, so upgrading from 2.0.0
needs no code changes.

### Added

- Python 3.15 support. The test suite now runs on 3.15 in CI, and the package
  declares it on PyPI.
  ([#58](https://github.com/shenxianpeng/badgepy/pull/58))

## [2.0.0] - 2026-10-15

The first release to require Python 3.10, and the one that closes every open
feature request left behind when [google/pybadges](https://github.com/google/pybadges)
was archived in August 2025.

### Upgrading from 1.x

1. **Python 3.9 no longer works.** Move to 3.10 or later before upgrading.
2. **Badges that set a part title or a center image render different SVG.**
   The markup changed to fix the two bugs described under *Fixed* below. If you
   store generated SVGs in version control, expect a diff on those badges, and
   regenerate them. Badges without part titles or a center image are byte-for-byte
   unchanged.
3. **Nothing else breaks.** `badge()` keeps every 1.x argument with its previous
   default, and the CLI keeps every 1.x flag.

Coming from pybadges rather than badgepy 1.x? See the
[migration guide](docs/pybadges-migration.md).

### Added

- `--style` on the command line and `style=` on `badge()`, selecting `flat`
  (the default, unchanged from 1.x) or `flat-square` (square corners, no
  gradient). The accepted values are exported as `badgepy.STYLES`. An unknown
  style raises `ValueError`.
  ([#53](https://github.com/shenxianpeng/badgepy/pull/53),
  upstream [google/pybadges#28](https://github.com/google/pybadges/issues/28))
- Badges from structured local data, via the `from-json`, `from-toml`,
  `from-pyproject` and `from-lock` subcommands. The first three take `--query`
  to pick a value out of the document and `--thresholds` to color it by that
  value; `from-lock` reads a named package out of a `uv.lock` or `poetry.lock`.
  All four take `--label` / `--template` to shape the badge, and `--on-error`
  (`raise`, `badge` or `hide`) with `--error-message` / `--error-color` to
  choose between failing and emitting a fallback badge.
  ([#32](https://github.com/shenxianpeng/badgepy/pull/32))
- A `progress` preset, for percentage or numerator/denominator progress badges
  (`--numerator`, `--denominator`, `--message`).
  ([#32](https://github.com/shenxianpeng/badgepy/pull/32))
- `--logo-width` / `logo_width=` to size the logo image, and `--font-family` /
  `font_family=` to set the SVG `font-family`. Both default to the values 1.x
  hard-coded, so existing badges are unaffected.
  ([#32](https://github.com/shenxianpeng/badgepy/pull/32))
- A [pybadges migration guide](docs/pybadges-migration.md), plus guides for
  [CI integration](docs/ci-integration.md) and
  [migrating from shields.io](docs/shields-migration.md).
  ([#32](https://github.com/shenxianpeng/badgepy/pull/32),
  [#47](https://github.com/shenxianpeng/badgepy/pull/47))

### Changed

- Remote logos requested with `embed_logo` / `--embed-logo` now time out after
  10 seconds instead of waiting indefinitely, so an unresponsive host can no
  longer block the caller. A timeout raises `requests.Timeout`.
  ([#47](https://github.com/shenxianpeng/badgepy/pull/47))
- Those requests now send a User-Agent identifying badgepy
  (`badgepy/<version> (+https://github.com/shenxianpeng/badgepy) python-requests/<version>`)
  rather than the bare `python-requests` one. Hosts such as Wikimedia reject the
  generic agent, so embedding a logo from Wikipedia works now.
  ([#52](https://github.com/shenxianpeng/badgepy/pull/52),
  upstream [google/pybadges#40](https://github.com/google/pybadges/issues/40))

### Fixed

- `left_title`, `right_title` and `center_title` are shown when hovering that
  part of the badge. They used to sit on background shapes that the gradient and
  text covered, so browsers only ever showed `whole_title`. The titles now live
  on transparent hit areas drawn above everything else. **This changes the SVG
  output of badges that set a part title.**
  ([#51](https://github.com/shenxianpeng/badgepy/pull/51),
  upstream [google/pybadges#26](https://github.com/google/pybadges/issues/26))
- A badge with a `center_image` but no `center_link` or `whole_link` no longer
  renders `<a xlink:href="None">`, a link to the relative URL `None`.
  **This changes the SVG output of such badges.**
  ([#51](https://github.com/shenxianpeng/badgepy/pull/51))
- Color values wrapped in quotes, such as `"'#c00'"`, are unquoted before use
  instead of producing an invalid SVG color. This is what made the README's
  `--right-color='#c00'` example render dark.
  ([#29](https://github.com/shenxianpeng/badgepy/pull/29),
  upstream [google/pybadges#48](https://github.com/google/pybadges/issues/48))
- Passing `None` for `left_color` or `right_color` falls back to the documented
  default instead of emitting an empty `fill`.
  ([#29](https://github.com/shenxianpeng/badgepy/pull/29))

### Removed

- Python 3.9 support. `requires-python` is now `>=3.10`, 3.9 is gone from the CI
  matrix, and the source uses PEP 604 unions (`X | None`) throughout.
  ([#34](https://github.com/shenxianpeng/badgepy/pull/34),
  [#44](https://github.com/shenxianpeng/badgepy/pull/44))

[Unreleased]: https://github.com/shenxianpeng/badgepy/compare/v2.0.1...HEAD
[2.0.1]: https://github.com/shenxianpeng/badgepy/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/shenxianpeng/badgepy/compare/v1.3.0...v2.0.0
