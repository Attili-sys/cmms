# Requests, categories and organization access: observed specification

## Scope, handling and confidence

This specification analyzes **S063–S074**, captured on 2026-10-17 at approximately 22:30–22:32 UTC, corresponding to **2026-10-18 at 01:30–01:32 in Qatar**. Sources are the supplied [manifest](../00_INDEX/EVIDENCE_MANIFEST.json), all corresponding accessibility snapshots and visually reviewed screenshots. No browser control or network access was used to prepare this analysis.

The operator opened queues, registries and unsubmitted forms, and expanded permission definitions. **No permission checkbox, ownership/status toggle, create/save action or other business mutation was performed.** Visible assigned states describe the current matrix presentation, not tested authorization. No role impersonation, account creation, request transition, category change or team assignment was attempted.

Some local evidence contains trial-account identifiers. This prose deliberately omits their emails and usernames. References point to local evidence for authorized review; screenshots must be checked before external sharing. “Observed” means visible content or a recorded interface response. Atlas recommendations and acceptance tests are independent proposals, not claims about Sentrix’s server implementation. Atlas source was not inspected.

## Maintenance request queue and filters

The [Maintenance Requests route](https://sentrixfm.com/manager/business/maintenance-requests) sits in WORK MANAGEMENT, separately from hard/soft service work and SOP Management. The page heading is MAINTENANCE REQUESTS, with a management subtitle and **Home / Admin / Maintenance** breadcrumb. The captured queue says **Showing 0 of 0**. Its status segments are **All Requests**, **Submitted**, **Approved**, **Rejected** and **In Progress**, each with zero count. [S063](../06_SCREENSHOTS/S063.jpg)

The empty state invites the user to create a first request or change filters, but there is **no visible Create Request control in this inspected manager view**. This is an affordance mismatch, not proof that request creation is unavailable in every role or portal. No populated row, request detail, requester identity, location field, approval action, assignment path or conversion to work order was demonstrated.

Opening **Advanced Filter** exposes a floating panel headed Advanced Filters with **Cancel** and **Apply**. Both the screenshot and accessibility snapshot contain no visible criteria inputs in this session. The panel may be unconfigured or incomplete; a rendering/data issue is also possible. No criterion was entered or applied, so functional filtering is not established. [S064 screenshot](../06_SCREENSHOTS/S064.jpg), [S064 snapshot](../07_EVIDENCE/S064.txt)

The status names suggest an intended request-review process but do not prove allowed transitions, mandatory reasons, approval authority, notifications or an execution lifecycle. In particular, Approved and In Progress are labels in an empty navigation strip, not evidence that an approval successfully creates work.

**Atlas recommendation:** define request intake, triage, review and work fulfillment explicitly. Provide a role-appropriate next action in the empty state; if the manager cannot create requests, explain where requests originate. Keep requester-visible progress connected to actual work while preserving separate request and work identities. A proposed first version should support receipt, duplicate detection, approval/rejection reasons, conversion/linking to work and an auditable decision timeline. None of these behaviors was verified here.

## Category registry and rich-text drawer

The [category registry](https://sentrixfm.com/manager/business/categories) claims hierarchical organization in its subtitle. Captured rows are **Mechanical Systems**, **Electrical Systems**, **Building Infrastructure** and **Support Services**. Each displays a descriptive summary, Main Office location, Active status and October 17, 2026 creation date. Columns are Name, Location, Status, Created and Actions; the footer confirms four entries. Advanced Filters and Create Category are visible. [S065](../06_SCREENSHOTS/S065.jpg)

Row controls expose Edit, Duplicate, Deactivate and Delete, although Duplicate has an untranslated accessible action key. None was executed. The accessibility tree includes keyboard guidance for sorting and navigation; that guidance does not prove complete keyboard operability. No parent column, tree or nested relationship was observed, despite the hierarchical wording. [S065 snapshot](../07_EVIDENCE/S065.txt)

Create Category opens a wide right drawer over the list, with expand and close controls. Fields are required **Name**, **Description** using a rich-text editor, and **Sort Order** initially **0** with guidance that lower values come first. Description’s toolbar offers paragraph/heading selection, bold, italic, link, lists, indentation, image upload, quotation, table insertion, undo and redo. Some controls start disabled. Footer actions are Cancel and disabled Create. No text, image or formatting was entered. [S066](../06_SCREENSHOTS/S066.jpg)

No parent or location selector appears in the captured drawer. The registry’s Main Office association might derive from global context, but that was not tested. Rich-text persistence, sanitization, embedded-media behavior and export rendering are unknown. The screenshot also shows a dense editor/form boundary around Sort Order; a still image alone cannot determine whether this is an editor-height/layout issue or an intentional arrangement.

**Atlas recommendation:** begin with a clear service taxonomy and explicit scope. If categories can be hierarchical, expose parent selection and path; if they are flat, avoid promising a hierarchy. Separate rich instructions from searchable summaries. Define duplication naming, deactivation effects and historical references so retiring a category does not erase meaning from old requests/work. Keep formatting and upload capabilities proportional to actual category-authoring needs.

## Permission matrix: exact observed assignments

The [Permission Matrix](https://sentrixfm.com/manager/business/roles-permissions-managements/matrix) is labeled **System Defined**. Columns are **Company Owner**, **Facility Manager**, **Technician** and **User**, with displayed totals **12**, **8**, **3** and **1** permissions. Categories are **Core Management (3)**, **CAFM Operations (7)**, **Analytics & Reporting (1)** and **System & Integrations (1)**. [S067](../06_SCREENSHOTS/S067.jpg)

Expand All Categories was used, exposing twelve rows with descriptions, resource/action labels and role checkboxes. The following reconstructs the visible checked states from [S068’s accessibility snapshot](../07_EVIDENCE/S068.txt); it is a UI assignment table, **not a tested authorization result**.

| Permission label / code | Owner | Manager | Technician | User |
|---|:---:|:---:|:---:|:---:|
| Company Settings / COMPANY_MANAGE | ✓ | — | — | — |
| Manage Roles & Permissions / ACCESS_CONTROL_MANAGE | ✓ | — | — | — |
| User Management / USER_MANAGE | ✓ | — | — | — |
| Execute Work Orders / WORK_ORDER_EXECUTE | ✓ | ✓ | ✓ | — |
| Asset Management / ASSET_MANAGE | ✓ | ✓ | — | — |
| Category Management / CATEGORY_MANAGE | ✓ | ✓ | — | — |
| Location Management / LOCATION_MANAGE | ✓ | ✓ | — | — |
| Working Item Management / WORK_ORDER_MANAGE | ✓ | ✓ | — | — |
| Workflow Management / WORKFLOW_MANAGE | ✓ | ✓ | — | — |
| View Assets / ASSET_VIEW | ✓ | ✓ | ✓ | — |
| Analytics & Reports / ANALYTICS_VIEW | ✓ | ✓ | ✓ | ✓ |
| Manage Integrations / SYSTEM_INTEGRATION_MANAGE | ✓ | — | — | — |

This layout distinguishes **execution** from **management** and **asset viewing** from **asset management**. The working-item description groups work orders, PPM and inspections; the execute description advertises task execution and recording operational inputs. These are permission descriptions, not demonstrations of those actions. Similarly, analytics wording includes exports, while integration wording mentions API keys/webhooks; no export or integration-management capability was tested in this scope.

Controls include Expand All, Collapse All, Toggle Compact View, Refresh, role-wide select/deselect and row-wide assign/remove. Checkboxes are exposed as settable, but none was changed. No save model, confirmation, immediate persistence, role inheritance or rollback is established. [S068](../06_SCREENSHOTS/S068.jpg)

## Role registry and role creation

The [Roles registry](https://sentrixfm.com/manager/business/roles-permissions-managements/roles) shows the same four roles, all **System** and **Active**. Columns include role/description, type, status, users, permission chips and actions. Each role displays user count **1**. View is available; Edit/Delete are disabled with explanations that system roles cannot be edited/deleted. No role detail was opened. [S069](../06_SCREENSHOTS/S069.jpg)

This protection differs from the matrix’s visible assignment controls. The evidence cannot resolve whether matrix controls are restricted at execution, whether only role metadata is immutable, or whether the pages have inconsistent policy. Do not claim system roles are fully immutable or editable based solely on these surfaces.

Create Role opens a modal with required **Role Name** and **Role Code**, **Active Role** initially shown enabled, multiline Description, Labels with comma-separated guidance, and a Permissions selector. Cancel and disabled Create Role are present. No values, permissions or status were changed; selector options and role-code uniqueness validation were not inspected. [S070](../06_SCREENSHOTS/S070.jpg), [S070 snapshot](../07_EVIDENCE/S070.txt)

**Atlas recommendation:** publish understandable capability groups and separate metadata edits from permission edits. Give administrators a change summary, affected-user count and recovery path for sensitive changes. Use immutable permission identifiers, but translate descriptions into operational language. Avoid treating one broad “manage” permission as proof that every privileged action has an appropriate independent check.

## User directory and per-location role assignments

The [user directory](https://sentrixfm.com/manager/business/users/list) has User, Email, Role, Locations, Status, Created At and Actions columns, plus Advanced Filters and Create User. Two captured rows show Technician and Company Owner, both Active. One shows Main Office; another shows multiple location chips with **+12** overflow. Names are missing or represented by fallback identifiers, and accessible action labels contain **null null**. Account values are intentionally omitted here. [S071](../06_SCREENSHOTS/S071.jpg)

Directory row count and the role registry’s four separate user counts do not reconcile from this evidence. Different scope/filtering or demo data could explain it; no cause is established. Location chips also do not prove whether assignments include descendants or whether one summarized Role column represents every assignment.

The Create User modal includes optional profile image with advertised JPG/PNG/GIF/WebP, maximum 5MB; required First Name, Last Name, Email, Username, Password and Confirm Password; Status initially enabled; and Account Ownership initially disabled. Its explanatory text claims owners have full administrative data access. Ownership is displayed separately from role assignments; its precedence and backend semantics are unverified. [S072 screenshot](../06_SCREENSHOTS/S072.jpg)

The lower **Location & Role Assignments** section is captured in [S072’s accessibility snapshot](../07_EVIDENCE/S072.txt). It says users can have specific roles at one or more locations and that each location may differ. Controls are Select Location, Select Role, **Select Team (Optional)** and Add. Team is disabled until a location is selected; Add and Create User are initially disabled. Guidance requires at least one location-role assignment. No assignment was added.

The text says team membership can be added after creation while also offering an optional team selector in this form. This is an unresolved wording/workflow inconsistency. The form demonstrates intended location-bound roles and team dependency, not enforcement of assignment uniqueness, restricted role selection, password rules, invitations or account lifecycle policies.

## Teams, locations and managers

The [teams route](https://sentrixfm.com/manager/business/user-groups/list) appears as **Teams** in navigation but **USER GROUPS / Create Group** in content. Columns are Group Name, Location, Manager, Members, Created At and Actions. One maintenance-group row belongs to Main Office, displays a manager and **two members**, and has view/edit/delete affordances. The created-date and action labels contain untranslated keys. Neither group details nor membership changes were inspected. [S073](../06_SCREENSHOTS/S073.jpg)

Create Group opens a modal with required Name, Location and Manager, plus Description. Location starts at Main Office; the snapshot lists Main Office and Demo Branch choices. Manager initially exposes only a selection placeholder, and Create is disabled. The operator notes an initial no-users-in-location condition, but S074’s screenshot/AX do not independently establish an explicit message or the actual eligible-user population. Do not conclude that the location has no users, especially given the existing registry row. No location selection or manager lookup was changed. [S074 screenshot](../06_SCREENSHOTS/S074.jpg), [S074 snapshot](../07_EVIDENCE/S074.txt)

## Independent Atlas access model and acceptance tests

Propose separate entities for identity, organizational membership, scoped role assignment, role capabilities, team membership and team responsibility. Keep account ownership an explicit elevated policy with audited administration rather than an unexplained bypass flag. Decide whether scopes inherit through location descendants; display that decision wherever assignments are edited. Team membership should not silently grant administrative privileges unless an explicit policy says so.

Recommended tests belong in an authorized Atlas development/test environment; **none was run against Sentrix**:

1. Verify each role’s permitted and denied operations through both UI and server requests, including direct record access. Hidden buttons alone are insufficient evidence.
2. Use two organizations and multiple sibling/child locations. Test list, detail, search, counts, attachments, reports and exports against the same effective scope.
3. Test a person who is manager at one site and technician at another; verify context switching cannot combine privileges incorrectly.
4. Verify users cannot grant capabilities or ownership beyond their authority. Cover role modification, bulk assignments, disabled roles and revoked memberships.
5. Check whether task execution is limited to assigned work and whether management rights imply execution. Preserve actor/scope/policy evidence in audit records.
6. Ensure team managers and members are eligible for the team location; explain empty/dependent selectors and reject inconsistent assignments server-side.
7. Reconcile role user counts, directory filters and assignment chips. Explain disabled submit buttons and render missing names safely in accessible labels.
8. Exercise request approval/rejection with reasons, repeated submissions and linked work; keep category retirement and rich-text rendering consistent with historical records.

## REA prompts and unresolved questions

Derive an independent permission vocabulary from the observed manage/execute/view distinctions. Diagram location-role and optional-team assignments without assuming a database schema. Rebuild the empty request queue/filter states faithfully, then design a usable intake-to-work flow as a clearly labeled Atlas proposal. Review matrix and role protection inconsistencies before prescribing permission-edit UX.

Remaining unknowns include server enforcement, ownership precedence, role inheritance, descendant scopes, permission-change persistence, authentication/session revocation, request transitions, category hierarchy and team eligibility. These captures support concrete administrative-interface research. They do not establish secure multi-tenant authorization or a working end-to-end request workflow.
