# Atlas → premium CAFM: evidence-based decisions

Prepared 18 October 2026 (Asia/Qatar). This is a planning blueprint, not an implementation or a deployment. Atlas application files were not modified and no tests were run during this research pass.

## Decision

**Retain the original Java API, React web app and Expo mobile app. Improve their contracts and daily workflows, then add enterprise FM capabilities.** SentrixFM provides useful interaction references, but the observed trial has inconsistent counts, untranslated labels, failed reporting/storage routes, unfinished financial analytics and apparent template business pages. It should not be the authority for correctness or feature completeness.

A premium CAFM should let a regional manager identify a real exception, dispatch it within the correct site and SLA, let a technician complete the required evidence, reconcile costs/stock and leave an auditable record. Smoothly demonstrating that journey matters more than matching a navigation menu.

## Atlas evidence boundary

The selected local checkout is `/Users/attiliab/Documents/GitHub/cmms`, branch `unrestricted-selfhosted`, HEAD `8b29331dd18396cb73f314cd4c6c268a4ee92c07`. Its remote identifies the user's Atlas fork. At inspection, Git reported untracked `.claude/` and `cmms/`; neither was changed. The repository's AGENTS.md identifies `api/`, `frontend/`, `mobile/` as the product and says to leave the separate Canvas `cmms/` implementation alone.

Discovery used the existing codebase-memory-mcp index `cmms`, followed by specific source snippets. **Fifteen selected snippet spans were compared against the current files and all matched.** This validates the cited spans, not freshness or completeness of the whole graph. The overview mixes Java/React/Expo and the separate Python subtree; aggregate route/file counts are not a product feature count. [Graph evidence](../07_EVIDENCE/ATLAS_GRAPH_EVIDENCE.json), [current-span verification](../07_EVIDENCE/ATLAS_SOURCE_VERIFICATION.json).

The older `ATLAS_CAFM_DECISION_REPORT.md` in the repository audited `b23f5bd1…`, not this HEAD. Its reported 1,996 passing tests are historical evidence, not tests executed here. Its broader security, ledger, scheduling and mobile findings are candidates for revalidation on the current branch. The commercial-restriction work is a separate branch change; removing a gate does not implement previously absent business behavior.

## What to reuse, extend or build

