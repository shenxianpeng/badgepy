# badgepy, anybadge, genbadge and pybadges compared

All four are Python tools that write shields.io-style SVG badges. They differ mostly in
where the badge value comes from and how much of the badge you can customize. This page
helps you pick one; it was written by the badgepy maintainer, so check the numbers against
each project if it matters to you.

Versions compared: badgepy 2.0.1, anybadge 1.16.0, genbadge 1.1.3, pybadges 3.0.1
(November 2026).

## At a glance

| | badgepy | anybadge | genbadge | pybadges |
|---|---|---|---|---|
| **Latest release** | 2.0.1 (Oct 2026) | 1.16.0 (Jan 2025) | 1.1.3 (Nov 2025) | 3.0.1 (Oct 2023), archived Aug 2025 |
| **Python** | 3.10–3.15 | 3.7+ | no declared limit | fails to import on 3.13+ |
| **Runtime dependencies** | Jinja2, requests, filetype | packaging | click, Pillow, requests, setuptools; `defusedxml` for reports (`genbadge[coverage]`, `genbadge[tests]`) | Jinja2, requests (it also imports `pkg_resources` without declaring setuptools) |
| **Where the SVG is made** | Locally | Locally | shields.io HTTP API by default, locally with `--local` | Locally |
| **Reads values from files** | JUnit XML, Cobertura XML, JSON, TOML, `pyproject.toml`, `uv.lock` / `poetry.lock`, key-value files | No, you pass the value | JUnit XML, coverage XML, flake8 statistics | No |
| **Color thresholds** | `--thresholds` on JSON/TOML values; fixed rules for JUnit and coverage | Yes: value/color pairs, built-in templates (pylint, coverage, ...), semantic versions | Fixed rules per report type | No |
| **Styles** | `flat`, `flat-square` | `default`, `gitlab-scoped`, custom SVG template | One local template | `flat` |
| **Logos, links, hover titles** | Yes: logo from a URL or embedded, links and titles per part, center image | No | No | Yes |
| **Python API** | `badgepy.badge()`, same arguments as `pybadges.badge()` | `anybadge.Badge` | Mostly a CLI | `pybadges.badge()` |
| **License** | Apache-2.0 | MIT | BSD-3-Clause | Apache-2.0 |

## Which one should I use?

- **You use pybadges today.** Use badgepy. It keeps the pybadges API, flags and SVG
  output, and fixes the `imghdr` and `pkg_resources` import errors. See the
  [pybadges Migration Guide](pybadges-migration.md).
- **Your CI already computes the number, and you only want a colored badge with as few
  dependencies as possible.** anybadge fits well: one dependency, and flexible thresholds
  including semantic versions.
- **You only need test, coverage or flake8 badges, and calling shields.io is fine.**
  genbadge reads those reports directly. Add `--local` if your CI must not call out.
- **You want badges from reports or project files without calling any service, with logos
  and links, from the command line or from Python.** Use badgepy.

## The same coverage badge in each tool

Starting from a `coverage.xml` written by `pytest --cov --cov-report=xml`:

```sh
# badgepy
pip install badgepy
badgepy from-coverage coverage.xml -o badges/coverage.svg

# genbadge (--local skips the shields.io request)
pip install "genbadge[coverage]"
genbadge coverage -i coverage.xml -o badges/coverage.svg --local

# anybadge reads no report files, so pass the percentage yourself
pip install anybadge
anybadge --label=coverage --value=85.5 --suffix=% --file=badges/coverage.svg coverage
```

For GitHub Actions, GitLab CI and Jenkins examples, see the
[CI Integration Guide](ci-integration.md).

## See also

- [Shields.io vs badgepy](../README.md#shieldsio-vs-badgepy), if you are deciding between a
  hosted badge service and generating badges yourself
- [Shields.io Migration Guide](shields-migration.md)
