# Atlas CAFM decision report

Audit of the original Atlas CMMS (Java API, React web app, Expo mobile app) against the Facilio public research collection. Prepared 2026-10-17.

The question this report answers: **to make Atlas a premium enterprise CAFM, what should we reuse, fix, extend, build, or defer?**

## 1. Verdict

Atlas covers most CMMS features in source. A Facilio-style feature list would score it well. **The gaps are integrity problems, not missing features.**

Status changes are not checked on the server. "Required" fields are enforced only in the browser. Users without the right permissions can still find work orders through search. The parts ledger is not a reliable record of stock. PM schedules can stop running or create duplicates without anyone noticing. Notifications and webhooks are dropped after a single failed attempt. Chart drill-down is disabled in the code. The mobile app does not work offline.

Atlas also has no typed site → building → floor → space model, no site-scoped permissions, and no SLA or overdue engine.

**Recommendation.** Spend the first two phases making the existing work-order, PM, inventory, and permission flows correct and auditable. Next, add a typed location hierarchy with site-scoped access, then SLA/overdue handling and offline field execution. Defer most of the platform-builder ideas in the Facilio material: stateflow canvas, layout editor, custom modules, connected apps, dashboard builder, RFQ, and AI.

**Decide this first.** About 25 Atlas features are behind a commercial license check. These include history, signatures, files, labor and cost, webhooks, custom roles, field configuration, the request portal, workload, and API keys. How we resolve that (§6) changes whether those features count as REUSE or not.

---

## 2. Baseline record

| Item | Value |
|---|---|
| Intended original ref | `main` (also `origin/main`, `upstream/main` = `Grashjs/cmms`, and local `canvas-deploy`). All four point at the same commit, so the ref is not ambiguous. |
| Commit | `b23f5bd1c6cd43bcc07b978a220d0788e27cb6be` — "fix: update CompanyService to use lazy injection for PaddleService" |
| Tags at HEAD | `deployed-backend`, `deployed-frontend` |
| Remotes | `origin` = `Attili-sys/cmms`, `upstream` = `Grashjs/cmms`. No `git fetch` was run, so upstream may have newer commits. |
| Versions | `api/pom.xml` 0.0.1-SNAPSHOT; Spring Boot 3.5.16; Java 17 |
| Licence | AGPLv3 (`LICENSE`) or the INTELLOOP commercial licence (`COMMERCIAL_LICENSE.MD`) |

**Local modifications, kept apart from the baseline.**

- `git status` shows only `?? cmms/`, the untracked Canvas Python replacement. `api/`, `frontend/`, `mobile/`, and `home/` match HEAD exactly.
- Your earlier customisations (sidebar `locked: true`, the subscription deletions, `home/score.yaml`, and others; 692 files) are **not in the working tree**. They are in `stash@{0}` ("On canvas-deploy: !!GitHub_Desktop<canvas-deploy>").
- Nothing was popped, applied, committed, or deleted.
- The Java tests ran on a `git archive b23f5bd1 api` export in a scratch directory, not on the working tree.

**Scope.**

- Assessed: `api/` (Java), `frontend/` (React), `mobile/` (Expo).
- Excluded from implementation claims: `cmms/` (Python replacement) and `home/` (marketing). Marketing copy appears only where it makes a claim the code contradicts.

**Path abbreviations used below.** `J/` = `api/src/main/java/com/grash/`, `R/` = `api/src/main/resources/`, `F/` = `frontend/src/`, `M/` = `mobile/`. Line numbers are at `b23f5bd1`.

---

## 3. Evidence and method

### 3.1 Evidence classes

| Label | Meaning |
|---|---|
| **[src]** | Read in source at `b23f5bd1`. A behaviour claim, but not run. |
| **[src✓]** | Read in source, then re-read by the report author during verification (see §3.3). |
| **[test]** | Executed in this audit. |
| **[doc]** | Atlas's own docs (`README.MD`, `api/Current features.pdf`, `dev-docs/`). States intent, not behaviour. |
| **[mkt]** | Marketing copy (`home/`, atlas-cmms.com). Not evidence of behaviour. |
| **[inf]** | Inference from code that was read. Needs a test before it is acted on. |
| **F-xxxx (rev)** | Facilio capsule with a reviewed synthesis. Public documentation, not a tenant test. |
| **F-xxxx (auto)** | Facilio capsule that was auto-generated (793 of 858). Topic cue only; weak evidence. |
| **F-xxxx (mkt)** | Facilio marketing page. |

### 3.2 Tests executed [test]

The command ran in Docker on a clean export of the committed baseline:

```
docker run maven:3.9.9-eclipse-temurin-17 mvn -B test
```

It used Testcontainers Postgres through the host Docker socket.

Result: **`Tests run: 1996, Failures: 0, Errors: 0, Skipped: 0` — BUILD SUCCESS** (4 min 52 s).

This covers 90 test classes, including integration suites for work orders, assets, locations, meters, PM, requests, roles, users, and API docs.

**What the green run does not prove:**

- Quartz runs on the in-memory RAM store in tests (`api/src/test/resources/application-test.yml`). Production uses JDBC. Fire times, DST handling, misfires, restarts, and clustering are not exercised.
- `ScheduleServiceTest` mocks the `Scheduler`.
- No tests exist for `ReadingService` meter triggers, `WorkloadService`, or `WorkOrderService.getEvents` (calendar).
- Several defects in this report sit in tested areas because the tests assert current behaviour. For example, `PreventiveMaintenanceServiceTest.patch_enablesScheduleAfterUpdate` asserts re-enable *without* rescheduling.

**Not executed:** the React or mobile builds, any browser or device session, and the Atlas Docker Compose stack. No Atlas container was running locally. The API was never started against MinIO or SMTP.

### 3.3 Discovery and coverage gaps

- **Graph.** codebase-memory-mcp project `Users-attiliab-Documents-GitHub-cmms` (HEAD `b23f5bd1`, 26,774 nodes) was used for discovery, `trace_path`, and symbol lookups. `WorkflowService.findByMainConditionAndCompany` callers came back as exactly 10, matching grep. `scheduleNextWorkOrderJobAfterCompletion` callers were confirmed.
- **Grep fallback.** Line-precise reads used grep and sed, because the graph does not return line ranges for bodies.
- **Known index exclusions:** `mobile/screens/assets` and `api/.../dto/analytics/assets`. Those files were read directly.
- **The cmms/ folder** is untracked but indexed. It was excluded by path.
- **Parallel inspection.** Five read-only agents inspected these areas in parallel: WO lifecycle and permissions; PM and meters; inventory and procurement; locations, customization, and analytics; web and mobile.
- **Author re-reads (marked [src✓]).** I re-read these claims myself:
  - `PurchaseOrderController.respond` (approval adds stock, writes no ledger entry)
  - `FileController.handleFileUpload` / `FileService.uploadFiles` (`bypass`)
  - `PartQuantityController.patch` (stock changes before the 403 check)
  - `ApplicationInitializer:48` (commented-out reschedule)
  - `application.yml` Quartz JDBC settings and email default
  - `WorkOrderService.changeStatus` completion path
  - `PreventiveMaintenanceService.patch:127`
  - `CustomFieldValueService.setCustomFields`
  - no server reader of `FieldType.REQUIRED/HIDDEN` or `isRequired()`
  - `Location` fields
  - `LicenseService.getLicensingState`
  - `Consts.usageBasedFreeLimits`
  - `WorkflowRepository` (no `enabled` filter)
  - `WorkOrderService.getSearchCriteria` fallback comment
  - `RoleService.patch`
  - `UserService.patchUserRole`
  - `WorkOrderController.getByAsset`
  - `WorkOrderCreationJob` guards
  - `F/content/own/Analytics/WorkOrder/index.tsx` (`return;// TODO`)
  - `M/store/index.ts` persist config
  - `COMMERCIAL_LICENSE.MD` §3.4
- **Inferred, not verified.**
  - MapStruct PATCH null-overwrite: generated sources are absent, so this is unverified.
  - POST-time status mass assignment on work orders and POs: needs a request-level test.
  - Async rollback interaction between Quartz and JPA.

### 3.4 Research inputs read

- `README.md`, `00_INDEX/METHOD_AND_LIMITS.md`, `15_GAP_ANALYSIS/GAP_ANALYSIS.md`, `15_GAP_ANALYSIS/ATLAS_BASELINE.md`, `REA_TARGETS.md`.
- Capsule scope summaries for the Facilio IDs cited.
- `SOURCE_MANIFEST.csv`, for each source's review level.

