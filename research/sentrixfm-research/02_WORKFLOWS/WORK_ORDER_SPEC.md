# Sentrix work orders: observed product and UX specification

**Later evidence:** [Full record and builder follow-up](FULL_RECORD_AND_BUILDER_SUPPLEMENT.md) adds S091–S106 and corrects the ambiguous S014 drawer observation. Read both before drawing conclusions.

Prepared **2026-10-18, Asia/Qatar** from the supplied trial captures. Acquisition timestamps in the [evidence manifest](../00_INDEX/EVIDENCE_MANIFEST.json) are UTC, predominantly late on October 17. The inspected route is the authenticated work-order workspace, `/manager/business/operations/my-tasks`.

This document analyzes read-only observations. No work order was created, edited, deleted, assigned, dragged into another status, approved, completed or otherwise transitioned. No attachment, SOP selection, part allocation or stock movement was submitted. Opening creation UI produced an **unsaved form**, not evidence of a persisted draft. Atlas's codebase and live configuration have not been inspected; all Atlas adaptation proposals are independent design recommendations, not verified feature gaps.

## 1. Evidence and confidence

Use **Observed** for information visible in screenshots, accessibility snapshots or the operator's manifest notes; **UI-stated** for behavior the application describes but that was not exercised; **Inferred** for a plausible domain model; and **Proposed for Atlas** for an independent implementation direction.

Several evidence text files contain only incremental accessibility-tree differences. Missing text in such a file does not prove the control or content was absent. Screenshots and manifest notes supplement these differences. The screenshots are desktop captures around 1280 × 657 pixels, so content below the viewport may not appear in an image even when recorded in the accessibility snapshot. This was not an accessibility audit, responsive-device test or backend/API investigation.

| Evidence | Surface | Primary use |
|---|---|---|
| [S001](../06_SCREENSHOTS/S001.jpg) | Table overview | Shell, page anatomy, summary metrics, table density |
| [S002](../06_SCREENSHOTS/S002.jpg), [S003](../06_SCREENSHOTS/S003.jpg) | Advanced filters and status choices | Filter structure and status vocabulary |
| [S004](../06_SCREENSHOTS/S004.jpg) | Kanban | Lane/card composition and counts |
| [S005](../06_SCREENSHOTS/S005.jpg) | Calendar | View controls and temporal presentation |
| [S006](../06_SCREENSHOTS/S006.jpg)–[S011](../06_SCREENSHOTS/S011.jpg) | Six creation tabs | Form structure, validation and lifecycle messaging |
| [S012](../06_SCREENSHOTS/S012.jpg) | Part selector | Planned item association |
| [S013](../06_SCREENSHOTS/S013.jpg) | Standalone detail drawer | Record information architecture and controls |
| [S014](../06_SCREENSHOTS/S014.jpg) | Workflow-linked row after View action | Exceptional detail-opening observation |
| [S015](../06_SCREENSHOTS/S015.jpg), [S016](../06_SCREENSHOTS/S016.jpg) | Global context/navigation | Location scope and module naming clues |
| [S017](../06_SCREENSHOTS/S017.jpg)–[S020](../06_SCREENSHOTS/S020.jpg) | Reporting path | Reporting affordance and isolated request failure |

## 2. Workspace and information architecture

### 2.1 Application shell

**Observed — S001.** A dark sidebar approximately 250 pixels wide anchors a white top bar and pale, slightly lavender content area. The sidebar groups dashboards, facility structure and work management; the selected work-management item reads **My Tasks**, while the content heading reads **Work Orders**. Visible neighboring modules include locations/sublocations, inventory, assets, consumables and service areas. This establishes adjacency, not verified integration behavior.

The top bar contains a menu toggle, global search, active-location selector with a main-location badge, Business Hub entry and utility icons. The work-order screen occupies the remaining width. A floating chat control overlaps the lower-right region across multiple screens, including forms. The product uses purple/blue for selected navigation and primary controls, with colored status/priority/label badges. Typography and spacious panels aim for a modern enterprise dashboard, but the density of the work-order table conflicts with that spaciousness. [Screenshot S001](../06_SCREENSHOTS/S001.jpg)

