# Developer interfaces and API concepts

Research date: **2026-10-17**. This report uses publicly accessible static documentation. No authenticated APIs, FOQL queries, tenant metadata, developer accounts or CLI commands were executed. SDK/CLI details reflect documentation observed on this date and may change. Atlas source was not inspected.

## Observed public evidence

The [current developer portal](https://facilio.com/developers/) links REST APIs, scripting, Connected Apps, Vibe, agents, SDKs and FOQL. The older [Help developer guide](https://facilio.com/help/docs/category/developer-guide/) still links a separate legacy documentation host. Retain the provenance of both, but use current official pages when describing current developer products.

The [API reference landing page](https://facilio.com/developers/docs/api-reference/) links the public [Swagger UI](https://facilio.com/developers/swagger-ui.html). Static inspection of that shell found its [OpenAPI YAML reference](https://static.facilio.com/developers/api/v5/openapi.yaml). The specification host returned HTTP 403 for its robots file, so collection stopped at the link. The specification was not fetched. This report makes no claim about complete endpoint coverage, rate limits or response schemas. A public documentation shell is not evidence of a working API request or entitlement.

The Help guide separately documents [developer-role administration](https://facilio.com/help/docs/admin-guide/developer-space/API%20Setup/Overview/): assigning Dev Admin enables the API Clients section in profile settings. The assignment and revocation pages show access-management UI. This establishes a documented administrative concept, not the full authorization contract of every current API product.

[FOQL Overview](https://facilio.com/developers/docs/foql/index/) documents a read-only, SQL-like interface over module records. It supports selecting fields, filters, relationship traversal, grouping, aggregates, ordering and pagination; the navigation also links subqueries, errors and limits. The public page identifies a POST-based query endpoint and bearer-token example. The endpoint was not called. Its value here is the product concept: one query vocabulary spanning operational modules.

[Connected Apps SDK Installation](https://facilio.com/developers/docs/connected-apps/sdk-reference/installation/) documents CDN-delivered browser SDK channels rather than an npm package for that embedded-app interface. It recommends the beta channel for new development/mobile support in the observed documentation. Do not confuse this with Vibe’s separately named npm SDK. The adjacent research file explains those extension surfaces.

[Script Execution Contexts](https://facilio.com/developers/docs/script-reference/execution-contexts/) exposes invocation contracts: record-bound automation receives a map associated with the module, whereas scheduler execution has no triggering record. These contracts are useful API-design references even without executing scripts.

## Atlas implementation opportunities — inference

Publish a versioned API contract alongside the product. A premium CAFM should let a customer inspect resource definitions, permissions, examples, pagination, filtering and errors without guessing undocumented routes. This can support integrations, imports, customer portals and automation through one maintained surface.

Prefer a stable record/resource contract over mirroring every frontend screen. Model assets, spaces, vendors, contracts and work separately, with explicit relationships and identifiers. Publish action endpoints for business transitions so integrations cannot accidentally sidestep approvals, required evidence or audit history by directly assigning a status.

An authorized query layer could simplify cross-module dashboards, but it needs deliberate boundaries: enforce organization and row permissions, cap complexity, constrain relationship depth and aggregate sizes, and report helpful validation errors. SQL-like syntax alone does not establish safety or performance. These are recommendations for Atlas, not reverse-engineered guarantees about Facilio.

For implementation sequencing, first inventory Atlas’s actual API and authorization model, then stabilize essential resources and transition actions. Add generated reference documentation and working examples. Introduce broader cross-module query functionality only after the data relationships and permission rules are consistent. Build compatibility tests around customer-facing contracts rather than copying vendor examples.

## Open questions and evidence limits

- Does the current Swagger reference fully cover system modules and custom modules?
- How are tenant-defined field names and schemas discovered?
- What are the actual pagination, rate, concurrency and query-complexity limits?
- Which OAuth, token and service-account flows are available for each product/region?
- How are API versions deprecated, and which capabilities require specific editions?

Answers require further public documentation or authorized vendor clarification; the static research does not establish them.

## REA analysis prompts

1. Inspect only publicly linked Swagger/documentation assets and record their exact provenance; do not execute tenant requests.
2. Map documented resources/actions to an independent Atlas domain model and identify missing relationship contracts.
3. Compare the query language’s purpose with the needs of Asset 360 and portfolio dashboards.
4. Produce a public-documentation checklist for Atlas, marking every unsupported assumption explicitly.