The research's own limits apply. It reflects public documentation only. It has no tenant validation, no edition or licensing data, and no verified API schema. Of its 858 capsules, 793 are automated.

`ATLAS_BASELINE.md` treated Atlas at product-description level and said explicitly that it had not inspected the code. This report replaces that baseline.

---

## 4. Challenge to the previous coverage inventory

The pasted inventory was careful and mostly accurate. These corrections change decisions.

| Inventory claim | Correction | Evidence |
|---|---|---|
| Branch `canvas-deploy`, dirty working tree, about 76 changed paths | Now on `main`, the same commit, and clean except `cmms/`. Earlier edits are stashed, so none of the inventory's working-tree findings (menu locks, deleted subscription UI) describe the baseline. | `git status`, `git stash list` |
| "Java tests not run" | 1,996 tests pass. Green tests lock in some defects (§3.2). | [test] |
| CU-06 Workflows "implemented" | **Partial.** The `enabled` flag is never read, 9 declared actions or conditions are no-ops, and only creation is licence-gated. | §5.9 |
| PO-01 Purchase orders "implemented" | **Partial.** Approval doubles as goods receipt with no ledger entry. A rejected PO can be approved later. Lines can be edited after approval. | §5.5 |
| RB-03 Row-level view "implemented" via `canBeViewedBy` | **Partial and leaky.** Work-order search falls back to all company work orders. `/work-orders/asset|location|part/{id}` skip per-WO checks. PM and vendor search ignore view-others. | §5.3 |
| WO-10 History "implemented" | Envers writes revisions, but reading them is licence-gated. The web UI has no history tab; history only appears in the PDF report. | §5.2 |
| CU-02 Field required/hidden "implemented" | **UI-only.** The server never reads `FieldType.REQUIRED/HIDDEN`, and custom-field `required` is never checked. | §5.10 |
| AN-01..05 analytics "implemented" | The endpoints exist (42), but **drill-down is stubbed in every analytics module**. Totals load all entities into memory. There are no location filters. | §5.8 |
| IN-03 Low stock "not traced" | Fires only on work-order consumption, licence-gated, repeats on every consumption, and never creates a reorder. | §5.5 |
| PM-04 "implemented" / Q5 "every RecurrenceType?" | All four types run. The real risks are restart/no-reconciliation, no clustering, completion-chain duplicates, and timezone inconsistency. | §5.4 |
| MO-04 offline "unverified" | Now **contradicted** by source: there is no outbox, and failed writes are lost (some silently). Marketing sells "Mobile Offline Mode" on a paid tier (`home/src/content/pricing/pricingData.ts:53`). | §5.11 |
| Q10 "What does `Current features.pdf` claim?" | It is an older machine-translated French "Grash Features" list. Its claims are covered by the code at feature level. It does not claim offline mode. | [doc] |
| Entitlements treated as one gate | There are **two gates**: `PlanFeatures` (self-hosted signups get BUSINESS = all features) and the Keygen `LicenseEntitlement` (all false without `LICENSE_KEY`). The licence is the binding gate on self-hosted. | §6 |

---

## 5. Findings by domain

### 5.1 Work-order lifecycle

**Status model and transitions**

- `Status` has only `OPEN, IN_PROGRESS, ON_HOLD, COMPLETE` (`J/model/enums/Status.java:6-10`) [src].
- `WorkOrderService.changeStatus` (`J/service/WorkOrderService.java:832-937`) accepts **any → any**, including COMPLETE → OPEN [src✓].
- The web uses a plain `<Select>` with all four values always offered (`F/content/own/WorkOrders/Details/WorkOrderDetails.tsx:394,621-679`). There is no resolve/close split and no cancel state [src].

**Who can edit**

- `canBeEditedBy` (`J/model/WorkOrder.java:117-120`) lets the creator or any assignee edit or complete, with no edit permission needed [src].
- So an assigned VIEW_ONLY user can complete a work order [inf].

**Completion gates**

- On COMPLETE, the server sets `completedBy/On`, stops asset downtime, chains the next PM, and stops timers (`:866-881`) [src✓].
- It does **not** check required fields, tasks, or `BLOCKED_BY` relations [src✓ for fields].
- The client `canComplete()` (`WorkOrderDetails.tsx:260-306`) checks the `complete*` field configs but stops at the first failure [src].

**Bypasses and crash paths**

- `create()` resets `completedBy/On/signature` but not `status` (`:130-133`), and `WorkOrderPostDTO extends WorkOrder`.
- So a POST could create a COMPLETE work order with null `completedOn` [inf]. That would crash `WorkOrder.isCompliant()` (`J/model/WorkOrder.java:95-97`), which `WOAnalyticsController:71` calls [inf].
- `changeStatus` calls `findById(id).get()` without a guard (`:835`), so an unknown id gives a 500 [src].

**Overdue**

- Nothing detects overdue work. `WebhookEvent.WORK_ORDER_OVERDUE` is `//TODO`, and no job checks due dates [src].
- "Overdue" exists only as counts (`WorkloadService:126-129`, `WorkOrderService.countUrgent:667-681`) [src].

**Requests**

- `RequestService.approve` (`J/service/RequestService.java:372-428`) creates the work order through `createWorkOrderFromRequest` [src].
- Approval is single-step, allowed for SETTINGS-viewers or the hard-coded `LIMITED_ADMIN` [src].
- Requesters get emails on status change only if `woUpdateForRequesters` is on. The email uses the acting user's locale (`WorkOrderService:901-930`) [src].

**Facilio reference.** WO lifecycle with approval, resolution, closure, and reopen (F-bb26eed29a rev). Transitions as controlled actions with validations and permissions (F-e44212888d rev, F-dc49c9c20b rev). Request-to-WO conversion with requester updates (F-da27f1730e rev, F-edf947c137 rev, F-bb1f5c3408 rev).

**Read.** Atlas has the record, tasks, time, cost, parts, signature, and relations. What it lacks is the **transition contract**. Fix that before building any visual stateflow.

### 5.2 History and audit

- `WorkOrder` is `@Audited(withModifiedFlag = true)` (`J/model/WorkOrder.java:33-34`) [src].
- `WorkOrderHistoryService.findByWorkOrder` returns an empty list without the `WORK_ORDER_HISTORY` entitlement (`J/service/WorkOrderHistoryService.java:51`). It maps only `revtype = 1`, so creation is not shown [src].
- Custom-field values and `firstTimeToReact` are `@NotAudited` [src].
- The web UI never dispatches `getWorkOrderHistories`; history appears only in the PDF report option (`F/content/own/WorkOrders/Details/ReportConfigFields.tsx:13`) [src].
- Assets and locations have no history surface [src].
- There is no soft delete outside `Asset.archived` and `WorkOrder.archived`. Parts, POs, vendors, files, and cost lines are hard-deleted with cascades, which erases their history [src].

### 5.3 Permissions and tenancy

**Model.** `Role` has five permission sets × 15 `PermissionEntity` values. The `canBe*By` helpers follow one pattern (view = permission ∧ (viewOther ∨ creator ∨ assignee)) [src].

**Tenancy.** Company isolation is enforced by `@PostLoad CompanyAudit.afterLoad` throwing after load (`J/model/abstracts/CompanyAudit.java:39-54`), plus `TenantAspect` on request bodies. There are no Hibernate filters [src].

**Gaps, all [src] unless marked**

