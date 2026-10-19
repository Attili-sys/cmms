# Sentrix planned preventive maintenance: observed product specification

Prepared **2026-10-18, Asia/Qatar** from local captures **S043–S047**, with asset-context evidence **S035**. The [manifest](../00_INDEX/EVIDENCE_MANIFEST.json) preserves UTC acquisition timestamps. Screenshots and substantive accessibility snapshots were inspected locally. No browser/network calls, schedule creation, edits, deletion, force synchronization, assignment or execution were performed for this analysis.

**Observed** describes supplied interface evidence; **UI-stated** describes explanatory product text without runtime confirmation; **Inferred** describes a candidate domain model; **Proposed for Atlas** is independent design advice. Atlas was not inspected. This document is not a recovered scheduler implementation or a demonstration that recurring work fires reliably.

## 1. List workspace and service scope

**Observed — S043.** The inspected route is the hard-service PPM list, with a `serviceType=hard` query parameter. Hard Service expands in the sidebar, exposing work orders, scheduled PPM and inspections. The page has a heading/breadcrumb, Advanced Filter, creation and refresh controls, four summary metrics, all/preventive/predictive shortcuts, and table/Kanban/calendar representation controls. The latter two modes were visible but not opened in S043–S047. Their presence does not establish drag behavior, event placement or persistence. [S043](../06_SCREENSHOTS/S043.jpg)

Many titles, buttons, headers and helper strings appear as unresolved `PPM_SCHEDULED.*` localization keys. This causes unusually wide controls and column headings; the table extends horizontally beyond the capture. The full snapshot contains more columns than the screenshot's initial viewport. Summary total/active values show twelve, while table pagination reports eight entries. The evidence does not establish whether the summaries count every service type, another source set, hidden criteria or stale state. Treat it as an unexplained scope difference, not proven data loss. [S043 snapshot](../07_EVIDENCE/S043.txt)

### Table model

The table contains selection, schedule/task identity, status, assignee, due date, frequency, next scheduled date, interval, priority, labels and actions. Ordinary rows display Scheduled and named recurring frequencies. Workflow-linked rows carry workflow/rules markers and show non-scheduled/not-applicable values in several timing columns, with a Force Sync affordance. No row action was executed. The full sample consists of scheduled examples alongside workflow-derived tasks, suggesting heterogeneous sources in one collection. This does not prove an underlying polymorphic schema. [S043](../06_SCREENSHOTS/S043.jpg), [snapshot](../07_EVIDENCE/S043.txt)

Frequency and interval are separate columns. Their displayed values do not by themselves reveal how an interval modifies a frequency, whether it is a lead time or another scheduling concept. Due and next-scheduled dates likewise need definitions. Do not derive an executable recurrence algorithm from example rows or reproduce all seeded task names. A source-specific N/A is a display state, not verified lifecycle behavior.

## 2. Creation form and capture-settlement caveat

**Observed — S044.** Creation opens a large modal with eight tabs. The untranslated keys identify Details, Location & Asset, Scheduling, Lifecycle, Spare Parts, Incoming Tasks, SOPs and Attachments. Several required sections have asterisks; Location & Asset and Incoming Tasks show an error badge, while some other sections show completion checks before meaningful input. Only Details, Scheduling, Lifecycle and Incoming Tasks contents were inspected in this set. Other tabs' names establish navigation intent, not their complete controls. [S044](../06_SCREENSHOTS/S044.jpg), [snapshot](../07_EVIDENCE/S044.txt)

An initial capture-stage observation reportedly exposed Create as enabled, but the settled accessibility/DOM observations show it disabled on the empty form. S044's current snapshot and later tabs record the disabled state. No submission was attempted. Therefore the evidence supports a **timing/settlement discrepancy**, not a backend validation defect, successful invalid submission or a permanent enabled-button error. Future investigations should wait for animation/state settlement before classifying a control's behavior. [S044 text](../07_EVIDENCE/S044.txt), [S047 text](../07_EVIDENCE/S047.txt)

## 3. Details: metadata and assignment

**Observed — S044.** Required markers appear on schedule name, category, priority, maintenance type and service type. Service type defaults to Hard in the inspected route. A helper near category indicates location-from-category intent. User and team assignment selectors and a short description field are also present. No dropdown option set, category choice or assignment was tested. [S044](../06_SCREENSHOTS/S044.jpg)

**Inferred:** classification and assignment metadata may be copied into generated work. The UI does not establish exactly what is inherited, whether later template changes affect existing orders, user/team precedence, multiple-assignee rules or category-driven location enforcement. Hard being selected is consistent with the route's scope but does not prove every possible entry path behaves the same way.

**Proposed for Atlas:** separate schedule identity from generated-order subject when users need different wording. Explain category/location inheritance, allow an intentional override where policy permits, and identify which assignment is accountable. Show whether changes apply only to future occurrences. Template metadata should have stable version meaning rather than silently rewriting existing execution records.

## 4. Scheduling: calendar selection and execution timezone

**Observed — S045.** The scheduling tab contains month, week and day selectors, then required start and end dates and required execution time. The time starts at 09:00; timezone is explicitly Asia/Qatar in this observation. Helper text for the timezone is untranslated. No selector was opened, no recurrence pattern was chosen and no dates were entered. The screenshot's localized date placeholder differs in style from other displayed dates, but this is not proof of a timezone computation error. [S045](../06_SCREENSHOTS/S045.jpg), [snapshot](../07_EVIDENCE/S045.txt)

