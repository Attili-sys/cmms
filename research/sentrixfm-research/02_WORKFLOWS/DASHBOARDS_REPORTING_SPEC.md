# Dashboards and reporting: observed specification and Atlas opportunities

## Scope and evidence standard

This specification analyzes captured Sentrix trial evidence **S015–S026** and the shared [observed design tokens](../03_UI_UX/DESIGN_TOKENS_OBSERVED.json). Captures were recorded on 2026-10-17 at approximately 22:20–22:22 UTC, corresponding to **2026-10-18 at 01:20–01:22 in Qatar**. It combines screenshots, accessibility snapshots and capture notes in the [manifest](../00_INDEX/EVIDENCE_MANIFEST.json). No additional browser control or network access was used to prepare this document.

“Observed” means a control, value, message or interaction result is present in that evidence. It does not establish backend correctness, persistence, permissions, data isolation, realtime delivery or formula validity. “Atlas recommendation” identifies independent proposed behavior, not a reconstruction of Sentrix internals. The existing Atlas codebase was not inspected.

Some snapshots contain only accessibility-tree differences, not complete screens. Some screenshots caught opening animations: [S016](../06_SCREENSHOTS/S016.jpg) is dimmed before the Business Hub panel is visible; [S017](../06_SCREENSHOTS/S017.jpg) shows a partially visible panel despite its manifest title describing the report initial state. Use [S015](../06_SCREENSHOTS/S015.jpg) and [S018](../06_SCREENSHOTS/S018.jpg) for stable report-toolbar evidence. These timing differences must not be interpreted as completed layouts or failed features.

## Information architecture and shared context

The left navigation places **Analytics Dashboard**, **Location Dashboard** and **Reporting** together under DASHBOARD. Facility structure and work-management links remain available underneath. The global header contains search, the **Main Office / Main** context selector and **Business Hub**, plus utility icons. The repeated header separates account/location context from page-specific report filters.

In S015, opening the location selector exposes **Main Office**, description **Headquarters**, a Main badge and selection checkmark; a second choice is **Demo Branch**, description **Empty location for demo purposes**. The active location was not switched. The report filter below simultaneously reads **All Locations**. This establishes two visible context controls, not their relationship. It is unknown whether “All Locations” means all descendants of Main Office, all authorized locations or another reporting scope.

The [S016 accessibility snapshot](../07_EVIDENCE/S016.txt) records Business Hub groups: Facility Management with Locations, Categories and Maintenance Requests; Maintenance Operations with Workflows, Maintenance Packages and Working Items; Analytics & Reports with Dashboard and Reports; and Quick Actions with New Working Item, New Workflow and Maintenance Request. It also exposes Close Business Hub. The screenshot animation prevents a reliable assessment of its final width, clipping or responsive layout. Presence of a link does not verify that its destination works.

**Atlas recommendation:** use one explicit, persistent scope model. A report should state both the selected facility context and whether descendants are included. Label a cross-portfolio scope clearly. Preserve the scope in links and explain why a card and its destination list agree. Do not rely on a global location label alone to communicate a report’s effective query.

## Standard report generator