| # | Gap | Location |
|---|---|---|
| P1 | WO search falls back to all company WOs for roles without WORK_ORDERS view. Developer comment: "Work order is viewed by everyone" [src✓]. | `J/service/WorkOrderService.java:604-662` |
| P2 | `GET /work-orders/asset|location|part/{id}` check only the parent, then return all of its WOs [src✓]. These are `@PreAuthorize("permitAll()")`, with the user resolved inside the method. | `J/controller/WorkOrderController.java:85-138` |
| P3 | PM search and vendor search ignore view-others. | `PreventiveMaintenanceService:265-285`, `VendorService:86-92` |
| P4 | Role PATCH has no SETTINGS check and skips `PlanFeatures.ROLE` [src✓]. | `J/service/RoleService.java:59-72` |
| P5 | `patchUserRole` has no grant ceiling. A PEOPLE_AND_TEAMS editor can assign ADMIN [src✓]. | `J/service/UserService.java:566-584` |
| P6 | The client-supplied `bypass=true` skips the FILES permission and plan check on upload [src✓]. | `J/controller/FileController.java:47-48`, `J/service/FileService.java:78-83` |
| P7 | Part-quantity PATCH changes stock before the 403 check. `consumePart` commits in its own transaction [src✓]. | `J/controller/PartQuantityController.java:193-219` |
| P8 | PO `status` is likely settable at POST, which would skip approval and receipt [inf]. | `PurchaseOrderController:96` |
| P9 | `AdditionalCost` extends `Audit`, not `CompanyAudit`, so it has no tenant column or `@PostLoad` guard. | `J/model/abstracts/Cost.java:12` |
| P10 | `/locations/mini` and `/vendors/mini` have no view check. | `LocationController:67-72`, `VendorController:53-57` |
| P11 | API keys act as their creator with full role authority and have no scopes. | `J/security/ApiKeyAuthFilter.java:63-79` |
| P12 | **No site or location scoping.** `User.location` (`J/model/User.java:86`) and `Team.locations` (`J/model/Team.java:53-60`) are never read for authorization. | grep, negative |

**Facilio reference.** Location-scoped applicability and role-specific views (F-92098144f3 rev, F-bb5a132a96 rev). Portal audience visibility (F-f4ab0dcbcd rev).

**Read.** P1–P11 are **FIX** items that block any enterprise rollout. P12 is the largest structural gap for a multi-site estate.

### 5.4 Scheduling: PM, meters, calendar, workload

**Store and restart**

- Quartz uses the JDBC store (`R/application.yml:21-26`) with no clustering settings [src✓].
- Startup reconciliation is commented out: `// if (!cloudVersion) scheduleService.findActive().forEach(scheduleService::reScheduleWorkOrder);` (`J/ApplicationInitializer.java:48`) [src✓].
- Triggers persist across a restart, but a trigger that is lost is never rebuilt [inf].
- Two API instances sharing one database would each run a non-clustered scheduler, which double-fires PMs [inf].

**Lifecycle holes**

- PM PATCH sets `schedule.disabled = false` without rescheduling (`J/service/PreventiveMaintenanceService.java:127`) [src✓].
- No API disables a schedule. `SchedulePatchDTO` has no `disabled` field [src].
- A hidden "stale" rule auto-disables a PM when the last 5 WOs have no `firstTimeToReact` (`ScheduleService:80-85`) [src].

**Completion-based PMs**

- Each transition to COMPLETE chains a new one-shot job (`WorkOrderService:876-877`) [src✓].
- Chained jobs (`wo-job-chained-{id}-{epoch}`) are never cancelled by `stopScheduleJobs` [src].
- Chained jobs have no `endAt(endsOn)` [src].
- Complete → reopen → complete therefore schedules duplicates [inf].

**Timezones**

- WEEKLY cron uses the company timezone [src].
- MONTHLY and YEARLY use the JVM default [src].
- DAILY is a fixed 24 h × frequency interval with FIRE_NOW misfire, so the anchor drifts after an outage [inf].
- Due date = fire time + `dueDateDelay` [src].

**Generated work order**

- Copies title, asset, location, assignees, tasks, files, and `copyOnRepeat` custom fields. It does **not** copy parts or customers (`WorkOrderService.getWorkOrderFromWorkOrderBase:457-481`) [src].
- No occurrence idempotency key [src].
- Unlicensed, generation stops at the 30-active-WO cap and the occurrence is lost [inf; cap src✓].

**Meter triggers**

- Evaluated on reading create **and** PATCH (`ReadingService:79,123,151-192`) [src].
- No dedupe or edge detection: every reading beyond the threshold creates a new WO [src].
- `recurrent` and `waitBefore` are stored but never read [src].
- No usage-interval ("every N hours") trigger [src].

**Calendar**

- `PreventiveMaintenanceService.getEventsByCriteria` iterates fire times from `startsOn`, capped at 1,000, then drops past ones. A daily PM older than about 1,000 days shows no future events [inf from :338-353].
- COMPLETED_DATE PMs never appear [src].

**Workload**

- `WorkloadService` capacity is minutes per day from `ShiftConfiguration`, with no shift windows [src].
- Completed WOs still count against capacity [src].
- Team WOs count in full for every member [inf].
- Placement is hard-coded to 08:00 (`:198-206`) [src].
- No tests cover workload or the calendar [src].

**Facilio reference.** Planned maintenance and job plans (F-353f162447 rev, F-373847871e rev). Readings in PM (F-942b974efb auto). Resource planner (F-b33bd8ad03 rev).

**Read.** The scheduling engine exists. **FIX** it before extending it; a premium CAFM cannot silently miss statutory PMs.

### 5.5 Inventory and procurement

**Stock model**

- One `Part.quantity` (double) per part, with no storeroom. There is a `//TODO //Location` comment (`J/model/Part.java:69,207-208`) [src].
- `@Version` exists on `Part` only [src].
- `PartTransaction` uses the sign of the quantity as its type. It has no unit-cost snapshot, user, PO link, or location [src].

**Ledger gaps.** These change stock **without** a `PartTransaction`:

- PO approval (`J/controller/PurchaseOrderController.java:165-177`) [src✓]
- manual `PATCH /parts/{id}` quantity [src]
- import [src]

**Reversal gaps**

- Removing a part through the work-order list-replace PATCH does not restore stock [src].
- Deleting a WO, PO, or part cascades and erases transactions, with no reversal [src].
- `DELETE /part-quantities/{id}` does reverse stock [src].

**Procurement**

- Approval *is* the receipt. There is no partial receipt [src✓].
- REJECTED → APPROVED is allowed [src✓].
- Lines stay editable after approval [src].
- The workflow APPROVE action sets the status without adding stock (`J/service/WorkflowService.java:139-141`) [src].
- There is no requisition, RFQ, quote, invoice, or contract entity [src, search negative].

**Low stock**

- Only inside `PartService.consumePart` (`:166-196`), gated by `LOW_STOCK_ALERTS` [src].
- No de-duplication [src].
- `CREATE_PURCHASE_ORDER` workflow action is `//TODO` (`WorkflowService:162-164`) [src✓].

**Costing**

- Costs are computed at the current part price, with no snapshot (`WorkOrderService.getPartCost:532-539`) [src].
- Labor and vendor rates are integer `long`, and `Labor.getCost` truncates [src].
- `includeToTotalCost` and `includeToTotalTime` are never read [src].
- Resuming a timer overwrites `startedAt` (`J/controller/LaborController.java:88`) [src].

**Facilio reference.** Storerooms, item/tool types, and inventory requests (F-2d985bbdac, F-07d4ced808, F-35ebe9816b, all auto, so weak). RFQ (F-802bb98c69 rev). Receivables (F-fd8da69785 auto). Procurement detail and visibility (F-f4ab0dcbcd rev). Invoice matching (F-d7e60997a9 mkt).

**Read.** **FIX** the ledger and **EXTEND** POs with a receipt step. Multi-storeroom stock is a legitimate **EXTEND** later. RFQ and invoice matching are **DEFER** unless an ERP is not the system of record (§12, Q8).

### 5.6 Files

- Upload is licence-gated (`FILE_ATTACHMENTS`) and allows 35 MB per file [src].
- There is no MIME allow-list and no AV scan [src].
- Bearer-style presigned URLs last 3 hours (`J/mapper/FileMapper.java:31`) [src].
- `hidden` is not enforced on get-by-id [src].
- `StorageService` has no delete, so objects are orphaned [src].
- Public request-portal upload is protected only by a UUID and a rate limit [src].
- Plus P6 `bypass`.

**Read:** **FIX** (hardening). The relationship model (many-to-many to assets, WOs, locations, parts, requests, tasks) is reusable.

### 5.7 Locations and assets

**Location model** (`J/model/Location.java`) [src✓]

- Fields: name, address string, lat/long, `parentLocation` (any depth), workers, teams, vendors, customers, files, custom fields.
- **No type or level, no timezone, no area, no operating hours.**
- Cycle checks catch self-parenting only [src].
- Repositories have no recursive or descendant queries (`J/repository/LocationRepository.java`). `LocationController` serves one level of children [src].

**Floor plans** (`J/model/FloorPlan.java`): an image plus `area` with no unit. There are no pins [src].

**Super accounts** (`SuperAccountRelation`) give cross-company read. No API creates them, and analytics are single-company (`J/utils/Helper.java:415-422`) [src]. **Not a portfolio model.**

