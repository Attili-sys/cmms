# Facilio public research → Atlas enterprise CAFM

**Prepared 17 October 2026.** A broad, deduplicated reference collection for independently upgrading Atlas’s product model and user experience. Public documentation and product illustrations are separated from design proposals. No Facilio account or Atlas codebase was accessed.

## Start here

1. [REA_TARGETS.md](REA_TARGETS.md) — ranked workflows, local screenshots and concrete analysis outputs.
2. [GAP_ANALYSIS.md](15_GAP_ANALYSIS/GAP_ANALYSIS.md) — upgrade opportunities grounded in a public Atlas baseline.
3. [Offline UI gallery](13_SCREENSHOTS/GALLERY.html) — filter original embedded images by source/topic; open in a browser after extracting the archive.
4. [Coverage matrix](00_INDEX/COVERAGE_MATRIX.md) and [method/limits](00_INDEX/METHOD_AND_LIMITS.md) — what was captured, what remains partial and how evidence should be interpreted.

## Collection at a glance

- **858 deduplicated source capsules**, representing 889 captured page URLs (31 aliases: 21 exact-body and 10 shared-video-identifier aliases).
- **65 reviewed source paraphrases** plus 793 clearly labeled automated discovery capsules. Reviewed topic syntheses connect the material into product/UX findings; the catalog is broader than the set of individually reviewed workflows.
- **1,995 unique image files**, associated with original source pages; screenshots, diagrams, animations and product illustrations are retained separately.
- **43 public video-library entries** with dates/durations and exact embedded player/direct-media references. Video files and full transcripts are not included.
- Source URLs, titles, available page dates, UTC retrieval times, response/image hashes, URL aliases, robots snapshots and access outcomes are preserved in the manifests.

## Capability → Atlas upgrade map

| Folder | Facilio reference | Likely Atlas upgrade area |
|---|---|---|
| [01 Product modules](01_PRODUCT_MODULES/README.md) | Multi-persona facilities operating model; tenant, booking, visitor and related modules | Coherent navigation and end-to-end service journeys |
| [02 Work/maintenance](02_WORK_ORDERS_MAINTENANCE/README.md) | WO lifecycle, PM, job plans, requests, dispatch; [mobile/offline](02_WORK_ORDERS_MAINTENANCE/MOBILE_UX.md) | Premium daily execution and clear next actions |
| [03 Assets/spaces](03_ASSETS_SPACES/README.md) | Asset lifecycle, portfolio hierarchy, floor/space context, readings | Asset 360 and location command centers |
| [04 Vendor/SLA/contracts](04_VENDOR_SLA_CONTRACTS/README.md) | Vendor/contact/access, business commitments and contract references | Provider portal, calendars, escalations and commercial scope |
| [05 Procurement](05_PROCUREMENT/README.md) | Requisition, RFQ, award, quote, order and receipt | Connected purchasing and invoice-review handoffs |
| [06 Inspections/forms](06_INSPECTIONS_FORMS/README.md) | Builder, schedules, scoring, execution and evidence | Reusable compliance workflows and corrective work |
| [07 Dashboards/analytics](07_DASHBOARDS_ANALYTICS/README.md) | Views, reports, KPIs, pivots, readings and diagnostics | Portfolio exceptions with trustworthy drill-downs |
| [08 Automation/stateflows](08_AUTOMATION_STATEFLOWS/README.md) | Event rules, visual lifecycles and transition controls | No-code rules and auditable business actions |
| [09 Customization](09_CUSTOMIZATION_PLATFORM/README.md) | Modules, fields, templates, relationships, layouts and roles | Shared business-object/form/record framework |
| [10 Developer/API](10_DEVELOPER_API/README.md) | REST shell, FOQL, SDKs and building integration agents | Stable data/action/query contracts |
| [11 Scripting/extensions](11_SCRIPTING_CONNECTED_APPS_VIBE/README.md) | Script contexts, connectors, embedded apps, Connections and Vibe | Separate integration and UI extension surfaces |
| [12 AI](12_AI/README.md) | Record/global copilots, form assistance, photo validation and Atom | Focused assistance with context and reviewable writes |
| [13 Screenshots](13_SCREENSHOTS/README.md) | Original public UI assets and offline gallery | Screen anatomy and interaction references |
| [14 Videos](14_VIDEOS_LINKS/VIDEO_LINKS.md) | Short public walkthrough/player links and selected webinar pages | Motion and sequence references for later permitted review |
| [15 Gap analysis](15_GAP_ANALYSIS/README.md) | Atlas public baseline versus documented Facilio depth | Prioritized upgrade hypotheses and acceptance outcomes |

## How to use the evidence

Read each topic’s **RESEARCH.md** for a reviewed synthesis. Use its **README.md** as the source catalog, then open a capsule for dates, provenance, local image links and related pages. Filenames have stable URL-derived source IDs. Images use content hashes; their manifest connects them back to the pages that explain them.

**Documentation** establishes what the vendor publicly describes. **Marketing and demo pages** illustrate positioning and possible interaction patterns. **Release notes** provide date-specific changes. **Atlas recommendations** are independent proposals. None is a hands-on validation of a tenant or a verified gap in your fork.

Atlas already publicly advertises work orders, asset hierarchy, maintenance planning, inventory, mobile access and dashboards, with automation/purchasing/roles also described in its README. The upgrade map targets greater depth and coherence, not the assumption that these functions are absent.

## Important boundaries

The capture follows public links and conservative robots exclusions. Excluded pages, denied hosts and failures remain logged. The public Swagger shell’s static OpenAPI asset is **link-only** because its host denied the robots check; API schema coverage is unverified. Detailed native contract/invoice administration flows remain partial. Older mobile and newer AI/platform documentation may describe different product generations.

This is a broad collection within the enumerated sources, not an exhaustive mirror of every Facilio web property. No authentication, paywall, robots rule or technical restriction was bypassed. No raw scraped page HTML, vendor documentation bodies or complete transcripts are redistributed. Original screenshots retain their respective owners’ rights and are research references, not assets to ship in Atlas.

## Registers and verification

- [SOURCE_MANIFEST.csv](00_INDEX/SOURCE_MANIFEST.csv) / [JSON](00_INDEX/SOURCE_MANIFEST.json): URLs, titles, dates, local paths, summaries and hashes.
- [IMAGE_MANIFEST.csv](13_SCREENSHOTS/IMAGE_MANIFEST.csv) / [JSON](13_SCREENSHOTS/IMAGE_MANIFEST.json): source-to-image relationships and image hashes.
- [VIDEO_MANIFEST.json](14_VIDEOS_LINKS/VIDEO_MANIFEST.json): publisher metadata and exact player/media links.
- [EXCLUSIONS_AND_FAILURES.csv](00_INDEX/EXCLUSIONS_AND_FAILURES.csv), [ACCESS_LOG.json](00_INDEX/ACCESS_LOG.json), [ROBOTS_SNAPSHOTS.json](00_INDEX/ROBOTS_SNAPSHOTS.json).
- [COLLECTION_STATS.json](00_INDEX/COLLECTION_STATS.json), [VISUAL_QA.md](00_INDEX/VISUAL_QA.md), [VALIDATION.md](00_INDEX/VALIDATION.md).
