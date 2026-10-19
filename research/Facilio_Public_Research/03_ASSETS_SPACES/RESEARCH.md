# Portfolio hierarchy and Asset 360

Research date: **2026-10-17**. This synthesis uses public Facilio documentation. Atlas capability statements are hypothetical because no Atlas installation or source repository was examined.

## Supported structure and navigation

[Creating Space Hierarchy](https://facilio.com/help/docs/user-guide/facilio-modules/portfolio-management/illustrating-portfolio-management/Creating-Space-Hierarchy/) documents sites containing buildings, buildings containing floors, and spaces with subspaces. Spaces can also belong directly to a site or building; those without a floor are treated as independent spaces. This matters when modeling gardens, parking and other areas that do not fit a rigid floor tree. Site configuration includes timezone and geographical boundary; buildings and floors have occupancy and area attributes. The same page demonstrates floor-plan upload and a builder that places descriptive markers and interactive controls. Treat connected lighting/temperature control as documented UI intent, not evidence that every integration is immediately available.

[Viewing and Associating Portfolio Details](https://facilio.com/help/docs/user-guide/facilio-modules/portfolio-management/illustrating-portfolio-management/Viewing%20and%20Associating%20Portfolio%20Details/) is the strongest location-detail reference. A selected place gathers associated locations, readings, operating information, documents and counts of assets, alarms and work orders. Counts link to the relevant module. Related records, safety information and history occupy separate sections. Hazards can be associated with the location, with precautions appearing from the configured safety plan. This demonstrates contextual navigation rather than an isolated address form.

## Asset lifecycle and operational context

[Working with Assets](https://facilio.com/help/docs/user-guide/facilio-modules/asset-management/working-with-assets/) describes maintenance schedules, readings, ownership cost, downtime/stateflow history, lifecycle dates, transfers and QR codes. Those are ingredients of an Asset 360 workspace, although the phrase here is an analytical label rather than a guarantee of one specific Facilio screen. [Managing Assets](https://facilio.com/help/docs/user-guide/facilio-modules/asset-management/working-with-assets/managing-assets/) provides concrete creation, status, rotating-asset and relocation interactions. Use the screenshots to investigate which actions are contextual and what information is required to complete a transfer.

[Readings](https://facilio.com/help/docs/admin-guide/space-assets/readings/) extends the model beyond static records. Configurable measurements apply to physical assets and location levels; thresholds can support alarms and the values feed analytics and maintenance use cases. [Managing Relationships](https://facilio.com/help/docs/admin-guide/customization/managing-modules/customizing-the-module/managing-relationships/) supplies a broader platform reference for configurable forward/reverse links, including many-to-many and meter relationships.

## Hypothetical Atlas opportunities

Audit Atlas's location model before introducing new hierarchy levels. Potential improvements include a portfolio browser, contextual location overview, asset timeline, operating calendars, linked costs/documents and visible maintenance/alarm history. Reusable relationship navigation could deliver more value than separate disconnected screens. Indoor floor plans are a later opportunity if actual customers need spatial dispatch or controls; first establish accurate identifiers, permissions and data ownership.

## Evidence limits and review questions

The public pages are strong evidence of intended forms, navigation and relationships, but do not establish asset-volume limits, history retention, cross-site transfer restrictions or integration commissioning effort. Screenshots may reflect different product generations. Verify timezone handling, independent-space permissions, move history, and the distinction between meters, assets and virtual calculated elements before turning this reference into a schema proposal. Preserve URL capitalization and encoded spaces when following the location documentation.