**Observed context — S015/S016.** The global location picker exposes more than one location, while Business Hub groups facility management, maintenance operations, analytics/reports and quick actions. Terms such as tasks, working items, maintenance requests, workflows and work orders coexist. Their exact equivalence is not established. For Atlas, choose one primary term per object and explain conversions between objects explicitly rather than inheriting this vocabulary wholesale. [S015](../06_SCREENSHOTS/S015.jpg), [S016](../06_SCREENSHOTS/S016.jpg)

### 2.2 Page hierarchy

**Observed — S001.** The content stacks these layers:

1. Work Orders heading and compact count sentence.
2. Breadcrumb through the business/operations hierarchy.
3. Advanced Filter, New Work Order and refresh controls.
4. Four summary metrics: total, active, completed and overdue.
5. Maintenance-oriented shortcuts: all, corrective, predictive and emergency.
6. Representation switch: table, Kanban and calendar.
7. Current representation's content.

This is a useful composition: triage information above, classification shortcuts next, then the operational collection. However, each row of chrome consumes vertical space before any work appears. At the captured height, the table shows roughly one complete row and part of another because the work-order text wraps heavily. The page's top-level summary says 12 total and 12 active, while the capture notes record table pagination of 13 entries. These are **different displayed counts**, not proven database corruption. The scope of counters, hidden filters, source distinctions, pagination and refresh timing remains unknown. [S001](../06_SCREENSHOTS/S001.jpg), [manifest notes](../00_INDEX/EVIDENCE_MANIFEST.json)

## 3. Table, Kanban and calendar

### 3.1 Table view

**Observed — S001/S014.** Table columns comprise selection, work order, assignee, created date/time, status, priority, labels and actions. The work-order cell combines an icon, title, short description and category/context line. Standalone records show category context; the inspected workflow-linked row shows source/rules markers. Header sort affordances appear, with created date visually emphasized. Sorting semantics and bulk-selection actions were not exercised.

Rows expose eye/view, pencil/edit and trash/delete icons. Presence does not prove permission, confirmation, cascading behavior or successful execution. Assignees in inspected rows are unassigned; that says nothing about the wider trial's assignment capabilities. The label and priority badges carry both text and icons, so the information is not purely color encoded. [S001](../06_SCREENSHOTS/S001.jpg), [S014](../06_SCREENSHOTS/S014.jpg)

The title column is narrow relative to its contents, producing several lines for a normal operational title. Long descriptions and context then stretch row heights further. This makes comparisons and scanning harder and hides record counts/pagination below the viewport. **Proposed for Atlas:** give title/context a larger share of width; limit descriptions to a preview; allow configurable columns and density; keep status, owner and due date visible; show the full subject in a detail preview or tooltip. A compact due/overdue indicator would support dispatch better than relying on creation time alone. These are proposed choices, not observed Sentrix features.

### 3.2 Kanban view

**Observed — S004 and manifest.** The representation uses five status lanes: Pending, In Progress, On Hold, Completed and Cancelled. Lane headers carry a color marker and item count; empty lanes show an icon and explanatory text. At the captured width, the first few lanes occupy the visible area and later lanes extend beyond it. Cards show a subject, small avatar-like illustration, priority badge, creation date and service/maintenance classifications. A view affordance appears on the card. Capture notes also identify overflow and drag containers; no drag was performed. [S004](../06_SCREENSHOTS/S004.jpg)

Pending shows ten cards in the recorded observation, while the page summary remains twelve active and the table previously reported thirteen entries. Possible explanations include different source inclusion, filtering or counting conventions; none was verified. Do not normalize these numbers silently when reconstructing the UX. The avatar-like graphic must not be treated as evidence of an assigned person, particularly while corresponding table rows show unassigned.

**Inferred boundary:** lanes suggest a status-oriented board. They do not prove all pairwise transitions are valid or that dragging persists changes. **Proposed for Atlas:** make any transition an explicit permission-checked action, announce unmet requirements and retain keyboard alternatives to dragging. Show whether lane counts include filtered-out records, workflow-linked tasks and paginated data.

### 3.3 Calendar view