The interface exposes a custom calendar-selection model. It does **not** settle whether weeks mean weeks of month or year, whether selected dimensions are intersected or combined, how unspecified dimensions behave, or what happens in short months. Neither an occurrence preview nor a readable recurrence sentence is visible in the supplied tab. The list's named frequencies do not prove this form contains corresponding simple presets.

**Unknown runtime rules:** inclusive/exclusive end dates, execution window tolerance, daylight-saving handling in other timezones, missed-run recovery, scheduler clock source, duplicate prevention, service outages, lead time, holiday/business calendars, pause/resume and rescheduling. A default local timezone is useful UX evidence; it cannot establish reliable scheduling.

**Proposed for Atlas:** provide clear presets plus an advanced rule builder only when needed. Convert selections into a readable sentence and preview several upcoming dates in the execution timezone. State whether recurrence is calendar-based or completion-based, how skipped occurrences behave and whether start/end are inclusive. Keep due duration distinct from generation time and recurrence interval. Surface validation inline with specific reasons, such as no matching dates, rather than exposing internal localization keys.

## 5. Lifecycle explanation versus execution proof

**UI-stated — S046.** The Lifecycle tab presents an initial scheduled-stage concept and a three-stage explanation: schedule setup, automatic generation of live work when an execution window arrives, and completion feedback to the master schedule. It also indicates that status editing occurs after creation. This is a conceptual product promise in the interface. No scheduled record was created, clock advanced, generated order opened or closure feedback observed. [S046](../06_SCREENSHOTS/S046.jpg), [snapshot](../07_EVIDENCE/S046.txt)

**Inferred candidate model:** a persistent schedule definition produces individual work-order occurrences and receives their execution outcomes. This is a sensible domain distinction, but the captures do not reveal job infrastructure, identifiers, occurrence states, retries or integrity guarantees. A schedule and a generated order should not be conflated merely because both use task-like labels.

[S035](../06_SCREENSHOTS/S035.jpg) gives complementary asset-context evidence: an asset's PPM tab is empty and offers Schedule PPM. It establishes a contextual association/entry point, without verifying that clicking it prepopulates asset metadata or creates linked work.

## 6. Incoming Tasks and uninspected tabs

**Observed — S047.** Incoming Tasks shows an untranslated heading, description and missing-required-fields message, with one tab error. The panel has no visible dependency controls in this unfilled state. It might require earlier fields or provide workflow-related configuration, but that is inference only. It is not evidence of functioning predecessor dependencies, automatic task import or a permanently empty editor. [S047](../06_SCREENSHOTS/S047.jpg), [snapshot](../07_EVIDENCE/S047.txt)

Location/asset, spare-parts, SOP and attachment tabs are visible navigation choices in S044–S047. Their specific pickers, upload restrictions, procedure requirements, material rules and validation were not inspected here. An SOP asterisk alongside a completion check is a presentation ambiguity, not proof that required SOP validation can be bypassed. Do not fill these gaps using a different form's controls without new evidence.

## 7. UX findings and Atlas design lessons

The form provides useful separation between operational metadata, recurrence and lifecycle education, and explicitly showing execution timezone is valuable. However, untranslated labels dominate the hierarchy, wrap navigation across multiple lines and conceal business meaning. The panel devotes substantial space to generic lifecycle prose while prerequisite feedback in Incoming Tasks does not tell the operator which fields to complete. Optional/required/complete/error distinctions are inconsistent in the untouched form. These are observed presentation issues, not claims about scheduler correctness. [S044–S047](../06_SCREENSHOTS/S044.jpg)

**Proposed for Atlas:** retain a concise schedule definition, asset scope, procedure version, generation rule and owner. Use a full page or appropriately sized editor if eight sections cannot fit clearly in a modal. Put occurrence preview and prerequisites close to recurrence settings; contextual lifecycle help can remain secondary. Distinguish schedule state from occurrence completion and expose generated-order history, next run and generation errors. Workflow-derived items need explicit source/parent context rather than opaque N/A columns or a maintenance-oriented Force Sync label without explanation.

Permission checks, keyboard navigation, focus restoration, contrast, screen-reader announcements and narrow-screen layouts were not tested. The long localization keys themselves are a clear usability problem; actual accessibility conformance needs separate measurement.

## 8. Proposed acceptance criteria for an independent implementation

These are **future Atlas requirements to consider**, not tests performed against Sentrix:

1. One documented scope reconciles summary counts, source filters and list pagination.
2. A recurrence rule produces a readable description and reproducible timezone-aware occurrence preview.
3. Date-range, empty-pattern, short-month and daylight-saving cases have explicit validated behavior.
4. Generation is idempotent per schedule occurrence, with observable retries and recovery after outages.
5. Schedule versions and generated work retain traceable relationships; editing future rules preserves historical execution meaning.
6. Due duration, generation lead time, recurrence frequency and interval have distinct labels and semantics.
7. Asset, assignment, procedure and planned-material inheritance is visible before publication and auditable afterward.
8. Pause, resume, skip, reschedule and retire operations clearly explain effects on existing and future occurrences.
9. Missing prerequisites identify actual fields and provide navigation; empty required forms remain disabled after settlement and are rejected consistently if submitted through another path.
10. All labels/help resolve in supported locales, and tab navigation and validation work with keyboard/assistive technology.
11. A failed scheduler/report dependency produces a scoped error rather than an apparently successful empty state.
12. Completion feedback is verified using actual generated orders before claiming end-to-end PPM execution.

The strongest reference is the separation of a recurring definition from field execution. Reliable generation, dependencies and closure feedback remain unverified by these read-only captures.
