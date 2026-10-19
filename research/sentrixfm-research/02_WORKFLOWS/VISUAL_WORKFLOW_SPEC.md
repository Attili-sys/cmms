# Sentrix visual workflows: observed product and UX specification

**Later evidence:** [Full record and builder follow-up](FULL_RECORD_AND_BUILDER_SUPPLEMENT.md) adds S091–S106 and corrects the ambiguous S014 drawer observation. Read both before drawing conclusions.

Prepared **2026-10-18, Asia/Qatar** from local evidence **S055–S062**. UTC acquisition timestamps and route provenance remain in the [evidence manifest](../00_INDEX/EVIDENCE_MANIFEST.json). All eight screenshots and their substantive accessibility snapshots were reviewed locally. No browser or network access was used for this analysis.

The inspection opened existing workflow views, canvas/task configuration and an export menu. **No Save, Run Now, Verify, export, task insertion, deletion or configuration submission was performed.** This is product/UX research, not a verified execution, persistence, dependency or security assessment. Atlas's implementation was not inspected; adaptation proposals are independent recommendations, not confirmed feature gaps.

## 1. Evidence vocabulary and capture caveats

**Observed** identifies information visible in the supplied captures. **Inferred** identifies a plausible relationship or contract that the UI suggests, without recovering backend implementation. **Proposed for Atlas** identifies a future design choice or test, not existing behavior.

Screenshots show one viewport and capture moment. Accessibility snapshots can contain offscreen or nested content not visibly expanded in the corresponding image. In particular, S056's tree contains package/item detail while the image foregrounds top-level workflow cards; do not reconstruct an exact expansion state from both as if they were a single settled frame. S055's later table rows are sparsely rendered in the screenshot. Loading or capture timing could explain this, but no cause was verified. S062 is a bounded sparse-route observation, described separately below.

## 2. Registry and composition model

### List view

**Observed — S055.** The workflow registry provides List/Grid switching, Filters and Create Workflow, followed by a table with name, automation, package count, creator and actions. An existing row exposes an Open BPMN Editor link and Manual Execution text. Several table headers remain untranslated. Row action controls have little or no descriptive name in the snapshot. Their icons alone do not establish permission or successful behavior. Creator information was not needed for this analysis and is not reproduced. [S055](../06_SCREENSHOTS/S055.jpg), [snapshot](../07_EVIDENCE/S055.txt)

This registry is a definition-management surface: it names reusable operational structures and exposes a visual editor. Manual Execution suggests an invocation mode, but no automatic trigger configuration was inspected and no manual invocation was performed. Sorting/filtering controls were present without their full options or query behavior being tested.

### Grid view

**Observed — S056.** Three workflow cards are represented in the capture set. Each combines a title/description, package count, a separate PPM count, Active badge, percentage/progress bar, creation/update information and action affordances. The snapshot identifies Run Now and editor/view/edit/delete controls, some with descriptive help text. Percentage values are zero in the sample; calculation, denominator and refresh timing are unknown. Active must not be interpreted as validated, currently executing or production ready. [S056](../06_SCREENSHOTS/S056.jpg), [snapshot](../07_EVIDENCE/S056.txt)

Nested package content in the accessibility tree includes a package heading, Parallel badge, working-item count, progress, item label, View Details and Add Item. One workflow has four packages, while the other observed examples have one each. The evidence therefore supports this **visible composition hierarchy**:

**Workflow → Maintenance Package → Working Item**.

These are user-facing objects or groupings. The captures do not settle whether packages are owned, shared, copied or versioned, whether items can belong to multiple packages, or whether Parallel governs items within a package or packages across a workflow. Package position and phase-like names do not establish prerequisite ordering. A PPM badge of zero alongside working items elsewhere is an unresolved counting distinction, not proof that items are disconnected or absent.

**Proposed for Atlas:** retain both a compact registry for administration and an expandable composition outline for comprehension. Show definition status, readiness and run status separately. Explain progress and counts, and use consistent labels for workflow definitions, packages, task definitions, schedules and actual work orders.

## 3. Visual canvas anatomy

### Common editor frame

**Observed — S057/S060.** The visual-editor route includes the workflow identity, breadcrumbs and Back, Undo, Redo, vertical movement, Verify, Export and Save controls. Movement buttons are disabled in the inspected state. A palette supplies hand, lasso, space adjustment and PPM Task tools; selected-task context controls expose task append, annotation, delete and PPM configuration affordances. None of those editing operations was performed. The canvas carries a bpmn.io credit, which indicates a diagramming component reference rather than the scope of the product's execution engine. [S057](../06_SCREENSHOTS/S057.jpg), [S058 snapshot](../07_EVIDENCE/S058.txt), [S060](../06_SCREENSHOTS/S060.jpg)

