# Inspections and SOP forms: observed specification and Atlas opportunities

## Scope and evidence boundaries

This specification covers **S048–S054**, captured in the Sentrix trial on 2026-10-17 around 22:28 UTC, corresponding to **2026-10-18 around 01:28 in Qatar**. It uses the supplied [manifest](../00_INDEX/EVIDENCE_MANIFEST.json), accessibility snapshots and screenshots. All seven screenshots were visually reviewed. No browser control, network request or product mutation was performed to prepare this document.

The capture operator opened an existing inspection, opened the SOP builder, added **one Text Input to an unsaved local draft**, opened its inspector and added **one local validation-rule row** to expose the rule palette. Neither field **Update** nor SOP **Save** was clicked. The inspector and SOP draft were cancelled. The operator reports that the library visibly returned to **0 Templates / 0 Instances**. S050 directly documents the initial zero-count baseline; the supplied S048–S054 images do not themselves contain that later cleanup screen. The return observation is therefore operator-supplied provenance, not a fabricated post-save screenshot.

Local builder interactions are verified; persistent template creation, instance creation, checklist execution and runtime validation are **untested**. “Observed” below describes captured interface content. Proposed Atlas behavior is independent design guidance; Atlas source was not inspected.

## Inspections information architecture and list

The inspected route is [Hard Service Inspections](https://sentrixfm.com/manager/business/operations/inspections?serviceType=hard). Navigation places Inspections under **Hard Service**, next to Work Orders and PPM Scheduled. **SOP Management** is a separate work-management destination; Workflows sits in another sidebar grouping. This establishes adjacent capabilities in the information architecture, not a demonstrated link between an inspection and a specific SOP instance.

[S048](../06_SCREENSHOTS/S048.jpg) shows an INSPECTIONS heading and an untranslated breadcrumb value **INSPECTIONS.LIST.TITLE**. Summary cards display **Total Inspections 12**, **Active Inspections 12**, **Completed Inspections 0**, **Overdue Inspections 0**. The table’s captured footer says **Showing 1 to 4 of 4 entries**. The twelve-versus-four difference could reflect a global summary versus hard-service filtering, but its cause is unverified. Do not call the four rows a twelve-record result or assume the cards update with the service filter.

Visible classification buttons are **All**, **Preventive**, **Corrective**, **Predictive** and **Emergency**. **Table View** is active, with **Kanban View** available. No alternate classification or Kanban behavior was tested, and no visible Create Inspection call to action is captured. Header and row selection checkboxes exist, but no selection or bulk operation was performed.

The [S048 snapshot](../07_EVIDENCE/S048.txt) records columns Inspection, Status, Priority, Assignee, an untranslated created-at column, an untranslated labels column, and Actions. Inspection cells combine title, truncated description, category, an execution-mode badge and maintenance classification. The execution-mode text itself is an untranslated key, including **INSPECTIONS.EXECUTION_RULES.MODE_STANDALONE**, so do not infer a complete execution-rule engine from the badge.

The four captured records are:

| Inspection | Status | Priority | Assignee |
|---|---|---|---|
| Preventive Hard — Safety Equipment Inspection | Scheduled | Medium | Unassigned |
| Predictive Hard — Equipment Condition Assessment | Scheduled | Critical | Unassigned |
| Preventive Hard — Structural Integrity Check | Scheduled | Low | Unassigned |
| Predictive Hard — Electrical Panel Assessment | Scheduled | Low | Unassigned |

All show Mechanical Systems as category and October 17, 2026 / 9:56 PM as created information. Label combinations vary, including Label 5/Urgent and numbered labels. Row actions expose descriptive accessible names for View details, Edit and Delete. Only View details was used. Existence of an Edit/Delete control does not establish allowed mutation, confirmation behavior or server permissions.

**Atlas recommendation:** make summary scope explicit, distinguish inspection lifecycle from maintenance classification, and provide an obvious path from an inspection to its checklist/evidence. Preserve human-readable labels in every visible and accessible surface. If inspections are filtered working items, make that model understandable without leaking internal localization keys.

## Inspection detail: bounded result

Viewing the safety-equipment inspection opens a right-side panel over a dimmed list. Its heading is the untranslated **INSPECTIONS.DETAILS.TITLE**. The panel shows the full inspection name, a short compliance description, Scheduled and Medium badges, Preventive/Hard classifications, and a **Basic Information** section. The latter contains an identifier beginning `working-item-`, category Mechanical Systems, and created date October 17, 2026. Controls are close, Delete, Cancel and Edit. [S049](../06_SCREENSHOTS/S049.jpg), [S049 snapshot](../07_EVIDENCE/S049.txt)

No checklist questions, answer controls, completion action, attachment evidence, pass/fail result, signature, technician assignment editor or execution history is visible in this captured detail. That limits what can be claimed: an inspection record detail panel works for this item; inspection execution is not demonstrated. A working-item identifier suggests shared entity naming but does not establish the internal database schema or prove all inspection records share work-order behavior.

For Atlas, the useful pattern is preserving list context while inspecting a record. The independent improvement is a detail surface that connects identity to action: responsible person, location/asset, applicable procedure revision, due date, execution progress and outstanding exceptions. Show unavailable data explicitly instead of implying that a metadata-only record is an executed compliance inspection.

## SOP library and template-versus-instance concept

The [SOP library](https://sentrixfm.com/manager/business/operations/sop-management/library) has heading **SOP LIBRARY**, **0 Templates • 0 Instances**, Advanced Filter and Create SOP. The main card says All SOPs with count zero, offers a Search SOPs field, and segments **All / Templates / Instances**. Its table columns are SOP Name, Type, Category, Fields, Version, Created At and Actions. The empty state says No SOPs Found and invites creation. [S050](../06_SCREENSHOTS/S050.jpg)

These labels support an intended distinction between reusable procedures and instantiated forms. They do not establish how an instance is generated, whether it snapshots a template, which entity owns it, or how answers are stored. No nonempty template/instance row, instance detail, revision history or link from the inspected inspection was captured. Search/filter controls are visible affordances, not verified queries.

**Atlas recommendation:** formalize three separate concepts: a procedure template; an immutable published template revision; and an execution instance referencing that revision and its work/location/asset context. Store answers and evidence against stable field identifiers. A later template edit must not silently alter completed inspection evidence. This is an independent proposed model, not an observed Sentrix persistence design.

## Builder structure and section model

[S051](../06_SCREENSHOTS/S051.jpg) shows a full-page Create SOP builder. Top actions are **Back to List**, **Preview Mode**, **Cancel** and **Save**. Save wraps beneath the other buttons at this desktop width. The accessibility tree exposes raw action keys for Preview Mode and Save even though their visible text is readable. No preview or save outcome was tested.

Basic Information contains required **Name**, **Category** initially No Category, **Version** initially 1.0, and multiline **Description**. Category options and version semantics were not explored. The builder begins with **Form Fields (0)** and a **General Information** section labeled **Level 1**. It offers Add Section, Add Subsection/accessible Add Nested Section, Delete Section and Add Field to Section. A separate **Fields List** panel mirrors General Information. [S051 snapshot](../07_EVIDENCE/S051.txt)

This is evidence of a section-based composition surface with a nesting affordance. No subsection was created, no section removed, and no reordering behavior or depth limit was established. After the local Text Input addition, the builder shows Form Fields (1) and the field appears under General Information in both the canvas and Fields List. That verifies local structural feedback, not database persistence. [S053 snapshot](../07_EVIDENCE/S053.txt)

## Nine field types

Opening Add Field presents a large **Select Field Type** modal with search and **All Fields / Basic Inputs / Advanced / Media** categories. Cards show an icon, name, category badge and explanatory text. The footer indicates the chosen type and has Cancel and Add Field. All nine types are visible in [S052](../06_SCREENSHOTS/S052.jpg):

| Category | Type | Advertised purpose; execution untested |
|---|---|---|
| Basic | Text Input | Short, single-line responses |
| Basic | Text Area | Longer notes and descriptions |
| Basic | Number Input | Numeric measurements or quantities |
| Basic | Date Picker | Date-based input |
| Basic | Checkbox | Boolean/confirmation input |
| Advanced | Dropdown Select | One choice from configured options |
| Advanced | Digital Signature | Signature-pad input |
| Media | File Upload | Document attachments |
| Media | Photo Capture | Captured or uploaded images |

Only Text Input was added locally. The other eight type cards do not prove working mobile cameras, signing, file storage, constraints, answer submission or document generation. Search/category filtering behavior was not tested. A card description advertising file types is not evidence of upload security or server-side checks.

## Text field inspector and validation palette

The **Edit Field** modal in [S053](../06_SCREENSHOTS/S053.jpg) identifies Text Input and separates general properties from Text Input Configuration. Required **Field Label** initially reads Text Input; required **Display Order** is 1; Placeholder reads Enter Text Input; Help Text is multiline and empty. The page identifies an auto-generated field ID with a masked-looking `field-****` display. This does not establish uniqueness, identifier stability or storage format.

Minimum Length and Maximum Length controls are present. The screenshot shows pale **0** and **255**, while the accessibility tree supplies no actual values. Treat these as displayed hints/default-looking content, not verified configured bounds. Explanatory text describes minimum/maximum character counts. Below, the snapshot reports No validation rules configured yet and **Add Validation Rule**. Footer actions are **Cancel**, **Preview**, **Update**, with a separate close control. The modal contains internal scrolling; the full configuration does not fit one captured viewport. [S053 snapshot](../07_EVIDENCE/S053.txt)

Adding a rule locally exposes **Rule 1**, a remove control, required **Validation Type** defaulting to **Required Field**, and required **Error Message** initially **This field is required**. [S054](../06_SCREENSHOTS/S054.jpg) visibly shows the top of the open palette; its [accessibility snapshot](../07_EVIDENCE/S054.txt) and capture notes enumerate Required Field, Custom Validation, Minimum Length, Maximum Length, Pattern/Regex, Email Format, URL Format, Alphanumeric Only and No Special Characters. URL Format and Alphanumeric Only are concatenated in one accessibility text node, so the captured notes help disambiguate them.

No custom expression editor, regex value, numeric rule parameter or alternate rule-type configuration was inspected. No invalid answer was entered into a rendered form. The presence of both length properties and length validation types raises an unresolved precedence/duplication question. Neither Update nor Save was invoked; even local rule configuration must not be described as published or enforced.

## UX findings and independent Atlas acceptance criteria

The useful observed patterns are a searchable field palette, section hierarchy, an outline beside the canvas, contextual field configuration and human-readable validation messages. Weaknesses include untranslated strings, dense modal scrolling, ambiguous save layers and inaccessible meaning when icons or placeholder-like numbers carry important information. The library separates template and instance labels but provides no observed explanation of their relationship.

For an Atlas implementation, separate **apply field changes to draft**, **save draft**, **publish revision** and **complete inspection**. Use distinct action labels so a supervisor understands which scope each operation affects. Preserve or discard draft changes explicitly when navigating. Show field-level validity and a procedure-level error summary. Mark preview as a simulation and prevent preview answers from becoming actual execution records.

Proposed acceptance criteria, all untested in Sentrix:

1. Cancelling the field inspector restores its prior draft configuration; cancelling an unsaved procedure does not create a library record. Confirm abandonment when meaningful changes exist.
2. Adding, nesting or reordering sections updates the outline, field counts and execution order consistently; stable IDs survive label/order changes.
3. Invalid configurations such as minimum greater than maximum cannot be published. Define one source of truth when properties and rules overlap.
4. Client and server enforce the same published rules, with localized, field-associated errors and defined behavior for optional empty values.
5. Upload/photo/signature controls have explicit limits, failure/retry states and evidence provenance; an empty checkbox does not ambiguously mean unanswered or failed.
6. Executions retain the applicable revision, answers, actor, timestamps and review outcome. Failed checks can create traceable corrective work without overwriting the original observation.
7. Keyboard users can operate the palette, section actions and inspector; focus returns to the originating control after dismissal. Mobile execution must be designed and verified separately.

## REA prompts and unresolved questions

Reconstruct the captured list, palette and local inspector states without inventing saved output. Derive an independent template/revision/instance schema, marking proposed fields clearly. Map every validation choice to the additional parameters and runtime tests it would require. Design a short asset safety checklist with an evidence-backed failure path, then specify how completed results become auditable records.

Open questions include instance creation and ownership, published-version behavior, conditional visibility, branching, scoring, repeatable sections, mobile/offline execution, permissions, approvals, media storage and reporting. None should be claimed from these captures. The evidence establishes a tangible local SOP-building surface and an inspection metadata interface; it does not establish a completed inspection-compliance lifecycle.