**Observed — S005.** Month/week/day controls sit above a calendar with a centered month heading and single/double arrow navigation. The captured month is October 2026, with a conventional weekday grid and muted dates outside the month. Capture notes describe a clustered event expansion and a workflow event displayed at a creation-like time. The screenshot's visible upper portion does not independently establish the full event list. [S005](../06_SCREENSHOTS/S005.jpg), [manifest](../00_INDEX/EVIDENCE_MANIFEST.json)

**Unknown:** whether placement uses created time, due date, planned start, a workflow timestamp or another field; timezone behavior; duration; unscheduled records; overlap handling; and whether calendar edits are available. Do not label it a verified maintenance scheduler. **Proposed for Atlas:** state the calendar's date basis visibly, distinguish due dates from appointments, provide an unscheduled-work queue and display the selected site's timezone. A future implementation should preserve filters and selected records consistently across all three views.

## 4. Advanced filtering

**Observed — S002.** A large anchored panel overlays the workspace without navigating away. It uses two columns for Source, Status, Priority, Assignee, Service Type, Maintenance Type, Category, and due-date start/end. Cancel and Apply sit at the bottom. A badge showing one appears beside Advanced Filter even though no explicit selection was made during this inspection. Its meaning could be a default criterion or existing state, so it should not be called a verified counting defect. [S002](../06_SCREENSHOTS/S002.jpg)

**Observed — S003.** The status dropdown lists all statuses plus Pending, In Progress, On Hold, Completed and Cancelled. These are selectable filter values only. No filter was applied, and this observation does not validate inclusion/exclusion logic, single-versus-multi selection, date boundaries, empty results or persistence across navigation. Source/category/service/maintenance options were not expanded in the supplied captures. [S003](../06_SCREENSHOTS/S003.jpg)

**Proposed for Atlas:** expose active-filter chips outside the panel, a named reset action and a meaningful result count. Distinguish organization-wide search from work-order search. Include accessible labels, explicit timezone/date-boundary guidance and a clear explanation of Source. Preset maintenance shortcuts and advanced maintenance filters should resolve to one visible query state rather than becoming independent hidden conditions. If custom saved views are added, record scope and sharing separately from the current visual representation.

## 5. Create Work Order: common form behavior

**Observed — S006–S012.** New Work Order opens a wide modal over a dimmed collection. A heading and top-right close control precede six tabs: Basic Details, Location & Asset, Spare Parts, SOP & Procedures, Attachments and Execution. Tabs can be visited out of order. A bottom action area offers Cancel and Create; Create is disabled in the unfilled observations. Some tab screenshots extend beyond the viewport, so the footer is not visible in every image. No submission was attempted. [S006](../06_SCREENSHOTS/S006.jpg), [S008](../06_SCREENSHOTS/S008.jpg), [S012](../06_SCREENSHOTS/S012.jpg)

Basic Details initially reports five errors and Location & Asset one; optional tabs display completion checks despite empty content. This is an observed **initial form-validity presentation**, not six failed server validations. The accessibility tab descriptions expose untranslated localization identifiers, and some display strings have similar fallback issues. The design communicates completeness across a large form but initially frames untouched required inputs as errors.

**Proposed for Atlas:** use “required details remaining” before a save attempt; show actual errors after interaction or submission; link each summary item to its field. Optional empty sections should say optional rather than complete. The final action should explain why it is unavailable. Avoid a strict step-by-step wizard if users need to assemble details in any order, but preserve navigation, draft state and clear completion requirements.

### 5.1 Basic Details

**Observed — S006.** The first section captures core metadata. Required indicators appear on name, priority, category, maintenance type and service type. A name counter starts at 0/200 and description at 0/1000. These communicate intended limits; actual client/server enforcement, Unicode counting and truncation were not tested. Labels and due date appear without required markers. The fields use a dense four-column arrangement in the capture. [S006](../06_SCREENSHOTS/S006.jpg), [S006 snapshot](../07_EVIDENCE/S006.txt)

An Assignment Strategy section offers user assignment, team assignment and Assign to Me. Multiple-person cardinality, user/team precedence, assignment permission and automatic routing remain unknown. An Approval Configuration region contains quality-check and client-approval flags. Their help text states that the respective check/approval is required before completion. Both are off in the untouched form. This is **UI-stated gating intent**, not an exercised completion rule.

