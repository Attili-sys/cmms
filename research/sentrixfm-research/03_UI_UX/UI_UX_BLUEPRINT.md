# UI/UX blueprint and critique

Evidence-based inspection, 18 October 2026 (Asia/Qatar). Observations describe this trial account and browser session. Recommendations are independent proposals for Atlas. The collection includes successful, empty, failed and transitional screens so apparent polish does not hide uncertainty.

## Overall shell and information architecture

At the initial 1280×657 viewport the shell uses an approximately 250px dark sidebar, a 70px white top bar and a pale gray/lavender content background. The sidebar scrolls independently. Top-bar elements include search, current/main location selector, Business Hub, language, app/utility icons, fullscreen, notifications and avatar. A floating AI button sits at the lower right. The sidebar groups dashboards, facility structure, work management, workflows, organization, communication and business operations. [S001](../06_SCREENSHOTS/S001.jpg), [S038](../06_SCREENSHOTS/S038.jpg).

Strength: navigation relates operational work to facility context instead of listing every entity alphabetically. Weakness: long labels truncate; Teams versus User Groups and Working Items versus Work Orders introduce competing names. Breadcrumbs often use `javascript:void(0)` rather than useful parent destinations. The Business Hub duplicates sidebar entry points; its menu inventory is useful, but S016/S017 contain animation and S107 shows the menu clipped at the lower right. None should be treated as a complete, well-positioned menu layout reference.

**Atlas proposal:** preserve the site's location context in the shell, expose the current scope and whether descendants are included, and keep a compact set of daily destinations: Overview, Work, Assets & Spaces, Inspections, Inventory, Vendors, Reports and Administration. Choose one vocabulary and use it in navigation, headings, APIs, help and mobile. Keep administrative and exploratory features away from the technician's daily list.

## Visual system

Measured body: Poppins, 13px/19.5px, weight 400, text `#495057`, background `#f8f8fb`. Measured primary button border/color family includes `rgb(85,110,230)` (`#556ee6`). White surfaces, purple/blue primary buttons, outlines for secondary actions, colored badges, icon circles, card shadows and gradient record heroes recur. Page headings are generally small and semibold; full record heroes are substantially larger. [Measured tokens](DESIGN_TOKENS_OBSERVED.json).

The visuals are coherent enough to orient the user, but component density and geometry vary. The work table wraps long names and descriptions into tall rows, while cost/time and inspection details leave large empty regions. Colorful KPI circles and hero cards consume vertical space without always adding actionable meaning. Many icon fonts appear as private-use glyphs in accessible names; visual consistency is not equivalent to semantic accessibility.

**Atlas proposal:** create tokens for spacing, typography, surfaces, borders, semantic colors and focus states. Design comfortable and compact table densities. Reserve strong color for state and primary action. Prefer clear typography and aligned data over decorative counts. Derive a fresh system from Atlas's existing React components; no frontend-stack migration is justified by this reference.

## Lists, filters and view switching

Work orders provide maintenance-type segmentation and Table/Kanban/Calendar. Advanced filters expose source, status, priority, assignee, service/maintenance type, category and due-date range. This gives users different task lenses. However, the same session shows summary 12, table pagination 13 and Kanban 10 cards. Filter/pagination scope is a plausible explanation, not established. PPM and inspection summaries likewise differ from the scoped visible rows. A persistent “1” filter badge appears without a clear selected-condition summary. [S001–S005](../06_SCREENSHOTS/S001.jpg), [S043](../06_SCREENSHOTS/S043.jpg), [S048](../06_SCREENSHOTS/S048.jpg).

The maintenance-request filter opens a panel with no visible criteria. Empty inventory says no entries match current criteria even when the account simply has no items. These states should not force users to guess whether data is absent, filtered, forbidden or failed to load. [S041](../06_SCREENSHOTS/S041.jpg), [S064](../06_SCREENSHOTS/S064.jpg).

**Atlas proposal:** one shared query object drives every representation. Display scope, active-filter chips, visible/total counts and a clear reset. Saved views should be named, owner/role-scoped and shareable deliberately. A chart click, table count, Kanban lane and export must agree on the underlying record set. Keep columns selectable, freeze identity where needed and summarize long descriptions without inflating every row. Treat bulk selection as an explicit mode with a persistent selection summary.

## Record hierarchy: drawer and full page

A right drawer enables quick review while preserving the list. Full records have durable URLs, larger identity blocks and related-data tabs. This is one of the strongest reusable patterns. The drawer/full record disagree for the workflow-linked task: Standalone in the drawer versus a named parent workflow on the full page, plus Unknown Status/N/A inconsistencies. [S013](../06_SCREENSHOTS/S013.jpg), [S092](../06_SCREENSHOTS/S092.jpg), [S093](../06_SCREENSHOTS/S093.jpg).

**Atlas proposal:** one canonical record header includes ID/title, current lifecycle state, site/path, primary asset, assignee, priority and SLA. The drawer uses a reduced projection of the same header, and every related link carries context. Full pages group Overview, Execution, Related Records, Costs, Documents and Timeline according to role. Keep status changes as named actions with reason/validation feedback; do not silently offer a button with no observable effect.

## Forms and validation

