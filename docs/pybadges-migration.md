# Migrating from pybadges to badgepy

badgepy is the maintained continuation of [google/pybadges](https://github.com/google/pybadges),
which was archived in June 2024 (its last release, 3.0.1, dates from October 2023).
The `badge()` API and the command-line flags are unchanged, so for most projects
migrating is a one-line dependency change plus a find-and-replace of the import.

## Why migrate?

pybadges 3.0.1 no longer imports on current Python environments:

| Environment | `import pybadges` |
|---|---|
| Python 3.13+ | `ModuleNotFoundError: No module named 'imghdr'` — `imghdr` was removed from the standard library ([PEP 594](https://peps.python.org/pep-0594/)) |
| Python 3.12 and earlier, without setuptools or with a setuptools release that no longer ships `pkg_resources` (e.g. 84.0.0) | `ModuleNotFoundError: No module named 'pkg_resources'` |

Note that virtual environments created with Python 3.12+ no longer include setuptools
by default, so the second failure can appear even before you upgrade Python.

badgepy removes both dependencies, supports Python 3.10–3.14, and is actively maintained.

## Step 1: Update your dependencies

```diff
- pybadges==3.0.1
+ badgepy>=1.3.0
```

The optional Pillow-based text measurer keeps the same extra name:

```diff
- pybadges[pil-measurement]
+ badgepy[pil-measurement]
```

> [!NOTE]
> badgepy 2.0 and later require Python 3.10+. If you still need Python 3.9, pin `badgepy>=1.3,<2`.

## Step 2: Update imports

```diff
- from pybadges import badge
+ from badgepy import badge
```

`badgepy.badge()` accepts every pybadges argument, in the same order, so existing calls
(including positional ones) work unchanged. It adds two optional keyword arguments,
`logo_width` and `font_family`.

| pybadges | badgepy |
|---|---|
| `pybadges.badge` | `badgepy.badge` |
| `pybadges.text_measurer` | `badgepy.text_measurer` |
| `pybadges.precalculated_text_measurer` | `badgepy.precalculated_text_measurer` |
| `pybadges.pil_text_measurer` | `badgepy.pil_text_measurer` |
| `pybadges.precalculate_text` | `badgepy.precalculate_text` |
| `pybadges.version.__version__` | `importlib.metadata.version("badgepy")` |

To rename every reference in a repository at once:

```sh
git grep -l pybadges -- '*.py' | xargs perl -pi -e 's/\bpybadges\b/badgepy/g'
```

Review the result afterwards: `pybadges.version` has no badgepy equivalent module and
should be replaced with `importlib.metadata.version("badgepy")` as shown above.

## Step 3: Update command-line usage

```diff
- python -m pybadges --left-text=build --right-text=passing --right-color=green
+ badgepy --left-text=build --right-text=passing --right-color=green
```

`python -m badgepy` works as well. All pybadges flags are supported with the same meaning.

## What stays the same

- **Rendered output**: for the same arguments, badgepy produces the same SVG markup as
  pybadges 3.0.1, so golden-image tests and cached badges keep matching.
- **Text measurement**: the same pre-calculated DejaVu Sans width table is used by default,
  and the Pillow measurer is still available via `--use-pil-text-measurer`.

## Behavior changes

- **Remote logo timeout**: when `embed_logo=True` (or `--embed-logo`) fetches an HTTP/HTTPS
  logo, badgepy gives up after 10 seconds and raises `requests.Timeout`. pybadges waited
  indefinitely, which could block a web server worker.
- **Remote logo User-Agent**: logo requests identify themselves as
  `badgepy/<version> (+https://github.com/shenxianpeng/badgepy) python-requests/<version>`.
  Hosts such as Wikimedia reject the generic `python-requests` User-Agent that pybadges
  sent, so embedding a logo from Wikipedia now works
  ([google/pybadges#40](https://github.com/google/pybadges/issues/40)).
- **Quoted colors**: color values wrapped in quotes, such as `"'#c00'"`, are unquoted
  before use instead of producing an invalid SVG color.

## What you get in addition

Beyond the pybadges feature set, badgepy can generate badges from local data without any
external service:

- [Preset badges](../README.md#preset-badges) for build, coverage, version, license and progress
- [CI report badges](../README.md#ci-report-badges) from JUnit and Cobertura XML files
- Badges from JSON, TOML, `pyproject.toml` and lock files
- Writing badges straight to a file with `-o` / `--output`

If something that worked with pybadges behaves differently in badgepy, please
[open an issue](https://github.com/shenxianpeng/badgepy/issues).