**Asset detail**

- Tabs: details, WOs, parts, files, meters, downtimes, analytics (`F/content/own/Assets/Show/index.tsx:166-173`) [src].
- No PM tab, no history tab, and no child tree [src].

**Location detail**

- Tabs: assets, files, WOs, floor plans, people (`F/content/own/Locations/LocationDetails.tsx:75-79`) [src].

**Downtime integrity**

- A WO created with `assetStatus` sets status but writes no downtime (`WorkOrderService:119-123`) [src].
- Completion forces OPERATIONAL [src].
- `findFirst` closes only one open record [src].
- Parent assets get duplicate open records [inf].

**Reliability metrics**

- MTTR = labor hours / WO count (`AssetService:686-693`) [src].
- MTBF uses truncated whole days (`:665-684`) [src].

**Facilio reference.** Optional-level space hierarchy with timezone and boundary (F-de60dc01d5 rev). Location command centre with counts and drill-downs (F-249ef123b9 rev). Operating hours (F-9e91073a80 auto). Asset status and transfer (F-f83334c178 rev).

**Read.** Untyped `parentLocation` can carry the hierarchy, so **EXTEND** Location; do not replace it. Add a level/type, timezone, and recursive queries.

### 5.8 Reporting and analytics

**Endpoints**

- 42 endpoints across 5 controllers (`J/controller/analytics/*`) [src].
- Most load whole entities with `findByCompanyAndCreatedAtBetween` and aggregate in Java [src]. `mobile/overview` loads **all** company WOs (`WOAnalyticsController:95,129`) [src].
- Caffeine caches for 20 min with no invalidation [src].
- `DateRange.filterFields` is declared but ignored, so there is no location or asset slicing [src].
- `costs-time` filters by `createdAt` rather than `completedOn` [inf].

**Drill-down is disabled in the UI.**

- Every analytics module's modal handler begins with `return;// TODO` (`F/content/own/Analytics/WorkOrder/index.tsx:21`, also Asset/Part/Request) [src✓].
- Modals render `rows={[]}` [src].

**Gating**

- Plan feature `ANALYTICS` plus role permission [src].
- `ADVANCED_ANALYTICS` is never referenced [src].

**Other gaps:** no scheduled or emailed reports, no saved views (filters and columns live in localStorage via `F/hooks/useTableState.ts`), and export does not take the current filters [inf].

**Facilio reference.** Views, columns, filters, and scheduled exports (F-1bc174cae1 rev). Portfolio drill-downs (F-249ef123b9 rev).

**Read.** **FIX** drill-down and filters on the existing charts and **EXTEND** with server-side saved views. **DEFER** a dashboard builder.

### 5.9 Workflows and automation

**Model.** `Workflow` = one main trigger + conditions + **one** action (`J/model/Workflow.java:25-39`). It runs synchronously in-transaction [src].

**Triggers**

- Ten triggers are wired; `trace_path` confirms 10 callers [src].
- No trigger exists for status change (other than COMPLETE), overdue, assignment, or meter reading [src].

**Actions that do nothing**

- WO/request `ADD_CHECKLIST` and `SEND_REMINDER_EMAIL`
- request `APPROVE`
- PO `ASSIGN_CATEGORY`
- part `CREATE_PURCHASE_ORDER`
- task `CREATE_REQUEST` and `CREATE_WORK_ORDER`
- condition `TITLE_CONTAINS` (always false)

All of these appear in the UI builder [src].

**Execution defects**

- **`enabled` is never read**, so disabled workflows still run [src✓ repository].
- PATCH re-creates the workflow with `enabled(true)` [src].
- WO workflow actions run *after* `notify()` and the webhook, so assignees set by a workflow are never notified (`WorkOrderService:138-146`) [src].
- Execution is not licence-gated; only creation is [src].

**Facilio reference.** Event workflows distinct from stateflows (F-6cbbb5fe62 rev). Custom buttons (F-0ea8634546 rev). Stateflows (F-dc49c9c20b, F-e44212888d rev).

**Read.** **FIX** the existing rule engine first. Only then **EXTEND** with status-change and overdue triggers. Status transitions belong in the WO transition contract (§5.1), not in workflows. **DEFER** a stateflow canvas.

### 5.10 Customization

**Custom fields** [src✓]

- Types: SHORT_TEXT, LONG_TEXT, NUMBER, SINGLE_CHOICE, DATE, DATE_TIME, LINK (`J/model/enums/CustomFieldType.java`).
- Used on WO, asset, location, customer, vendor, part, meter, PM, request, and meter trigger.
- **No server validation** of `required`, type, or options. `setCustomFields` clears all values before writing (`J/service/CustomFieldValueService.java:21-46`).
- Not in CSV import or export, not in analytics. Filters on them are unreliable because each filter makes its own join [src/inf].
- `PURCHASE_REQUEST` entity type is dead [src].

**Field configuration** [src✓]

- `OPTIONAL/REQUIRED/HIDDEN` for 18 WO fields and 6 request fields.
- **The server never reads it.**
- Global, not per category or asset class [inf].
- Editing is licence-gated (`FIELD_CONFIGURATION`); the web gates it under `REQUEST_CONFIGURATION` even for WOs [src].

**Request portal:** `RequestPortalField.required` is not checked on the server [src].

**Facilio reference.** Typed form builder, sections, lookups, and conditional rules (F-e8a72b65c5 rev). Detail layouts by role (F-bb5a132a96 rev).

**Read.** **FIX** validation on the existing configuration. **EXTEND** types with boolean, multi-select, and lookup later. **DEFER** a layout or form builder.

### 5.11 Mobile and offline

**Persistence** [src✓]

- `persistReducer({ key: 'root', storage: AsyncStorage })` persists the whole store, with no whitelist (`M/store/index.ts:15-19`).
- Never purged [src], so cached data can survive logout or a company switch [inf].

**No outbox** [src]

- Every mutation calls `fetch` directly (`M/utils/api.ts:71-103`), with a retry only after a 401 refresh.
- Offline completion fails with a snackbar.
- Reading creation has no `catch`, so the value is lost silently (`M/slices/reading.ts:91-104`).
- Photo upload fails.
- NetInfo is used only to block scan and create actions (`M/screens/HomeScreen.tsx:200-204`, `M/components/actionSheets/CreateEntitiesSheet.tsx:81`).

**Coverage gaps** [src]

- Not on mobile: PM screens, purchase orders, calendar, workload, asset downtime, or history.
- NFC is disabled on iOS (`M/screens/ScanAssetScreen.tsx:26-27`).

**What is reusable**

- Completion with signature and feedback mirrors the web.
- Tasks with photo per task.
- Barcode and NFC lookup (licence `NFC_BARCODE`).
- Expo push registration (`M/contexts/AuthContext.tsx:629-702`).

**Marketing contradiction** [mkt]

- `home/src/i18n/translations/en.ts:1441` (`feature_mobile_offline_mode`), on the Professional tier in `pricingData.ts:53`.
- `en.ts:1634` ("work offline when needed").
- The industries page claims technicians can close jobs "even offline".

**Facilio reference.** Offline WO capability boundary: allowed actions, restricted actions, automation resumes online (F-798839f692 rev; F-3a606d7d36 auto).

**Read.** **BUILD** a bounded offline outbox for the field actions, with an explicit online/offline capability matrix. Do not claim offline in marketing until it ships.

### 5.12 Integrations

**Webhooks**

- HMAC-signed and SSRF-validated [src].
- Single attempt, no delivery log, timestamp not signed [src].
- Four PO/overdue events are `//TODO` [src].
- Dispatched inside transactions, before commit [inf].

**Email**

- Off by default (`R/application.yml:136`, `enable: ${ENABLE_EMAIL_NOTIFICATIONS:false}`) [src✓].
- No queue or retry [src].

**API**

- No versioning [src].
- springdoc `/v3/api-docs/**` is `permitAll` [src].
- Keys have no scopes (P11) [src].

**Identity**

- One OAuth provider per instance: Google, or Microsoft on the `common` tenant (`J/configuration/OAuth2ClientRegistrationConfig.java:45`) [src].
- No SAML or generic OIDC [src].
- LDAP syncs one company; it does not re-sync roles or map teams or locations [src].

**Zapier:** sample payloads only [src].

**Integrations tab:** the web "Connectors" tab says "Coming soon" (`F/content/own/Settings/Integrations/Connectors.tsx`) [src].

