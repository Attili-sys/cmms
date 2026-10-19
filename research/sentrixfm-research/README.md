# SentrixFM research → Atlas CAFM blueprint

Authenticated manager-UI research captured **18 October 2026 (Asia/Qatar)**. Start with the decisions and inspect the evidence before implementing. Atlas application code remains unchanged.

## Start here

1. [Atlas comparison and phased roadmap](05_ATLAS_UPGRADE_MAP/ATLAS_COMPARISON_AND_ROADMAP.md) — what to reuse, fix, extend, build and defer.
2. [UI/UX blueprint](03_UI_UX/UI_UX_BLUEPRINT.md) — shell, lists, drawers, full records, forms, builders, dashboards, errors, accessibility and responsive lessons.
3. [Gap analysis](GAP_ANALYSIS.md) — concise capability/priority comparison.
4. [Searchable offline screenshot gallery](index.html) — all107states, source links, capture notes and AX references.
5. [Ranked analysis targets](REA_TARGETS.md) — highest-impact screens/workflows for a design or reverse-engineering agent.
6. [Coverage](00_INDEX/COVERAGE_MATRIX.md), [method/limits](00_INDEX/METHOD_SCOPE_AND_LIMITS.md), [resume checkpoint](00_INDEX/RESUME.md), [tooling status](00_INDEX/TOOLING_STATUS.md).

## What this package contains

- 107 screenshot/AX evidence pairs with original source URLs and timestamps.
- Detailed module specifications, field/action/state maps and skeptical UX observations.
- Observed/inferred domain model and frontend architecture clues.
- Measured design properties and a bounded 390px responsive inspection.
- A focused comparison with the current Atlas Java source: fifteen selected snippet spans matched current files at HEAD `8b29331dd18396cb73f314cd4c6c268a4ee92c07`.
- A roadmap with dependencies, proposed acceptance criteria and a four-screen initial design sprint.
- REA Codex setup/readiness evidence and explicit unfinished tooling/runtime questions.

This is a substantial first pass, **not exhaustive backend reverse engineering**. Forms, buttons and feature flags do not prove that a feature executes correctly. Read-only scope excluded saving records, status changes, invitations, permissions/settings changes, uploads, financial actions and messages. The SOP draft inspection was cancelled without saving. No credentials/tokens or hidden state were extracted. Screenshots include ordinary trial/account context; this is a private research package, distinct from the earlier public Facilio collection.

## Capability → Atlas upgrade map

| Reference capability | Best evidence | Atlas direction |
|---|---|---|
| Work queue and quick/deep detail | S001–S014,S092–S098 | Shared query/detail contracts; validated execution and coherent drawer/full page |
| Portfolio/location context | S015,S027–S029,S105 | Extend existing parentLocation into typed hierarchy, subtree queries and scoped roles |
| Asset 360 | S030–S037,S091,S095,S106 | Reuse existing asset relationships; add trustworthy PM/history/cost views |
| PPM scheduling | S043–S047 | Reuse Schedule; explicit timezone/preview and reliable occurrence generation |
| Inspections/forms | S048–S054 | Extend existing tasks/checklists into versioned definitions and typed results |
| Process composition | S055–S061,S102–S104 | Finish current automation rules; later add packages/dependencies and a tested editor |
| Inventory/requisitions | S038–S042 | Ledger/partial receiving/stock correctness before broad purchasing |
| Roles per location | S067–S074 | Build membership scope and test server enforcement |
| Command center/reporting | S019–S026 | Metric definitions, reliable drill-down and exception queues |
| AI/integrations/mobile | S076,S079–S084,S099–S101 | Claims need validation; reliable integrations/offline work before AI expansion |

## Module specifications

- [Work orders](02_WORKFLOWS/WORK_ORDER_SPEC.md)
- [Full record and builder follow-up](02_WORKFLOWS/FULL_RECORD_AND_BUILDER_SUPPLEMENT.md) — later findings correct earlier ambiguities.
- [Dashboards/reporting](02_WORKFLOWS/DASHBOARDS_REPORTING_SPEC.md)
- [Location model](02_WORKFLOWS/LOCATION_MODEL_SPEC.md)
- [Assets/inventory](02_WORKFLOWS/ASSETS_INVENTORY_SPEC.md)
- [Preventive maintenance](02_WORKFLOWS/PPM_SPEC.md)
- [Inspections/SOP](02_WORKFLOWS/INSPECTIONS_SOP_SPEC.md)
- [Visual workflows](02_WORKFLOWS/VISUAL_WORKFLOW_SPEC.md)
- [Requests, organization and access](02_WORKFLOWS/REQUESTS_ORGANIZATION_ACCESS_SPEC.md)
- [Settings, AI and secondary modules](02_WORKFLOWS/SETTINGS_AI_SECONDARY_MODULES_SPEC.md)
- [Observed model and architecture](04_DOMAIN_MODEL/OBSERVED_MODEL_AND_ARCHITECTURE.md)

## Read these findings skeptically

Sentrix's useful references include location-aware navigation, per-location roles, tabbed record pages, a configurable SOP inspector and workflow/package composition. The observed trial also has report and file-library Not Found errors, failing asset history, unfinished financial mappings, Coming Soon email/SMS, offline AI, apparent2019project/invoice templates and inconsistent record counts. These are bounded session findings, not a universal assessment of the vendor.

Atlas already contains much of the CMMS foundation. The strongest plan is to make execution, authorization, schedules, stock and side effects correct; then add typed site context, SLA, inspections, scoped vendor workflows and a polished operational UI. A visual builder or AI button should follow a proven requirement.

## Folder structure

| Folder | Contents |
|---|---|
| 00_INDEX | Evidence manifest, navigation, scope, coverage, progress and tooling |
| 01_SCREEN_CATALOG | Per-state catalog and capture index |
| 02_WORKFLOWS | Detailed module specifications and supplementary findings |
| 03_UI_UX | UX blueprint, observed tokens, responsive metrics |
| 04_DOMAIN_MODEL | Observed/inferred relationships and architecture boundaries |
| 05_ATLAS_UPGRADE_MAP | Current-source comparison and prioritized roadmap |
| 06_SCREENSHOTS | Original captured JPEG screenshots and overview contact sheets |
| 07_EVIDENCE | AX snapshots, current Atlas snippet evidence and frontend inventory |
| 08_TOOLING | Sanitized REA registration/readiness diagnostics |

The [evidence manifest](00_INDEX/EVIDENCE_MANIFEST.json) is the source of truth for URLs/timestamps. Some early AX files are differential snapshots; their manifest metadata identifies them. Later full snapshots and screenshot corrections take precedence. The gallery uses local assets and works offline after unzipping; source links open authenticated Sentrix pages only when the user chooses them.
