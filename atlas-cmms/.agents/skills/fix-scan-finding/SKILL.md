---
name: fix-scan-finding
description: Use when a security finding appears — a leaked secret, a SAST rule, a vulnerable
  dependency — from a reviewer, GitHub, or any scanner the user ran; and when the user says "fix the
  security findings", the app's Security tab or the portal's bell names vulnerabilities to fix, or
  `canvas status` shows a scan line.
---

## Files

Edits the file the finding names. Never a config file that silences it.

## Choosing

A finding comes from gitleaks — `canvas validate`, the upload's credential scan, pre-commit or CI — from a dependency audit,
or from the platform's daily scan of what the app runs: say which.

**The platform's scan** — `canvas security` (`--json` for every finding) — sorts each by who fixes it. Fix
**yours**: the app's own packages, each with the command that moves it to a fixed version. **The platform's**
(its base image, its Postgres) and those with **no fix yet** are not the app's to fix: say so, and leave them.

A leaked secret is never fixed by moving the value. Delete it, and have its owner **rotate** it —
git history keeps the old value.

## What to do

1. Read the finding: file, line, rule — or, from the platform's scan, `canvas security --json`'s `yours`
2. Explain what it means in one sentence
3. Fix the code; for a dependency, raise its version — the command `canvas security` gives each, else the
   Stack table's *a dependency* (AGENTS.md)
4. Re-run whatever found it, and *the tests*; a scan's fix ships with `canvas deploy`, and the app's next
   daily scan clears it

## What NOT to do

- **Never** suppress a rule. No `# nosemgrep`, no `# noqa`, no allowlist entry. The one exception is `validate`'s: `gitleaks:allow` on a line that is a documented example, not a credential.
- Do not 'fix' a secret by moving it elsewhere in the repo.
