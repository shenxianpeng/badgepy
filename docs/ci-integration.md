# CI Integration Guide

This guide shows how to use badgepy in CI pipelines to automatically generate badges from test results and coverage reports.

## GitHub Actions

### Use the badgepy action

The action installs badgepy in its own virtual environment, so it doesn't touch your
job's Python packages, and runs one badgepy command per line of `args`:

```yaml
- name: Run tests with coverage
  run: pytest --junitxml=results.xml --cov --cov-report=xml

- name: Generate badges
  uses: shenxianpeng/badgepy@v2.1.0
  with:
    args: |
      from-coverage coverage.xml -o badges/coverage.svg
      from-junit results.xml -o badges/tests.svg
      from-pyproject --query project.version --label version -o badges/version.svg
```

Each line takes the same arguments as the `badgepy` command, without the word `badgepy`.
Blank lines and lines starting with `#` are skipped. Quote values that contain spaces,
and use forward slashes in paths, also on Windows runners. The runner needs Python 3.10
or later on its `PATH`; GitHub-hosted runners have it, and on other runners add
`actions/setup-python` first.

The steps below install badgepy with `pip` instead, which works the same way.

### Generate badges from test results

```yaml
- name: Run tests
  run: pytest --junitxml=results.xml

- name: Generate test badge
  run: badgepy from-junit results.xml -o badges/tests.svg

- name: Upload badge artifacts
  uses: actions/upload-artifact@v4
  with:
    name: badges
    path: badges/
```

### Generate badges from coverage reports

```yaml
- name: Run tests with coverage
  run: pytest --cov --cov-report=xml

- name: Generate coverage badge
  run: badgepy from-coverage coverage.xml -o badges/coverage.svg
```

### Display badges in Job Summary

```yaml
- name: Add badges to summary
  run: |
    echo "## Build Status" >> $GITHUB_STEP_SUMMARY
    echo '![tests](badges/tests.svg)' >> $GITHUB_STEP_SUMMARY
    echo '![coverage](badges/coverage.svg)' >> $GITHUB_STEP_SUMMARY
```

### Using preset badges

```yaml
- name: Generate build badge
  run: badgepy preset build passing -o badges/build.svg

- name: Generate progress badge
  run: badgepy preset progress 75 --label docs -o badges/docs.svg

- name: Generate version badge
  run: |
    VERSION=$(python -c 'import importlib.metadata as m; print(m.version("badgepy"))')
    badgepy preset version "$VERSION" -o badges/version.svg
```

### Generate badges from local JSON/TOML data

```yaml
- name: Generate package metadata badges
  run: |
    badgepy from-pyproject --query project.name --label package -o badges/package.svg
    badgepy from-json package.json --query version --label npm -o badges/npm.svg
    badgepy from-lock uv.lock jinja2 --label jinja2 -o badges/jinja2.svg
```

Use thresholds when the selected JSON/TOML value is numeric:

```yaml
- name: Generate coverage summary badge
  run: |
    badgepy from-json coverage-summary.json \
      --query total.lines.pct \
      --label coverage \
      --template "{value}%" \
      --thresholds "90:brightgreen,80:green,60:yellow,0:red" \
      -o badges/coverage.svg
```

## pre-commit

To keep a committed badge in sync with your project, regenerate it in a
[pre-commit](https://pre-commit.com) hook. This example rebuilds a version badge
whenever `pyproject.toml` changes:

```yaml
repos:
  - repo: https://github.com/shenxianpeng/badgepy
    rev: v2.1.0
    hooks:
      - id: badgepy
        name: version badge
        args: [from-pyproject, --query, project.version, --label, version, -o, badges/version.svg]
        files: ^pyproject\.toml$
```

If the badge was out of date, the hook writes the new one and fails the commit, as
formatters do. Stage the updated badge and commit again. Add one hook entry per badge,
each with its own `args` and `files`.

## GitLab CI

### Generate and publish badges

```yaml
generate-badges:
  stage: test
  script:
    - pytest --junitxml=results.xml --cov --cov-report=xml
    - badgepy from-junit results.xml -o badges/tests.svg
    - badgepy from-coverage coverage.xml -o badges/coverage.svg
  artifacts:
    paths:
      - badges/
    reports:
      junit: results.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

### Use as project badges

In GitLab, go to **Settings > General > Badges** and point the badge image URL to your pipeline artifact:

```
https://gitlab.com/your-project/-/jobs/artifacts/main/raw/badges/coverage.svg?job=generate-badges
```

## Jenkins

### Pipeline example

```groovy
pipeline {
    agent any
    stages {
        stage('Test') {
            steps {
                sh 'pytest --junitxml=results.xml --cov --cov-report=xml'
            }
            post {
                always {
                    junit 'results.xml'
                }
            }
        }
        stage('Badges') {
            steps {
                sh 'badgepy from-junit results.xml -o badges/tests.svg'
                sh 'badgepy from-coverage coverage.xml -o badges/coverage.svg'
                sh 'badgepy preset build "${currentBuild.result ?: "passing"}" -o badges/build.svg'
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'badges/*.svg', allowEmptyArchive: true
        }
    }
}
```

### Display with HTML Publisher plugin

Use the [HTML Publisher Plugin](https://plugins.jenkins.io/htmlpublisher/) to display badges on the build page.

## Output Management

### Recommended directory structure

```
project/
├── badges/          # Generated badge SVGs (add to .gitignore)
│   ├── build.svg
│   ├── coverage.svg
│   └── tests.svg
├── .gitignore       # Include: badges/
└── ...
```

### Converting SVG to PNG

badgepy generates SVG badges. If you need PNG output, use `cairosvg`:

```bash
pip install cairosvg
cairosvg badges/coverage.svg -o badges/coverage.png
```