The single-package example shows a large pool-like rectangle labeled by workflow and a lane-like band named for the package. A task card sits inside the band. The multi-package example uses a shared workflow boundary divided into four package bands, confirmed by the full snapshot even though the last band extends below the screenshot. This supports a mapping from composition to diagram containment. It does not prove that lanes represent organizational roles, as they commonly might in other BPMN tools; here package names label them.

### Task cards and readiness signals

**Observed — S057/S060.** Tasks combine a short title, classification badges, a numeric badge, an edit/configuration affordance and a warning. The single-task example uses SAFE and PRED; its inspector later displays Safety and Predictive, supporting that mapping for this inspected item. Other tasks use HARD/SOFT and PREV/EMER-like labels. The meaning of bare numbers such as seven is not explained by these captures and should remain undecoded. Some multi-phase cards have separately identified asset counts, with accessibility text specifying two or three assigned assets. [S057](../06_SCREENSHOTS/S057.jpg), [S060 snapshot](../07_EVIDENCE/S060.txt)

Each inspected task exposes a missing-assignment warning. A triangular visual marker and accessible description identify the issue, so readiness is communicated beyond color alone. Dotted outlines may indicate validation or selection styling, but their exact semantics were not tested. The canvas is useful because classification, affected resources and configuration incompleteness are visible without opening each task.

**Unknown:** whether assignment warnings prevent saving, verifying, publishing or running; whether they derive from user or team assignment; and whether other issues have equal or greater priority. Verify was not invoked. An Active workflow can coexist with these warnings in the supplied views, so lifecycle status and configuration completeness must be treated as different concepts.

### What the diagram does not establish

No connecting edges are visible in the inspected initial multi-phase viewport. This is not proof that the entire workflow has no connectors or that sequence support is absent. Start/end events, gateways, conditions, timers, message events, exception paths and compensation were not demonstrated. Phase-like names, Parallel badges and a BPMN editor label do not verify standard BPMN execution semantics, dependency enforcement or scheduling reliability. No engine trace or completed run was captured.

## 4. Task inspector: domain form inside a diagram

**Observed — S058.** Selecting/configuring an existing task opens a wide modal using the PPM form family. Despite inspecting an existing item, its heading is the untranslated creation-title key, and the footer says Create, disabled in the recorded state. This is evidence of reused form presentation, not proof that saving would duplicate or replace the task. No submission occurred. [S058](../06_SCREENSHOTS/S058.jpg), [snapshot](../07_EVIDENCE/S058.txt)

The modal exposes Details, Location & Asset, Scheduling, Lifecycle, Spare Parts, Incoming Tasks, SOPs and Attachments. The current task name, maintenance/service types and description are populated. Priority presents an unselected prompt; user/team assignment controls are also unselected. Category is disabled, with location-from-category help. A Maintenance Package section contains workflow-mode explanatory keys that are not translated. These observations suggest configuration context inherited from the diagram, but the actual inheritance rules remain unknown.

The reuse is a promising product idea: operational task configuration can stay structured instead of being squeezed into arbitrary diagram properties. However, the creation wording obscures whether the user is editing the selected item, adding an occurrence or configuring a template. Required markers, completion checks and error badges coexist, without explaining all missing prerequisites. Classification fields and package context should be distinguished from execution-specific data.

**Observed — S059.** Incoming Tasks contains untranslated heading/description and empty/no-task plus complete-scheduling messages. No predecessor selector or usable task collection is visible in this state. It may be gated by scheduling or another prerequisite; that possibility is not proof of functional dependency modeling. The error badge does not disclose a complete backend rule. [S059](../06_SCREENSHOTS/S059.jpg), [snapshot](../07_EVIDENCE/S059.txt)

**Proposed for Atlas:** use an explicit Edit Task Definition inspector with the selected package/workflow breadcrumb. Show inherited fields and their source; explain disabled controls. Save task configuration separately from running work, and make draft versus persisted changes visible. Replace missing-prerequisite messages with named fields and direct navigation. Avoid presenting completion checks on empty optional sections as if they represented reviewed operational readiness.

## 5. Export and standalone package route

**Observed — S061.** Opening Export reveals BPMN 2.0 (`.bpmn`) and Image (`.svg`) choices. Neither was selected. These are format affordances only: no file was generated or inspected, no schema conformance checked and no import/round-trip tested. They do not establish executable interchange compatibility, completeness of custom metadata or safe re-import. [S061](../06_SCREENSHOTS/S061.jpg), [snapshot](../07_EVIDENCE/S061.txt)