The date input's visible placeholder uses a day/month/year language convention while recorded dates elsewhere use a different display convention. That is a consistency signal, not a verified timezone error. The assignment-section description also mentions priority even though priority is above, which weakens section precision.

**Proposed for Atlas:** use an adaptive two-column layout for descriptive work metadata; group classification intentionally; explain whether maintenance type and service type drive routing or reporting. Make owner versus contributing team distinct, show due date with timezone context, and expose approval responsibility, sequence and rejection handling when a gate is enabled. Preserve a minimal intake path for users who lack detailed classification knowledge.

### 5.2 Location & Asset

**Observed — S007.** A full-width search field advertises lookup by name, code, type or location. A selected-assets area shows zero and an empty-state message. Beneath it, a location tree shows an office root and floor children with expansion controls. No node was expanded, no asset was selected, and the tab continues to show one missing requirement. [S007](../06_SCREENSHOTS/S007.jpg), [snapshot](../07_EVIDENCE/S007.txt)

**Inferred:** the UI anticipates asset associations, probably potentially plural because it displays a selected collection and count. The exact maximum cardinality is unknown. The single validation issue could require a location, asset or combined selection rule; the capture does not settle which. Floor children support hierarchical location presentation, not proof of an enterprise portfolio/building/space ontology.

**Proposed for Atlas:** show selected location breadcrumbs, distinguish searching the location tree from searching assets, and state the rule explicitly (“choose a service location,” with assets optional if appropriate). Explain whether selecting multiple assets creates one joint order or several orders. Keep selection counts, removal actions and inaccessible/retired asset states clear. These behaviors require product decisions beyond this evidence.

### 5.3 Spare Parts

**Observed — S008/S012.** The initial tab is an empty state with one Add Spare Part call to action. Opening it reveals an inline item row: item-type filter, searchable part picker, planned quantity numeric control, Add and Cancel. The screenshot shows an initial planned quantity of one. Add is disabled without a chosen part. No part was selected or allocated. [S008](../06_SCREENSHOTS/S008.jpg), [S012](../06_SCREENSHOTS/S012.jpg)

**Inferred:** work orders can carry planned material requirements. This does not demonstrate stock reservation, deduction, storeroom selection, price capture, substitutions, actual consumption, returns or procurement. The picker could combine consumables and spare parts, but actual option types were not opened.

**Proposed for Atlas:** separate planned quantity, reserved quantity and consumed quantity; show unit and stock location; explain availability without quietly changing inventory during planning. Keep inventory events auditable. A compact parts table should display quantities, stock status and cost basis only where the underlying implementation supports them. Do not derive inventory-accounting behavior from the word “planned.”

### 5.4 SOP & Procedures

**Observed — S009.** The tab invites selection of standard operating procedure templates. It has a heading, descriptive sentence, upper action and large empty-state region with another selection button. The snapshot exposes an Add Templates action while the visual presentation uses Select SOP Templates. No selector contents, template details or execution checklist was inspected. [S009](../06_SCREENSHOTS/S009.jpg), [snapshot](../07_EVIDENCE/S009.txt)

**Inferred:** reusable procedure definitions can be associated with work orders. The interface does not establish template versioning, answer types, required evidence, scoring, branching, sign-off or synchronization behavior. Plural wording suggests a collection but does not prove limits.

**Proposed for Atlas:** distinguish a reference document from an executable procedure. Freeze or record the version attached to the order, show expected duration/skills where available and surface required steps in the technician workspace. Avoid two competing buttons that perform the same empty-state action unless both serve a clear navigation need. Changes to a master template should not silently alter historical evidence.

### 5.5 Attachments

**Observed — S010.** The tab describes supporting documents/photos/files, but the visible drop zone specifically advertises images: JPG, PNG, GIF and WebP, with a 5 MB limit. A message requires saving the work order before attachment, and Upload is disabled. Some empty-state strings remain untranslated in the accessibility snapshot. No file was browsed, dropped or uploaded. [S010](../06_SCREENSHOTS/S010.jpg), [snapshot](../07_EVIDENCE/S010.txt)

There is a UX contradiction in offering an attachment section during creation while preventing the operation until after creation. Broad introductory language also exceeds the types advertised by the drop zone. This does not prove other file types are rejected everywhere; it describes this surface only.