| Area | Atlas evidence inspected now | SentrixFM evidence | Decision |
|---|---|---|---|
| Location hierarchy | `Location.java:26–178` already has parentLocation, address/coordinates, workers, teams, vendors, customers, files, custom fields | Generic levels, main/current flags, location selector, detail/edit (S027–S029) | **Reuse + extend.** Add explicit location types, subtree queries/roll-ups and scoped access. Do not rebuild the tree merely because Sentrix has one. |
| Asset foundation | `Asset.java:30–262` has location, parentAsset, category, assigned people/teams, vendor/part/file links, costs, warranty, serial/model/status and custom fields | Asset tabs, QR actions, documents, lifecycle and multi-asset work (S030–S037, S091–S106) | **Reuse + improve UX.** Build coherent Asset 360 on existing relationships; add missing history and PM projections deliberately. |
| Roles and sites | `User.java:22–183` has a single Role and one Location; Location permissions depend on role/creator/assignment methods | Mandatory user-location-role assignments, optional teams; matrix distinguishes execute/manage (S067–S074) | **Build scoped membership.** Separate company role, site role, assignment and contractor audience. UI configuration alone is insufficient. |
| Work execution | `WorkOrderService.changeStatus:832–937` handles signature requirement, timestamps, timers, PM follow-up and notifications | Create tabs, quality/client-approval flags, full record (S006–S012, S092–S098) | **Fix + extend.** Introduce a server-owned transition contract and validation before adding more status controls. |
| PPM | `Schedule.java:21–85` contains recurrence type/basis, frequency, start/end, days, due delay; generation method copies tasks/custom-field policy | Explicit execution timezone and calendar selections (S043–S047) | **Reuse + harden.** Verify restart/misfire/DST/occurrence idempotency, then improve recurrence preview and timezone UX. |
| Inspections/forms | `TaskBase.java:24–56`, `Task.java:25–69` provide template/result linkage, task type, values, notes/images, asset/meter context | Nine SOP field types, nested sections, validation inspector (S048–S054) | **Extend.** Add versioned definitions, typed answers, evidence and failure-to-corrective behavior, building on tasks. |
| Custom fields | `CustomField.java:21–69` has label/type/entity/required/order/options/copyOnRepeat | Field inspector exposes placeholder/help/length/rule types (S053–S054) | **Extend existing schema/validation.** A configurable object platform is later scope. |
| Automation | `Workflow.java:19–40` is a condition/action rule. `WorkflowService.java:21–208` contains implemented assignments plus TODO/no-op actions and no enabled guard in the shown run methods | Workflow/package/task visual composition, strategy/trigger choices (S055–S061, S102–S104) | **Fix rules first; build process orchestration separately when needed.** Atlas Workflow and Sentrix Workflow are different concepts. |
| Procurement | `PurchaseOrder.java:17–100` includes approval status/vendor/shipping; service:25–81 provides persistence/search | Empty stores/requisitions and apparent sample invoice (S038–S042, S088–S089) | **Reuse + harden receiving/ledger.** Sentrix trial does not demonstrate a stronger PR/RFQ/PO/invoice chain. |
| Vendors | `Vendor.java:20–98` has company/rate/assets/locations/parts/custom fields | No dedicated vendor/contractor module observed in the inspected navigation | **Extend based on Atlas/Facilio needs.** Contacts, compliance expiry and scoped vendor jobs before portal access. |
| Command center | Existing React analytics entry points and prior audit's drill-down/in-memory concerns; not freshly audited end-to-end here | Three analytics tabs and location dashboard; undefined/mismatched metrics, unfinished financials (S021–S026) | **Improve queries and shared metric definitions first**, then a role-specific exception workspace. |
| SLA/contracts | Not established by this focused Atlas source pass; prior audit reports no engine | SLA percentage shown, but no rule/timer/escalation configuration observed | **Design/build when required.** A dashboard percentage is not evidence of an SLA engine. |
| Integrations | Prior audit reports API/webhook foundations and single-attempt delivery; needs current revalidation | API flag and offline AI; no successful external integration demonstrated | **Harden event delivery/scopes.** Prefer explicit connectors over a plugin platform initially. |
| Mobile | Expo app is established repository architecture; offline behavior not retested here | Feature flag claims native mobile; only responsive web inspected | **Reuse + validate field operation/offline outbox.** No native-app parity claim is justified. |

Source line ranges above describe the exact inspected spans and can be found by qualified symbol in the retained evidence JSON. They do not imply every caller or endpoint was audited.

## Concrete findings from current Atlas snippets

`changeStatus` checks for a non-null status and required completion signature, then sets the requested status. The inspected method contains no previous-state/next-state allow-list or required-task/blocker check. That is a concrete reason to define transitions centrally. It also schedules completion-based PM work inside the completion path, while later notification/workflow dispatch is guarded by a previous-status comparison. Review repeat-completion and transaction boundaries with tests before changing it. This pass does not establish every caller's validation.

`WorkflowService` implements assignment of team/user/asset/category/location/priority, but its ADD_CHECKLIST and SEND_REMINDER_EMAIL branches return with TODOs. Other run methods similarly contain TODO work. The shown run methods do not inspect `workflow.enabled`; the lookup calls a repository method whose implementation was not re-read here. Treat these as specific service-level gaps and verify repository/caller filtering before claiming disabled workflows run globally.

`Location.parentLocation` and `Asset.parentAsset` already exist. Calling hierarchical locations or asset nesting “missing” would be false. The inspected Location class does not declare a portfolio/site/building/floor/space type, and the inspected User class does not expose a user-location-role collection. Those are distinct extensions from simply adding a tree UI.

## Proposed delivery sequence

Effort is deliberately expressed by dependency and exit criteria rather than invented calendar estimates. Each phase should be sized against the actual team and a selected deployment scale.

### Phase 0 — baseline and trust checks

Run the original stack in an isolated development environment with Postgres, storage and mail configured. Capture the branch/commit, current tests, representative datasets and deployment topology. Revalidate the older audit's authorization, stock-before-permission, upload-bypass, PM restart, ledger and mobile-write claims on this branch. Record each as confirmed, fixed or unresolved. No new enterprise UI should conceal those results.

