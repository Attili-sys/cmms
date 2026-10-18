# AJ CAFM Web Application (`frontend/` — Powered by Canvas)

React + TypeScript + Redux Toolkit single-page application for **AJ CAFM**, compiled and bundled into the Canvas Python backend (`atlas-cmms/src/static/` and `atlas-cmms/src/static/ui/`).

---

## 1. Build & Sync Workflow

From `frontend/`:

```bash
npm install
npm run lint    # runs ESLint across src/**/*.{js,jsx,ts,tsx}
npm run build   # compiles production bundle into frontend/build/
```

> **Note:** `frontend/package.json` does not define a `test` script. Always verify with `npm run lint` and `npm run build`.

### Syncing the Compiled Bundle to `atlas-cmms/`

After `npm run build` succeeds, copy `frontend/build/*` into both `atlas-cmms/src/static/` and `atlas-cmms/src/static/ui/` while preserving `atlas-cmms/src/static/ui/runtime-env.js`:

```bash
cp -r build/* ../atlas-cmms/src/static/
cp -r build/static/* ../atlas-cmms/src/static/ui/static/
cp build/index.html build/asset-manifest.json build/manifest.json ../atlas-cmms/src/static/ui/
```

---

## 2. Architecture Overview

```
src/
├── components/         Shared UI components, "Powered by Canvas" branding (Logo, LogoSign, AppInit)
├── contexts/           JWT/SSO authentication context (JWTAuthContext.tsx) and TitleContext
├── content/own/        Feature screens:
│   ├── WorkOrders/             Work orders table, calendar, details drawer, tasks, labor, costs
│   ├── PreventiveMaintenance/  PM schedules and triggers
│   ├── Requests/               Service requests and approval actions
│   ├── Assets/                 Asset hierarchy tree, details, downtime tracking
│   ├── Locations/              Location hierarchy tree, floor plans, map integration
│   ├── Inventory/              Parts and MultiParts (Sets)
│   ├── Meters/                 Meters, readings, and work order triggers
│   ├── PeopleAndTeams/         Users and maintenance teams
│   ├── Categories/             7 category types (WorkOrder, Asset, Meter, Part, PO, Cost, Time)
│   ├── Settings/               General, Work Order Config, Request Config, Checklists, Roles, Workflows
│   └── Imports/                CSV import screens (/app/imports -> redirects to /app/imports/work-orders)
├── hooks/              useBrand ("Powered by Canvas"), useAuth, permissions hooks
├── i18n/translations/  16 locale JSON files (see src/i18n/translations/AGENTS.md)
├── layouts/            ExtendedSidebarLayout (Navy #1D174E sidebar with Gold #D69D10 active accent)
├── models/owns/        TypeScript interfaces matching backend DTOs (see ../atlas-cmms/API_CONTRACTS.md)
├── router/             React Router v6 definitions (app.tsx, account.tsx, base.tsx)
├── services/           api.ts fetch wrapper using runtime-env.js (API_URL="/api")
└── slices/             37 Redux Toolkit slices communicating with /api/* endpoints
```

---

## 3. Key Frontend Rules

1. **Branding:** All external product logos and upstream links have been removed and replaced with **"Powered by Canvas"** (`src/components/Logo`, `src/components/LogoSign`, `src/hooks/useBrand.ts`).
2. **Hierarchy State Sync:** The Locations (`src/slices/location.ts`) and Assets (`src/slices/asset.ts`) screens render from `state.locationsHierarchy` (`GET /api/locations/children/{id}/paginated`) and `state.assetsHierarchy` (`GET /api/assets/children/{id}/paginated`). Any reducer action that adds, edits, or deletes a location or asset must update both the flat list and the `*Hierarchy` array.
3. **Translations (`src/i18n/translations/AGENTS.md`):** Translate values only; never rename JSON keys.
4. **Backend DTO Contracts:** See [`../atlas-cmms/API_CONTRACTS.md`](../atlas-cmms/API_CONTRACTS.md) for the exact JSON shapes returned by `atlas-cmms/`.
