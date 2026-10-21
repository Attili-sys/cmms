# Asset Management Plans (`assets-management-plans/`)

This folder contains the actionable engineering execution plans for the **AJ CAFM** Asset Management domain, derived from the signed-off architecture and runtime audit in [`ASSET_MANAGEMENT_SPEC.md`](../ASSET_MANAGEMENT_SPEC.md).

---

## Active Plan (Current Scope — Fixes Only)

| Plan | Scope | Status |
|---|---|---|
| [`01_ASSET_MANAGEMENT_FIXES_PLAN.md`](./01_ASSET_MANAGEMENT_FIXES_PLAN.md) | **Strictly defect & Java-parity contract fixes (Rev 2)** across `atlas-cmms/` and `frontend/`. Covers all **9 P0 security/crash defects**, all **10 P1 correctness/UX/parity defects**, and the **3 broken existing-feature contracts (`C-01`, `C-02`, `C-03`)** across all Asset tabs (`Details`, `Work Orders`, `Downtimes`, `Meters`, `Parts`, `Files`, `Analytics`), Import/Export, plus Qatari Riyal (`QR`) default currency and all 30 non-asset backend/RBAC/workflow parity fixes (`tests/test_asset_fixes.py` + `tests/test_non_asset_audit_fixes.py` — 80 tests passing). **Zero net-new product features.** | **Implemented & Deployed (`@c9e197b0d631`)** |

---

## Explicitly Out of Scope (Deferred Until All Fixes Pass)

Per reviewer sign-off and engineering direction, the following **net-new features** are **excluded** from [`01_ASSET_MANAGEMENT_FIXES_PLAN.md`](./01_ASSET_MANAGEMENT_FIXES_PLAN.md) and deferred to future feature plans once the core asset management stack is 100% defect-free:

- **Stage 3 (Net-New Portion)**: Asset Movement / Custody History audit ledger (`asset_movement_history` table + timeline UI) and formal Decommission/Recommission wizard modal.
- **Stage 4 (Net-New Features)**: Always-on authenticated QR label sheet (`"Powered by Canvas"` print layout), contextual quick-action speed dial on Asset Detail, and Warranty countdown banner + filter presets.
- **Stage 6 (Net-New Features)**: Explainable Asset Criticality (`A/B/C`) and Condition/Health Score (`0–100`) matrix.
- **Stage 7 (`C-04` Net-New Features)**: Financial Lifecycle / Straight-Line & Declining-Balance Depreciation engine, RAV separation, and configurable Repair-vs-Replace threshold banner.
