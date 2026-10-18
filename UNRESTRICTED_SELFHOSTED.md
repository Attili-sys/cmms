# Unrestricted self-hosted edition

This branch defines one self-hosted capability policy:

> When `CLOUD_VERSION=false`, every feature that is implemented in this source
> tree is available without a commercial subscription, activation key, license
> file, numerical commercial quota, trial period, or periodic connection to a
> licensing or billing service.

Authentication, company/site isolation, role permissions, approval rules,
validation, audit history, rate limits, upload limits, and other
resource-protection controls are not commercial restrictions and remain in
force.

## Licensing and corresponding source

The repository root contains the GNU Affero General Public License version 3.
The affected Java backend, React frontend, and Expo mobile source are in this
repository and do not contain a component-level license exception that
supersedes the root license. Existing copyright and license notices have been
preserved.

Operators must publish the exact Corresponding Source used for their deployed
images and set `SOURCE_CODE_URL` to that public repository or source archive.
The web sidebar and mobile settings screen expose this URL. The published
source must include local modifications, build files, lockfiles, deployment
configuration, and installation information. This document is an engineering
record, not legal advice.

## Restrictions removed

### Backend

- `LicenseService` returns a valid `Self-Hosted Unrestricted` capability state
  containing every `LicenseEntitlement` when `CLOUD_VERSION=false`. It returns
  before reading a license file, consuming Keygen request state, or making a
  Keygen HTTP request.
- The legacy `SubscriptionPlan.features` field remains in the database and API
  for compatibility, but its getter exposes all implemented `PlanFeatures`.
  Existing plan rows are not rewritten.
- Existing entitlement checks therefore allow implemented features including
  SSO/LDAP, work-order history, workflows, webhooks, branding, NFC/barcodes,
  custom roles, attachments, time/cost tracking, linking, signatures,
  preventive-maintenance views and triggers, asset hierarchy/downtime, stock
  alerts, vendors/customers, field configuration, voice notes, API access,
  request portals, analytics, and resource planning.
- Commercial entity thresholds for assets, locations, parts, preventive
  maintenance schedules, active work orders, checklists, meters, users, and
  multiple companies are bypassed by the unrestricted capability state. No
  larger replacement quota was introduced.
- Additional user-count checks in signup, invitations, user enablement, and
  role changes are bypassed only in unrestricted self-hosted mode. Role and
  company-membership checks still run. New self-hosted subscriptions store
  `usersCount=0` as an unlimited/unused compatibility value; it is not enforced
  as a quota.
- More than one enabled workflow can be created. Settings permission is still
  required.
- Subscription-expiry scheduling removes legacy expiry jobs and does not
  schedule new ones in unrestricted self-hosted mode. The expiry job and
  `resetToFreePlan` also independently refuse to downgrade a self-hosted
  installation, disable preventive-maintenance schedules, or set upgrade and
  downgrade flags.
- Paddle checkout and Paddle webhook processing are rejected before external
  calls when self-hosted. Keygen-backed license creation/renewal is therefore
  not part of self-hosted operation.

### React web client

- Plan-feature checks resolve as available when `CLOUD_VERSION=false`.
- Upgrade/downgrade redirects and self-hosted upgrade prompts are removed.
- The company plan card identifies the unrestricted edition and has no billing
  action.
- The Paddle JavaScript SDK was removed from the self-hosted frontend build.
- A configurable Corresponding Source link is shown in the sidebar.

### Expo mobile client

- Legacy plan-feature checks no longer hide implemented mobile behavior.
- The backend entitlement response unlocks NFC/barcode behavior.
- A Corresponding Source link is available in Settings.

### Configuration and deployment

- The self-hosted Compose configuration forces `CLOUD_VERSION=false` and no
  longer passes Keygen, license-file, activation-key, or Paddle credentials.
- Compose builds the backend and frontend images from this checkout and tags
  them locally. Named PostgreSQL and MinIO volumes are unchanged, so rebuilding
  images does not delete application data.

