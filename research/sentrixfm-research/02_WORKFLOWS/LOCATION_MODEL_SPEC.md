# Location model: observed specification and Atlas opportunities

## Scope and confidence

This specification uses **S015–S029**, focusing on the global location selector, location dashboards and location administration. Capture times around 2026-10-17 22:20–22:23 UTC correspond to **2026-10-18 01:20–01:23 in Qatar**. Sources are the supplied [evidence manifest](../00_INDEX/EVIDENCE_MANIFEST.json), accessibility snapshots, screenshots and [observed design tokens](../03_UI_UX/DESIGN_TOKENS_OBSERVED.json). No browser operation or network request was made to write this analysis.

The capture operator opened an existing location detail and edit form. **No field was changed, no image selected, no coordinate action executed, and no Update submitted.** No create, delete, move, map navigation, context switch or settings mutation is established. Consequently, form controls describe visible affordances only; they do not prove persistence, validation enforcement, permissions or backend location scoping.

The central modeling constraint is important: Sentrix visibly presents a **generic location hierarchy with numeric levels**. A node named Floor 101 and a building-shaped icon do not prove typed Portfolio → Site → Building → Floor → Space entities. This document keeps observed labels separate from a proposed Atlas CAFM model.

## Entry points and context selection

The main sidebar places **Locations / Sublocations** under FACILITY STRUCTURE alongside Store & Inventory, Assets and Consumables. Location Dashboard is separately grouped with Analytics Dashboard and Reporting. The global header retains the current location regardless of which of these pages is visible. This makes location both an administrative resource and an operational context, but the rules connecting those concepts were not tested.

In [S015](../06_SCREENSHOTS/S015.jpg), the global selector is open on **Main Office**, with **Main** badge, description **Headquarters** and a selected checkmark. **Demo Branch** appears beneath with **Empty location for demo purposes**. Only two choices are visible, while location administration later reports fourteen records. A plausible interpretation is that the selector lists roots or allowed operational contexts, but that is unverified. It could also reflect filtering, permissions or a distinct scope. Do not encode the two-choice list as the complete location inventory.

The report toolbar reads All Locations while the global header reads Main Office. Likewise, the analytics hub calls its data global while showing Main Office identity. These observations reveal an ambiguous context boundary rather than a proven access-control rule. [S015](../06_SCREENSHOTS/S015.jpg), [S021](../06_SCREENSHOTS/S021.jpg)

**Atlas recommendation:** define scope explicitly as a selected node plus descendant-inclusion policy and authorization intersection. Display a readable path in context selectors. Differentiate “current workspace,” “record location,” “report filter” and “default/main site.” When switching context, warn about unsaved work and explain the newly effective record set. These are independent product requirements, not observed Sentrix behavior.

## Location management overview

