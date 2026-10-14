# How to Contribute

Bug reports, feature requests and pull requests are all welcome. For larger
changes, please open an issue first so we can agree on the approach before you
spend time on it.

## Licensing

badgepy is licensed under the [Apache License 2.0](LICENSE). By submitting a
pull request, you agree that your contribution is licensed under the same
terms. No separate contributor license agreement is required.

## Development setup

```sh
git clone https://github.com/shenxianpeng/badgepy.git
cd badgepy
python -m venv venv
source venv/bin/activate
pip install -e .[dev]
```

## Before submitting a pull request

Run the nox sessions that CI runs:

```sh
nox -s lint unit type_check
```

- Add or update tests for any behavior change.
- If a change affects rendered badges, regenerate the golden images with
  `python build_golden_images.py` and review the SVG diffs.
- Use a [Conventional Commits](https://www.conventionalcommits.org) style pull
  request title (for example `feat: add flat-square style` or
  `fix: handle empty coverage report`); release notes are generated from them.

## Code reviews

All submissions, including those from maintainers, are reviewed through GitHub
pull requests.

## Community guidelines

Please be respectful and constructive in issues, discussions and reviews.