**Proposed for Atlas:** either stage local files with the unsaved form and upload after successful creation, or make the post-save requirement explicit before a user enters the section. Show precise formats and size limits, progress, retry, removal and permission states. Separate request evidence, safety documents and completion evidence if those distinctions affect lifecycle rules. Storage architecture and malware handling are not observable here.

### 5.6 Execution

**Observed — S011.** The tab is chiefly explanatory rather than an execution console. It states that new orders start Pending, displays Pending as the current stage and shows an introductory roadmap: creation, planning/assignment and execution. It says status changes happen after creation through an execution workflow. No editable state control or tested transition is established by this form. [S011](../06_SCREENSHOTS/S011.jpg), [snapshot](../07_EVIDENCE/S011.txt)

**UI-stated, unverified:** server initialization to Pending, later lifecycle transitions, supervisor review and real-time tracking. The roadmap does not show every possible state or rejection path and must not be treated as a complete state machine.

**Proposed for Atlas:** move generic guidance into a concise contextual panel; use execution space for actual assignee actions only after creation. Describe the next eligible action and its requirements. If quality and client approval are enabled, show them as explicit gates with owners and evidence rather than letting them appear as unexplained completion failures.

## 6. Record detail drawer and source differences

### 6.1 Standalone work-order drawer

**Observed — S013.** View opens a right-side drawer occupying just over half the desktop width while retaining the dimmed collection behind it. The header has title, full-detail, expand and close affordances. The body repeats the title, adds a description, status and priority, and identifies the order as standalone. Sections contain created/updated timestamps, assignment, maintenance/service classification, category/workflow context and labels. The snapshot includes context and labels beyond the screenshot's visible body. [S013](../06_SCREENSHOTS/S013.jpg), [snapshot](../07_EVIDENCE/S013.txt)

The inspected standalone drawer is predominantly informational. No start, pause, complete or approval action appears in its recorded text. This does not prove such actions are absent from the full-detail page, other roles, other states or lower/alternate surfaces. Full-detail and expansion controls were not exercised in this evidence set.

**Proposed for Atlas:** retain a fast preview drawer for triage, but distinguish “preview” from “execute.” Reduce duplicate title emphasis, place identity/status/next action together and use consistent sections for location, assets, procedure, materials, evidence and activity. Provide deep linking and a clear path to a complete workspace. Preserve collection filters/scroll when returning, and expose loading/failure states inside the drawer.

### 6.2 Workflow-linked item observation

**Observed — S014 and operator notes.** One workflow-linked row carries Workflow Related and Has Rules markers, an N/A status and action icons. After its View action, two observations showed the list without a drawer or visible error. The standalone drawer had opened successfully immediately before this. The record title is unnecessary to the conclusion and seeded row data is not reproduced here. [S014](../06_SCREENSHOTS/S014.jpg), [manifest](../00_INDEX/EVIDENCE_MANIFEST.json)

This is **one unsuccessful detail-opening observation**, not proof that workflow-linked records are generally unavailable, missing or unpersisted. Possible causes include different navigation logic, an event/UI issue, data mismatch, permissions or transient behavior; none was verified. N/A may reflect a source-specific status model or missing mapping, but should not be interpreted as a lifecycle state without further evidence.

**Proposed for Atlas:** present a common preview contract for all collection items, with a clear source badge and parent-workflow link. When an item cannot open, retain the collection and show an actionable error. Normalize user-facing status semantics while preserving the source's underlying state identity; never silently treat unknown as Pending or Completed.

## 7. Data model clues and unverified rules

The following is an analytical domain sketch, **not a recovered database schema, API contract or verified Sentrix implementation**.