The observed list route is [Locations Management](https://sentrixfm.com/manager/business/locations/list). [S027](../06_SCREENSHOTS/S027.jpg) shows heading **LOCATIONS MANAGEMENT**, subtitle **Manage your business locations**, and breadcrumb **Home / Admin / Super Admin / LOCATIONS MANAGEMENT**. This administrative breadcrumb coexists with the facility-structure sidebar link. It indicates multiple navigation vocabularies, not proof that only a super administrator can access the page.

Four summary cards show **Total Locations 14**, **Active Locations 14**, **Inactive Locations 0**, and **Current Location Main Office**. The active view is **Hierarchy**; a segmented switch also offers **Table** and **Map**. Neither alternate view was inspected within this evidence scope, so their columns, map markers, filtering, clustering and navigation remain unknown.

The hierarchy section includes a count **14**, a separate Hierarchy badge, heading **Location Hierarchy**, and guidance to expand/collapse or select a location. Two visible top-level rows are Demo Branch and Main Office. Demo Branch has description/city **Empty location for demo purposes · Tokyo** and an Active badge. Main Office has **Headquarters · London**, Main badge, and **2 sub-locations**. Its expanded branch begins with **Floor 101**, **Level 1**, and description **Floor 1 at level 1 of Main Office · London**. Deeper descendants are outside this screenshot’s stable visible area. [S027](../06_SCREENSHOTS/S027.jpg)

Indented connectors, chevrons, repeated location illustrations and right-aligned icons communicate hierarchy. Capture notes identify row affordances as view, create sublocation, edit, settings and delete; their exact invocation results were not tested. The screenshot visibly supports eye, plus, pencil, gear and trash symbols. Some rows are horizontally dense; the lower branch continues below the viewport, near a floating chat button. This is evidence of the desktop layout only.

## Observed model and inference boundary

The minimum supported conceptual model contains a location identity, name, description, active flag, main flag, current-context indication, numeric level, parent/child presentation, address information, coordinates and an image affordance. “Parent/child presentation” does not establish the database schema or whether a node has exactly one parent. “Current location” could be user/session context rather than stored resource metadata. The captured detail route contains a location-prefixed UUID-like identifier; it does not establish a universal identifier format.

Do not infer explicit site/building types, floor numbering rules, leaseable spaces, gross/net area, occupancy, geofenced boundaries, tenant ownership, timezone inheritance, service calendars, polygon geometry or asset inheritance. None is demonstrated here. Likewise, “2 sub-locations” is a displayed count whose direct-child versus full-descendant meaning was not tested. Level 0 and Level 1 reveal depth labels for captured nodes, not a fixed maximum depth.

**Atlas recommendation:** retain generic parent links for flexibility, then add explicit, optional semantic types where business workflows require them. A site and a room should not be distinguished solely by tree depth. Allow a realistic campus to have extra grouping levels without breaking reporting or asset addresses. Define any permitted parent/type combinations through configuration rather than silently assuming every enterprise has the same hierarchy.

## Main Office detail surface

The [captured detail](../06_SCREENSHOTS/S028.jpg) is a full page with **MAIN OFFICE**, description Headquarters and breadcrumb back to Locations Management. Header actions are **Back to List**, **View on Map**, **Edit** and **Delete**. Presence of Delete is not evidence that deletion is permitted or safe; no confirmation or result was inspected.

A prominent information strip says **Viewing location: Main Office** and explains that the page displays that record’s details. A left identity/navigation card shows an image, Main Office and Main Location. The accessibility snapshot lists **Overview — General location information**, **Address — Location address details**, **Coordinates — GPS location data**, and **Technical — ID and metadata**. Only Overview content was inspected. The other navigation labels establish section intent but not their fields or whether selecting them changes route, tab or scroll position. [S028 snapshot](../07_EVIDENCE/S028.txt)

Location Overview displays Name **Main Office**, Status **Main Location**, Active **Yes**, Main Location **Yes**, Level **0**, Current Location **Yes**, Description **Headquarters**. These separately rendered concepts should remain separate in analysis. In particular, “Status: Main Location” blends role/default semantics with a status label, while Active is shown independently. Atlas should avoid storing all of them as one mutually exclusive enum simply because the interface groups them visually.

**Atlas recommendation:** make detail pages answer operational questions beyond identity: where is this place, what belongs to it, who is responsible, and what needs action? Use a stable breadcrumb, explicit type and children count, manager/contact ownership, related assets/work, and a scoped dashboard link. Keep the destructive action visually distinct. An independent implementation can use these patterns without copying the original page composition or imagery.

## Existing location edit form

[S029](../06_SCREENSHOTS/S029.jpg) shows **EDIT LOCATION**, subtitle **Update location details**, breadcrumb ending Edit Location, **Cancel**, and **Update**. The [snapshot](../07_EVIDENCE/S029.txt) marks Update disabled. It was not submitted, so its disabled state cannot be conclusively attributed to a pristine form, missing required values or another condition.

Visible fields and captured initial values are:

| Field | Required indicator | Captured value or placeholder |
|---|---|---|
| Name | Yes | Main Office |
| Manager | Yes | Enter manager user ID; dropdown collapsed |
| Address | Yes | Empty; Enter street address |
| City | Yes | London |
| State/Province | Yes | Empty; Enter state or province |
| Country | Yes | UK |
| Postal Code | Yes | Empty; Enter postal code |
| Description | No | Headquarters; multiline control |

Manager appears to be a dropdown, but neither user choices nor search behavior were inspected. A raw help key, **LOCATIONS.FORM.HELP.MANAGER_REQUIRED_LEVEL0**, is visible below the address fields. This exposes untranslated UI text and suggests an intended level-specific rule; it does not prove the rule’s actual implementation. Existing required address/manager fields appear empty, but no validation attempt was made. It is unknown whether the record is legacy/demo data, whether data mapping is incomplete, or whether validation is deferred.

The form includes **Location Image**, drag/drop or browse guidance, supported formats **JPG, PNG, GIF, WebP**, maximum **5MB**, and **Choose Image**. Upload acceptance, preview, removal, server checks and persistence were not tested. No status, main-location toggle, parent selector or type field is visible in the captured form area; this does not establish that they exist nowhere else.

Coordinates offers **Get from Address**, **My Location**, **Clear**, and **How to use the map**. Numeric latitude/longitude controls show approximately **51.47256372** and **−0.16263628**. The accessibility tree retains slightly different floating-point precision, so do not infer stored rounding from the screenshot. It also records a selected-location marker, zoom-in/out controls and Leaflet/OpenStreetMap attribution below the visible screenshot area. No geocoding, browser permission, map click, marker drag or coordinate save was tested. [S029 snapshot](../07_EVIDENCE/S029.txt)

## Dashboard relationship and unresolved consistency

Location Control Center shows Work Orders **0**, Scheduled PPM **0**, SLA Compliance **0.0%**, Critical Assets **0**, while its lower content contains active task rows and an asset summary **Active 10 / Maint. 0 / Down 0**. The same coexistence remains in evidence after Load. Top Asset Issues shows named assets, issue counts and Next PPM N/A. [S024](../06_SCREENSHOTS/S024.jpg), [S025 snapshot](../07_EVIDENCE/S025.txt), [S026](../06_SCREENSHOTS/S026.jpg)

These captures demonstrate location-oriented presentation of operational data but not a validated relationship query. Cards and rows may use different status/time/entity definitions or loaders. The scope, denominator and update behavior are unverified. Similarly, analytics reports fourteen active locations but zero assets; this cannot resolve whether location descendants are included. Use these inconsistencies as questions for an implementation contract, not as grounds to invent missing backend behavior.

## Independent Atlas implementation specification

Proposed location data should separate stable identity, organization ownership, parent reference, display name, optional semantic type, lifecycle state and address/coordinate metadata. Treat “main/default” as a configured organizational preference with defined uniqueness, and “current” as user/session context. Keep manager assignment as an explicit relationship. Store numeric depth as derived information where practical, avoiding conflicting depth and parent values.

Proposed workflows should support create root, create child, inspect, edit metadata, move with impact preview, deactivate and archive. These were not observed to work in Sentrix. Before implementing moves, define how descendants, assets, scheduled work and historical reports behave. Preserve immutable historical location references when work closes; otherwise moving an asset or renaming a room can silently rewrite the apparent context of old maintenance records.

For Atlas UX, use tree search that preserves ancestor paths, visible selected/current/default distinctions, meaningful action labels, keyboard expand/collapse, and readable long names. Keep Table/Hierarchy/Map as alternative views of the same filtered set, with counts that reconcile. A map should distinguish missing coordinates from zero coordinates and should not require rooftop GPS precision for an internal room. A blank state should say whether there are no children, no search matches or insufficient access.

For forms, show validation explanations adjacent to fields and explain disabled actions. Localize help strings and replace internal ID wording with a searchable person selector. Make location/geocoding consent explicit, retain manual entry, and give clear errors for invalid coordinates or unavailable lookup services. These are recommended behaviors, not claims about the captured implementation.

The observed shell uses Poppins and compact controls on a pale background, with blue primary actions, outlined secondary controls, purple/green badges and red destructive affordances. The token file reports 13px body text and primary **#556ee6** at a **1280 × 657** viewport. Prefer an independent Atlas design system that keeps hierarchy/action contrast clear; token sampling does not establish responsive/mobile behavior. [design tokens](../03_UI_UX/DESIGN_TOKENS_OBSERVED.json)

## REA prompts and acceptance questions

1. Annotate S027’s generic hierarchy without replacing node names with unproven schema types.
2. Separate record flags, navigation context and aggregate scope using S015/S021/S028.
3. Translate S029 into an independent form specification including untouched, invalid, loading, failure and saved states; mark every uncaptured state as proposed.
4. Define reconciliation tests so child counts, active totals, asset membership and dashboard drilldowns agree.

Outstanding questions include parent cardinality, hierarchy depth limits, main-location uniqueness, authorized context switching, address inheritance, coordinate meaning, manager requirements, deletion constraints and audit coverage. The strongest conclusion is a usable hierarchy/detail/edit interaction reference with several observed clarity gaps. Persistence, authorization and a fully typed enterprise space model remain unverified.
