# Sentrix assets and inventory: observed product specification

**Later evidence:** [Full record and builder follow-up](FULL_RECORD_AND_BUILDER_SUPPLEMENT.md) adds S091–S106 and corrects the ambiguous S014 drawer observation. Read both before drawing conclusions.

Prepared **2026-10-18, Asia/Qatar** from local evidence **S030–S042**. UTC acquisition timestamps are preserved in the [manifest](../00_INDEX/EVIDENCE_MANIFEST.json). Screenshots and accessibility snapshots were reviewed locally; no browser or network access was used for this analysis. No asset, store, item, requisition, attachment or status was created or changed. Atlas has not been inspected, so its adaptation section describes independent proposals rather than verified missing features.

## 1. Evidence boundaries and timing

**Observed** means visible in the supplied captures or recorded by their operator. **Inferred** identifies a plausible domain relationship, not a recovered implementation. **Proposed** identifies an Atlas design choice to assess later. Accessibility snapshots may include content below the screenshot viewport and repeated application-shell elements; those repetitions are not separate module features.

[S031](../06_SCREENSHOTS/S031.jpg) records a status-history retrieval error while the underlying asset screen is visible. [S032](../06_SCREENSHOTS/S032.jpg) was captured during dismissal: the error panel is fading, and its snapshot still describes the dialog. It must not be presented as a settled overlay defect. [S033](../06_SCREENSHOTS/S033.jpg) is the settled asset overview and [its full snapshot](../07_EVIDENCE/S033.txt) supplies the substantive record fields. [S037](../06_SCREENSHOTS/S037.jpg) independently repeats the history error when that tab is selected. These observations concern history retrieval; the registry and record overview were accessible.

## 2. Asset registry

**Observed — S030.** Asset Management offers Advanced Filter, Table View, Tree View and New Asset. The table combines an image/name/description cell with type, status, QR code, location, work-order/PPM metric badges and last-updated date. The operator records ten demo assets; this is the captured sample, not a scale claim. Classification values vary across equipment, component and tool. Visible records have commissioned status. Tree View, filters and new-asset creation were not exercised in this evidence set. [S030](../06_SCREENSHOTS/S030.jpg)

Embedding QR codes and maintenance counts directly in the registry makes a physical asset and its operational history discoverable together. However, image previews and wrapped subjects make rows tall. Full QR symbols occupy substantial width even when scanning is not the user's immediate task. Locations show a deep leaf, while higher-level ancestry is not visible in the registry cell. The selected record's detail later shows a blank location path; this inconsistency should be investigated without assuming either the location reference or underlying data was lost.

**Proposed for Atlas:** prioritize asset identifier, name, location breadcrumb, lifecycle/operating condition and maintenance risk. Offer compact and image-rich density modes. Put QR viewing/printing behind a clear action or expandable cell; do not sacrifice scanability to display every code permanently. Keep table/tree switching scoped to the same query, and define how counts relate to visible filters.

## 3. Asset detail as a contextual workspace

**Observed — S033.** The full page has title/breadcrumbs, Back/Edit/Change Status/Delete actions, then Overview, Work Orders, PPM Schedules, Documents and History tabs. The overview begins with a large image section; the full accessibility snapshot also exposes basic information, location information and quick actions. Fields include asset type, commissioned status, serial number, manufacturer, model, description, location path and related-asset count. A QR section exposes Copy, Download, Print and Share affordances. Contextual Create Work Order and Schedule PPM controls are present, alongside unresolved generic localization keys on other actions. None was executed. [S033](../06_SCREENSHOTS/S033.jpg), [snapshot](../07_EVIDENCE/S033.txt)

The image-heavy top of the overview consumes most of the visible desktop height before important technical fields appear. Demonstration imagery does not consistently depict the named asset, so it provides layout evidence rather than trustworthy equipment documentation. The snapshot's serial/manufacturer/model values are unnecessary for understanding the schema and are intentionally not reproduced. The detail's location path displays a dash despite the registry's leaf location. Related assets displays zero; this does not reveal whether the intended relationship is assembly, redundancy, dependency or merely association.

[S034](../06_SCREENSHOTS/S034.jpg) and [S035](../06_SCREENSHOTS/S035.jpg) show empty work-order and PPM associations with contextual creation calls to action. They demonstrate relationship-oriented navigation and a proposed next step, not successful propagation of asset context into a new record. Both an upper action and a repeated empty-state action appear. The selected asset's empty associations do not prove the wider trial has no work orders or PPMs.

[S036](../06_SCREENSHOTS/S036.jpg) separates Photos from Documents & Manuals, each with a drop zone and file-selection control; the latter is clearer in the full snapshot than the visible viewport. No upload was attempted. File-size/type rules, versioning, document permissions, progress, failure recovery and storage are unknown. [S037](../06_SCREENSHOTS/S037.jpg) shows a history-empty presentation behind an error. A retrieval failure must not be interpreted as proof of zero historical events.

