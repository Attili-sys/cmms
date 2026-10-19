# AI product and interaction research

Research date: **2026-10-17**. These are public-documentation observations and vendor presentations. No AI feature, tenant, model, integration or action was executed. Atlas proposals below are independent design inferences.

## Documented assistant interactions

The [FM Co-Pilot guide](https://facilio.com/help/docs/ai-guide/fm-co-pilot/) carries **April 2026, v1.0**. It describes a global conversation surface for operational questions and bulk changes. Users inspect affected records and approve or reject proposed writes. The guide specifies up to 50 records per query, 10 MB per uploaded file and personal prompt templates. Voice input includes a transcription review step. These limits belong to that documented version; they do not establish the limits of every Atom product.

The [Technician Co-Pilot guide](https://facilio.com/help/docs/ai-guide/technician-co-pilot/) describes a different scope: the currently open record. Its web/mobile header entry point opens a contextual conversation panel. Users can query history or propose notes and other updates, then review the change preview. The guide explicitly confines its context and requires approval for changes. Both copilots depend on administrator-enabled feature access.

The [Form Assistant](https://facilio.com/help/docs/ai-guide/form-assistant/) takes documents or natural-language descriptions and proposes field values inside an existing form. Confidence is communicated visually, and users review/correct values before saving. This preserves the familiar form as the final source of truth. An Atlas implementation should pair color with readable confidence labels and explanations; that accessibility improvement is a recommendation, not an observed Facilio feature.

The [Photo Validator](https://facilio.com/help/docs/ai-guide/photo-validator/) compares before/after evidence at work-order or task level. The documented detailed view puts images beside a scoring explanation. It assists a manager’s existing approval decision. Its April 2026 guide says a score is computed once and does not refresh after photos are replaced. Record this limitation rather than assuming continuous revalidation.

Additional public AI guides cover [dashboard creation](https://facilio.com/help/docs/ai-guide/dashboard-builder/), [form text assistance](https://facilio.com/help/docs/ai-guide/text-assistance/), [scripting assistance](https://facilio.com/help/docs/ai-guide/script-assistant/) and [Ops Vision](https://facilio.com/help/docs/ai-guide/ops-vision/). Their source capsules and local images provide the entry points; availability and production behavior remain untested.

## Marketing and demo evidence

The [Atom suite page](https://facilio.com/ai-suite/) presents Mira for service intake, Luca for invoice validation, FM Copilot for operational actions and OpsVision for portfolio interpretation. The [AI assistants product page](https://facilio.com/product/atom-ai-assistants/) illustrates an exception-to-action-to-outcome loop, completion validation, audit-report interpretation and contractor communications. Treat broad autonomy, accuracy and deployment claims as vendor statements.

The [public video library](https://facilio.com/videos/) adds focused walkthroughs of helpdesk onboarding, channels, contact capture, conversation history, invoice checking, compliance and portfolio analysis. Exact embedded player and direct MP4 references are preserved in [VIDEO_LINKS.md](../14_VIDEOS_LINKS/VIDEO_LINKS.md). Playback and end-to-end behavior were not tested. An illustrated future-facing scenario should not override a specific user guide’s approval requirement.

## Atlas opportunity — inference

Start with three narrow interactions: draft a work order from a technician’s description; explain the current asset/work record with source links; propose a resolution note for review. Show the record scope, the fields that will change and the normal validation/approval result. Retain attribution and change history.

Build broader exception summaries only after location, priority, SLA and cost data are trustworthy. Portfolio questions require consistent metric definitions and authorization. A voice intake agent also needs reliable requester identity, location disambiguation and human escalation; a polished conversation alone does not supply those foundations.

The highest-value REA question is how suggestions, evidence, record context and business actions share one interface. Inspect the captured copilot and form-assistant screens before designing a general chat page.

## Unknowns

Model providers, regional processing, actual error rates, action coverage, tenant licensing, current feature limits and the relationship among differently dated AI product names are not established by this collection. No performance or accuracy claims have been independently validated.