Exit: a repeatable request→approve→assign→execute→complete journey; a known list of failures; representative user personas and site fixtures; production deploy/backup/restore plan. Retain the working Java implementation.

### Phase 1 — correct work execution and reliable side effects

Define allowed transitions and actors, required fields/tasks/evidence, reasons for holds/reopen/cancel, optimistic concurrency and append-only transition events. Validate those in services on every API and mobile path. Fix/hide unsupported workflow actions and honor enablement consistently. Introduce transactional event/outbox delivery with retry, idempotency and a failed-delivery queue.

Exit demonstration: an unauthorized user cannot discover or alter another scope's work; incomplete required evidence prevents completion; a duplicate request creates one transition and one downstream effect; a failed notification is visible and retried; history explains who changed what and why.

### Phase 2 — schedule and stock truth

Retain Schedule/PM entities. Add a unique occurrence identity, explicit IANA timezone, next-occurrence preview, restart reconciliation, misfire policy and completion-chain deduplication. Separate scheduled occurrence from generated work order and completed result.

For inventory, establish immutable movements, reservation/issue/return/adjustment semantics and quantity reconciliation. Separate PO approval from receiving. Model partial receipts and returns before sourcing sophistication.

Exit demonstration: restart/DST/duplicate-delivery fixtures generate one intended job; paused schedules stay paused; stock reconciles to movements; approving a PO does not silently receive goods; partial receipt is auditable and permission-checked before stock changes.

### Phase 3 — enterprise context and the premium daily UI

Extend location types and roll-ups, then site membership/role scope. Apply the same authorization-aware query context to list, counts, tree, search, exports, analytics and related-record tabs. Add saved views and a command center showing unassigned urgent jobs, overdue work, upcoming statutory PM and failing inspections.

In parallel, design one detail shell for work orders, assets and locations: persistent identity/context, overview, execution/related records, cost, documents and timeline. Preserve quick drawers and durable full pages. Add a compact technician view and manager-specific defaults without a layout-builder product.

Exit demonstration: regional manager sees only permitted sites; selection of a building filters counts/list/export identically; every KPI drills to its contributing records; drawer/full page agree; empty, loading, failed and unavailable data are distinct; 390px task access remains efficient and labeled.

### Phase 4 — service commitments, inspections and contractors

Add SLA policies with response/resolution clocks, business calendars, hold semantics, escalation routing, exceptions and policy version history. Extend task/checklist definitions into versioned inspection templates with typed answers, scores, attachments and corrective-work links. Add vendor contacts, certifications/insurance expiry and scoped contractor assignment. Introduce a vendor portal only after authorization boundaries are tested.

Exit demonstration: an SLA clock can be explained from events; an inspection failure creates one linked corrective job; a technician can record necessary evidence offline and see pending/rejected sync states; expired vendor compliance blocks assignment according to an explicit policy; contractor access exposes only assigned work.

### Phase 5 — platform features justified by real demand

Consider process templates with packages/dependencies, a visual editor, dashboard composition, custom modules and integrations only after repeated workflows require them. A process canvas should edit a tested runtime model with publish/version/migrate/simulate/monitor behavior. Add an AI assistant first for permission-scoped read-only retrieval with citations; any later write proposal must be previewable and governed by the same domain actions.

## First design sprint

Create four connected prototypes using realistic Atlas data: manager exception queue → work-order drawer → full execution page → Asset 360. Include one normal job, one blocked job, a failed report and an empty asset history. Show the mobile version of the same assigned job. Establish table density, filters, typography, action hierarchy, accessible labels and error states before expanding the menu.

Use Sentrix references S001–S013 for navigation/view switching; S093–S097 for full records; S033–S036 for Asset 360; S051–S054 for field inspector structure; S072 for scoped-role onboarding. Use Facilio reviewed workflow capsules for service breadth, but retain their public-documentation confidence level.

## Definition of “better”

Better means fewer steps to finish real work, consistent record context, trustworthy numbers, permission-safe scope, reliable schedules and integrations, accessible controls and explainable failures. It is not the presence of more gradients, a BPMN logo, an AI chat button or an invoice template. The supplied research supports planning these outcomes; it is not proof that every desired enterprise requirement has been discovered.
