# Full records and builder follow-up

Captured 18 October 2026 (Asia/Qatar). This supplements the earlier work-order, asset and visual-workflow specifications. Evidence S091–S106 is later than the first inspection and takes precedence where it resolves an earlier ambiguity. These are read-only UI observations, with no saved records or status transitions.

## Work-order drawer versus full record

The workflow-linked Final Re-energization & Certification task **does open a drawer** on a fresh, settled attempt. S014 did not establish a broken feature; S092 resolves that uncertainty. The drawer has the title, description, priority, classification, assignment, labels and maintenance-package context. It displays Unknown Status, Workflow Related and Has Rules, while its category/workflow field says Standalone. This is an inconsistency within the presentation of the same record, not proof that the underlying relationship is absent. [S092 screenshot](../06_SCREENSHOTS/S092.jpg), [snapshot](../07_EVIDENCE/S092.txt).

The drawer's View Full Details action navigates to a distinct record URL under `/manager/business/operations/work-orders/working-item-…`. The full page shows the actual parent workflow name, Annual Facility Power System Overhaul, plus the package. Its header contains record title, No Location, Unknown Status, Critical and Soft, followed by Edit, Delete, Print and a back control. The five tabs are Overview, Cost & Time, Assets, SOP and History. This drawer-to-full-page pattern is worth reusing: quick triage preserves the list, while detailed work has a durable URL. Atlas should ensure both views use the same data projection and status/relationship formatting. [S093](../06_SCREENSHOTS/S093.jpg).

Overview exposes a status-management card and four indicators: Days Open 0, Priority Rank 0, Assets 3 and SOP Progress 0%. The task was created on the previous date, so Days Open may use elapsed whole days rather than calendar dates; its formula was not inspected. Priority Rank 0 alongside Critical has no visible definition. These should be treated as undefined metrics, not an actionable priority algorithm. Assignment is Unassigned and location is absent. The task is a seeded record and cannot establish how a well-configured live task behaves.

Cost & Time shows two cards. Cost has Total Cost $0.00 and an empty-data message. Time has Estimated 0h and Actual 0h and a separate empty-data message. Both have Edit actions, which were not used. The view does not demonstrate a labor-entry ledger, rates, materials, tax, cost categories or an approval process. [S094](../06_SCREENSHOTS/S094.jpg).

Assets contains **three actual asset cards** with name, commissioned status, leaf location, QR code and Track Asset action. This confirms that this observed work item relates to multiple assets in its presentation. It does not prove the storage design or whether costs and completion are recorded per asset. Atlas's directly inspected Asset model has a parent asset and location; its work-order model must be considered separately before adopting multi-asset jobs. A migration should distinguish one primary asset, related assets and per-asset execution results. [S095](../06_SCREENSHOTS/S095.jpg).

SOP shows No SOPs attached and Attach SOP. History settles to No history available. Neither empty state proves the feature is absent. No attachment or edit was performed. A Change Status click on this Unknown Status workflow-linked task produced no new dialog or visible result after settlement. This is a bounded action-feedback failure for this record, not a demonstrated transition policy or evidence that ordinary tasks cannot change status. [S096](../06_SCREENSHOTS/S096.jpg), [S097](../06_SCREENSHOTS/S097.jpg), [S098](../06_SCREENSHOTS/S098.jpg).

## Asset creation

The create modal has Asset Information, Location and Lifecycle tabs. Asset Information splits images/metadata from core properties. Image guidance permits JPG, PNG, GIF and WebP up to 5MB. Metadata fields are Category, Tags (comma-separated) and Parent Asset; these appeared as text inputs, so a validated relationship picker was not demonstrated. Core fields include required name, type and status, then serial number, manufacturer, model, purchase price, purchase date and warranty expiry. Description uses a rich-text editor with headings, emphasis, links, lists, images, quotes and tables. Create is disabled on the empty form. [S091](../06_SCREENSHOTS/S091.jpg).

The Location tab initially selects Main Office and describes it as Branch/Site. It simultaneously advises selecting a sub-location and says the asset will be saved here. This supports a generic site/root concept, but not a complete, typed portfolio/site/building/floor/space schema. An expandable location tree is present. No different location was selected. [S105](../06_SCREENSHOTS/S105.jpg).

