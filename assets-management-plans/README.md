# Asset Management Plans (`assets-management-plans/`)

This folder contains the actionable engineering execution plans for the **AJ CAFM** Asset Management domain, derived from the signed-off architecture and runtime audit in [`ASSET_MANAGEMENT_SPEC.md`](../ASSET_MANAGEMENT_SPEC.md).

---

## Active Plan (Current Scope — Fixes Only)

| Plan | Scope | Status |
|---|---|---|
| [`01_ASSET_MANAGEMENT_FIXES_PLAN.md`](./01_ASSET_MANAGEMENT_FIXES_PLAN.md) | **Strictly defect & Java-parity contract fixes (Rev 2)** across `atlas-cmms/` and `frontend/`. Covers all **9 P0 security/crash defects**, all **10 P1 correctness/UX/parity defects**, and the **3 broken existing-feature contracts (`C-01`, `C-02`, `C-03`)** across all Asset tabs (`Details`, `Work Orders`, `Downtimes`, `Meters`, `Parts`, `Files`, `Analytics`), Import/Export, plus Qatari Riyal (`QR`) default currency and the non-asset backend/RBAC/workflow parity fixes. **Zero net-new product features.** | **Implemented on `migrate-python`.** The whole `atlas-cmms` suite is 86 pytest tests. Canvas build **#19** (`@8ecc014ddf63`) is deployed healthy and synced. |
| [`02_STOCK_LEDGER_AND_FLOOR_PLAN_PINS_PLAN.md`](./02_STOCK_LEDGER_AND_FLOOR_PLAN_PINS_PLAN.md) | **Stock movement ledger and floor-plan asset pins** across `atlas-cmms/` (migrations `005`, `006`) and `frontend/`. Every part quantity change becomes a `part_transaction` ledger row (receive, issue, count, WO/PO movements); floor plans gain kind, revisions, PDF upload, and asset pins on a normalised 0..1 canvas. | **Implemented (pending deploy).** The whole `atlas-cmms` suite is 115 pytest tests. |

---

## Explicitly Out of Scope (Deferred Until All Fixes Pass)

Per reviewer sign-off and engineering direction, the following **net-new features** are **excluded** from [`01_ASSET_MANAGEMENT_FIXES_PLAN.md`](./01_ASSET_MANAGEMENT_FIXES_PLAN.md) and deferred to future feature plans once the core asset management stack is 100% defect-free:

- **Stage 3 (Net-New Portion)**: Asset Movement / Custody History audit ledger (`asset_movement_history` table + timeline UI) and formal Decommission/Recommission wizard modal.
- **Stage 4 (Net-New Features)**: Always-on authenticated QR label sheet (`"Powered by Canvas"` print layout), contextual quick-action speed dial on Asset Detail, and Warranty countdown banner + filter presets.
- **Stage 6 (Net-New Features)**: Explainable Asset Criticality (`A/B/C`) and Condition/Health Score (`0–100`) matrix.
- **Stage 7 (`C-04` Net-New Features)**: Financial Lifecycle / Straight-Line & Declining-Balance Depreciation engine, RAV separation, and configurable Repair-vs-Replace threshold banner.