| Candidate concept | Supporting UI | Confidence and unresolved behavior |
|---|---|---|
| Work order identity and descriptive metadata | Name/description fields; titles in list/drawer | Observed fields; ID format, uniqueness and persistence untested — S001/S006/S013 |
| Priority | Required selector and badges | Observed dimension; complete option list/routing effects unknown — S006/S014 |
| Maintenance type and service type | Separate required controls; card/drawer badges | Separate UI classifications observed; dependency rules untested — S004/S006/S013 |
| Category/context | Required category; category/workflow detail grouping | Observed taxonomy surface; source-dependent relationship uncertain — S006/S013/S014 |
| Assignment | User/team selectors, self-assignment, unassigned display | Observed controls; ownership versus collaboration, multiplicity and precedence unknown — S006/S013 |
| Labels | Selector and several chips on rows | Multiple labels observed; management and permissions untested — S001/S006 |
| Due timestamp | Optional date field and due-range filters | Observed inputs; time component, timezone, overdue algorithm unknown — S002/S006 |
| Location and assets | Tree and selected-assets collection | Association UI observed; cardinality and required combination unknown — S007 |
| Planned work-order material | Part picker plus planned quantity | Planning intent observed; stock or financial transactions unproven — S008/S012 |
| SOP association | Template selection UI | Reusable association inferred; versions and execution answers unknown — S009 |
| Attachment association | Save-first message and upload area | Record-bound attachment intent; storage and upload flow not tested — S010 |
| Lifecycle | Filter enum, lanes and Pending initialization text | Status vocabulary observed; allowed transitions and terminal semantics unverified — S003/S004/S011 |
| Approval policy | Quality/client flags | Gate intent stated; approver, sequence, decision history and enforcement unknown — S006 |
| Origin/workflow linkage and rules | Standalone badge versus workflow/rules markers | Source distinction observed; polymorphism and parent relationships inferred — S013/S014 |

Creation, planning, execution and reporting may use different underlying object types or queries; the counts/source differences make this a question worth investigating. Do not claim a shared backend model from shared visuals alone. Likewise, “real-time” wording does not establish subscriptions, live updates or timing guarantees.

## 8. Usability and accessibility observations

These are desktop review findings with evidence and bounded conclusions. They are not certified conformance failures.

| Observation | User consequence | Evidence | Atlas design response |
|---|---|---|---|
| Narrow title column and extensive wrapping | Few records visible; slower comparison | S001/S014 | Allocate title width, cap previews, offer density controls |
| Several count totals do not reconcile visibly | Operator may not understand workload scope | S001/S004 manifest | Use a shared explicit query scope and explain exclusions |
| Filter badge is unexplained at inspection start | Hidden-state uncertainty | S002 | Surface active criteria and meaningful count semantics |
| Empty form immediately reports errors | Feels like failure before interaction | S006/S007 | Differentiate incomplete from invalid; summarize actionable requirements |
| Optional empty tabs show completion checks | May imply work was reviewed or supplied | S008–S011 | Use optional/empty labels; reserve complete for meaningful completion |
| Localization keys exposed in accessibility descriptions and attachment empty state | Unpolished or confusing announcements | S006/S010 text | Test resolved labels/fallbacks in all supported locales |
| Icon-only controls use glyph-like accessible names; some drawer controls supply descriptive Help text | Actual announcement depends on platform interpretation | S013 text | Provide direct descriptive names, tooltips and reliable button semantics |
| Generic generated field names appear in snapshots | Label association needs verification | S006/S007 text | Ensure programmatic labels and error relationships; do not infer failure from IDs alone |
| Very pale placeholder/secondary text and small badges | Readability concern at this scale | S002/S006/S010 | Measure contrast and size before claiming compliance |
| Floating chat overlaps form/footer region | Potential interference with primary action or content | S008/S012/S013 | Reposition support UI during dialogs and drawers |
| Document/file language conflicts with image-only drop-zone hint | Ambiguous upload expectation | S010 | Align instructions with supported formats |
| Attachments require a save inside a creation form | Forces a return visit or disrupts evidence capture | S010 | Stage files or explain post-save step clearly |
| Repeated subject/header and repeated empty-state SOP actions | More visual repetition than information | S009/S013 | Simplify hierarchy and establish one dominant next action |
| My Tasks, Work Orders and Working Items coexist | Object identity and navigation can be unclear | S001/S016 | Adopt a consistent vocabulary and explicit object relationships |

Keyboard tab order, focus trapping/restoration, escape behavior, focus visibility, dropdown arrow-key operation, screen-reader live announcements, touch targets and responsive layouts were **not tested**. Drag containers alone do not establish accessible drag-and-drop. Date display differences warrant localization review but do not establish a timezone computation defect.