**Import and export**

- Import is effectively synchronous: `@Async` is self-invoked (`J/service/AsyncImportService.java:34-37`) [inf].
- All-or-nothing import with no per-row errors [src].
- Part import maps `nonStock` from `category` (`J/service/PartService.java:286`) [src].
- CSV export has no formula-injection escaping [src, search negative].

**Facilio reference.** Connected Apps (F-db8b8ab003 rev). Vibe/CLI (F-310535d1fa). FOQL and REST (research marks API schema unverified).

**Read.** **FIX** delivery reliability. **EXTEND** with scoped keys and a versioned API. **DEFER** an extension platform.

### 5.13 Operational reliability

**Strengths [src]**

- 816 Liquibase changesets.
- Sentry.
- `/health-check`.
- Bucket4j rate limiting.
- 17 mail locales.
- `dev-docs/Backup.md` (manual `pg_dump` plus MinIO zip).
- `@PostLoad` tenancy.

**Weaknesses [src unless marked]**

- Caches and rate limits are per node.
- No correlation IDs or structured logs.
- Actuator is not exposed.
- `@Version` only on `Part`.
- No soft delete for commercial records.
- No scheduled backups.
- Quartz is not clustered.
- Single-attempt async side effects.
- MapStruct PATCH probably nulls omitted fields and un-archives work orders (`J/mapper/WorkOrderMapper.java:12-16`, primitive `archived`) [inf, high priority to test].

---

## 6. Entitlement restrictions versus absent implementation

Atlas has two independent gates:

- **Plan features** (`PlanFeatures`). On self-hosted, every signup gets BUSINESS, which includes all of them (`J/service/UserService.java:201-204`).
- **Licence entitlements** (`LicenseEntitlement`). Validated against Keygen or a licence file. Without `LICENSE_KEY` and `LICENSE_FILE_PATH`, `getLicensingState()` returns invalid and **every entitlement is false** (`J/service/LicenseService.java:55-81`) [src✓].

**Gated features (code exists; licence required)**

- Free caps (`J/utils/Consts.java:52-64`) [src✓]: 30 active WOs, 50 assets, 100 parts, 10 locations, 10 PMs, 10 meters, 10 checklists, 5 users.
- Gated off without a licence:
  - files
  - labor/time and additional cost
  - signatures
  - WO linking
  - WO history read
  - field-configuration edit
  - custom roles
  - webhooks
  - low-stock alerts
  - vendors/customers create
  - API keys
  - request portal
  - SSO/LDAP
  - workload / resource planning
  - condition-based PM (meter triggers)
  - asset downtime
  - PM calendar projection
  - NFC/barcode (mobile)
- Workflows: only one can be created.

**Absent (no code, or `//TODO`)**

- WO transition rules
- server-side required-field enforcement
- task-completion and `BLOCKED_BY` gates
- overdue / SLA / escalation
- site-scoped permissions
- multi-level approvals
- PO receiving
- storerooms
- saved views
- analytics drill-down (UI stub)
- offline outbox
- webhook and email retry
- the 9 no-op workflow actions and conditions
- PO and overdue webhooks
- typed locations
- recursive location queries
- requisition / RFQ / invoice / contract
- vendor contacts and compliance
- a vendor portal or login

**Why this matters**

`COMMERCIAL_LICENSE.MD §3.4` forbids circumventing the licence key **under the commercial licence**. The AGPLv3 path permits modification, but then network users are owed the corresponding source.

**This is a legal and commercial decision, not an engineering one.** Until it is made, every "REUSE" below that depends on a gated feature reads as **"REUSE, conditional on licence path"**.

I am not giving legal advice. Ask counsel which path fits Al Jazeera's intended use.

---

## 7. Can existing primitives carry the needs?

| Need | Existing primitive | Can it carry it? | Verdict |
|---|---|---|---|
| Portfolio → site → building → floor → space | `Location.parentLocation`, floor plans, custom fields | Yes, structurally, with an added `type`/level, timezone, area, and recursive queries. Custom fields cannot drive permissions or roll-ups. | EXTEND `Location` |
| Site-scoped access | `User.location`, `Team.locations`, `Location.workers/teams` | The data exists but is unused. Needs a scope resolver applied in every search spec and `canBe*By`. | BUILD on existing fields |
| Required evidence at completion | `FieldConfiguration` (`complete*`), `requiredSignature`, tasks | Yes, once the server enforces them. | FIX |
| Inspections | `Task` types incl. `INSPECTION`, `MULTIPLE`, `METER`; checklists; PM schedules | Partly. Needs versioned templates, scoring, and failed-answer → corrective WO. | EXTEND checklists |
| SLA commitments | `dueDate`, `firstTimeToReact`, `isCompliant`, workflows, Quartz | No. Workflows have no time-based triggers. Needs a policy model and a timer job. | BUILD |
| Exception queue / command centre | 42 analytics endpoints, list filters, `countUrgent`, workload overdue counts | Partly. Needs drill-down, location filters, and saved views. | FIX + EXTEND |
| Event automation | `Workflow` rules | Yes, once fixed (enabled flag, no-op actions, ordering). Not a lifecycle engine. | FIX |
| Vendor management | `Vendor` (rate, links to assets/locations/parts) | Master data only. Needs contacts, compliance expiry, and WO assignment. | EXTEND |
| Reliability KPIs | `AssetDowntime`, MTBF/MTTR endpoints | The data exists; the definitions are non-standard. | FIX definitions |

---

## 8. Decision register

**Effort scale** (relative, for one developer familiar with the codebase, including tests): **S** ≤ 1 week · **M** 1–3 weeks · **L** 1–2 months · **XL** > 2 months.

**Confidence** describes how sure we are the deficiency and the remedy are right: H / M / L.

### D-01 Authorization hardening: **FIX**

- **Benefit.** Technicians, requesters, and contractors see and change only what they should. This is a precondition for any multi-team or contractor rollout.
- **Existing.** Role model, `canBe*By`, `@PostLoad` tenancy (§5.3).
- **Deficiency.** P1–P11.
- **Dependencies.** None. Do this first.
- **Effort.** M.
- **Confidence.** H (P8 and P9 need a confirming test).
- **Acceptance**
  - Each of P1–P11 has a failing-then-passing integration test.
  - A role without WORK_ORDERS view gets 0 results from search and the sub-resource listings.
  - `bypass` is ignored for non-internal callers.
  - Stock is unchanged after a 403 on part-quantity PATCH.
  - Role PATCH needs SETTINGS.
  - Assigning ADMIN needs ≥ ADMIN.
  - POST cannot set `status`.

### D-02 Work-order transition contract and server-side completion validation: **FIX + EXTEND**

- **Benefit.** Completed means completed. Evidence, tasks, and signatures are guaranteed. Statistics become trustworthy.
- **Existing.** `changeStatus`, `FieldConfiguration`, `requiredSignature`, tasks, relations, client `canComplete()`.
- **Deficiency.** Any-to-any transitions, UI-only REQUIRED, no task or BLOCKED_BY gate, a POST can create COMPLETE, a 500 on unknown id, and first-error-only UX (§5.1, §5.10).
- **Dependencies.** D-01.
- **Effort.** M (validation and allowed-transition table). Adding CANCELLED plus a resolve/close split is another M; it touches analytics and mobile.
- **Confidence.** H.
- **Acceptance**
  - A configured transition table is enforced in `changeStatus`.
  - COMPLETE returns 422 listing **all** unmet requirements (fields, open tasks, signature, open `BLOCKED_BY`). Web and mobile show the full list.
  - Reopen needs a reason and is recorded.
  - Custom-field `required`, type, and options are validated on create and patch.
  - Request-portal `required` is enforced.
  - A POST with `status ≠ OPEN` is rejected or normalized.
  - Facilio reference: F-bb26eed29a, F-e44212888d.

### D-03 PM scheduler reliability: **FIX**

- **Benefit.** No missed or duplicate statutory maintenance, and predictable due dates across sites.
- **Existing.** Quartz JDBC store, `ScheduleService`, `WorkOrderCreationJob`, calendar projection, completion chaining (§5.4).
- **Deficiencies**
  - no startup reconciliation
  - no clustering
  - completion-chain duplicates and missing `endsOn`
  - re-enable without reschedule
  - no disable API
  - MONTHLY/YEARLY ignore the company timezone
  - DAILY drift
  - calendar projection breaks after 1,000 occurrences
  - parts not copied
  - occurrences lost at the licence cap
