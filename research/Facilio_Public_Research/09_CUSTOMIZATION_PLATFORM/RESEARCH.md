# Customization platform: product research

Research date: **2026-10-17**. Public static documentation only; no tenant configuration was opened or changed. Observations describe what Facilio documents. Atlas opportunities are design hypotheses because the user’s Atlas codebase was not audited.

## Observed public model

[Customization Overview](https://facilio.com/help/docs/admin-guide/customization/managing-modules/overview/) describes modules containing records, fields and templates. [Types of Modules](https://facilio.com/help/docs/admin-guide/customization/managing-modules/types-of-modules/) separates protected system modules from customer-created modules. Both can have associated forms, fields and actions, while some default elements remain protected. [Creating a Module](https://facilio.com/help/docs/admin-guide/customization/managing-modules/creating-a-module/) connects a new business object to an initial template and optional stateflow.

[Managing Templates](https://facilio.com/help/docs/admin-guide/customization/managing-modules/customizing-the-module/managing-templates/) documents a form builder with typed controls, lookups, uploads, signatures, subforms and sections. Properties govern defaults, mandatory fields and editability. Lookup values can depend on another field; form rules react to initial load or field changes. Those rules can adjust visibility, editability, required inputs, values and picklist filtering. The screenshots make this a strong reference for progressively revealing relevant operational questions.

[Managing Fields](https://facilio.com/help/docs/admin-guide/customization/managing-modules/customizing-the-module/managing-fields/) presents shared system/custom field inventories and related-record aggregate fields. [Customizing Details Page Layout](https://facilio.com/help/docs/admin-guide/customization/managing-modules/customizing-the-module/customizing-details-page-layout/) documents layouts selected by record criteria and role sharing, with adjustable Summary/Related sections, field widths and tabs. The page identifies protected areas and a maximum of five configurable sections.

[Managing Relationships](https://facilio.com/help/docs/admin-guide/customization/managing-modules/customizing-the-module/managing-relationships/) covers relationship cardinalities, forward/reverse labels, indirect relationship paths and meter-specific associations. [Viewing Related Fields](https://facilio.com/help/docs/admin-guide/customization/managing-modules/customizing-the-module/viewing-related-fields/) explains lookup-based record links. [Viewing Extended Modules](https://facilio.com/help/docs/admin-guide/customization/managing-modules/customizing-the-module/viewing-extended-modules/) introduces parent/child modules with inherited properties. Together these reveal a configurable data model supporting the configurable screen model.

[Managing Custom Buttons](https://facilio.com/help/docs/admin-guide/customization/managing-modules/customizing-the-module/managing-custom-buttons/) shows actions placed on details, list rows, bulk selections and list toolbars, gated by permissions and criteria. This is useful evidence that customization includes operational behavior, not just additional fields.

## Atlas implementation opportunities — inference

The foundational upgrade is shared metadata: module definitions, typed fields, relationship definitions, form templates, record layouts and action definitions. Build operational modules on these primitives gradually. A single generic record editor is insufficient if different roles need different priorities, evidence and decisions.

Begin with one complete vertical slice, such as Asset 360: a common asset identity, category-specific attributes, location breadcrumbs, related work/cost/documents and role-sensitive actions. Reuse that infrastructure for vendor compliance or permits. This proves whether customization improves real work before investing in a large no-code designer.

Treat stored values, form presentation and authorization as separate concerns. Hiding a field must not authorize or forbid backend access. Enforce types and required business constraints on the server, even when conditional forms guide the user. Scope records and lookups by organization/site permissions. Define schema evolution and import/export behavior before offering unrestricted field creation.

Role-specific detail pages could be a visible premium upgrade: a technician sees the job/evidence next; a manager sees risk and cost; procurement sees commercial commitments. Use shared records and explicit permissions beneath those layouts. These are proposed Atlas patterns, not a claim that Facilio uses a particular database or rendering architecture.

## Open questions

- How are module/schema revisions migrated, audited and promoted between environments?
- How are conflicting layout criteria resolved?
- Which custom controls, relationships and defaults work offline or on mobile?
- What limits apply to custom modules, fields, rollups and relationship traversal?

## REA analysis prompts

1. Annotate the form builder’s control palette, properties panel, rule editor and save feedback.
2. Separate form layout, detail layout and relationship configuration in the observed information architecture.
3. Produce an independent Atlas layout spec for technician, manager and vendor views of the same record.
4. Rank customization options by real operational value and implementation dependency; avoid reproducing every setting first.
