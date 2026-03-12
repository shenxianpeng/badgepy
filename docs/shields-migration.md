# Migrating from shields.io to badgepy

badgepy can serve as a local replacement for shields.io static badges, giving you full control without external dependencies.

## Why migrate?

- **No external dependency**: badges are generated locally, no network requests to shields.io
- **CI-friendly**: generate badges as part of your build pipeline
- **Customizable**: full control over colors, labels, and output
- **Offline**: works without internet access

## URL mapping

| shields.io URL | badgepy CLI command |
|---|---|
| `https://img.shields.io/badge/build-passing-brightgreen` | `badgepy preset build passing` |
| `https://img.shields.io/badge/coverage-85%25-green` | `badgepy preset coverage 85` |
| `https://img.shields.io/badge/version-v1.2.3-blue` | `badgepy preset version v1.2.3` |
| `https://img.shields.io/badge/license-MIT-blue` | `badgepy preset license MIT` |
| `https://img.shields.io/badge/any_label-any_message-orange` | `badgepy preset custom "any message" --label "any label" --color orange` |

## Python API mapping

shields.io static badge:
```
https://img.shields.io/badge/{label}-{message}-{color}
```

badgepy equivalent:
```python
from badgepy.presets import custom_badge
svg = custom_badge(label="label", message="message", color="color")
```

## Using the Flask server as a drop-in replacement

The badgepy server example provides a shields.io-compatible URL endpoint:

```bash
cd server-example
flask run --port 8080
```

Then replace shields.io URLs in your markdown:

```diff
- ![build](https://img.shields.io/badge/build-passing-brightgreen)
+ ![build](http://localhost:8080/badge/build-passing-brightgreen)
```

The URL format is: `/badge/{label}-{message}-{color}`

## Generating badges from CI reports

Unlike shields.io, badgepy can parse CI artifacts directly:

```bash
# From JUnit XML test reports
badgepy from-junit test-results.xml -o badges/tests.svg

# From Cobertura XML coverage reports
badgepy from-coverage coverage.xml -o badges/coverage.svg

# From generic key-value files
badgepy from-generic metrics.json --output-dir badges/
```

## Preset badges reference

| Preset | Usage | Auto-coloring |
|---|---|---|
| `build` | `badgepy preset build <status>` | passing=brightgreen, failing=red, error=red, pending=yellow |
| `coverage` | `badgepy preset coverage <percentage>` | 90+=brightgreen, 80+=green, 70+=yellowgreen, 60+=yellow, 40+=orange, <40=red |
| `version` | `badgepy preset version <version>` | blue |
| `license` | `badgepy preset license <license>` | blue |
| `custom` | `badgepy preset custom <message> --label <label> --color <color>` | user-specified |