Work-order creation separates basic details, location/assets, spare parts, SOP, attachments and execution. PPM reuses that structure and adds scheduling and incoming tasks. Asset creation groups information/location/lifecycle. The structure reduces one very long form, but tabs can show error badges before interaction and green completion marks on optional empty panels. Several labels are untranslated keys. PPM Create briefly appeared enabled before settling to disabled; that is a render-timing observation, not a validation exploit. [S006–S012](../06_SCREENSHOTS/S006.jpg), [S044–S047](../06_SCREENSHOTS/S044.jpg), [S091](../06_SCREENSHOTS/S091.jpg).

Attachments explain that a work order must be saved first, whereas the same modal presents an upload area. Asset Lifecycle shows timestamps and metrics before creation. Workflow creation starts with a 65% progress bar despite blank required inputs. These patterns make the apparent state more confident than the user's actual progress.

**Atlas proposal:** show required indicators consistently, validate after blur/attempted progression, give an error summary linked to the exact field/tab, and preserve all inputs on failure. Mark optional sections as optional rather than complete. When an action is unavailable, explain its prerequisite. Label drafts distinctly and display audit events only for persisted records. Separate “configured” from “tested” for schedules and automation.

## SOP builder and visual workflow editor

The SOP library distinguishes definitions/templates from instances. Its builder combines basic information, hierarchical sections and a field list. The type picker has search and Basic/Advanced/Media categories; the field inspector separates common properties from type-specific configuration and validation rules. This is a useful progressive-disclosure pattern. [S050–S054](../06_SCREENSHOTS/S051.jpg).

The workflow editor uses pools, lanes and task cards. Classification badges, asset counts and missing-assignment warnings surface incomplete configuration on the canvas. Context actions support task configuration. However, task text and lane labels can be cramped, warning meanings depend on tooltips and the shared PPM inspector opens under a Create title for an existing task. The process model also uses terms that are distinct from Atlas's condition/action automations. [S057–S061](../06_SCREENSHOTS/S060.jpg), [S102–S104](../06_SCREENSHOTS/S103.jpg).

**Atlas proposal:** build a reliable form schema and versioned result model before the form-builder UI. Build automation as readable “when / if / then” rules first; add process packages only for real dependency requirements. A later canvas needs zoom/fit, an outline, readable labels, a validation panel linked to nodes, keyboard navigation, undo semantics and clear draft/published versions. A canvas should be an editor for a tested execution model, not a substitute for one.

## Dashboards and truthful feedback

Sentrix offers a visually distinct analytics hub with command-center/operations/financial tabs and a location dashboard. The approach is useful: executive overview and local operations are different jobs. The observed values are not reliable specifications for Atlas metrics. Undefined “Optimal/Peak” reassurance, empty charts, unexplained percentages and zero-cost indicators are weak evidence. The financial panel explicitly says mapping is unfinished. The report generation and resource library show raw endpoint errors. [S021–S026](../06_SCREENSHOTS/S021.jpg), [S020](../06_SCREENSHOTS/S020.jpg), [S083](../06_SCREENSHOTS/S083.jpg).

**Atlas proposal:** show data freshness, scope, metric definitions and underlying records. Use “unavailable” for unimplemented or failed data, not zero. Errors should say what failed, retain filters and offer retry or another route; technical request paths belong in expandable diagnostics. An exception queue with ownership, severity, age and next action is more useful than a decorative executive dashboard.

## Accessibility and responsive behavior

This was not a formal WCAG audit. No keyboard-only or screen-reader session was run. Evidence supports narrower findings: several icon actions lack meaningful accessible names; narrow-screen record tabs lose textual labels and have no DOM `aria-label`/`title`; translation keys leak into controls; some UI text is small and table rows crowded. Contrast ratios and focus trapping were not measured, so no compliance score is assigned.

At 390×844 the settled task list reflows but stacks summary and view controls so the table begins near the bottom. The full record reflows well after settlement, while the top bar remains clipped and an untranslated current-status label exceeds its container. The immediate inline resize observation was transitional; saved S099 had already reflowed and S101 is the deliberate settled recheck. Root/body width measurements are 390, so do not claim document-wide overflow from the first screenshot. [S100](../06_SCREENSHOTS/S100.jpg), [S101](../06_SCREENSHOTS/S101.jpg), [metrics](RESPONSIVE_METRICS.json).

**Atlas proposal:** retain accessible names for icons; use 44px touch-target goals where practical; provide visible focus, error associations and dialog titles; verify keyboard traversal. On mobile, prioritize assigned jobs, quick search/scan, task evidence and sync state. Collapse summaries into compact chips, use a context-aware app bar and reduce filters to a discoverable sheet. Test at actual device sizes with realistic long names and translated labels.

## Proposed UX acceptance checklist

- User can identify current site/subtree and active filters on every list and dashboard.
- Every count/chart opens the exact contributing records; export matches them.
- Drawer and full page show the same lifecycle state, owner and relationships.
- Every visible action either succeeds, opens a clear surface, or explains why unavailable.
- Loading, empty, unauthorized, unavailable and failed states are visually distinct.
- Drafts do not masquerade as saved audit records; validation is specific and timely.
- No untranslated keys or private-use glyph-only accessible names in supported languages.
- Main field execution is usable at 390px without losing action labels or record context.
- Destructive and status-changing actions have proportional safeguards and retained history.
- A realistic end-to-end task is tested with a manager and a technician before adding another module.
