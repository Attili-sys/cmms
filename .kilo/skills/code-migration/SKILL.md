---
name: code-migration
description: Move code from one implementation to another function by function, tests first and code second, and check two implementations of one app for parity, with jscpd --compare as the progress measure and a coverage map binding each function to its tests. Use when porting a library or app to another language or framework (Java to Kotlin, JavaScript to Rust, a Python library to TypeScript, an iOS app to Android), when asked what is left to port, or when comparing the Android and iOS versions of an app.
---

# code-migration

`jscpd --compare SOURCE TARGET` pairs every function of one folder with the function of the other folder that does the same job, in any pair of languages, and lists the functions that have no counterpart. This skill uses it to measure a port: what is ported, what is left, and whether the port you just wrote was recognized.

A port runs in two phases: the tests first, then the code they check. A coverage report of the source's tests tells which tests exercise which function, so each function is ported together with the tests that prove it works.

## Setup

`--compare` pairs functions with a code embedding model that runs inside jscpd. Download it once (548 MB, CodeRankEmbed). Ask the user before you start the download:

```bash
npx jscpd --semantic-download
```

jscpd caches the vectors, so a repeat run embeds only the functions whose code changed and takes seconds.

Pick the two paths and keep them fixed for the whole port: the source first, the target second.

### Keep vendored and generated code out

Before the first run, ensure `.gitignore` excludes: `node_modules/`, `.venv/`, `target/`, `build/`, `dist/`, `.jscpd-compare/`.

## Measure

```bash
npx jscpd --compare api/src/main/java/com/grash/ cmms/app/
```

The first line is the port's progress: share of source functions with a counterpart in the target. "Only in source" = work left.

For tracking:
```bash
npx jscpd --compare api/src/main/java/com/grash/ cmms/app/ -r json -o .jscpd-compare --silent
```

The JSON has `code` and `tests` sections, each with `sides[0]` (source), `sides[1]` (target), `unmatched`, and `readyToPort` (unmatched functions whose callees all have counterparts — start here).

## Plan: tests first, then code

Port the tests before the code. Build a map from each source function to the tests that exercise it using coverage:

1. Get coverage of Java tests: `mvn test jacoco:report` → `target/site/jacoco/`
2. Take source functions from `code.sides[0].unmatched` in the JSON report
3. Map: function (file, start, end) → tests that ran lines in that range
4. Port tests first into `cmms/tests/`, then port the code

## Phase 2: port the code

Order: use `readyToPort` list (functions whose callees all have counterparts). After each batch, rerun the comparison.

## Key options for this project

```bash
# Ignore Java build output and Python venv
npx jscpd --compare api/src/main/java/com/grash/ cmms/app/ \
  --ignore "**/target/**,**/.venv/**,**/__pycache__/**" \
  --format java,python
```