## Controls deliberately retained

- JWT, refresh-token, OAuth/LDAP, and password-policy behavior.
- Spring Security role checks and entity-level create/view/edit/delete
  permissions.
- Company ownership and company/site isolation checks.
- Purchase-order approvals and workflow condition validation.
- Sanitization, DTO validation, URL validation, and file type/size checks.
- Audit logging/history and session/API-key revocation.
- Authenticated, unauthenticated, brute-force, and file-upload rate limits.
- Database, HTTP pool, scheduler, upload-size, and storage protection settings.

## Implemented versus unsupported

Unlocking a gate does not implement unfinished code. The workflow engine still
contains explicit `TODO` branches:

- Work order/request `ADD_CHECKLIST`
- Work order/request/purchase-order `SEND_REMINDER_EMAIL`
- Part `CREATE_PURCHASE_ORDER`
- Task `CREATE_REQUEST` and `CREATE_WORK_ORDER`

Those actions remain unsupported and should not be represented as working.
Other third-party integrations still require their own credentials and service
availability: SMTP/SendGrid, object storage, Google Maps/GCP, Sentry, Firebase,
Clarity, Intercom, and OAuth providers. They are integrations, not Atlas
license checks.

The supplied deployment still depends on PostgreSQL, an S3-compatible object
store (`pgsty/silo` in Compose), and Nginx, plus Java/Maven, Node/npm, and Expo
toolchains when building from source. Operators remain responsible for the
licenses and lifecycle of those independently distributed dependencies.

Cloud-only Paddle and Keygen Java code remains for source/API compatibility
when `CLOUD_VERSION=true`; the unrestricted Compose deployment does not
configure or call it.

Existing records are not deleted or plan-migrated. A user or workflow that was
manually disabled remains disabled. Historical subscription downgrades may
have disabled users, schedules, or workflows before this version; the software
does not automatically re-enable those records because it cannot reliably
distinguish an old commercial downgrade from an administrator's intentional
disablement.

## Build your own deployment images

1. Check out the exact commit to deploy.
2. Copy `.env.example` to `.env`, replace every example secret, and set
   `SOURCE_CODE_URL` to publicly accessible Corresponding Source for that exact
   commit.
3. Build locally from source:

   ```bash
   docker compose build --pull api frontend
   ```

4. Record immutable image digests:

   ```bash
   docker image inspect atlas-cmms-backend:unrestricted-selfhosted \
     --format '{{index .RepoDigests 0}} {{.Id}}'
   docker image inspect atlas-cmms-frontend:unrestricted-selfhosted \
     --format '{{index .RepoDigests 0}} {{.Id}}'
   ```

5. Push those images to an operator-controlled registry if required, update
   the `image:` references to immutable digests, and retain the source URL for
   as long as the images are offered or operated.

The usual `docker compose up -d` starts the deployment after images are built,
but no deployment was performed as part of this implementation.

For a mobile build, set `API_URL` and `SOURCE_CODE_URL`, install exactly from
`mobile/package-lock.json`, and use the Expo local/native build appropriate for
the target platform. Publish the same exact source alongside any conveyed
mobile binary.

## Branding and UI

All product logos and upstream branding have been removed and replaced with **"Powered by Canvas"**:

- Deleted `logo.png`, `logo-white.png`, and `favicon*` from `frontend/public/`
- Replaced `LogoSign` and `Logo` components (`frontend/src/components/LogoSign/index.tsx`, `frontend/src/components/Logo/index.tsx`) and loading screen (`frontend/src/components/AppInit/index.tsx`) with **"Powered by Canvas"** text badge
- Replaced `useBrand` defaults (`frontend/src/hooks/useBrand.ts`) with `name: "Powered by Canvas"`, `shortName: "Canvas"`
- Removed "Powered by Intelloop" and upstream documentation links from the sidebar and header