The observed route is [Standard Reports](https://sentrixfm.com/manager/business/reports/api-powered-reports). The stable initial screen has a page title/breadcrumb, a blue gradient toolbar card, then a large white empty-state panel. The toolbar orders controls as **All Locations**, **Facility Overview**, **Last 30 Days**, **Generate**. The empty state asks the user to choose a report type/time period and generate a report. Badges claim Real-time Data and Multi-tenant Isolation; these are UI claims, not security or freshness evidence. [S015](../06_SCREENSHOTS/S015.jpg)

Opening the report selector shows icon/label rows and a checkmark on the current selection. S018 visibly includes **Facility Overview**, **Work Order Summary**, **Asset Health**, **Cost Analysis** and **PPM Compliance Index**. Capture notes additionally enumerate **Executive Summary**, **Critical Issues** and **Forensic KPI**; those three are manifest-recorded options outside the fully visible portion of this screenshot, rather than independently legible screenshot content. No report-type-specific output was successfully verified. [S018](../06_SCREENSHOTS/S018.jpg)

After Work Order Summary was chosen, an additional **Top 25 (Standard)** selector is visible behind the error modal, and Generate occupies a second toolbar row. Its alternatives and exact effect were not inspected. This is evidence of a changed toolbar configuration, not proof of a functional ranking limit. [S019](../06_SCREENSHOTS/S019.jpg)

### Observed report failure

Generating **Work Order Summary / All Locations / Last 30 Days** produced an error, not a report. S019 and S020 both show **Not Found** and `Cannot POST /api/rapport-management/work-order-summary`, with an **OK** button. S019 additionally shows the same failure in a top-right toast while the centered modal is open. The manifest’s S019 title “generated result” must not be read as successful generation. No export was triggered, and no export format, generated table, print view or downloadable report is established. [S019 snapshot](../07_EVIDENCE/S019.txt), [S020 screenshot](../06_SCREENSHOTS/S020.jpg)

This is a failure of the tested trial path. It does not prove that every report, account or product edition fails. It also does not establish whether the underlying cause is routing, deployment configuration or an unavailable feature. The displayed endpoint is captured UI error text; it was not requested separately.

**Atlas recommendation:** distinguish not configured, no matching data, loading and request failed. Preserve filters after failure; show one actionable error surface with Retry and a support reference. Keep raw route diagnostics in an expandable technical detail rather than duplicating them in a toast and blocking modal. A report catalog should expose only implemented reports, or label previews explicitly. Build one useful work-order report end to end before multiplying report names.

## Strategic Analytics Hub

The [analytics route](https://sentrixfm.com/manager/dashboards/analytics-dashboard) offers **Command Center**, **Operations** and **Financials** tabs. Its toolbar shows **Last 30 Days**, **Live Sync OFF** and **Refresh Hub**. Live sync was not toggled; refresh correctness was not demonstrated. S021 also shows **Hub Sync: 01:21:29**, Main Office/Headquarters/London, **Operational Status: Optimal** and **System Online Since: October 17, 2026**. Timestamp timezone, freshness semantics and the basis of the health assertion are unknown. [S021](../06_SCREENSHOTS/S021.jpg)

The Command Center displays Active Tasks **12**, Critical Alerts **0**, Total Assets **0**, Active Locations **14**. Its accessibility evidence includes “Stable Flux,” “Performance: Peak,” “Zero Critical,” “Status: Optimal,” “Asset Health,” “94.2% Sync” and “Total Hubs.” These reassuring labels lack visible calculation definitions. Capture notes report empty asset/technician charts; the snapshot additionally identifies a Global Completion Rate chart. There is no evidence of chart drilldown, editable widgets or a saved dashboard builder. [S021 snapshot](../07_EVIDENCE/S021.txt)

Selecting Operations exposes **Mean Time to Repair 0 hrs**, **First Time Fix Rate 100.0%**, **SLA Compliance 0.0%**, and **Backlog 12**. Work Order Status Distribution lists Pending **12** and Scheduled **24**. An Asset Ecosystem Health table is present in the accessibility snapshot with Category, Health Score, Status, Active Issues and Next PPM columns; populated category rows were not captured. [S022 screenshot](../06_SCREENSHOTS/S022.jpg), [S022 snapshot](../07_EVIDENCE/S022.txt)

These numbers cannot be reconciled from the available definitions: pending/scheduled might represent different entities, overlapping sets, schedules or separate time scopes. First-time-fix at 100% alongside MTTR zero does not establish high service quality. Sample counts and eligibility rules were not supplied. Treat these as displayed values with unverified semantics.

Financials displays Estimated Budget **$0**, Actual Spend **$0**, Cost Variance **$0 / 0.0% Variance**, and Work Volume **0 / Avg. $0 per unit**. Crucially, its Financial Data Note explicitly says **financial column mapping is in progress** and actual values will populate as cost-tracking fields are deployed to production work orders. The preceding period sentence renders “last days” with the numeric duration missing. Therefore this capture documents incomplete financial integration, not working cost accounting. Currency selection, tax treatment and cost formulas are unknown. [S023](../06_SCREENSHOTS/S023.jpg)

**Atlas recommendation:** show metric definitions, denominator/sample count, scope and last successful refresh. Render unavailable financial mapping as unavailable, not as authoritative zero spend. Use neutral “insufficient data” states for rates without eligible completed work. Let each KPI open the exact supporting record set; otherwise the executive summary cannot be checked operationally.

## Location Control Center

The [location dashboard](https://sentrixfm.com/manager/dashboards/location-dashboard) has a blue welcome banner, **Last 30 Days** and **Load**. Its KPI cards display Work Orders **0** with Active/Current scope labels; Scheduled PPM **0** with Recurring/Planned; SLA Compliance **0.0%** with Target **98%**; and Critical Assets **0** with Priority/Requires care. Beneath are **Operational Volume Trends**, **Asset Health**, **Top Asset Issues** and **Maintenance Logistics**. [S024](../06_SCREENSHOTS/S024.jpg)

Load was invoked. Capture notes describe skeleton loading while existing rows remained, and S025 records a later numeric/row state. Exact loading duration and atomic completion cannot be established from stills. Values remained zero while the captured asset summary showed **Active 10 / Maint. 0 / Down 0**, and active task rows were present. This coexistence is an important unresolved scope/definition inconsistency, not proof that all counts are wrong. [S025 snapshot](../07_EVIDENCE/S025.txt)

Top Asset Issues includes Industrial Power Tools Set **7**, Powered Forklift Unit #1 **6**, Diagnostic Testing Equipment **5**, Water Distribution System **3**, CNC Machining Center Unit A **3**, Boiler System Primary **3**, Portable Generator Unit **2**, Chiller System Main **2**, Main Electrical Panel Room 101 **1**, Rooftop HVAC Unit #1 **0**. Rows show Next PPM **N/A** and Operational. Whether “Issues” counts open work, historical faults or something else is unverified. Assets with issues can still be labeled operational; those concepts should not automatically be equated. [S025 snapshot](../07_EVIDENCE/S025.txt)

Maintenance Logistics offers Active Tasks and Audit Logs. Captured task examples include corrective mechanical failure, structural monitoring and monthly fire safety; statuses include Pending and Scheduled, with **09:56 PM** displayed repeatedly and ambiguous **? .** assignee text. Audit Logs replaces the list with a lock illustration, a message directing users to Reporting and **Open Reports**. The link was not followed; no audit record, export or completeness guarantee was established. [S026](../06_SCREENSHOTS/S026.jpg)

## Visual patterns and independent Atlas specification

At the measured **1280 × 657** viewport, the shell uses an approximately 250px dark sidebar and 70px header. Observed tokens include Poppins, 13px body text, background **#f8f8fb**, primary **#556ee6**, body text **#495057**, border **#eff2f7**, success **#34c38f**, warning **#f1b44c** and danger **#f46a6a**. Buttons commonly measure 32px high. Bootstrap radius variables are zero while particular banners, badges and the floating chat control visibly use custom rounding; do not apply one global radius inferred from a single component. No mobile layout was captured. [design tokens](../03_UI_UX/DESIGN_TOKENS_OBSERVED.json)

For Atlas, implement a compact operational command center before decorative status language. Recommended first release: explicit scope/date controls; a trustworthy overdue/backlog/PPM/SLA row; a prioritized action list; asset-risk exceptions; and a report opening the same supporting records. Separate work-order events from planned occurrences when calculating volumes. Make missing source data visible per widget so one unavailable financial feed does not blank the whole page.

Proposed acceptance criteria, not observed Sentrix behavior: filters remain stable on tab changes; only the latest requested scope may update widgets; stale data is labeled during refresh; every rate has a defined zero-denominator state; report errors preserve selections; keyboard focus remains visible; charts have accessible textual summaries; and an audit destination returns scoped, dated evidence. Test numerical reconciliation across cards, lists and reports using known fixtures.

## REA prompts and remaining questions

1. Reconstruct the report toolbar and its empty/failure states from S015/S018–S020; do not invent successful output.
2. Inventory every metric’s entity, status set, time field and denominator. Mark each unknown before defining an Atlas equivalent.
3. Explain the visible zero-versus-existing-record discrepancies without assuming a cause; list the evidence needed to resolve them.
4. Design an independent Atlas scope/freshness/error contract and a single useful report with drilldown.

Open questions include whether report selection persists, which date field drives each filter, whether global and report scopes intersect, how scheduled work is counted, what issue/health labels mean, whether refresh is partial, and whether any export or live-sync path works. This evidence supports a detailed interface reference and a strong list of pitfalls; it does not support a claim of complete enterprise analytics functionality.
