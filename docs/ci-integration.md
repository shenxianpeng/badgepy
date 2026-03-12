# CI Integration Guide

This guide shows how to use badgepy in CI pipelines to automatically generate badges from test results and coverage reports.

## GitHub Actions

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

- name: Generate version badge
  run: badgepy preset version "$(python setup.py --version)" -o badges/version.svg
```

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