### Color scheme

| Token | Value | Applied to |
|---|---|---|
| Navy | `#1D174E` | Sidebar background, primary button color |
| Gold | `#D69D10` | Active/selected sidebar item accent |
| Pale gray | `#f2f5f9` | Page background (unchanged from upstream) |

### Disabled navigation sections

Four sections are intentionally locked — they appear grayed out in the sidebar
(non-interactive) and redirect to `/app/work-orders` when accessed by URL:

- **Statistics** — analytics dashboards
- **Purchase orders**
- **Vendors & customers**
- **Files**

These sections remain in the codebase and can be re-enabled by removing the
`disabled: true` flag from their entries in
`frontend/src/layouts/ExtendedSidebarLayout/Sidebar/SidebarMenu/items.ts` and
restoring their route definitions in `frontend/src/router/app.tsx`.

## Canvas Python Port (`atlas-cmms/` / `aj-cafm`)

The entire Java Spring Boot backend (`api/`) has been ported to Python (`atlas-cmms/`) using **FastAPI**, **SQLAlchemy 2.0**, **Alembic**, and **`ajnkit-core`**, and deployed to Canvas under the app name **`aj-cafm`** (`https://aj-cafm--innovation.canvas.ajnai.net`):

- **72 SQLAlchemy ORM entity models + 53 association tables** (`atlas-cmms/src/models/`) and **44 enums** (`atlas-cmms/src/models/enums.py`) with 100% schema parity against the Liquibase/PostgreSQL baseline (`migrations/versions/0001_initial_schema.py`). See `atlas-cmms/DATABASE.md` for the full schema reference.
- **241 REST API endpoints** across 6 modular routers (`atlas-cmms/src/routes/`) matching the frontend's expected paths, hierarchy endpoints (`/children/{parent_id}/paginated`), and hydrated camelCase DTO shapes (`atlas-cmms/src/services/serializer.py`). See `atlas-cmms/API_CONTRACTS.md` for the full contract reference.
- **Authentik SSO auto-provisioning** (`atlas-cmms/src/deps/current_user.py`): reads `ajnkit.identity.caller(request.headers)`, provisions the initial Company, `CompanySettings`, `GeneralPreferences`, `WorkOrderConfiguration`, `WorkOrderRequestConfiguration`, all 24 default `FieldConfiguration` rows, and `ROLE_SUPER_ADMIN` user on first sign-in.
- **Unrestricted Self-Hosted Policy**: `CLOUD_VERSION="false"` in `atlas-cmms/score.yaml`; `SubscriptionPlan.features` always returns all 20 `PlanFeatures` values (`atlas-cmms/src/services/license_service.py`).
- **Bundled React SPA**: Compiled `frontend/build/` assets are served directly by FastAPI (`atlas-cmms/src/spa.py`) with `/runtime-env.js` injected at runtime.

## Verification

- **Canvas Python Test Suite (`atlas-cmms/`)**: 57 pytest tests pass (`.venv/bin/pytest -q`), including:
  - `tests/test_schema_matches_dump.py` (DDL parity across all entity and association tables)
  - `tests/contract/test_openapi_covers_catalog.py` (241-endpoint OpenAPI contract check)
  - `tests/routes/test_all_routes_and_jobs.py` (end-to-end CRUD, search, permissions, workflows, analytics, PDF generation, and background jobs)
  - `tests/test_crud_contracts.py` (frontend-backend DTO hydration, `/children/0/paginated` hierarchy pagination, PM `Schedule`, and Checklist `TaskOption` contracts)
  - `tests/test_smoke.py` (40-endpoint Canvas post-deploy smoke test)
- **Ruff Linter (`atlas-cmms/`)**: `.venv/bin/ruff check .` passes with zero warnings (`E9`, `F`, `B`, `S`, `ASYNC`).
- **React Frontend (`frontend/`)**: `npm run lint` and `npm run build` pass cleanly.