**Proposed for Atlas:** place technical identity and operating context ahead of decorative imagery; distinguish lifecycle status, operational condition and maintenance health explicitly. Keep location ancestry consistent everywhere. Show an inline history-retrieval failure with Retry while retaining other tabs, and distinguish failed, loading and genuinely empty states. A unified asset workspace could connect maintenance, planned work, documents and recorded changes without claiming telemetry, depreciation, warranty or cost functionality that these captures do not demonstrate.

## 4. Stores, items and requisitions

### Stores

**Observed — S038/S039.** Inventory Stores contains Advanced Filter, View Requisitions, View All Consumables and Create Store. The empty table has name, location, description and actions. Create Store opens a compact modal requiring name and location, with optional description. Required-field messages appear before input, and Create is disabled. Neither location options nor submission behavior was inspected. [S038](../06_SCREENSHOTS/S038.jpg), [S039](../06_SCREENSHOTS/S039.jpg)

**Inferred:** a store belongs to a physical location and groups inventory. The captures do not establish multiple-location membership, bin hierarchy, custodians, transfers or receiving. An empty store registry is a local observation; it does not show whether another scope has populated stores.

### Consumables

**Observed — S041/S042.** Inventory Management offers All Items, Reorder Needed, Spare Part, Material and Tool segments, plus filtering and Add New Item. The empty table anticipates item details, status, stock balance, unit price, expiry and actions. “Consumables” is therefore an umbrella term that includes tools, not proof that all objects are consumed in the accounting sense. [S041](../06_SCREENSHOTS/S041.jpg)

The creation modal displays:

| Field group | Visible inputs and defaults | Boundary |
|---|---|---|
| Identity | Required name and type; optional SKU/code | Uniqueness and full type options untested |
| Storage | Required store/storage location | Store picker not expanded |
| Quantity basis | Required unit of measure, default Pieces | Unit conversions and fractional quantities unknown |
| Stock policy | Minimum and maximum values initially zero | Help indicates alert threshold/capacity, not executed automation |
| Pricing | Unit price initially zero, USD selected; purchase price | Purchase price help suggests last buying price; valuation method unknown |
| Tracking | Optional expiry and description | Batch/lot/serial tracking not shown |

Create Consumable is disabled; required messages appear for untouched name/type/store fields. Cancel and Discard Changes coexist. No values were entered and no creation was attempted. An SKU-looking placeholder must not be treated as an assigned identifier. [S042](../06_SCREENSHOTS/S042.jpg), [snapshot](../07_EVIDENCE/S042.txt)

### Requisitions

**Observed — S040.** The empty requisition queue has date, item, quantity, work order, status and actions, plus a zero-count description covering pending/processed requests. This supports an intended link between material demand and work execution. No request, approval, issue, rejection, stock movement or fulfillment action was observed. It does not demonstrate procurement, a purchase-order lifecycle or automatic replenishment. [S040](../06_SCREENSHOTS/S040.jpg)

## 5. Relationships and unknown backend rules

**Inferred model:** asset → location; asset ↔ related asset; work order → asset; PPM → asset; document → asset; store → location; inventory item → store; requisition → item and work order. This is a candidate conceptual map only. Cardinality, cascade behavior, access scope, shared item masters across stores and event retention remain unknown.

Assets and inventory both expose a tool concept. Do not assume these are one entity, automatically linked records or interchangeable resources. Commissioned status does not establish availability or health. The presence of unit/purchase price does not prove work-order costing or financial integration. QR controls do not establish public sharing, scanning authorization or mobile behavior. None of these questions was tested by mutations.

## 6. Independent Atlas adaptation and proposed acceptance criteria

Assess Atlas's existing asset, stock and maintenance objects before adding fields. A strong adaptation would preserve reliable identity and location context, make asset history resilient to partial errors, and distinguish physical assets from item quantities. Separate item master data, per-store balances, requisition demand and stock transactions if actual workflows require those distinctions. Any reorder alert should explain threshold, unit, reserved quantity and considered store. Translate labels consistently and delay error treatment until meaningful interaction; measure contrast, focus behavior and keyboard navigation independently.

The following are **proposed future acceptance criteria**, not tests performed here:

1. Registry and asset detail resolve the same location reference and readable ancestry, including after relocation.
2. History failures leave overview/documents usable and never display a false “no events” success state.
3. Contextual maintenance creation visibly preselects the intended asset and can be cancelled without side effects.
4. Asset status changes require permission and record actor, reason and effective time; permitted transitions are explicit.
5. Store/item required fields, unit rules and duplicate identifiers are validated consistently and explained accessibly.
6. Requisition planning, reservation, issue, return and adjustment have distinct audited effects if implemented; planning alone does not deduct stock.
7. Stock balance/reorder calculations reconcile to recorded transactions and a visible store scope.
8. Currency, precision, purchase price and valuation semantics are explicit rather than inferred from a label.
9. Uploads expose format/size limits, progress/retry and document permissions; QR actions have a clear authorization model.
10. Table/tree filters, empty/error states and keyboard access remain consistent on supported screen sizes.

The reference's strongest lesson is contextual linkage. Its unresolved errors and sparse inventory sample also show why a polished screen must be assessed separately from verified operational behavior.
