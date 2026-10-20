# Non-Asset Modules Audit & Parity Report (Java Spring Boot → Python FastAPI)

- **Document ID**: `NON-ASSET-AUDIT-01`
- **Audit Target**: All non-asset backend modules in `atlas-cmms/src/` vs original reference implementation in `api/src/main/java/com/grash/` and frontend contracts in `frontend/src/slices/` and `frontend/src/content/own/`.
- **Auditor Role**: Principal Backend & Security Auditor
- **Audit Policy**: Skeptical, assumption-free, line-by-line verification. **Zero modifications to existing codebase files.**

---

## 1. Executive Summary & Audit Scorecard

Following the audit of the Asset & Location module ([`ASSET_MANAGEMENT_SPEC.md`](file:///Users/attiliab/Documents/GitHub/cmms/ASSET_MANAGEMENT_SPEC.md)), this audit evaluated all remaining functional modules in the system:
1. **Work Orders, Tasks, Labor, Part Quantities & Additional Costs**
2. **Preventive Maintenance & Schedules**
3. **Parts, MultiParts, Purchase Orders, Vendors & Customers**
4. **Meters, Readings, Requests, Request Portal, Workflows & Checklists**
5. **Users, Roles, Teams, Company Settings & Authentication**
6. **Non-Asset Analytics (Work Orders, Parts, Requests, Users)**

### Key Audit Findings

1. **Systemic Multi-Tenant Security & Isolation Breaches (`P0`)**:
   - **Un-scoped Auxiliary Entities via Generic CRUD Router**: `Schedule`, `Reading`, and `AdditionalCost` models do not define `company_id`. When mounted via `build_crud_router`, `scoped_select()` applies no tenant filter because `hasattr(model, "company_id")` is false, and `assert_company_access()` silently exits early when `target_company_id is None`. Consequently, `GET /schedules`, `GET /readings`, and `GET /additional-costs` expose data across all tenants, and their respective `PATCH` / `DELETE` endpoints permit arbitrary cross-tenant tampering.
   - **Cross-Tenant Role Disclosure & Mutation**: `GET /roles` queries the entire table across all tenants, and `PATCH /roles/{id}` / `DELETE /roles/{id}` perform zero tenant verification or system role guards (`role.role_type == 0`), allowing any tenant to view, modify, or delete system roles and other companies' custom roles.
   - **Public Request Portal Lockdown**: Public Request Portal endpoints enforce authentication (`Depends(get_current_user)`), returning `401 Unauthorized` to anonymous building occupants scanning QR codes, while filing requests under `current_user.company_id` rather than resolving the tenant from the portal UUID.
   - **UI Configuration Collision**: `patch_ui_configuration` mutates `db.scalar(select(UiConfiguration).limit(1))` without tenant scoping, causing all tenants to overwrite a single global configuration.
   - **Checklist Mini Route Leak**: `GET /checklists/mini` executes `select(Checklist).all()`, leaking proprietary checklists across tenants.

2. **Silent Data Loss & Disconnected Side Effects (`P0`)**:
   - **`editWOPartQuantities` Data Destruction Bug**: In `PATCH /part-quantities/work-order/{id}`, Python skips integer elements (`for item in payload: if not isinstance(item, dict): continue`). Because the React UI (`frontend/src/slices/partQuantity.ts`) sends `parts: number[]` (e.g. `[1, 2, 5]`), Python skips all incoming parts, marks all existing part quantities as deleted, wipes them from the work order, and restocks warehouse inventory.
   - **Direct PartQuantity CRUD Missing Stock Lifecycle**: `PATCH /part-quantities/{id}` and `DELETE /part-quantities/{id}` use generic `build_crud_router` without hooks. Manual quantity edits bypass warehouse stock adjustments, and deletions permanently lose inventory without restocking.
   - **Task Duplication Explosion**: `patch_tasks_for_wo` and `patch_tasks_for_pm` generate brand new `TaskBase`, `TaskOption`, and `Task` rows on every save instead of reconciling by ID, leading to exponential row accumulation and lost technician notes.
   - **Labor Timer Zero-Out**: `POST /labors/work-order/{id}` ignores the `?start=` query parameter, and stopping a timer never computes elapsed duration, leaving labor time and costs at 0.
   - **Purchase Order Approval Stock Reversal Bug**: Approving a PO increments stock, but rejecting an already approved PO (`approved=False`) transitions status to `REJECTED` without reverting the added inventory stock.

3. **Inert Business Engines & Dropped Contracts (`P0` / `P1`)**:
   - **Completely Inert Workflows Engine**: Java `WorkflowService` triggers automated assignments, status changes, and notifications on WO, Request, PO, Part, and Task events. Python implements CRUD endpoints for `Workflow` models, but zero execution engine exists.
   - **PM Recurrence Engine Breakdown**: Background PM generation ignores recurrence intervals (`WEEKLY`, `MONTHLY`, `YEARLY`), ignores `schedule_days_of_week` (e.g., Mon/Wed/Fri), and ignores `recurrence_based_on == COMPLETED_DATE`.
   - **Work Order Status RBAC & Lifecycle Gaps**: `PATCH /work-orders/{id}/change-status` only checks company access (not `can_edit_object`), ignores `required_signature`, fails to clear `completed_on` and `completed_by_id` when moving away from `COMPLETE`, and leaves active labor timers running.
   - **Analytics Contract Mismatches**: Route paths diverge (`/work-orders/costs/time` vs `/work-orders/complete/costs-time`) and return generic fallbacks (`[]` or `{ count: 0, total: 0 }`), causing undefined property crashes in Redux slices.

---

## 2. Complete Issue & Parity Inventory (24 Tracked Items)

| Issue ID | Module | Severity | Summary | Python Citation | Java Citation | Frontend Citation |
|---|---|:---:|---|---|---|---|
| `WO-P0-01` | Work Orders | **P0** | Labor Timer URL Contract Mismatch & Duration Zero Out | [`work_orders_pm.py:404-456`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/work_orders_pm.py#L404-L456) | [`LaborController.java:51-60`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/LaborController.java#L51-L60) | [`labor.ts:153-158`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/labor.ts#L153-L158) |
| `WO-P0-02` | Work Orders | **P0** | PartQuantities WO Array of Ints Payload Drops All Parts & Wipes Existing Stock | [`parts_po_tasks.py:378-380`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/parts_po_tasks.py#L378-L380) | [`PartQuantityController.java:72-108`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/PartQuantityController.java#L72-L108) | [`partQuantity.ts:135-149`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/partQuantity.ts#L135-L149) |
| `WO-P0-03` | Work Orders | **P0** | Direct PartQuantity CRUD Bypasses Inventory Deduction & Restock Lifecycle | [`parts_po_tasks.py:322-328`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/parts_po_tasks.py#L322-L328) | [`PartQuantityController.java:195-242`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/PartQuantityController.java#L195-L242) | [`partQuantity.ts:16-50`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/partQuantity.ts#L16-L50) |
| `WO-P0-04` | Work Orders | **P0** | Task Duplication Explosion on WO & PM Edits | [`parts_po_tasks.py:299-391`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/parts_po_tasks.py#L299-L391) | [`TaskController.java:106-150`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/TaskController.java#L106-L150) | [`task.ts:106-118`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/task.ts#L106-L118) |
| `WO-P0-05` | Work Orders | **P0** | Work Order M2M Collections & `customFieldValues` Dropped on Save | [`work_orders_pm.py:84-142`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/work_orders_pm.py#L84-L142) | [`WorkOrderService.java:110-145`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/service/WorkOrderService.java#L110-L145) | [`workOrder.ts:180-210`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/workOrder.ts#L180-L210) |
| `WO-P1-01` | Work Orders | **P1** | Work Order Status Change Missing RBAC, Signature Verification & Completion Reset | [`work_orders_pm.py:510-535`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/work_orders_pm.py#L510-L535) | [`WorkOrderService.java:833-895`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/service/WorkOrderService.java#L833-L895) | [`workOrder.ts:240-270`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/workOrder.ts#L240-L270) |
| `WO-P1-02` | Work Orders | **P1** | AdditionalCost Generic CRUD Cross-Tenant Security Hole & Missing Object RBAC | [`parts_po_tasks.py:678-699`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/parts_po_tasks.py#L678-L699) | [`AdditionalCostController.java:45-120`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/AdditionalCostController.java#L45-L120) | [`additionalCost.ts:35-85`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/additionalCost.ts#L35-L85) |
| `PM-P0-01` | PM & Schedules | **P0** | Schedule Generic CRUD Cross-Tenant Reschedule & Data Leak | [`work_orders_pm.py:1084-1108`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/work_orders_pm.py#L1084-L1108) | [`ScheduleController.java:38-70`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/ScheduleController.java#L38-L70) | [`preventiveMaintenance.ts:120-155`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/preventiveMaintenance.ts#L120-L155) |
| `PM-P0-02` | PM & Schedules | **P0** | Trigger Work Order Fails to Clone Tasks, Checklists, or Due Date Delay | [`work_orders_pm.py:593-626`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/work_orders_pm.py#L593-L626) | [`PreventiveMaintenanceService.java:153-205`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/service/PreventiveMaintenanceService.java#L153-L205) | [`preventiveMaintenance.ts:160-170`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/preventiveMaintenance.ts#L160-L170) |
| `PM-P0-03` | PM & Schedules | **P0** | Background PM Generator Ignores Recurrence Type, Days of Week, and Completed Date Basis | [`pm_generator.py:14-108`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/jobs/pm_generator.py#L14-L108) | [`ScheduleService.java:110-180`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/service/ScheduleService.java#L110-L180) | N/A (Background) |
| `PM-P1-01` | PM & Schedules | **P1** | Workload Overview Route Returns Hardcoded Empty Arrays | [`work_orders_pm.py:655-660`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/work_orders_pm.py#L655-L660) | [`PreventiveMaintenanceController.java:110-135`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/PreventiveMaintenanceController.java#L110-L135) | [`preventiveMaintenance.ts:80-95`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/preventiveMaintenance.ts#L80-L95) |
| `PO-P0-01` | Parts & PO | **P0** | Purchase Order Approval Missing RBAC & Approval Reversal Inventory Bug | [`parts_po_tasks.py:626-674`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/parts_po_tasks.py#L626-L674) | [`PurchaseOrderController.java:163-177`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/PurchaseOrderController.java#L163-L177) | [`purchaseOrder.ts:156`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/purchaseOrder.ts#L156) |
| `PO-P0-02` | Parts & PO | **P0** | MultiParts Cross-Tenant Part Injection & Information Disclosure | [`parts_po_tasks.py:559-574`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/parts_po_tasks.py#L559-L574) | [`MultiPartsController.java:45-75`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/MultiPartsController.java#L45-L75) | [`multiPart.ts:80-120`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/multiPart.ts#L80-L120) |
| `PO-P0-03` | Parts & PO | **P0** | Part M2M Associations Dropped on Save & Serialized as Empty Arrays | [`parts_po_tasks.py:40-75`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/parts_po_tasks.py#L40-L75) | [`PartService.java:70-115`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/service/PartService.java#L70-L115) | [`part.ts:110-160`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/part.ts#L110-L160) |
| `PO-P1-01` | Parts & PO | **P1** | Vendor & Customer Custom Fields and File Attachments Completely Dropped | [`assets_locations.py:412-438`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/assets_locations.py#L412-L438) | [`VendorService.java:45-75`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/service/VendorService.java#L45-L75) | [`vendor.ts:60-95`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/vendor.ts#L60-L95) |
| `PO-P1-02` | Parts & PO | **P1** | Purchase Order `customFieldValues` Dropped on Save & Read | [`parts_po_tasks.py:598-615`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/parts_po_tasks.py#L598-L615) | [`PurchaseOrderService.java:60-95`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/service/PurchaseOrderService.java#L60-L95) | [`purchaseOrder.ts:20-50`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/purchaseOrder.ts#L20-L50) |
| `REQ-P0-01` | Requests | **P0** | Public Request Portal Authentication Lockdown & Ignored Portal UUID | [`meters_requests_workflows_misc.py:188-206`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/meters_requests_workflows_misc.py#L188-L206) | [`RequestController.java:69-75`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/RequestController.java#L69-L75) | [`request.ts:150-160`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/request.ts#L150-L160) |
| `REQ-P0-02` | Meters | **P0** | Reading CRUD Cross-Tenant Leak & Trigger WorkOrder Injection | [`meters_requests_workflows_misc.py:228-264`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/meters_requests_workflows_misc.py#L228-L264) | [`ReadingController.java:35-85`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/ReadingController.java#L35-L85) | [`meter.ts:130-165`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/meter.ts#L130-L165) |
| `REQ-P0-03` | Checklists | **P0** | Checklist Mini Route Cross-Tenant Leak | [`parts_po_tasks.py:455-462`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/parts_po_tasks.py#L455-L462) | [`ChecklistController.java:45-60`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/ChecklistController.java#L45-L60) | [`checklist.ts:110-125`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/checklist.ts#L110-L125) |
| `REQ-P1-01` | Workflows | **P1** | Inert Workflows Engine: Zero Automation Execution on Lifecycle Events | [`meters_requests_workflows_misc.py:555-616`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/meters_requests_workflows_misc.py#L555-L616) | [`WorkflowService.java:65-190`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/service/WorkflowService.java#L65-L190) | [`workflow.ts:50-130`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/workflow.ts#L50-L130) |
| `AUTH-P0-01` | Auth & Users | **P0** | Cross-Tenant Role Disclosure, Tampering, and Deletion | [`auth_users.py:755-827`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/auth_users.py#L755-L827) | [`RoleController.java:29-62`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/RoleController.java#L29-L62) | [`role.ts:80-120`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/role.ts#L80-L120) |
| `AUTH-P0-02` | Auth & Users | **P0** | Single Shared `UserSettings` Row Assigned to All Newly Created Users | [`auth_users.py:581`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/auth_users.py#L581) | [`UserService.java:152-250`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/service/UserService.java#L152-L250) | [`user.ts:230-234`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/user.ts#L230-L234) |
| `AUTH-P0-03` | Auth & Users | **P0** | System-Wide UIConfiguration Collision Across Tenants | [`auth_users.py:470-484`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/auth_users.py#L470-L484) | [`CompanySettingsService.java:90-110`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/service/CompanySettingsService.java#L90-L110) | Shell UI |
| `AUTH-P1-01` | Auth & Users | **P1** | User Invitations Contract Mismatch & Array Crash | [`auth_users.py:623-645`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/auth_users.py#L623-L645) | [`UserController.java:120-145`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/UserController.java#L120-L145) | [`user.ts:245-281`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/user.ts#L245-L281) |
| `AN-P0-01` | Analytics | **P0** | Work Order Costs/Time Path Mismatch & Destructive Fallback Return Type | [`analytics.py:121, 154-165`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/analytics.py#L121) | [`WOAnalyticsController.java:536`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/analytics/WOAnalyticsController.java#L536) | [`workOrder.ts:393-410`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/analytics/workOrder.ts#L393-L410) |
| `AN-P0-02` | Analytics | **P0** | Part Analytics Sub-Routes Completely Unimplemented and Return `[]` | [`analytics.py:201-222`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/analytics.py#L201-L222) | [`PartAnalyticsController.java:64-160`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/analytics/PartAnalyticsController.java#L64-L160) | [`part.ts:123-210`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/analytics/part.ts#L123-L210) |
| `AN-P0-03` | Analytics | **P0** | Request Analytics Overview Route Missing & Type Mismatch | [`analytics.py:241-268`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/analytics.py#L241-L268) | [`RequestAnalyticsController.java:45-90`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/analytics/RequestAnalyticsController.java#L45-L90) | [`request.ts:105-188`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/analytics/request.ts#L105-L188) |
| `AN-P0-04` | Analytics | **P0** | User Analytics Endpoint Missing & DTO Property Casing Regression | [`analytics.py:271-293`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/analytics.py#L271-L293) | [`UserAnalyticsController.java:37-65`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/analytics/UserAnalyticsController.java#L37-L65) | [`user.ts:59-97`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/analytics/user.ts#L59-L97) |

---

## 3. Detailed Technical Findings & Fix Designs

### Domain 1: Work Orders, Labor, PartQuantities, Additional Costs & Tasks

#### `WO-P0-01`: Labor Timer URL Contract Mismatch & Duration Zero Out
- **Files**:
  - Python: [`atlas-cmms/src/routes/work_orders_pm.py:404-456`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/work_orders_pm.py#L404-L456)
  - Java: [`api/src/main/java/com/grash/controller/LaborController.java:51-60`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/LaborController.java#L51-L60), [`api/src/main/java/com/grash/service/LaborService.java:88-94`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/service/LaborService.java#L88-L94)
  - Frontend: [`frontend/src/slices/labor.ts:153-158`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/labor.ts#L153-L158)
- **Root Cause**:
  1. The React frontend calls:
     ```typescript
     api.post<Labor>(`labors/work-order/${id}?start=${start}`, {});
     ```
  2. Python declared:
     ```python
     @labors_router.post("/work-order/{wo_id}")
     def create_labor_for_wo(wo_id: int, payload: dict[str, Any] = Body(...), ...)
     ```
     This endpoint expects a full JSON body for a manual labor entry and completely ignores the query parameter `?start=true|false`.
  3. Python invented a non-standard endpoint `@labors_router.post("/controlling-time-timer")` that no frontend code ever calls.
  4. In both endpoints, when a timer is stopped (`started = False`), Python never computes the elapsed seconds (`(now - labor.started_at).total_seconds()`). The `duration` remains `0`, so work order labor costs and technician labor hours are never recorded.
  5. The endpoint lacks tenant verification: it never asserts that `wo.company_id == current_user.company_id`.
- **Technical Fix Design**:
  Reconcile `POST /api/labors/work-order/{wo_id}` to handle both timer control (`?start=true|false`) and manual creation:
  ```python
  @labors_router.post("/work-order/{wo_id}")
  def handle_labor_for_wo(
      wo_id: int,
      start: bool | None = Query(default=None),
      payload: dict[str, Any] = Body(default_factory=dict),
      current_user: User = Depends(get_current_user),
      db: Session = Depends(get_db),
  ) -> dict[str, Any]:
      wo = db.get(WorkOrder, wo_id)
      if not wo or wo.company_id != current_user.company_id:
          raise CustomException(status_code=404, message="WorkOrder not found")
      
      if start is not None:
          existing_timer = db.scalar(
              select(Labor).where(
                  Labor.work_order_id == wo_id,
                  Labor.assigned_to_id == current_user.id,
                  Labor.started.is_(True),
              )
          )
          if start:
              if existing_timer:
                  return _serialize_labor(existing_timer, db)
              labor = Labor(
                  work_order_id=wo_id,
                  assigned_to_id=current_user.id,
                  started=True,
                  started_at=datetime.now(timezone.utc),
                  duration=0,
                  hourly_rate=current_user.rate or 0.0,
                  company_id=current_user.company_id,
              )
              db.add(labor)
              db.commit()
              db.refresh(labor)
              return _serialize_labor(labor, db)
          else:
              if not existing_timer:
                  raise CustomException(status_code=404, message="No running timer found")
              now = datetime.now(timezone.utc)
              elapsed_seconds = int((now - existing_timer.started_at).total_seconds()) if existing_timer.started_at else 0
              existing_timer.started = False
              existing_timer.duration = (existing_timer.duration or 0) + elapsed_seconds
              existing_timer.hourly_rate = current_user.rate or 0.0
              db.commit()
              db.refresh(existing_timer)
              return _serialize_labor(existing_timer, db)
      else:
          # Handle manual labor record creation
          ...
  ```

---

#### `WO-P0-02`: PartQuantities WO Array of Ints Payload Drops All Parts & Wipes Existing Stock
- **Files**:
  - Python: [`atlas-cmms/src/routes/parts_po_tasks.py:378-380, 434-442`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/parts_po_tasks.py#L378-L380)
  - Java: [`api/src/main/java/com/grash/controller/PartQuantityController.java:72-108`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/PartQuantityController.java#L72-L108)
  - Frontend: [`frontend/src/slices/partQuantity.ts:135-149`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/partQuantity.ts#L135-L149)
  - Frontend UI Caller: [`frontend/src/content/own/WorkOrders/Details/WorkOrderDetails.tsx:1023`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/content/own/WorkOrders/Details/WorkOrderDetails.tsx#L1023)
- **Root Cause**:
  1. The React UI dispatches `editWOPartQuantities(id, parts: number[])`:
     ```typescript
     export const editWOPartQuantities = (id: number, parts: number[]): AppThunk =>
       async (dispatch) => {
         const partQuantities = await api.patch<PartQuantity[]>(
           `${basePath}/work-order/${id}`,
           parts, // Array of part IDs: e.g. [1, 2, 5]
           null
         );
     ```
  2. In Java (`PartQuantityController.java:74-76`), the method signature is:
     ```java
     public Collection<PartQuantityShowDTO> patchWorkOrder(@RequestBody List<Long> parts, @PathVariable("id") Long id)
     ```
  3. In Python (`parts_po_tasks.py:378-380`), the loop explicitly ignores integers:
     ```python
     for item in payload:
         if not isinstance(item, dict):
             continue
     ```
  4. When called from the frontend, every item in `payload` is an `int`, so `continue` fires every iteration. The loop does nothing, and `seen_ids` remains empty.
  5. Lines 434-442 then execute:
     ```python
     for pq in existing_rows:
         if pq.id not in seen_ids:
             _consume_or_restore_part_stock(pq.part_id, -float(pq.quantity or 0.0), wo.id, current_user, db)
             db.delete(pq)
     ```
     Every existing `PartQuantity` on the Work Order is deleted, and its stock is restored to warehouse inventory!
- **Technical Fix Design**:
  Support both `payload: list[int | dict[str, Any]]`:
  ```python
  for item in payload:
      if isinstance(item, int):
          part_id = item
          item_id = None
          new_qty = 1.0  # Default quantity 1 matching Java PartQuantityController line 97
      elif isinstance(item, dict):
          item_id = item.get("id") if isinstance(item.get("id"), int) else None
          part_id = _extract_part_id(item)
          new_qty = float(item.get("quantity", 0) or 0)
      else:
          continue
  ```

---

#### `WO-P0-03`: Direct PartQuantity CRUD Bypasses Inventory Deduction & Restock Lifecycle
- **Files**:
  - Python: [`atlas-cmms/src/routes/parts_po_tasks.py:322-328`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/parts_po_tasks.py#L322-L328)
  - Java: [`api/src/main/java/com/grash/controller/PartQuantityController.java:195-242`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/PartQuantityController.java#L195-L242)
  - Frontend: [`frontend/src/slices/partQuantity.ts:16-50`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/partQuantity.ts#L16-L50)
- **Root Cause**:
  `pq_router = build_crud_router("/part-quantities", PartQuantity, custom_serializer=_serialize_part_quantity, after_create=_after_create_pq)`
  1. It provides no `before_patch` or `after_patch` hooks. When a technician edits a part quantity via `PATCH /part-quantities/{id}`, the quantity column in the database updates, but stock on `Part` is never adjusted, and no `PartTransaction` is generated.
  2. It provides no `before_delete` hook. When a user deletes a `PartQuantity` via `DELETE /part-quantities/{id}`, the row is removed from the DB, but warehouse stock is never restored. The inventory is permanently lost.
  3. It lacks parent `WorkOrder` / `PurchaseOrder` edit permissions: Java checks `savedPartQuantity.getWorkOrder().canBeEditedBy(user)`. Python allows any tenant user to modify or delete quantities on work orders they cannot edit.
- **Technical Fix Design**:
  Attach `before_patch` and `before_delete` hooks to `pq_router`:
  ```python
  def _before_patch_pq(pq: PartQuantity, payload: dict[str, Any], current_user: User, db: Session) -> None:
      if "quantity" in payload and pq.work_order_id:
          new_qty = float(payload["quantity"])
          delta = new_qty - float(pq.quantity or 0.0)
          if delta != 0:
              _consume_or_restore_part_stock(pq.part_id, delta, pq.work_order_id, current_user, db)

  def _before_delete_pq(pq: PartQuantity, current_user: User, db: Session) -> None:
      if pq.work_order_id and pq.part_id:
          _consume_or_restore_part_stock(pq.part_id, -float(pq.quantity or 0.0), pq.work_order_id, current_user, db)
  ```

---

#### `WO-P0-04`: Task Duplication Explosion on WO & PM Edits
- **Files**:
  - Python: [`atlas-cmms/src/routes/parts_po_tasks.py:299-391`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/parts_po_tasks.py#L299-L391)
  - Java: [`api/src/main/java/com/grash/controller/TaskController.java:106-150`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/TaskController.java#L106-L150)
  - Frontend: [`frontend/src/slices/task.ts:106-118`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/task.ts#L106-L118)
- **Root Cause**:
  In `patch_tasks_for_wo` and `patch_tasks_for_pm`:
  ```python
  for item in payload:
      tb = TaskBase(...)
      db.add(tb)
      db.flush()
      t = Task(task_base_id=tb.id, work_order_id=wo_id, ...)
      db.add(t)
  ```
  Every time a technician checks a checkbox or saves a WorkOrder/PM with tasks, Python generates brand new `TaskBase`, `TaskOption`, and `Task` rows. Existing rows are neither updated nor removed. The database accumulates duplicate tasks exponentially, and previous technician notes/values are overwritten or orphaned.
- **Technical Fix Design**:
  Reconcile existing tasks by matching `task.id` / `task.task_base_id`:
  - Fetch existing `tasks = db.scalars(select(Task).where(Task.work_order_id == wo_id)).all()`.
  - Identify incoming task IDs from `payload`.
  - For matching tasks: update `notes`, `value`, `user_id`, and child `TaskBase` fields (`label`, `task_type`).
  - For new tasks in payload: create `TaskBase`, `TaskOptions`, and `Task`.
  - For tasks omitted in payload: delete obsolete `Task` and associated `TaskBase`.

---

#### `WO-P0-05`: Work Order M2M Collections & `customFieldValues` Dropped on Save
- **Files**:
  - Python: [`atlas-cmms/src/routes/work_orders_pm.py:84-142`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/work_orders_pm.py#L84-L142), [`atlas-cmms/src/services/serializer.py:102, 375`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/services/serializer.py#L102)
  - Java: [`api/src/main/java/com/grash/service/WorkOrderService.java:110-145`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/service/WorkOrderService.java#L110-L145)
  - Frontend: [`frontend/src/slices/workOrder.ts:180-210`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/workOrder.ts#L180-L210)
- **Root Cause**:
  When a WorkOrder is created or patched, `apply_patch` ignores non-column keys. The tables `work_order_assigned_to_users`, `work_order_customers`, `work_order_files`, and `custom_field_values` are never updated.
  On serialization, `_MODEL_DEFAULT_LISTS["WorkOrder"]` defaults them to empty arrays `[]`.
- **Technical Fix Design**:
  Add `_sync_wo_associations(wo, payload, db)` in `_after_create_wo` and `_after_patch_wo`:
  - Sync `assignedTo` into `work_order_assigned_to_users`.
  - Sync `customers` into `work_order_customers`.
  - Sync `files` into `work_order_files`.
  - Sync `customFieldValues` into `CustomFieldValue` (`work_order_id = wo.id`).
  - Hydrate these collections in `_serialize_wo(wo, db)`.

---

#### `WO-P1-01`: Work Order Status Change Missing RBAC, Signature Verification & Completion Reset
- **Files**:
  - Python: [`atlas-cmms/src/routes/work_orders_pm.py:510-535`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/work_orders_pm.py#L510-L535)
  - Java: [`api/src/main/java/com/grash/service/WorkOrderService.java:833-895`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/service/WorkOrderService.java#L833-L895)
  - Frontend: [`frontend/src/slices/workOrder.ts:240-270`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/workOrder.ts#L240-L270)
- **Root Cause**:
  1. `change_wo_status` only performs `assert_company_access(current_user, wo)`. It does not verify object edit rights (`can_edit_object(current_user, wo, "WORK_ORDERS", db)`), allowing non-technicians/viewers to transition work order statuses.
  2. If `wo.required_signature` is true and status transitions to `COMPLETE` without a signature, Java throws `400 Bad Request`. Python ignores signature requirements.
  3. When transitioning status away from `COMPLETE` (e.g. reopening), Java explicitly resets:
     ```java
     mutableWO.setCompletedOn(null);
     mutableWO.setCompletedBy(null);
     ```
     Python retains the old `completed_on` timestamp, corrupting status reports and MTTR metrics.
  4. Active labor timers are never stopped when transitioning away from `IN_PROGRESS` or completing a work order.
- **Technical Fix Design**:
  Align `change_wo_status` with `WorkOrderService.java:833-895`:
  - Enforce `can_edit_object`.
  - Validate signature format and presence when `wo.required_signature` is set.
  - When status is not complete, clear `completed_on` and `completed_by_id`.
  - Stop running `Labor` timers for the work order.

---

#### `WO-P1-02`: AdditionalCost Generic CRUD Cross-Tenant Security Hole & Missing Object RBAC
- **Files**:
  - Python: [`atlas-cmms/src/routes/parts_po_tasks.py:678-699`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/parts_po_tasks.py#L678-L699)
  - Java: [`api/src/main/java/com/grash/controller/AdditionalCostController.java:45-120`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/AdditionalCostController.java#L45-L120)
  - Frontend: [`frontend/src/slices/additionalCost.ts:35-85`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/additionalCost.ts#L35-L85)
- **Root Cause**:
  1. The `AdditionalCost` table does not contain `company_id`.
  2. `ac_router = build_crud_router("/additional-costs", AdditionalCost)` mounts standard CRUD.
  3. `scoped_select()` applies no company filter when `company_id` is absent, allowing `GET /additional-costs` to leak all additional costs across all companies.
  4. In `PATCH` / `DELETE`, `assert_company_access()` exits early because `target_company_id is None`.
  5. In Java, access is governed strictly by checking the parent Work Order: `workOrder.canBeEditedBy(user)`.
- **Technical Fix Design**:
  Replace `build_crud_router` with custom route handlers that validate parent `WorkOrder.company_id == current_user.company_id` and enforce `can_edit_object(current_user, wo, "WORK_ORDERS", db)`.

---

### Domain 2: Preventive Maintenance & Schedules

#### `PM-P0-01`: Schedule Generic CRUD Cross-Tenant Reschedule & Data Leak
- **Files**:
  - Python: [`atlas-cmms/src/routes/work_orders_pm.py:1084-1108`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/work_orders_pm.py#L1084-L1108), [`atlas-cmms/src/models/pm_schedule.py:50`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/models/pm_schedule.py#L50)
  - Java: [`api/src/main/java/com/grash/controller/ScheduleController.java:38-70`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/ScheduleController.java#L38-L70)
  - Frontend: [`frontend/src/slices/preventiveMaintenance.ts:120-155`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/preventiveMaintenance.ts#L120-L155)
- **Root Cause**:
  1. `Schedule` has no `company_id` column.
  2. `schedules_router = build_crud_router("/schedules", Schedule, ...)` exposes generic CRUD.
  3. In `PATCH /schedules/{id}/reschedule`, Python runs `assert_company_access(current_user, sched)`. Because `sched` has no `company_id`, `assert_company_access` in `src/deps/company.py:73-74` does:
     ```python
     if target_company_id is None:
         return
     ```
     This allows ANY tenant user to reschedule ANY other tenant's PM schedules.
  4. `GET /schedules` similarly leaks all schedules across all tenants.
- **Technical Fix Design**:
  Validate schedule access via its linked `PreventiveMaintenance` record:
  ```python
  pm = db.scalar(select(PreventiveMaintenance).where(PreventiveMaintenance.schedule_id == sched.id))
  if not pm or pm.company_id != current_user.company_id:
      raise CustomException(status_code=403, message="Access is denied")
  ```

---

#### `PM-P0-02`: Trigger Work Order Fails to Clone Tasks, Checklists, or Due Date Delay
- **Files**:
  - Python: [`atlas-cmms/src/routes/work_orders_pm.py:593-626`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/work_orders_pm.py#L593-L626)
  - Java: [`api/src/main/java/com/grash/service/PreventiveMaintenanceService.java:153-205`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/service/PreventiveMaintenanceService.java#L153-L205)
  - Frontend: [`frontend/src/slices/preventiveMaintenance.ts:160-170`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/preventiveMaintenance.ts#L160-L170)
- **Root Cause**:
  `POST /api/preventive-maintenances/{id}/trigger-work-order` instantiates a bare `WorkOrder`:
  ```python
  wo = WorkOrder(
      title=pm.title,
      description=pm.description,
      priority=pm.priority,
      asset_id=pm.asset_id,
      location_id=pm.location_id,
      parent_preventive_maintenance_id=pm.id,
      company_id=pm.company_id,
      due_date=datetime.now(timezone.utc),  # <-- WRONG
  )
  ```
  1. It sets `due_date = now()`, completely ignoring `schedule.due_date_delay` (`now() + timedelta(days=schedule.due_date_delay)`).
  2. It does not clone any tasks from the PM schedule into the Work Order (`PreventiveMaintenanceService.java:153-157` clones each `TaskBase` and `TaskOption`).
  3. It does not copy PM custom field values or attachments to the generated Work Order.
- **Technical Fix Design**:
  Update `trigger_pm_work_order`:
  ```python
  due_date = None
  if pm.schedule and pm.schedule.due_date_delay:
      due_date = datetime.now(timezone.utc) + timedelta(days=pm.schedule.due_date_delay)
  wo = WorkOrder(..., due_date=due_date)
  db.add(wo)
  db.flush()
  
  # Clone tasks from PM to WO
  pm_tasks = db.scalars(select(Task).where(Task.preventive_maintenance_id == pm.id)).all()
  for pmt in pm_tasks:
      tb = db.get(TaskBase, pmt.task_base_id)
      if tb:
          new_tb = TaskBase(label=tb.label, task_type=tb.task_type, company_settings_id=tb.company_settings_id)
          db.add(new_tb)
          db.flush()
          for opt in tb.options:
              db.add(TaskOption(label=opt.label, task_base_id=new_tb.id))
          db.add(Task(task_base_id=new_tb.id, work_order_id=wo.id, company_id=pm.company_id))
  ```

---

#### `PM-P0-03`: Background PM Generator Ignores Recurrence Type, Days of Week, and Completed Date Basis
- **Files**:
  - Python: [`atlas-cmms/src/jobs/pm_generator.py:14-108`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/jobs/pm_generator.py#L14-L108)
  - Java: [`api/src/main/java/com/grash/service/ScheduleService.java:110-180`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/service/ScheduleService.java#L110-L180)
- **Root Cause**:
  In `pm_generator.py`:
  ```python
  sched.next_due_date = sched.next_due_date + timedelta(days=sched.frequency)
  ```
  1. It ignores `recurrence_type`: weekly schedules with specific days of the week (`daysOfWeek`), monthly schedules, and yearly schedules cannot be scheduled correctly by adding a fixed day count.
  2. It ignores `schedule_days_of_week`: a PM scheduled for "every Monday and Wednesday" simply advances by `frequency` days.
  3. It ignores `recurrence_based_on == COMPLETED_DATE`: if a maintenance task is completed late, Java calculates `next_due_date` starting from `last_completed_work_order.completed_on`. Python always advances from `sched.next_due_date`, leading to cascading overdue backlogs.
- **Technical Fix Design**:
  Implement Java's `ScheduleService.calculateNextDueDate()` algorithm in Python:
  - Check `schedule.recurrence_type`:
    - `DAILY`: `base_date + timedelta(days=schedule.frequency)`.
    - `WEEKLY`: calculate the next enabled day from `schedule_days_of_week`. If all weekly days have passed, jump by `(schedule.frequency) * 7` days to the first day of week.
    - `MONTHLY`: increment months using `relativedelta(months=schedule.frequency)`.
    - `YEARLY`: increment years using `relativedelta(years=schedule.frequency)`.
  - Check `schedule.recurrence_based_on`: if `COMPLETED_DATE`, check if latest WO is completed; if not, do not generate the next WO until the previous one is closed.

---

### Domain 3: Parts, Purchase Orders, MultiParts, Vendors & Customers

#### `PO-P0-01`: Purchase Order Approval Missing RBAC & Approval Reversal Inventory Bug
- **Files**:
  - Python: [`atlas-cmms/src/routes/parts_po_tasks.py:626-674`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/parts_po_tasks.py#L626-L674)
  - Java: [`api/src/main/java/com/grash/controller/PurchaseOrderController.java:163-177`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/PurchaseOrderController.java#L163-L177)
  - Frontend: [`frontend/src/slices/purchaseOrder.ts:156`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/purchaseOrder.ts#L156)
- **Root Cause**:
  1. `respond_purchase_order` lacks RBAC checks (Java checks `edit_other_permissions` on `PermissionEntity.PURCHASE_ORDERS`). Any technician can approve or reject POs.
  2. Line 648 checks `if is_approved and po.status != 0:` to add stock and write `PartConsumption(description="PART_RECEPTION")`.
  3. Line 670 sets `po.status = 0 if is_approved else 2`. If an already approved PO (`po.status == 0`) is subsequently rejected (`approved=False`), Python changes the status to `REJECTED` but never reverts the received inventory stock or creates a reversing transaction.
- **Technical Fix Design**:
  Enforce `can_edit(current_user, PermissionEntity.PURCHASE_ORDERS, db)`. If `not is_approved and po.status == 0` (reverting an approval), deduct the received quantities from `Part.quantity` and log a reversal transaction.

---

#### `PO-P0-02`: MultiParts Cross-Tenant Part Injection & Information Disclosure
- **Files**:
  - Python: [`atlas-cmms/src/routes/parts_po_tasks.py:559-574`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/parts_po_tasks.py#L559-L574)
  - Java: [`api/src/main/java/com/grash/controller/MultiPartsController.java:45-75`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/MultiPartsController.java#L45-L75)
  - Frontend: [`frontend/src/slices/multiPart.ts:80-120`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/multiPart.ts#L80-L120)
- **Root Cause**:
  In `_sync_multi_parts`:
  ```python
  for item in payload["parts"]:
      pid = item.get("id") if isinstance(item, dict) else item
      if isinstance(pid, int):
          db.execute(t_multi_parts_part_associations.insert().values(id_multi_parts=mp.id, id_part=pid))
  ```
  It never validates that `Part.id == pid` belongs to `current_user.company_id`. A tenant can associate parts belonging to other companies. When `_serialize_multi_parts` runs, it calls `_serialize_part` on those foreign parts, leaking another company's spare parts names, stock levels, costs, and warehouse locations.
- **Technical Fix Design**:
  Validate all part IDs before insertion:
  ```python
  part = db.get(Part, pid)
  if not part or part.company_id != current_user.company_id:
      raise CustomException(status_code=400, message=f"Invalid part {pid}")
  ```

---

#### `PO-P0-03`: Part M2M Associations Dropped on Save & Serialized as Empty Arrays
- **Files**:
  - Python: [`atlas-cmms/src/routes/parts_po_tasks.py:40-75`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/parts_po_tasks.py#L40-L75), [`atlas-cmms/src/services/serializer.py:115-123`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/services/serializer.py#L115-L123)
  - Java: [`api/src/main/java/com/grash/service/PartService.java:70-115`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/service/PartService.java#L70-L115)
  - Frontend: [`frontend/src/slices/part.ts:110-160`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/part.ts#L110-L160)
- **Root Cause**:
  `parts_router` does not have custom hooks or serializers for its 6 relationship tables:
  `part_vendors`, `part_customers`, `part_teams`, `part_locations`, `part_files`, and `CustomFieldValue`.
  When a user links vendors or storage locations to a spare part in the UI, the backend silently drops them, and GET returns empty arrays `[]`.
- **Technical Fix Design**:
  Implement `_sync_part_associations` in `parts_po_tasks.py`:
  - Sync association rows in `t_part_vendor_associations`, `t_part_customer_associations`, `t_part_team_associations`, `t_part_location_associations`, and `t_part_file_associations`.
  - Persist `customFieldValues`.
  - In `_serialize_part`, load and serialize each association mini-DTO list.

---

### Domain 4: Meters, Requests, Request Portal, Workflows & Checklists

#### `REQ-P0-01`: Public Request Portal Authentication Lockdown & Ignored Portal UUID
- **Files**:
  - Python: [`atlas-cmms/src/routes/meters_requests_workflows_misc.py:188-206, 365-375`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/meters_requests_workflows_misc.py#L188-L206)
  - Java: [`api/src/main/java/com/grash/controller/RequestController.java:69-75`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/RequestController.java#L69-L75)
  - Frontend: [`frontend/src/slices/request.ts:150-160`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/request.ts#L150-L160)
- **Root Cause**:
  1. Java allows anonymous public access (`@PreAuthorize("permitAll()")`) on `POST /requests/portal/{portal_uuid}` so unauthenticated building occupants can scan a QR code and submit a ticket.
  2. Python declared:
     ```python
     @requests_router.post("/portal/{portal_uuid}")
     def create_portal_request(
         portal_uuid: str,
         payload: dict[str, Any] = Body(...),
         current_user: User = Depends(get_current_user),  # <-- LOCKDOWN!
         db: Session = Depends(get_db),
     ):
     ```
     Any unauthenticated submission receives `HTTP 401 Unauthorized`.
  3. Furthermore, line 198 sets `company_id=current_user.company_id`. It never looks up `RequestPortal` by `portal_uuid`! If `portal_uuid` belonged to Tenant B, it would be misfiled under `current_user`'s company.
  4. The file upload endpoint for the public portal (`POST /files/upload/request-portal/{portal_uuid}`) similarly requires `current_user`, blocking photo attachments from public users.
- **Technical Fix Design**:
  Remove `Depends(get_current_user)` from both public endpoints and resolve `company_id` strictly via `RequestPortal`:
  ```python
  @requests_router.post("/portal/{portal_uuid}")
  def create_portal_request(
      portal_uuid: str,
      payload: dict[str, Any] = Body(...),
      db: Session = Depends(get_db),
  ) -> dict[str, Any]:
      portal = db.scalar(select(RequestPortal).where(RequestPortal.uuid == portal_uuid))
      if not portal:
          raise CustomException(status_code=404, message="Invalid request portal")
      
      company_id = portal.company_id
      req = Request(
          description=payload.get("description", ""),
          priority=payload.get("priority", 0),
          asset_id=payload.get("asset", {}).get("id") or payload.get("assetId"),
          location_id=payload.get("location", {}).get("id") or payload.get("locationId"),
          company_id=company_id,
      )
      db.add(req)
      db.commit()
      db.refresh(req)
      return _serialize_request(req, db)
  ```

---

#### `REQ-P0-02`: Reading CRUD Cross-Tenant Leak & Trigger WorkOrder Injection
- **Files**:
  - Python: [`atlas-cmms/src/routes/meters_requests_workflows_misc.py:228-264`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/meters_requests_workflows_misc.py#L228-L264), [`atlas-cmms/src/models/meters.py:40`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/models/meters.py#L40)
  - Java: [`api/src/main/java/com/grash/controller/ReadingController.java:35-85`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/ReadingController.java#L35-L85)
  - Frontend: [`frontend/src/slices/meter.ts:130-165`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/meter.ts#L130-L165)
- **Root Cause**:
  1. The `Reading` model contains `meter_id`, but has no `company_id` column.
  2. `readings_router = build_crud_router("/readings", Reading, after_create=_after_create_reading)` mounts generic CRUD.
  3. `GET /readings` queries `select(Reading)` without tenant scoping, leaking meter readings across all tenants.
  4. In `POST /readings`, Python creates a reading without asserting that `meter.company_id == current_user.company_id`.
  5. In `_after_create_reading`, if the target meter has configured `WorkOrderMeterTrigger` rules, an attacker in Tenant A can submit readings for Tenant B's meter to maliciously trigger WorkOrders inside Tenant B's organization.
- **Technical Fix Design**:
  Replace `build_crud_router` with dedicated endpoints mirroring Java `ReadingController.java`:
  - Enforce `meter.company_id == current_user.company_id` on reading creation.
  - Restrict reading queries strictly to `GET /readings/meter/{id}` with parent meter tenant validation.

---

#### `REQ-P0-03`: Checklist Mini Route Cross-Tenant Leak
- **Files**:
  - Python: [`atlas-cmms/src/routes/parts_po_tasks.py:455-462`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/parts_po_tasks.py#L455-L462)
  - Java: [`api/src/main/java/com/grash/controller/ChecklistController.java:45-60`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/ChecklistController.java#L45-L60)
  - Frontend: [`frontend/src/slices/checklist.ts:110-125`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/checklist.ts#L110-L125)
- **Root Cause**:
  ```python
  @checklists_router.get("/mini")
  def list_checklists_mini(
      current_user: User = Depends(get_current_user),
      db: Session = Depends(get_db),
  ) -> list[dict[str, Any]]:
      rows = db.scalars(select(Checklist)).all()
      return [{"id": c.id, "name": c.name} for c in rows]
  ```
  `select(Checklist).all()` has zero `where()` filter! In a multi-tenant deployment, every tenant sees the proprietary inspection checklists created by all other tenants.
- **Technical Fix Design**:
  Filter by `company_settings_id`:
  ```python
  company = db.get(Company, current_user.company_id)
  cs_id = company.company_settings_id if company else None
  rows = db.scalars(
      select(Checklist).where(Checklist.company_settings_id == cs_id)
  ).all()
  ```

---

#### `REQ-P1-01`: Inert Workflows Engine: Zero Automation Execution on Lifecycle Events
- **Files**:
  - Python: [`atlas-cmms/src/routes/meters_requests_workflows_misc.py:555-616`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/meters_requests_workflows_misc.py#L555-L616)
  - Java: [`api/src/main/java/com/grash/service/WorkflowService.java:65-190`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/service/WorkflowService.java#L65-L190)
  - Frontend: [`frontend/src/slices/workflow.ts:50-130`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/workflow.ts#L50-L130)
- **Root Cause**:
  In Java, `WorkflowService.runWorkOrder`, `runRequest`, `runPurchaseOrder`, `runPart`, and `runTask` execute automated business logic whenever entities are created or edited (matching conditions and triggering automated assignments, status changes, and notifications).
  In Python, only basic CRUD operations on `Workflow` models exist. There is zero execution engine hooked into `WorkOrder`, `Request`, `Part`, or `Task` lifecycles. Workflows configured in the UI are completely dead code.
- **Technical Fix Design**:
  Implement `WorkflowExecutionEngine` in `src/services/workflows.py` and call `execute_workflows(trigger_event, entity, db)` from service lifecycle hooks on WO, Request, and PO updates.

---

### Domain 5: Users, Roles, Teams, Company Settings & Auth

#### `AUTH-P0-01`: Cross-Tenant Role Disclosure, Tampering, and Deletion
- **Files**:
  - Python: [`atlas-cmms/src/routes/auth_users.py:755-827`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/auth_users.py#L755-L827)
  - Java: [`api/src/main/java/com/grash/controller/RoleController.java:29-62`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/RoleController.java#L29-L62), [`api/src/main/java/com/grash/service/RoleService.java:61-120`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/service/RoleService.java#L61-L120)
  - Frontend: [`frontend/src/slices/role.ts:80-120`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/role.ts#L80-L120)
- **Root Cause**:
  1. `list_roles` executes `db.scalars(select(Role)).all()`, returning every custom role created by all tenants.
  2. `patch_role` and `delete_role` take `{role_id}` from the path and directly update/delete it without checking `role.company_settings_id == current_user.company.company_settings_id`.
  3. A user can delete system default roles (`ROLE_CLIENT`, `ROLE_SUPER_ADMIN`) or modify another tenant's custom role permissions.
- **Technical Fix Design**:
  - Filter `GET /roles` to include only global default roles (`company_settings_id IS NULL`) plus the caller's custom roles (`company_settings_id == caller_cs_id`).
  - In `patch_role` and `delete_role`:
    - Disallow mutating/deleting system default roles (`role.role_type == 0` or `role.company_settings_id IS NULL`).
    - Assert `role.company_settings_id == caller_cs_id`.

---

#### `AUTH-P0-02`: Single Shared `UserSettings` Row Assigned to All Newly Created Users
- **Files**:
  - Python: [`atlas-cmms/src/routes/auth_users.py:581`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/auth_users.py#L581)
  - Java: [`api/src/main/java/com/grash/service/UserService.java:152-250`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/service/UserService.java#L152-L250)
  - Frontend: [`frontend/src/slices/user.ts:230-234`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/user.ts#L230-L234)
- **Root Cause**:
  Line 581 in `create_user`:
  ```python
  u = User(..., user_settings_id=current_user.user_settings_id)
  ```
  Every new user created in an organization is linked to the **exact same `UserSettings` record** as the administrator who created them. If any user toggles work order or purchase order email notifications, it modifies the setting for everyone sharing that record.
- **Technical Fix Design**:
  Create an independent `UserSettings` record for every new user:
  ```python
  new_us = UserSettings(
      email_notified=True,
      email_updates_for_work_orders=True,
      email_updates_for_requests=True,
      email_updates_for_purchase_orders=True,
      stats_for_assigned_work_orders=False,
  )
  db.add(new_us)
  db.flush()
  u = User(..., user_settings_id=new_us.id)
  ```

---

#### `AUTH-P0-03`: System-Wide UIConfiguration Collision Across Tenants
- **Files**:
  - Python: [`atlas-cmms/src/routes/auth_users.py:470-484`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/auth_users.py#L470-L484)
  - Java: [`api/src/main/java/com/grash/service/CompanySettingsService.java:90-110`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/service/CompanySettingsService.java#L90-L110)
  - Frontend: Shell navigation & tab rendering
- **Root Cause**:
  `patch_ui_configuration` queries:
  ```python
  ui = db.scalar(select(UiConfiguration).limit(1))
  ```
  It ignores tenant scoping. When Tenant B hides the "Meters" or "Vendors and Customers" tab in the UI, Tenant A's interface is mutated as well.
- **Technical Fix Design**:
  Scope `UiConfiguration` by `company_settings_id`:
  ```python
  company = db.get(Company, current_user.company_id)
  cs_id = company.company_settings_id if company else 1
  ui = db.scalar(select(UiConfiguration).where(UiConfiguration.company_settings_id == cs_id))
  if not ui:
      ui = UiConfiguration(company_settings_id=cs_id)
      db.add(ui)
  apply_patch(ui, payload)
  db.commit()
  ```

---

#### `AUTH-P1-01`: User Invitations Contract Mismatch & Array Crash
- **Files**:
  - Python: [`atlas-cmms/src/routes/auth_users.py:623-645`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/auth_users.py#L623-L645)
  - Java: [`api/src/main/java/com/grash/controller/UserController.java:120-145`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/UserController.java#L120-L145)
  - Frontend: [`frontend/src/slices/user.ts:245-281`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/user.ts#L245-L281)
- **Root Cause**:
  The frontend `inviteUsers` thunk expects an array of invitation objects:
  `const response = await api.post<UserInvitationMiniDTO[]>('/users/invite', payload);`
  Python returned an integer count or single object, causing frontend `.map()` invocations to fail with `TypeError: response.map is not a function`.
- **Technical Fix Design**:
  Return a list of serialized `UserInvitation` objects matching `UserInvitationMiniDTO[]`.

---

### Domain 6: Non-Asset Analytics (Work Orders, Parts, Requests, Users)

#### `AN-P0-01`: Work Order Costs/Time Path Mismatch & Destructive Fallback Return Type
- **Files**:
  - Python: [`atlas-cmms/src/routes/analytics.py:121, 154-165`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/analytics.py#L121)
  - Java: [`api/src/main/java/com/grash/controller/analytics/WOAnalyticsController.java:536`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/analytics/WOAnalyticsController.java#L536)
  - Frontend: [`frontend/src/slices/analytics/workOrder.ts:393-410`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/analytics/workOrder.ts#L393-L410)
- **Root Cause**:
  1. Frontend calls:
     ```typescript
     api.post<WOCostsAndTime>(`analytics/work-orders/complete/costs-time`, { start, end });
     ```
  2. Python declared:
     ```python
     @router.post("/work-orders/costs/time")
     ```
     Because of the path difference (`complete/costs-time` vs `costs/time`), the request hits `wo_analytics_fallback` (`/work-orders/{subpath:path}`).
  3. The fallback returns `{"count": 0, "total": 0}`.
  4. Redux expects `WOCostsAndTime` (`total`, `average`, `partCost`, `additionalCost`, `laborCost`, `laborTime`). All cost breakdown values are `undefined`, corrupting work order analytics dashboards.
- **Technical Fix Design**:
  Align endpoint path and ensure fallback responses match expected TypeScript object schemas:
  ```python
  @router.post("/work-orders/complete/costs-time")
  @router.get("/work-orders/complete/costs-time")
  def wo_complete_costs_and_time(...):
  ```

---

#### `AN-P0-02`: Part Analytics Sub-Routes Completely Unimplemented and Return `[]`
- **Files**:
  - Python: [`atlas-cmms/src/routes/analytics.py:201-222`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/analytics.py#L201-L222)
  - Java: [`api/src/main/java/com/grash/controller/analytics/PartAnalyticsController.java:64-160`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/analytics/PartAnalyticsController.java#L64-L160)
  - Frontend: [`frontend/src/slices/analytics/part.ts:123-210`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/analytics/part.ts#L123-L210)
- **Root Cause**:
  In `analytics.py`, Part analytics has only 1 route implemented (`/parts/consumptions/overview`), which hardcodes `totalConsumptionCost: 0.0`.
  The other 5 routes called by `frontend/src/slices/analytics/part.ts` are missing:
  - `POST /analytics/parts/consumptions/date`
  - `POST /analytics/parts/consumptions/assets`
  - `POST /analytics/parts/consumptions/pareto`
  - `POST /analytics/parts/consumptions/parts-category`
  - `POST /analytics/parts/consumptions/work-order-category`
  All hit `parts_analytics_fallback` and return `[]`, rendering all Part analytics graphs empty.
- **Technical Fix Design**:
  Implement the 5 aggregation endpoints by querying `PartTransaction` where `company_id == current_user.company_id` and `created_at` is between `start` and `end`. Group by date, asset, part, and category respectively.

---

#### `AN-P0-03`: Request Analytics Overview Route Missing & Type Mismatch
- **Files**:
  - Python: [`atlas-cmms/src/routes/analytics.py:241-268`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/analytics.py#L241-L268)
  - Java: [`api/src/main/java/com/grash/controller/analytics/RequestAnalyticsController.java:45-90`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/analytics/RequestAnalyticsController.java#L45-L90)
  - Frontend: [`frontend/src/slices/analytics/request.ts:105-188`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/analytics/request.ts#L105-L188)
- **Root Cause**:
  `frontend/src/slices/analytics/request.ts` dispatches `POST /analytics/requests/overview`.
  Python implements `@router.post("/requests/rate")` instead of `/requests/overview`.
  The request falls through to `requests_analytics_fallback` which returns `[]`.
  The slice expects an object `RequestStats { approved: 0, pending: 0, cancelled: 0, cycleTime: 0 }`. Receiving an array causes `stats.approved` to be undefined, breaking KPI cards on the Requests analytics page.
- **Technical Fix Design**:
  Alias `/requests/overview` to the rate statistics calculation and return the exact `RequestStats` dictionary structure.

---

#### `AN-P0-04`: User Analytics Endpoint Missing & DTO Property Casing Regression
- **Files**:
  - Python: [`atlas-cmms/src/routes/analytics.py:271-293`](file:///Users/attiliab/Documents/GitHub/cmms/atlas-cmms/src/routes/analytics.py#L271-L293)
  - Java: [`api/src/main/java/com/grash/controller/analytics/UserAnalyticsController.java:37-65`](file:///Users/attiliab/Documents/GitHub/cmms/api/src/main/java/com/grash/controller/analytics/UserAnalyticsController.java#L37-L65)
  - Frontend: [`frontend/src/slices/analytics/user.ts:59-97`](file:///Users/attiliab/Documents/GitHub/cmms/frontend/src/slices/analytics/user.ts#L59-L97)
- **Root Cause**:
  1. Frontend calls:
     - `GET /analytics/users/me/work-orders/overview`
     - `GET /analytics/users/two-weeks/work-orders/{userId}`
  2. Python implements neither. It implemented a custom `@router.post("/users/complete/work-orders")` that returns:
     ```python
     {"created": len(wos), "Completed": sum(...)}
     ```
     Notice `"Completed"` is capitalized, whereas TypeScript `UserWOStats` expects `"completed"` (lowercase).
  3. The real endpoints hit `users_analytics_fallback` returning `[]`, leaving technician personal performance metrics broken.
- **Technical Fix Design**:
  Implement the exact Java endpoints:
  - `GET /analytics/users/me/work-orders/overview`: counts WOs created by `current_user.id` vs completed by `current_user.id`. Return `{"created": int, "completed": int}`.
  - `GET /analytics/users/two-weeks/work-orders/{user_id}`: groups WOs by day for the last 14 days for the requested user.

---

## 4. Prioritized Implementation Roadmap

To resolve these defects systematically without breaking live functionality:

```mermaid
flowchart TD
    subgraph Phase 1 [Phase 1: Multi-Tenant Security & Isolation Lockdown]
        AUTH_ROLES["AUTH-P0-01: Fix Role Tenant Scoping & Delete Protection"]
        PORTAL_AUTH["REQ-P0-01: Fix Public Request Portal Auth & UUID Scoping"]
        CHECKLIST_LEAK["REQ-P0-03: Scope Checklist Mini Route by Tenant"]
        READING_ISOLATION["REQ-P0-02: Eliminate Un-scoped Reading CRUD & Lock Down Triggers"]
        SCHEDULE_ISOLATION["PM-P0-01: Eliminate Un-scoped Schedule CRUD & Protect Reschedule"]
        COST_ISOLATION["WO-P1-02: Eliminate Un-scoped AdditionalCost CRUD"]
        SETTINGS_ISOLATION["AUTH-P0-03: Fix UI Configuration Tenant Scoping"]
    end

    subgraph Phase 2 [Phase 2: Work Orders & Inventory Side-Effects]
        LABOR_TIMER["WO-P0-01: Fix Labor Timer Query Contract & Elapsed Calculation"]
        PART_ARRAY["WO-P0-02: Support Array-of-Ints Payload on WO PartQuantities"]
        PQ_CRUD["WO-P0-03: Add Stock Adjust & Restock Hooks to Direct PQ CRUD"]
        PO_APPROVAL["PO-P0-01: Fix PO Approval RBAC & Stock Reversal on Rejection"]
        TASK_RECONCILE["WO-P0-04: Reconcile Task Updates without Duplication"]
        M2M_WO_PART["WO-P0-05 & PO-P0-03: Wire M2M & Custom Field Hydration"]
    end

    subgraph Phase 3 [Phase 3: Preventive Maintenance & Automation Engine]
        PM_TRIGGER["PM-P0-02: Clone Tasks, Checklists & Compute Due Date on Trigger"]
        PM_CRON["PM-P0-03: Implement Full Recurrence Engine in pm_generator"]
        WORKFLOWS["REQ-P1-01: Implement Workflow Execution Engine on Lifecycle Events"]
        WO_STATUS["WO-P1-01: Wire Full WO Status Lifecycle, Signature & Timers"]
    end

    subgraph Phase 4 [Phase 4: Analytics Contract & Graph Restoration]
        WO_ANALYTICS["AN-P0-01: Fix Costs-Time Route & Breakdown Schema"]
        PART_ANALYTICS["AN-P0-02: Implement 5 Missing Part Consumption Endpoints"]
        REQ_USER_ANALYTICS["AN-P0-03 & AN-P0-04: Implement Request & User Analytics Endpoints"]
    end

    Phase 1 --> Phase 2
    Phase 2 --> Phase 3
    Phase 3 --> Phase 4
```

---

## 5. Summary & Sign-off

This audit establishes that the Java $\to$ Python stack migration left critical gaps in transaction side effects (inventory management, labor timing, PM recurrence, automated workflows) and multi-tenant security isolation outside the standard CRUD builder.

All 24 identified defects are accompanied by exact source code citations in Python, Java, and Frontend TypeScript, along with self-contained fix designs. Zero changes were made to application code files during this audit.