Lifecycle on an unsaved asset shows Planned, zero days in status, zero transitions, zero maintenance in the last 30 days and current create/update/change timestamps. Change Status is disabled and there is no history. These are **pre-save form values**, not evidence that an asset was created or lifecycle transitions were executed. Showing audit-looking timestamps before persistence may confuse users; Atlas should label a draft explicitly and show persisted audit history only after saving. [S106](../06_SCREENSHOTS/S106.jpg).

## Workflow creation and execution strategy

Create Workflow is a full page with four navigation sections: Basic Information, Maintenance Packages, Execution Logic and Automation & Scheduling. Basic Information requires name, category and workflow owner, and offers status, description and an image. The settled status is Draft. Form Completion says 65% before user input, which is not a trustworthy measure of required work remaining. Maintenance Packages and Automation & Scheduling look unavailable in this empty draft; clicking Packages produced no new panel. Do not infer their rules from the headings. [S102](../06_SCREENSHOTS/S102.jpg).

Execution Logic is accessible without filling the identity form. It presents two strategies: Parallel Independent and Sequential Dependency. Trigger choices are Manual, Scheduled by Date and Scheduled by Cron. Active Status guidance says an inactive workflow cannot generate new instances. Those are UI configuration options and explanatory claims. The inspection did not select them, save the workflow, run an instance or confirm dependency enforcement, failure handling, cron syntax, timezone semantics or idempotency. [S103](../06_SCREENSHOTS/S103.jpg).

After cancelling, the registry briefly rendered incompletely, with a blank heading and missing list/grid controls. One reload restored them. In the recovered grid, package View Details and Edit actions produced no new visible page/dialog in the observed attempt. This corroborates the need for clear action feedback but does not prove packages are unimplemented: their names, composition and lanes were already visible in the workflow grid and canvas. [S104](../06_SCREENSHOTS/S104.jpg).

## Responsive observations

A temporary 390×844 CSS-pixel viewport was used, then reset. This is a web-layout inspection, not a native iOS/Android test. The immediate inline observation after resizing caught transitional clipping. The later saved S099 screenshot had already reflowed, and S101 is the deliberate settled record recheck. [S099](../06_SCREENSHOTS/S099.jpg), [S101](../06_SCREENSHOTS/S101.jpg).

The settled task list reflows to the width of the viewport, but the four summary counts and their icons form a tall vertical block. Maintenance-type controls and Table/Kanban/Calendar controls each stack into full-width rows. The table begins near the bottom of an 844px screen, increasing the distance to the user's actual work. The top bar retains a wide logo region and clipped location selector. [S100](../06_SCREENSHOTS/S100.jpg).

The settled record page uses a full-width hero card, status/priority/service badges, icon actions and five icon-only tabs. The UI DOM shows no `aria-label` or `title` on these tab elements, and accessible names in the captured tree become icon glyphs. The current-status translation key also overflows its card. Root/body scrollWidth was 390, so this is not evidence of document-wide horizontal overflow; clipping occurs within specific components. [Responsive metrics](../03_UI_UX/RESPONSIVE_METRICS.json).

## Proposed Atlas requirements

1. One canonical record projection powers list, drawer and full page; workflow and asset relationships never change labels between surfaces.
2. Unknown status becomes a recoverable data-quality exception with an explanation and a safe next step. A visible action must open its intended surface or report why it cannot.
3. Numeric KPIs carry definitions and scope. Missing cost/history data is an explicit empty state, with loading and retrieval failure separate.
4. Work-order full pages expose execution, assets, costs, documents and history using existing Atlas services; multi-asset work should be an intentional domain extension.
5. At 390px, users reach assigned work quickly. Compact summary chips replace tall decorative stat blocks; tabs retain accessible names and touch targets.
6. A workflow strategy editor is a representation of a validated server model. Publishing, running, pausing and versioning require explicit contracts before a canvas is built.

These are proposed acceptance criteria for Atlas, not claims about SentrixFM's server behavior.