- **Dependencies.** Deployment topology (Q2). Licence path for the cap (Q1).
- **Effort.** M–L.
- **Confidence.** H on the defects, M on the clustering need.
- **Acceptance**
  - Startup reconciles every active schedule against `qrtz_*` and logs the differences.
  - Quartz is clustered (`isClustered`, `instanceId: AUTO`) or a single scheduler node is enforced.
  - Each occurrence has an idempotency key `(scheduleId, occurrenceDate)` with a unique constraint.
  - Re-completing a WO never creates a second future WO.
  - Chained jobs respect `endsOn` and are cancelled on disable or delete.
  - All recurrences use the company or site timezone.
  - Disable/enable is exposed in the API and UI.
  - The calendar returns future occurrences for PMs older than 3 years.
  - PM parts are copied to the WO as planned parts.
  - Integration tests run against the JDBC store.
  - Facilio reference: F-353f162447, F-373847871e.

### D-04 Typed location hierarchy with recursive roll-ups: **EXTEND**

- **Benefit.** One spatial context for assets, work, people, reporting, and access. This is the CAFM foundation.
- **Existing.** `Location.parentLocation` (any depth), floor plans, lat/long, workers and teams, custom fields.
- **Deficiency.** No type or level, timezone, area, or operating hours. No cycle check beyond self. No descendant queries (§5.7).
- **Dependencies.** Data migration plan for existing locations.
- **Effort.** M (model and recursive CTE queries) + M (UI tree and builder).
- **Confidence.** H.
- **Acceptance**
  - `Location.type` is one of SITE/BUILDING/FLOOR/SPACE/OTHER, with optional levels: a space may hang off a building directly.
  - Timezone is set on a site and inherited.
  - Area and capacity are available on spaces.
  - A–B–A cycles are rejected.
  - "WOs, assets, and PMs under building X including descendants" is one API call, backed by a recursive query with an index.
  - Location detail shows counts that drill into filtered lists.
  - Facilio reference: F-de60dc01d5, F-249ef123b9.

### D-05 Site-scoped access control: **BUILD (on existing fields)**

- **Benefit.** Regional teams and contractors are confined to their sites. This is required for any multi-site estate or vendor access.
- **Existing.** `User.location`, `Team.locations`, `Location.workers/teams` (unused for authorization).
- **Deficiency.** P12.
- **Dependencies.** D-01, D-04.
- **Effort.** L (every search spec, `canBe*By`, analytics, exports, mobile).
- **Confidence.** M (scope semantics need a product decision, Q4).
- **Acceptance**
  - A user scoped to site S sees and acts on only S's subtree across lists, detail, analytics, export, calendar, the webhook-free API, and mobile.
  - Admins remain unscoped.
  - Automated tests cover every listing endpoint.

### D-06 Inventory ledger integrity and PO receiving: **FIX + EXTEND**

- **Benefit.** Stock on hand can be trusted, consumption cost is historical, and audits reconcile.
- **Existing.** `PartTransaction`, `PartQuantity`, `consumePart`, restock, PO approval, `@Version` on `Part`.
- **Deficiency (§5.5).** Untracked movements, missing reversals, cascade-erased history, approval-as-receipt, REJECTED→APPROVED, post-approval edits, no price snapshot, integer rates, the import `nonStock` bug.
- **Dependencies.** D-01.
- **Effort.** M (ledger) + M (receipt step).
- **Confidence.** H.
- **Acceptance**
  - Every quantity change goes through one service that writes a typed transaction (CONSUME, RETURN, RECEIPT, ADJUST, IMPORT) with user, unit cost snapshot, and reference.
  - `Part.quantity` equals the sum of transactions; a nightly check alerts on drift.
  - Deletes are soft or blocked when transactions exist.
  - POs move DRAFT → PENDING → APPROVED → (PARTIALLY_)RECEIVED → CLOSED, and only RECEIPT adds stock.
  - Lines lock after approval.
  - Money uses `BigDecimal`.
  - Facilio reference: F-fd8da69785 (auto), F-f4ab0dcbcd.

### D-07 Overdue detection and SLA/escalation engine: **BUILD**

- **Benefit.** Turns due dates into accountable commitments. Supervisors see breaches before customers do.
- **Existing.** `dueDate`, `firstTimeToReact`, `isCompliant`, `countUrgent`, Quartz, webhook `WORK_ORDER_OVERDUE` (TODO).
- **Deficiency.** No job, policy, business calendar, or escalation (§5.1).
- **Dependencies.** D-02, D-04 (site timezone and calendars), D-08 (reliable delivery).
- **Effort.** L.
- **Confidence.** M (policy semantics need product input).
- **Acceptance**
  - Policies select by site, category, and priority, and define response and resolution targets on a business calendar with pause states (e.g. ON_HOLD).
  - Breaches are recorded as events.
  - Escalation levels notify roles.
  - `WORK_ORDER_OVERDUE` webhook fires once per breach.
  - Every SLA timer is visible on the WO.
  - Facilio reference: F-92098144f3 (rev); F-74c84599c6, F-bdd989f436 (auto).

### D-08 Reliable side effects (notifications, email, webhooks) and workflow fixes: **FIX**

- **Benefit.** Assignments, approvals, and integrations are not silently lost.
- **Existing.** `NotificationService`, mail factory, `WebhookDispatchService` (HMAC, SSRF guard), `WorkflowService`.
- **Deficiencies**
  - single-attempt delivery
  - dispatch before commit
  - email off by default
  - no status-change notice to assignees
  - workflow `enabled` ignored
  - 9 no-op actions/conditions shown in the UI
  - workflow assignments bypass notifications
  - PO webhooks TODO
- **Dependencies.** None.
- **Effort.** M.
- **Confidence.** H.
- **Acceptance**
  - Transactional outbox, dispatched after commit, with retries and backoff, a delivery log, and a dead-letter view in Settings.
  - Disabled workflows never run.
  - Unimplemented actions are hidden or implemented.
  - Workflow side effects emit the same notifications and webhooks as manual changes.
  - Assignees and the creator get status-change notices (configurable).
  - Facilio reference: F-6cbbb5fe62.

### D-09 Exception queue: analytics drill-down, filters, saved views: **FIX + EXTEND**

- **Benefit.** Managers go from KPI to the records to act on, in one place, per site.
- **Existing.** 42 endpoints, recharts pages with click handlers already wired, TanStack grid with column state, list filters.
- **Deficiency.** `return;// TODO` drill-down, ignored `filterFields`, in-memory aggregation, no saved views, export ignores filters, non-standard MTTR/MTBF, `createdAt` vs `completedOn` (§5.8).
- **Dependencies.** D-04 for location filters, D-05 for scoping.
- **Effort.** S (enable drill-down) + M (filters, SQL aggregates) + M (saved views).
- **Confidence.** H.
- **Acceptance**
  - Every chart segment opens the WO list with identical filters, and counts match.
  - Analytics accept site/location/asset/category filters.
  - Large tenants return in under 2 s at p95 (target to agree).
  - Saved views are stored server-side, shareable by role, and usable as the landing page.
  - Export honours the current view.
  - MTTR is based on repair downtime; MTBF uses operating time.
  - Facilio reference: F-1bc174cae1, F-249ef123b9.

### D-10 Mobile offline field execution: **BUILD**

- **Benefit.** Technicians in plant rooms, basements, and remote sites can finish work. It also removes a marketing claim the code contradicts.
- **Existing.** Persisted store, completion/signature/task/photo flows, NetInfo, Expo push.
- **Deficiency.** No outbox, silent loss, no purge on logout (§5.11).
- **Dependencies.** D-02 (server validation decides what can be queued), idempotent endpoints (D-03 pattern).
- **Effort.** L.
- **Confidence.** M (connectivity requirements are unknown, Q7).
- **Acceptance**
  - A documented online/offline capability matrix.
  - Assigned WOs and their tasks/assets are downloadable.
  - Offline: task answers, time entries, readings, photos, and completion with signature queue in a persistent outbox with idempotency keys, then sync with visible pending/failed states.
  - Server-side rejections surface per item.
  - Store is purged on logout and company switch.
  - No action is silently dropped.
  - Facilio reference: F-798839f692.

### D-11 Activity history and Asset/Location 360: **EXTEND**