**Observed — S062.** Navigating to the standalone Maintenance Packages route produced a sparse header/settings shell without package content or explicit error text in the captured session. Some header images also appear unresolved. This is not proof that package management is absent, permanently broken, restricted or empty. Its cause and loading duration are unknown. Packages are independently visible in S056's composition and S057/S060's diagram, so the sparse route must not negate those observations. [S062](../06_SCREENSHOTS/S062.jpg), [snapshot](../07_EVIDENCE/S062.txt)

**Proposed for Atlas:** use explicit loading, empty, permission and error states with retry/navigation choices. A route should not silently leave a shell. If export is offered, distinguish a diagram image from a machine-readable definition and document exactly which domain metadata and semantics the latter preserves.

## 6. Inferred data contracts, not recovered APIs

The following is a conceptual decomposition derived from the UI. Names are analytical and do not imply actual tables, endpoints or authorization design.

| Candidate contract | UI clues | Important unknown |
|---|---|---|
| Workflow definition | Identity, automation label, Active/progress, editor route | Ownership, versions, trigger semantics and count scope |
| Package composition | Nested package labels, Parallel badge, working-item counts | Ordering, reuse and concurrency semantics |
| Working-item definition | Diagram card plus structured PPM inspector | Task/schedule/work-order identity and lifecycle boundaries |
| Resource/classification references | Asset-count indicators, service/maintenance fields and assignment inputs | Cardinality, inheritance and permission filtering |
| Diagram layout | Pools, lanes, card placement and visual tools | Authoritative layout storage versus generated projection |
| Readiness issue | Missing-assignment warning and form errors | Rule scope, severity, recomputation and enforcement point |
| Exchange document | BPMN/SVG menu | Metadata coverage, interoperability and round-trip behavior |

A separate **run/instance contract is proposed**, not observed: a versioned definition could produce execution instances with durable step states and audit events. Keep visual layout distinct from operational data so moving a card does not accidentally change business meaning. If package order or connector position has semantics, make that explicit. Security controls, tenant isolation, server validation and transaction behavior were not assessed.

## 7. UX critique and independent Atlas direction

The strongest feature is the shared mental model across outline, package and canvas. The weaknesses are ambiguity between definition and execution, unexplained abbreviations/numbers, untranslated labels, and configuration that appears under creation wording. Large empty canvas areas coexist with tightly wrapped task labels; the floating palette obscures parts of the multi-phase left edge. Lane labels rotate, making long package names difficult to scan. A persistent application sidebar also reduces diagram workspace. [S056–S060](../06_SCREENSHOTS/S060.jpg)

Accessibility snapshots expose several canvas operations as containers rather than conventional buttons. This warrants keyboard/screen-reader investigation, but no such test was performed. The exact visual library, its credit and export labels do not guarantee accessible task selection or editing. **Proposed for Atlas:** supply a synchronized outline as a nonvisual and compact alternative, descriptive controls, visible focus, error navigation, fit-to-content/zoom controls and readable task detail previews. Expand/collapse packages without losing identity or selection.

## 8. Proposed Atlas implementation sequence and acceptance tests

This is an independent implementation sequence, not a claim about existing Atlas support:

1. **Define the objects.** Inspect Atlas's task, procedure, schedule and work-order concepts; define workflow/package/item identity and vocabulary before a diagram.
2. **Build composition first.** Implement an accessible outline with stable IDs, assignment, procedure/resource references and explicit readiness issues.
3. **Add a visual projection.** Map packages and tasks onto a canvas while keeping layout separate from business semantics; synchronize selection with the outline.
4. **Make configuration unambiguous.** Add a context-aware inspector, inheritance explanations, draft tracking and versioned publication if required.
5. **Implement only agreed execution semantics.** Define dependencies/concurrency, generation, retry, cancellation and permissions before adding a Run control. Introduce audit/observability with the engine, not after it.
6. **Add interchange deliberately.** Support documented export/import subsets and validate round trips instead of assuming a BPMN file guarantees compatibility.

The following are **proposed acceptance tests**, not tests run in this research:

- List, outline and diagram resolve the same workflow/package/item identities and explain every count.
- Editing a selected task updates the intended definition without creating duplicate work or silently starting a run.
- Readiness issues identify the exact field/node and enforce the documented publish/run policy consistently on the server.
- Moving/resizing visual elements changes only layout unless the product explicitly declares another effect.
- Dependency/concurrency behavior is verified with actual execution traces, including failures, retries and cancellation.
- Existing runs retain their definition version when future configuration changes.
- Assignments and resources respect scope/permission rules through every editor and execution entry point.
- Export preserves documented metadata; supported import/export round trips are deterministic and unsupported constructs are rejected clearly.
- Keyboard and assistive-technology users can select, inspect, validate and configure every item through a synchronized outline.
- Sparse routes, failed loads and unsaved changes show clear state and recovery choices.

The captures justify studying visual composition and structured configuration together. They leave execution semantics, dependencies, interchange correctness and security unverified.