## 9. Reporting failure is a separate observation

**Observed — S017–S020.** Standard Reports exposes location, report-type and date-range choices; Work Order Summary is one report option. Generating that report produced a visible Not Found dialog stating a POST route could not be handled. No report export occurred. This is a failure of that inspected report-generation path in the trial, not evidence that a work-order save failed, records did not persist, all reports fail or every product edition has the same problem. [S018](../06_SCREENSHOTS/S018.jpg), [S019](../06_SCREENSHOTS/S019.jpg), [S020](../06_SCREENSHOTS/S020.jpg)

**Proposed for Atlas:** surface report errors in the reporting workspace with the chosen scope retained, a retry path and a support reference. Keep lifecycle success and reporting availability separate in both UI messaging and monitoring. Report validity requires reconciling definitions with the operational collection rather than reusing a reassuring KPI number without traceability.

## 10. Independent Atlas adaptation specification

### 10.1 Product principles

The most useful reference is the combination of collection triage, contextual preview and multi-section work preparation. Recreate the capability in Atlas's own design language and domain model. Do not reproduce seeded data, proprietary wording, visual assets or uncertain backend behavior. First inspect Atlas's current objects, permissions and lifecycle; retain compatible mechanisms and fill verified needs.

### 10.2 Proposed workspace

Use one query context for list, board, calendar and summary counts. Display portfolio/site scope, active filter chips and a clear record total. Offer saved views if actual users need role-specific triage. Keep stable work-order identity and source context available in every representation. Show due risk, owner and next action prominently. A preview drawer should support quick inspection without losing the selected row; a full workspace should support execution and evidence.

### 10.3 Proposed creation and preparation

Start with a minimal valid order: subject, affected location, service need and appropriate priority. Require detailed taxonomies only where operational policy demands them. Add structured optional preparation for assets, assignment, planned materials, versioned SOPs and request evidence. Explain any missing required information near the final action. Preserve unsaved edits while moving across sections. Treat cancellation/discard and draft persistence as explicit product decisions; neither is proven by the inspected trial.

Where quality/client gates are enabled, collect approver scope and completion criteria. Represent multiple gates independently so execution progress does not obscure acceptance status. Draft parts should remain planning associations until an authorized stock action occurs. Stage attachments safely or show an unambiguous post-create upload step.

### 10.4 Proposed lifecycle and control model

Define permitted transitions with role, current state, prerequisites and audit events. Use a server-enforced transition operation, with UI preview of unmet conditions; this is an Atlas recommendation, not recovered Sentrix architecture. Decide deliberately whether “work finished,” “quality accepted,” “client accepted” and “closed” are separate states or independent acceptance flags. Handle pause reason, cancellation reason and reopen history if users require them. A workflow-derived item should expose its parent and any dependencies while sharing predictable collection/detail behavior.

### 10.5 Proposed review criteria before release

These are **future acceptance criteria**, not tests run against Sentrix or Atlas:

1. The same scope/filter yields explainable totals across summary, table and board; status/source exclusions are visible.
2. Calendar placement explicitly identifies the scheduling field and timezone; missing dates are handled consistently.
3. Required inputs, errors and disabled actions are understandable through keyboard and assistive technology.
4. Work-order creation, attachment retry and parts planning do not produce misleading success or duplicate records.
5. Approval requirements cannot be bypassed by another representation or direct transition action.
6. Workflow-linked and standalone items open consistently or report a useful, bounded error.
7. Inventory planning and stock consumption remain distinct and auditable.
8. Procedure versions and historical responses retain stable meaning after template changes.
9. Report failures preserve context and do not imply lost operational work.
10. Dense desktop use, narrower screens and modal/drawer focus behavior are verified independently.

## 11. Follow-up questions requiring new evidence

Highest-value unresolved questions are the full-detail execution surface, real transition/approval flow, source-specific status mapping, location-versus-asset validation, assignment multiplicity, SOP selector/execution behavior, material reservation/consumption, calendar date basis and count reconciliation. These require additional authorized observation or implementation evidence; the current captures cannot settle them. No additional interaction should be inferred as completed merely because its control is visible.