- **Benefit.** One record answers "what happened, who did it, what does it cost", which an enterprise audit needs.
- **Existing.** Envers on `WorkOrder`, `WorkOrderHistoryService`, asset tabs (WOs, parts, files, meters, downtimes, analytics).
- **Deficiency.** No history UI, history is licence-gated, creation and custom fields are not audited, assets and locations have no history and no PM tab, hard deletes (§5.2, §5.7).
- **Dependencies.** Licence path (Q1). D-04 for the location 360.
- **Effort.** M.
- **Confidence.** H.
- **Acceptance**
  - A WO timeline shows create, field changes (including custom fields), status changes with reasons, comments, parts, time, and files.
  - Asset and location pages add PM, history, and child-tree tabs.
  - Commercial records are soft-deleted.
  - Facilio reference: F-f83334c178, F-249ef123b9.

### D-12 Inspections built on checklists: **EXTEND**

- **Benefit.** Compliance rounds with scores, evidence, and automatic corrective work.
- **Existing.** Checklists, `TaskType` `INSPECTION`/`MULTIPLE`/`METER`, per-task notes and images, PM scheduling, task workflow trigger.
- **Deficiency.** No template versioning, scoring, or failure → corrective WO (the task `CREATE_WORK_ORDER` action is TODO).
- **Dependencies.** D-02, D-03, D-08.
- **Effort.** M–L.
- **Confidence.** M.
- **Acceptance**
  - Versioned templates.
  - Scheduled by location scope through PM.
  - Score is computed.
  - A failed answer can create a linked corrective WO with evidence.
  - Results can be reported per site.
  - Facilio reference: F-5d2cbfb143, F-dbe1a9a236.

### D-13 Vendor contacts, compliance, and WO assignment: **EXTEND**

- **Existing.** `Vendor` (rate, assets, locations, parts), custom fields.
- **Deficiency.** No contacts, compliance expiry, or vendor-on-WO link.
- **Dependencies.** None for master data; D-05 for any portal.
- **Effort.** M.
- **Confidence.** M.
- **Acceptance**
  - Vendor contacts.
  - Insurance and certification expiry with alerts.
  - Expired vendors cannot be assigned.
  - WO has an assigned vendor and cost.
  - Facilio reference: F-c475cbeb3a.

### D-14 Request lifecycle transparency: **REUSE + EXTEND**

- **Existing.** Approve/cancel, portal, requester emails.
- **Deficiency.** Requester locale is wrong, no reply thread, single-step approval.
- **Effort.** S–M.
- **Confidence.** H.
- **Acceptance**
  - Requester sees status and public updates in their own locale.
  - Optional multi-step approval by category or site.
  - Facilio reference: F-da27f1730e, F-edf947c137, F-bb1f5c3408.

### D-15 Workload and resource planner: **REUSE + FIX**

- **Existing.** `WorkloadController/Service`, shift capacity, unscheduled queue, web workload view.
- **Deficiency.** Completed WOs consume capacity, team double-counting, fixed 08:00 start, no PM forecast, no tests.
- **Effort.** M.
- **Confidence.** M.
- **Acceptance**
  - Capacity excludes completed work.
  - Shift windows are available.
  - PM forecast is shown.
  - Tests exist.
  - Facilio reference: F-b33bd8ad03.

### D-16 Files hardening: **FIX**

- **Effort.** S–M.
- **Confidence.** H.
- **Acceptance**
  - MIME/extension allow-list.
  - AV scan hook.
  - `hidden` is enforced.
  - Storage objects are deleted.
  - Signed-URL lifetime is ≤ 15 min.
  - `bypass` is removed (see D-01).

### D-17 Import/export correctness: **FIX**

- **Effort.** S–M.
- **Confidence.** H.
- **Acceptance**
  - Real async import with per-row results.
  - The `nonStock` mapping bug is fixed.
  - Custom fields are in import and export.
  - CSV formula escaping.
  - Export artifacts are cleaned up.

### D-18 Platform operations: **FIX**

- **Effort.** M.
- **Confidence.** M.
- **Acceptance**
  - Correlation IDs and structured logs.
  - Actuator health and readiness are exposed internally.
  - `@Version` on WorkOrder, PurchaseOrder, and Request.
  - A test proving PATCH does not null omitted fields.
  - Scheduled backups with a restore drill.
  - Shared cache and rate limits if more than one node.

### D-19 Scoped API keys and a versioned API: **EXTEND**

- **Effort.** M.
- **Confidence.** M.
- **Acceptance**
  - Per-key scopes and site scope.
  - `/api/v1` contract.
  - API docs gated.
  - Facilio reference: F-db8b8ab003 (for later placements).

### D-20 Custom field types (boolean, multi-select, lookup): **EXTEND**, after D-02

- **Effort.** M.
- **Confidence.** M.
- Facilio reference: F-e8a72b65c5.

---

## 9. Ten highest-value changes

Ranked for a premium enterprise CAFM. The ranking favours end-to-end trust and coherence over feature count.

| Rank | Change | Decision | Effort | Why this rank |
|---:|---|---|---|---|
| 1 | D-01 Authorization hardening | FIX | M | Data leaks and privilege escalation block any multi-team rollout. Cheap and certain. |
| 2 | D-02 WO transition contract and server-side completion validation | FIX+EXTEND | M | The core daily workflow. Without it, every KPI and audit is unreliable. |
| 3 | D-03 PM scheduler reliability | FIX | M–L | Missed or duplicate statutory PMs are the costliest silent failure in maintenance. |
| 4 | D-08 Reliable side effects and workflow fixes | FIX | M | Assignments, approvals, and integrations must not be lost. Prerequisite for SLA. |
| 5 | D-06 Inventory ledger and PO receiving | FIX+EXTEND | M+M | Stock and cost figures must reconcile before procurement depth is added. |
| 6 | D-04 Typed location hierarchy with roll-ups | EXTEND | M+M | The shared CAFM context that D-05, D-07, and D-09 depend on. |
| 7 | D-05 Site-scoped access | BUILD | L | Needed for regional teams and any contractor access. |
| 8 | D-09 Exception queue (drill-down, filters, saved views) | FIX+EXTEND | S+M+M | Turns the existing analytics into an operational landing page. Drill-down is a quick win. |
| 9 | D-07 Overdue/SLA engine | BUILD | L | The defining enterprise FM commitment. It ranks below 1–8 only because it depends on them. |
| 10 | D-10 Mobile offline outbox | BUILD | L | Field completion where coverage is poor. Also removes a contradicted marketing claim. |

**Runners-up:** D-11 history/360 (cheap, high audit value; do it alongside D-02 if the licence path allows), D-12 inspections, D-15 workload.

**Quick wins inside the top 10** (S each):

- Enable analytics drill-down.
- Remove the `bypass` path.
- Honour workflow `enabled`.
- Hide no-op workflow actions.
- Turn on email in deployments.
- Add the role-PATCH SETTINGS check.

---

## 10. Implementation sequence

Each phase ends with a demonstrable end-to-end journey, not a feature count. Keep the 1,996-test suite green, and add tests for every defect before fixing it.

**Phase 0: decisions and environment (1–2 weeks, before code)**

- Licence path (Q1).
- Deployment topology (Q2).
- Run the Compose stack with Postgres, MinIO, and SMTP enabled.
- Write failing tests for the P1–P11 items and the PATCH-null inference.

**Phase 1: trust the core (≈ 6–8 weeks)**

- D-01, D-02, D-03, D-08, D-16, plus the quick wins.
- Journey: *request → approve → WO → assign → execute tasks with evidence → complete with signature → requester notified → next PM generated exactly once.*

**Phase 2: operational truth (≈ 4–6 weeks)**

- D-06, D-11, D-17, D-18.
- Journey: *PM WO consumes planned parts → stock and cost reconcile → reorder PO → receive partially → full audit trail on WO, asset, and part.*

**Phase 3: enterprise context (≈ 8–10 weeks)**

- D-04, then D-05, then D-09.
- Journey: *regional manager logs in → sees only their sites → exception view of overdue and high-priority work by building → drills to records → saves and shares the view.*

**Phase 4: commitments and the field (≈ 10–12 weeks)**

- D-07, D-10, then D-12, D-13, D-15.
- Journey: *SLA-bound reactive job on a remote site → technician works offline → syncs → SLA met or escalated → inspection failure raises corrective work.*

**Phase 5: platform (only after a proven need)**

- D-19, D-20.
- Re-evaluate the deferrals in §11 against real usage.

