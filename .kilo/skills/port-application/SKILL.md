---
name: port-application
description: >
  Port, translate, or migrate source code from one programming language to another
  using a structured pipeline: inventory → translate → evaluate → fix, looping until
  100% accuracy. Use this skill whenever porting, migrating, translating, converting,
  or rewriting code from one language to another.
argument-hint: <source path or project description>
---

# Port Application — Source Code Porting Pipeline

Pipeline: **Port → Evaluate → Fix → Loop** until every file scores 100%.

**Accuracy over elegance** — an ugly-but-faithful port beats a clean-but-wrong one.
The original source code is the single source of truth.

## Pipeline overview

1. Phase 0: Discovery & Configuration (only phase with user interaction)
2. Phase 1: Port ALL file groups (porter subagent per group)
3. Phase 2: Evaluate ALL ported files (auditor subagent per group)
4. Phase 3: Fix files scoring < 100, then loop back to Phase 2
5. Repeat Phase 2→3 until every file hits 100%
6. Generate final reports

After Phase 0, the pipeline runs to completion autonomously.

## Phase 0 — Discovery & Configuration

Auto-detect source language, project name, file list. Confirm target language, output path, target framework. Save to `port-results/<slug>/request.md`.

Group source files into batches of 2–3 related files (header+impl, interface+impl, heavily cross-referencing files).

## Phase 1 — Porter subagent (per file group)

For each file, the porter must:
1. **Inventory**: list every function, constant, enum, global, cross-file dependency
2. **Translate** using these universal rules:
   - Preserve function/method names (adapt casing to target convention, comment original name)
   - Preserve ALL magic numbers, lookup tables, enum values EXACTLY
   - Preserve control flow — do not refactor loops, conditionals, or extract helpers
   - Preserve variable names from original
   - Do NOT add defensive null/bounds checks the original lacks
3. **Output**: complete target file + inventory checklist markdown

## Phase 2 — Auditor subagent (per file group)

Score 0–100 using:

| Category | Weight |
|---|---|
| Function Coverage | 40% |
| Logic Accuracy | 30% |
| Constants & Data Fidelity | 15% |
| Variable & State Fidelity | 15% |

Output: JSON + markdown eval. Run two independent scoring passes, average them.

**Decision Gate** (mechanical, no judgment):
- Score = 100 AND build passes → ACCEPT
- Score < 100 OR build fails → go to Phase 3

## Phase 3 — Fixer subagent (per file group)

Triage issues P0→P5 (P0 = behavior-breaking, P1 = missing functions). Fix P0 first. Always fix toward original source, never toward "better Python." Output complete corrected file + changelog + self-audit score. Then immediately loop to Phase 2.

No retry limit. Keep iterating until 100 AND build passes.

## Progress tracking with jscpd

```bash
# Measure port progress at any time
npx jscpd --compare api/src/main/java/com/grash/ cmms/app/ \
  --ignore "**/target/**,**/.venv/**,**/__pycache__/**" \
  --format java,python -r json -o .jscpd-compare --silent
```

Read `code.sides[0].percentage` for overall progress. `readyToPort` lists the next functions to work on.

## Java → Python type mapping for this project

| Java Type | Python/SQLAlchemy Type | Notes |
|---|---|---|
| `Long` / `long` | `int` | Python int is arbitrary precision |
| `String` | `str` | |
| `Boolean` / `boolean` | `bool` | |
| `Double` / `Float` | `float` | |
| `Date` | `datetime` | Use `datetime` from stdlib |
| `List<T>` | `list[T]` | |
| `Optional<T>` | `T \| None` | |
| `Map<K,V>` | `dict[K, V]` | |
| `enum` | `enum.Enum` subclass | |
| `@Entity` class | SQLAlchemy `DeclarativeBase` | |
| `@ManyToOne` | `relationship(..., foreign_keys=[...])` | |
| `@OneToMany` | `relationship(..., back_populates=...)` | |
| `@ManyToMany` | `relationship(..., secondary=association_table)` | |
| `@Id @GeneratedValue` | `mapped_column(Integer, primary_key=True)` | |
| `Page<T>` | `dict` with `content`, `totalElements`, `totalPages`, `number`, `size` | |
| `ResponseEntity<T>` | FastAPI return value + `status_code` | |
| `@PreAuthorize(...)` | `Depends(require_permission(...))` | |
| `@Transactional` | `async with db.begin():` or `async with AsyncSession` | |
| `@Service` | Python class, instantiated via FastAPI `Depends` | |
| `@RestController` | FastAPI `APIRouter` | |

## File output

`port-results/001-atlas-cmms-python/` — all reports, evals, changelogs, HTML dashboard.