Phases 1 and 2 can overlap where the files do not: D-06 touches inventory and PO code, while D-02 and D-03 touch WO and PM.

---

## 11. Deliberate deferrals

| Deferred | Facilio source | Why defer | Revisit when |
|---|---|---|---|
| Visual stateflow canvas | F-dc49c9c20b, F-e44212888d | Atlas first needs one correct, configurable transition table (D-02). A canvas over unreliable transitions adds risk. | Several record types need different lifecycles. |
| Role-specific detail-layout editor | F-bb5a132a96 | A builder is costly. Role-based default views and tabs (D-09/D-11) cover most of the value. | More than 3 personas need materially different layouts. |
| Custom modules / form builder | F-e8a72b65c5 | Custom fields lack validation and reporting today. Generalising before fixing multiplies defects. | D-02/D-20 done and repeated custom-object requests exist. |
| Dashboard builder | F-1bc174cae1 | Fixed analytics with drill-down and saved views (D-09) come first. A builder needs a metric layer that does not exist yet. | Shared metric definitions exist. |
| RFQ comparison and award; invoice matching | F-802bb98c69, F-d7e60997a9 (mkt) | Usually owned by ERP. Atlas lacks receiving and ledger integrity first (D-06). | Q8 confirms Atlas owns sourcing. |
| Contracts module | F-d7e60997a9 (mkt); research marks contract flows partial | Weak public evidence. Vendor compliance (D-13) and SLA (D-07) give most of the operational value. | Contract-driven SLA or billing becomes a requirement. |
| Vendor portal | F-c475cbeb3a, F-f4ab0dcbcd | Needs site scoping (D-05) and scoped visibility first, or it leaks data. | D-05 is done. |
| Connected Apps, Vibe/CLI, FOQL | F-db8b8ab003, F-310535d1fa | Needs a stable versioned API and action model first (D-19). | Third-party extension demand appears. |
| AI copilot and form assistant | F-8e0ab2ec31, F-4e163df3d6 | Needs trustworthy records, permissions, and reviewable writes. The research itself ranks it last. | Phases 1–3 are done. |
| Multi-company portfolios through super accounts | n/a | No management API and single-company analytics. Use D-04 instead. | Never, unless separate legal entities need hard isolation. |
| Kanban WO view (disabled in code) | n/a | Low value relative to saved views. | After D-09. |
| Mobile purchase orders and analytics | n/a | Field technicians do not need them. Keep mobile focused on execution. | Approver persona on mobile is requested. |
| IoT, telemetry, condition monitoring | F-942b974efb, F-d557019680 (auto) | Meter triggers need FIX first (dedupe, edge detection, usage intervals). Telemetry is a separate integration. | Meter triggers are fixed and a BMS integration is scoped. |

**Meter-trigger correctness itself is not deferred.** It folds into D-03 as follow-on work (effort M): dedupe or edge detection, usage-interval triggers, and wiring the `recurrent`/`waitBefore` fields.

---

## 12. Challenge to the Facilio-inspired recommendations

- **Most P0 items assume a working core.** `GAP_ANALYSIS.md` marks the command centre, portfolio hierarchy, Asset 360, premium execution, and role layouts as P0, and its first step is "reuse working Atlas capabilities". Several of those capabilities are not yet working correctly (§5). The real P0 is integrity (D-01–D-03, D-08), which the research could not see without the code.
- **The "Enterprise command center" (P0) depends on a drill-down that does not work.** It also depends on location filters that do not exist and on site scoping. It is achievable, but only after D-04, D-05, and D-09.
- **"Premium work execution" is right, but the gap is on the server, not the screen.** Atlas already shows tasks, time, parts, cost, and signature. A record shell redesign would hide the any-to-any transitions rather than fix them.
- **Role-specific layouts (P0 UX / P1 builder):** keep the UX goal and drop the builder (§11).
- **Procurement (P1) should split.** Receiving and ledger work is in scope (D-06); RFQ and invoices are not (§11). The research itself flags invoice-matching evidence as marketing-only.
- **Inspections (P1) fit Atlas well,** because the task types already exist. Its ranking holds.
- **SLA engine (P1) is right,** and arguably underrated. It is the clearest CAFM differentiator Atlas lacks entirely.
- **Offline (REA target 17)** is more urgent for Atlas than the research suggests, because Atlas marketing already sells the feature.
- **Evidence weight is mixed.** 793 of 858 capsules are automated topic cues. Storeroom, receivables, readings-in-PM, and SLA "define response" (F-2d985bbdac, F-fd8da69785, F-942b974efb, F-74c84599c6) are auto capsules and should not drive detailed specs without review.
- **Feature-count parity is the wrong goal.** Facilio's breadth (booking, tenant portal, visitors, telemetry, Vibe) is not evidence that Atlas users need it. Favour the five end-to-end journeys in §10.

---

## 13. Unresolved questions that could change decisions

| # | Question | Decisions affected |
|---|---|---|
| Q1 | **Licence path:** commercial licence (keep Keygen gates, REUSE gated features) or AGPLv3 (modify freely, obligation to provide source to network users)? Needs counsel. | D-03 cap, D-11, D-15, D-19, and every gated feature in §6 |
| Q2 | Single API instance or several behind a load balancer? | D-03 clustering, D-18 shared cache and rate limits |
| Q3 | Is the Java stack the production path, and is the Canvas `cmms/` effort paused? You said Java "for now". | All. A rewrite would change REUSE vs BUILD. |
| Q4 | Site-scoping semantics: by user, team, or role? Do supervisors see children only, or siblings too? | D-05, D-09, vendor portal |
| Q5 | Do sites span timezones or countries? | D-03, D-04, D-07 |
| Q6 | Expected scale: sites, assets, WOs per year, concurrent users? | D-09 (SQL aggregates priority), D-18 |
| Q7 | Real connectivity at field sites, and which actions must work offline? | D-10 scope and rank |
| Q8 | Which system of record owns purchasing, invoices, and contracts (ERP)? | D-06 scope, RFQ and contracts deferral |
| Q9 | Identity provider: Entra ID single-tenant? Is SAML required? Is LDAP group→role/site mapping needed? | D-05, D-19, identity extension |
| Q10 | Will we keep merging upstream `Grashjs/cmms`? Should fixes be upstreamed to limit fork drift? | Implementation approach for all FIX items |
| Q11 | Are the [inf] defects real at runtime: MapStruct PATCH nulling, PO/WO POST status mass assignment, `isCompliant` NPE, workflow rollback behaviour? | D-01, D-02, D-18 priority. Confirm with tests in Phase 0. |
| Q12 | Audit and retention obligations (regulatory, internal)? | D-11 soft delete, history retention |
| Q13 | Is the stashed `canvas-deploy` work (`stash@{0}`) still wanted? | Whether earlier UI decisions (menu locks, subscription removal) carry forward |
| Q14 | Has upstream moved since this audit? No fetch was run. | Baseline freshness |

---

## 14. Searches that did not prove absence

| Search | Result | Limitation |
|---|---|---|
| Graph regex `requisition|rfq|quotation|invoice|contract|receiv|warehouse|stockroom|bin|insurance|vendorportal|supplier` | 0 nodes | Naming variants or non-Java assets not covered |
| grep `isClustered|instanceId|misfireThreshold` | none | Env-injected Quartz properties at deploy time not visible |
| grep `WITH RECURSIVE`, "descendant" in repositories/services | none | Client-side tree walking possible |
| grep `FieldType.REQUIRED/HIDDEN`, `isRequired()` (author re-ran) | none | Reflection-based validation not ruled out (unlikely) |
| grep `savedView|SavedFilter|savedSearch` (API and web) | none | — |
| grep `overdue` beyond counts and enum | none | — |
| grep `user.getLocation()`, `Team::getLocations` for authorization | none | — |
| grep mobile `queue|offline|pendingActions|retry|purge` | only snackbar, logout comment, store | Third-party offline library under another name not ruled out (no dependency found) |
| grep `clamav|virus`, CSV formula escaping | none | — |
| MapStruct generated sources | absent (`target/` not built) | PATCH null behaviour is inferred |
| Graph index exclusions (`mobile/screens/assets`, `dto/analytics/assets`) | read directly | — |
| Facilio Swagger/OpenAPI | link-only in the research | Facilio API parity unknown |

---

*Nothing in the application code was changed and nothing was deployed. The Java tests ran in a throw-away container against a scratch export of `b23f5bd1`.*
