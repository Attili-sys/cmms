# Screen-state catalog

107 captured states. Dates are exact UTC capture timestamps; local research date is 18 October 2026, Asia/Qatar. These are observed UI states, not claims of working backend features.

## S001 — Work orders — table overview

Module: Work orders · Captured: 2026-10-17T22:17:15.086Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/my-tasks)

Initial trial screen. Header claims 12 total/12 active/0 completed/0 overdue; table pagination says 13 entries. 1280px screenshot has 250px dark sidebar, 70px header, white/light-lavender content, purple primary controls, four KPI groups. Work-order title wraps heavily; unassigned assignees and mostly pending statuses.

[Screenshot](../06_SCREENSHOTS/S001.jpg) · [AX evidence](../07_EVIDENCE/S001.txt)

## S002 — Work-order advanced filters

Module: Work orders · Captured: 2026-10-17T22:17:31.523Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/my-tasks)

Popover groups Source, Status, Priority, Assignee, Service Type, Maintenance Type, Category, and due-date start/end; footer Cancel/Apply. An unexplained badge 1 appears beside filter control before selections.

[Screenshot](../06_SCREENSHOTS/S002.jpg) · [AX evidence](../07_EVIDENCE/S002.txt)

## S003 — Status filter choices

Module: Work orders · Captured: 2026-10-17T22:17:37.472Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/my-tasks)

Visible choices: All Statuses, Pending, In Progress, On Hold, Completed, Cancelled. These are filter values, not proof every transition is permitted.

[Screenshot](../06_SCREENSHOTS/S003.jpg) · [AX evidence](../07_EVIDENCE/S003.txt)

## S004 — Work orders — Kanban

Module: Work orders · Captured: 2026-10-17T22:17:44.314Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/my-tasks)

Five lanes Pending, In Progress, On Hold, Completed, Cancelled; Pending shows 10 cards while page summary says 12 active and table previously showed 13 total entries. Cards show priority, creation date, service and maintenance type, View and an overflow control. Drag containers are exposed, but no cards were moved.

[Screenshot](../06_SCREENSHOTS/S004.jpg) · [AX evidence](../07_EVIDENCE/S004.txt)

## S005 — Work orders — calendar

Module: Work orders · Captured: 2026-10-17T22:17:55.879Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/my-tasks)

Month/week/day controls, month heading, previous/next month/year controls and collapsed +9 more event cluster. October 17 shows creation-time 9:56pm for a workflow task; precise choice of creation versus due-date scheduling is unverified.

[Screenshot](../06_SCREENSHOTS/S005.jpg) · [AX evidence](../07_EVIDENCE/S005.txt)

## S006 — Create work order — basic details

Module: Work orders · Captured: 2026-10-17T22:18:12.235Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/my-tasks)

Six-tab modal: Basic Details; Location & Asset; Spare Parts; SOP & Procedures; Attachments; Execution. Required name, priority, category, maintenance/service types; name 200/description 1000 character counters, labels and due date, user/team assignment, Assign to Me, quality-check and client-approval flags. Create disabled. Tab ARIA labels expose untranslated localization keys and Location & Asset reports 1 error on first open.

[Screenshot](../06_SCREENSHOTS/S006.jpg) · [AX evidence](../07_EVIDENCE/S006.txt)

## S007 — Create work order — location and asset

Module: Work orders · Captured: 2026-10-17T22:18:12.838Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/my-tasks)

Location and asset tab inspected without editing or submitting.

[Screenshot](../06_SCREENSHOTS/S007.jpg) · [AX evidence](../07_EVIDENCE/S007.txt)

## S008 — Create work order — spare parts

Module: Work orders · Captured: 2026-10-17T22:18:17.955Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/my-tasks)

Spare-parts tab, inspected without changes.

[Screenshot](../06_SCREENSHOTS/S008.jpg) · [AX evidence](../07_EVIDENCE/S008.txt)

## S009 — Create work order — SOP and procedures

Module: Work orders · Captured: 2026-10-17T22:18:18.558Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/my-tasks)

SOP/procedure tab inspected without submission.

[Screenshot](../06_SCREENSHOTS/S009.jpg) · [AX evidence](../07_EVIDENCE/S009.txt)

## S010 — Create work order — attachments

Module: Work orders · Captured: 2026-10-17T22:18:23.470Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/my-tasks)

Attachments tab; no files selected or uploaded.

[Screenshot](../06_SCREENSHOTS/S010.jpg) · [AX evidence](../07_EVIDENCE/S010.txt)

## S011 — Create work order — execution rules

Module: Work orders · Captured: 2026-10-17T22:18:24.015Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/my-tasks)

Execution tab; no rule or settings saved.

[Screenshot](../06_SCREENSHOTS/S011.jpg) · [AX evidence](../07_EVIDENCE/S011.txt)

## S012 — Work-order spare-part selector

Module: Work orders · Captured: 2026-10-17T22:18:47.967Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/my-tasks)

Part picker opened inside an unsaved draft; no selection or stock movement performed.

[Screenshot](../06_SCREENSHOTS/S012.jpg) · [AX evidence](../07_EVIDENCE/S012.txt)

## S013 — Standalone work-order detail drawer

Module: Work orders · Captured: 2026-10-17T22:19:01.197Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/my-tasks)

Read-only detail surface exposes title/description, status and priority, Standalone marker, created/updated dates, assignee, CAFM classification (maintenance/service type), category/workflow context and labels. Icon-only header controls lack descriptive accessible names. No execution/status action found in inspected detail text.

[Screenshot](../06_SCREENSHOTS/S013.jpg) · [AX evidence](../07_EVIDENCE/S013.txt)

## S014 — Workflow-linked task — detail action yielded no visible drawer

Module: Work orders · Captured: 2026-10-17T22:19:16.899Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/my-tasks)

Clicked View details on Final Re-energization & Certification Task after closing standalone drawer. Two subsequent observations showed the list only; no detail drawer or visible error. Root cause unverified. Existing row displays Workflow Related, Has Rules and status N/A.

**Capture correction:** Earlier ambiguous drawer-opening result; successful recheck S092 supersedes this negative observation.

[Screenshot](../06_SCREENSHOTS/S014.jpg) · [AX evidence](../07_EVIDENCE/S014.txt)

## S015 — Global location selector

Module: Navigation and reports · Captured: 2026-10-17T22:20:05.312Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/reports/api-powered-reports)

Opened location context selector without switching the active location.

[Screenshot](../06_SCREENSHOTS/S015.jpg) · [AX evidence](../07_EVIDENCE/S015.txt)

## S016 — Business Hub mega-navigation

Module: Navigation and reports · Captured: 2026-10-17T22:20:12.901Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/reports/api-powered-reports)

Opened global Business Hub to inspect discoverability and grouping of modules; no business data changed.

**Capture correction:** Transitional menu image; S107 confirms menu inventory but its placement is clipped.

[Screenshot](../06_SCREENSHOTS/S016.jpg) · [AX evidence](../07_EVIDENCE/S016.txt)

## S017 — Standard report generator — initial state

Module: Navigation and reports · Captured: 2026-10-17T22:20:24.816Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/reports/api-powered-reports)

Location, report-type and date-range selectors precede Generate; empty guidance explains how to start. Labels claim Real-time Data and Multi-tenant Isolation; these claims are not backend-verified.

**Capture correction:** Residual Business Hub overlay in screenshot; use S015/S018 for report controls.

[Screenshot](../06_SCREENSHOTS/S017.jpg) · [AX evidence](../07_EVIDENCE/S017.txt)

## S018 — Standard report type options

Module: Navigation and reports · Captured: 2026-10-17T22:20:57.398Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/reports/api-powered-reports)

Eight report types: Facility Overview, Work Order Summary, Asset Health, Cost Analysis, PPM Compliance Index, Executive Summary, Critical Issues, Forensic KPI.

[Screenshot](../06_SCREENSHOTS/S018.jpg) · [AX evidence](../07_EVIDENCE/S018.txt)

## S019 — Work-order report — generated result

Module: Navigation and reports · Captured: 2026-10-17T22:21:03.365Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/reports/api-powered-reports)

Read-only Generate action for Work Order Summary / All Locations / Last 30 Days. Capture of resulting view; no export triggered. Screenshot reached NotFound error by capture time; not a successful generated report.

**Capture correction:** Generation attempt failed: capture already displays Not Found, not a successful report. See S020.

[Screenshot](../06_SCREENSHOTS/S019.jpg) · [AX evidence](../07_EVIDENCE/S019.txt)

## S020 — Work-order report — request failure

Module: Navigation and reports · Captured: 2026-10-17T22:21:25.161Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/reports/api-powered-reports)

Generating Work Order Summary produced visible Not Found / Cannot POST /api/rapport-management/work-order-summary, repeated twice inside an OK modal. This is an observed failure of the trial path, not a claim about every report or edition.

[Screenshot](../06_SCREENSHOTS/S020.jpg) · [AX evidence](../07_EVIDENCE/S020.txt)

## S021 — Strategic analytics hub — command center

Module: Dashboards · Captured: 2026-10-17T22:21:42.138Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/dashboards/analytics-dashboard)

Dashboard shows Main Office context, Last 30 Days, Live Sync OFF, Refresh Hub, Command Center/Operations/Financials. KPIs active tasks 12, critical alerts 0, total assets 0, active locations 14; empty asset and technician charts coexist with reassuring Optimal/Peak/94.2% Sync labels whose calculations were not verified.

[Screenshot](../06_SCREENSHOTS/S021.jpg) · [AX evidence](../07_EVIDENCE/S021.txt)

## S022 — Analytics hub — operations

Module: Dashboards · Captured: 2026-10-17T22:21:46.833Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/dashboards/analytics-dashboard)

Operations tab inspected without toggling live sync or changing settings.

[Screenshot](../06_SCREENSHOTS/S022.jpg) · [AX evidence](../07_EVIDENCE/S022.txt)

## S023 — Analytics hub — financials

Module: Dashboards · Captured: 2026-10-17T22:21:47.550Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/dashboards/analytics-dashboard)

Financial tab inspected read-only; chart correctness unverified.

[Screenshot](../06_SCREENSHOTS/S023.jpg) · [AX evidence](../07_EVIDENCE/S023.txt)

## S024 — Location dashboard — initial scope

Module: Dashboards · Captured: 2026-10-17T22:22:22.408Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/dashboards/location-dashboard)

Location Control Center exposes Last 30 Days + Load, KPI cards, operational trend/asset health, top asset issues, Active Tasks/Audit Logs. Initial KPI work orders and PPM are 0 while task rows and ten active assets are already visible; load state/metric definitions need attention.

[Screenshot](../06_SCREENSHOTS/S024.jpg) · [AX evidence](../07_EVIDENCE/S024.txt)

## S025 — Location dashboard — after Load

Module: Dashboards · Captured: 2026-10-17T22:22:40.231Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/dashboards/location-dashboard)

Explicit Load was invoked. Loading state used skeletons while retaining existing asset/task rows. Capture records the subsequent settled state when available.

[Screenshot](../06_SCREENSHOTS/S025.jpg) · [AX evidence](../07_EVIDENCE/S025.txt)

## S026 — Location dashboard — audit log

Module: Dashboards · Captured: 2026-10-17T22:22:40.814Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/dashboards/location-dashboard)

Read-only Audit Logs tab.

[Screenshot](../06_SCREENSHOTS/S026.jpg) · [AX evidence](../07_EVIDENCE/S026.txt)

## S027 — Locations — hierarchy view

Module: Locations · Captured: 2026-10-17T22:23:07.458Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/locations/list)

Locations Management shows 14 total/14 active/0 inactive and Main Office context, switchable Table/Hierarchy/Map. Tree actions include view, create sublocation, edit, settings and delete, with untranslated help keys. No location changed.

[Screenshot](../06_SCREENSHOTS/S027.jpg) · [AX evidence](../07_EVIDENCE/S027.txt)

## S028 — Location detail — overview

Module: Locations · Captured: 2026-10-17T22:23:33.706Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/locations/details/location-7eff1521-07fa-4093-97fa-175efdc2539e)

Full-page Main Office record with Back to List, View on Map, Edit, Delete, and Overview/Address/Coordinates/Technical sections. Overview includes name, status, active/main/current flags, level 0 and description. A numeric location level is observed; typed site/building/floor schema is not established.

[Screenshot](../06_SCREENSHOTS/S028.jpg) · [AX evidence](../07_EVIDENCE/S028.txt)

## S029 — Location edit form

Module: Locations · Captured: 2026-10-17T22:23:42.596Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/locations/edit/location-7eff1521-07fa-4093-97fa-175efdc2539e)

Opened existing location form for inspection only; no values edited and no update submitted.

[Screenshot](../06_SCREENSHOTS/S029.jpg) · [AX evidence](../07_EVIDENCE/S029.txt)

## S030 — Asset registry — table

Module: Assets · Captured: 2026-10-17T22:24:02.468Z · differential AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/assets/list)

Ten demo assets with type, commissioned status, QR action, deep-leaf location, WO/PPM metric badges and updated date. Table/Tree modes and advanced filter/New Asset controls. Asset classifications vary (equipment/component/tool); dashboard operational status uses different wording, with semantics unverified.

[Screenshot](../06_SCREENSHOTS/S030.jpg) · [AX evidence](../07_EVIDENCE/S030.txt)

## S031 — Asset detail — status-history error

Module: Assets · Captured: 2026-10-17T22:24:13.801Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/assets/details/asset-b158b47e-ee69-4598-972a-ca6531c7859a)

Opening Boiler System Primary automatically raised Invalid Request / Validation Error: Failed to retrieve asset status history. Underlying asset record is visible, so history failure should be distinguished from registry failure.

[Screenshot](../06_SCREENSHOTS/S031.jpg) · [AX evidence](../07_EVIDENCE/S031.txt)

## S032 — Asset detail — overview and QR actions

Module: Assets · Captured: 2026-10-17T22:24:14.194Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/assets/details/asset-b158b47e-ee69-4598-972a-ca6531c7859a)

Transient screenshot while the asset-history error dialog was fading after dismissal. Use S033 for settled overview.

**Capture correction:** Fading error dialog after dismissal; use S033 for settled asset overview.

[Screenshot](../06_SCREENSHOTS/S032.jpg) · [AX evidence](../07_EVIDENCE/S032.txt)

## S033 — Asset detail overview — settled

Module: Assets · Captured: 2026-10-17T22:26:17.593Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/assets/details/asset-b158b47e-ee69-4598-972a-ca6531c7859a)

Status history retrieval failed on entry; dismissed error. Read-only overview.

[Screenshot](../06_SCREENSHOTS/S033.jpg) · [AX evidence](../07_EVIDENCE/S033.txt)

## S034 — Asset work orders — empty relationship

Module: Assets · Captured: 2026-10-17T22:26:23.392Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/assets/details/asset-b158b47e-ee69-4598-972a-ca6531c7859a)

Empty state with contextual create CTA; no creation attempted.

[Screenshot](../06_SCREENSHOTS/S034.jpg) · [AX evidence](../07_EVIDENCE/S034.txt)

## S035 — Asset PPM schedules — empty

Module: Assets · Captured: 2026-10-17T22:26:26.342Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/assets/details/asset-b158b47e-ee69-4598-972a-ca6531c7859a)

Contextual Schedule PPM CTA; recurrence behavior untested.

[Screenshot](../06_SCREENSHOTS/S035.jpg) · [AX evidence](../07_EVIDENCE/S035.txt)

## S036 — Asset document upload layout

Module: Assets · Captured: 2026-10-17T22:26:29.591Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/assets/details/asset-b158b47e-ee69-4598-972a-ca6531c7859a)

Separate Photos and Documents & Manuals dropzones; no file selection/upload.

[Screenshot](../06_SCREENSHOTS/S036.jpg) · [AX evidence](../07_EVIDENCE/S036.txt)

## S037 — Asset history — retrieval failure

Module: Assets · Captured: 2026-10-17T22:26:37.891Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/assets/details/asset-b158b47e-ee69-4598-972a-ca6531c7859a)

History tab reproduces failure retrieving asset status history.

[Screenshot](../06_SCREENSHOTS/S037.jpg) · [AX evidence](../07_EVIDENCE/S037.txt)

## S038 — Inventory stores — empty registry

Module: Inventory · Captured: 2026-10-17T22:26:48.349Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/store)

Store-level inventory navigation includes requisitions and global consumables.

[Screenshot](../06_SCREENSHOTS/S038.jpg) · [AX evidence](../07_EVIDENCE/S038.txt)

## S039 — Create inventory store modal

Module: Inventory · Captured: 2026-10-17T22:26:53.325Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/store)

Required name and location, optional description; premature required errors before input; no save.

[Screenshot](../06_SCREENSHOTS/S039.jpg) · [AX evidence](../07_EVIDENCE/S039.txt)

## S040 — Consumable requisitions — empty queue

Module: Inventory · Captured: 2026-10-17T22:26:59.015Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/store/requisitions)

Date/item/quantity/work-order/status/actions columns; no processing verified.

[Screenshot](../06_SCREENSHOTS/S040.jpg) · [AX evidence](../07_EVIDENCE/S040.txt)

## S041 — Consumables registry

Module: Inventory · Captured: 2026-10-17T22:27:07.892Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/store/consumables)

All Items, Reorder Needed, Spare Part, Material, Tool segments; stock/unit price/expiry columns.

[Screenshot](../06_SCREENSHOTS/S041.jpg) · [AX evidence](../07_EVIDENCE/S041.txt)

## S042 — Create consumable fields

Module: Inventory · Captured: 2026-10-17T22:27:12.116Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/store/consumables)

Name/type/store required; SKU,UOM,min/max stock, unit price,currency,purchase price,expiry,description. No creation.

[Screenshot](../06_SCREENSHOTS/S042.jpg) · [AX evidence](../07_EVIDENCE/S042.txt)

## S043 — Hard-service PPM schedule list

Module: PPM · Captured: 2026-10-17T22:27:20.810Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/ppm-scheduled?serviceType=hard)

Summary12 vs visible8; untranslated labels; frequency,next scheduled,interval,workflow rules; no force sync.

[Screenshot](../06_SCREENSHOTS/S043.jpg) · [AX evidence](../07_EVIDENCE/S043.txt)

## S044 — Create PPM — basic details

Module: PPM · Captured: 2026-10-17T22:27:24.641Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/ppm-scheduled?serviceType=hard)

Eight tabs; shared classification/assignment model. Create appears enabled on empty form; not clicked. Create settled to disabled in later DOM; initial enabled AX is a render timing artifact, not validation proof.

**Capture correction:** Initial AX Create-enabled state settled to disabled; not a proven validation bypass.

[Screenshot](../06_SCREENSHOTS/S044.jpg) · [AX evidence](../07_EVIDENCE/S044.txt)

## S045 — PPM recurrence — calendar selection and timezone

Module: PPM · Captured: 2026-10-17T22:27:36.822Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/ppm-scheduled?serviceType=hard)

Month/week/day selectors,required start/end,09:00 default,Asia/Qatar timezone; no scheduler reliability proven.

[Screenshot](../06_SCREENSHOTS/S045.jpg) · [AX evidence](../07_EVIDENCE/S045.txt)

## S046 — PPM lifecycle explanation

Module: PPM · Captured: 2026-10-17T22:27:41.059Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/ppm-scheduled?serviceType=hard)

UI describes scheduled record generating live work order then closure feedback; explanation not runtime proof.

[Screenshot](../06_SCREENSHOTS/S046.jpg) · [AX evidence](../07_EVIDENCE/S046.txt)

## S047 — PPM incoming tasks — sparse panel

Module: PPM · Captured: 2026-10-17T22:27:45.425Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/ppm-scheduled?serviceType=hard)

Panel exposes untranslated heading/description with error badge but no visible dependency controls.

[Screenshot](../06_SCREENSHOTS/S047.jpg) · [AX evidence](../07_EVIDENCE/S047.txt)

## S048 — Hard-service inspections

Module: Inspections and SOP · Captured: 2026-10-17T22:28:01.725Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/inspections?serviceType=hard)

Four rows but summary12, no visible create CTA, table/Kanban.

[Screenshot](../06_SCREENSHOTS/S048.jpg) · [AX evidence](../07_EVIDENCE/S048.txt)

## S049 — Inspection detail panel

Module: Inspections and SOP · Captured: 2026-10-17T22:28:06.120Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/inspections?serviceType=hard)

Sparse title,description,status,priority,classification,id,category,created; no checklist execution visible.

[Screenshot](../06_SCREENSHOTS/S049.jpg) · [AX evidence](../07_EVIDENCE/S049.txt)

## S050 — SOP library — templates and instances

Module: Inspections and SOP · Captured: 2026-10-17T22:28:14.827Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/sop-management/library)

Empty library with All/Templates/Instances segmentation and Create SOP.

[Screenshot](../06_SCREENSHOTS/S050.jpg) · [AX evidence](../07_EVIDENCE/S050.txt)

## S051 — SOP builder — section structure

Module: Inspections and SOP · Captured: 2026-10-17T22:28:31.408Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/sop-management/builder)

Name/category/version/description; nested sections, fields list,preview; no save.

[Screenshot](../06_SCREENSHOTS/S051.jpg) · [AX evidence](../07_EVIDENCE/S051.txt)

## S052 — SOP field type selector

Module: Inspections and SOP · Captured: 2026-10-17T22:28:34.858Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/sop-management/builder)

Nine types: text,textarea,number,date,checkbox,dropdown,signature,file,photo; categories/search.

[Screenshot](../06_SCREENSHOTS/S052.jpg) · [AX evidence](../07_EVIDENCE/S052.txt)

## S053 — SOP text field inspector

Module: Inspections and SOP · Captured: 2026-10-17T22:28:51.460Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/sop-management/builder)

Draft-only field added; label/order/placeholder/help/lengths/validation; no SOP saved.

[Screenshot](../06_SCREENSHOTS/S053.jpg) · [AX evidence](../07_EVIDENCE/S053.txt)

## S054 — SOP validation rule types

Module: Inspections and SOP · Captured: 2026-10-17T22:28:58.727Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/sop-management/builder)

Required/custom/min/max length/regex/email/URL/alphanumeric/no special chars; draft-only rule, no Update/Save.

[Screenshot](../06_SCREENSHOTS/S054.jpg) · [AX evidence](../07_EVIDENCE/S054.txt)

## S055 — Workflow registry

Module: Workflows · Captured: 2026-10-17T22:29:16.457Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/workflows)

Workflow name,automation,packages,creator; BPMN editor link; unlabeled row action buttons.

[Screenshot](../06_SCREENSHOTS/S055.jpg) · [AX evidence](../07_EVIDENCE/S055.txt)

## S056 — Workflow grid — package composition

Module: Workflows · Captured: 2026-10-17T22:29:20.268Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/workflows)

Three workflows, nested maintenance packages,parallel badges,working items,0%progress,Run Now unexecuted.

[Screenshot](../06_SCREENSHOTS/S056.jpg) · [AX evidence](../07_EVIDENCE/S056.txt)

## S057 — BPMN workflow canvas

Module: Workflows · Captured: 2026-10-17T22:29:38.420Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/workflows/workflow-8f63670f-ee04-4e9f-b7b2-7fb0dbec6f21/editor)

Pool/workflow,package lane,task card SAFE/PRED/7 badges,incomplete assignment warning; bpmn.io credit.

[Screenshot](../06_SCREENSHOTS/S057.jpg) · [AX evidence](../07_EVIDENCE/S057.txt)

## S058 — BPMN task configuration reuses PPM form

Module: Workflows · Captured: 2026-10-17T22:29:46.787Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/workflows/workflow-8f63670f-ee04-4e9f-b7b2-7fb0dbec6f21/editor)

Selected existing task opens create-titled PPM form,category disabled,workflow-mode explanation; no save.

[Screenshot](../06_SCREENSHOTS/S058.jpg) · [AX evidence](../07_EVIDENCE/S058.txt)

## S059 — BPMN task incoming tasks — gated empty

Module: Workflows · Captured: 2026-10-17T22:29:51.370Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/workflows/workflow-8f63670f-ee04-4e9f-b7b2-7fb0dbec6f21/editor)

No tasks and complete-scheduling messages,untranslated; no execution behavior tested.

[Screenshot](../06_SCREENSHOTS/S059.jpg) · [AX evidence](../07_EVIDENCE/S059.txt)

## S060 — Multi-phase workflow BPMN lanes

Module: Workflows · Captured: 2026-10-17T22:30:03.191Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/workflows/workflow-7c3f79b7-2166-49e5-b684-1ffb5ad3bec6/editor)

Four package lanes,task badges and missing assignment warnings; no connecting edges visible in initial viewport.

[Screenshot](../06_SCREENSHOTS/S060.jpg) · [AX evidence](../07_EVIDENCE/S060.txt)

## S061 — BPMN export menu

Module: Workflows · Captured: 2026-10-17T22:30:08.640Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/workflows/workflow-7c3f79b7-2166-49e5-b684-1ffb5ad3bec6/editor)

BPMN2.0 and SVG options; export not executed.

[Screenshot](../06_SCREENSHOTS/S061.jpg) · [AX evidence](../07_EVIDENCE/S061.txt)

## S062 — Maintenance Packages route — sparse shell

Module: Workflows · Captured: 2026-10-17T22:30:25.422Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/maintenance-packages)

Observed route rendered header/settings shell without package content after navigation; no error text. Bounded session observation.

[Screenshot](../06_SCREENSHOTS/S062.jpg) · [AX evidence](../07_EVIDENCE/S062.txt)

## S063 — Maintenance request queue

Module: Requests and categories · Captured: 2026-10-17T22:30:39.887Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/maintenance-requests)

Empty queue with submitted/approved/rejected/in progress status segments; no create CTA in observed manager view.

[Screenshot](../06_SCREENSHOTS/S063.jpg) · [AX evidence](../07_EVIDENCE/S063.txt)

## S064 — Request filters — empty panel

Module: Requests and categories · Captured: 2026-10-17T22:30:45.485Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/maintenance-requests)

Advanced Filter expands heading/cancel/apply with no visible criteria in this session.

[Screenshot](../06_SCREENSHOTS/S064.jpg) · [AX evidence](../07_EVIDENCE/S064.txt)

## S065 — Service category registry

Module: Requests and categories · Captured: 2026-10-17T22:30:53.970Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/categories)

Four location-bound active categories,description/status/date; page calls hierarchy but not yet observed parent controls.

[Screenshot](../06_SCREENSHOTS/S065.jpg) · [AX evidence](../07_EVIDENCE/S065.txt)

## S066 — Create category drawer

Module: Requests and categories · Captured: 2026-10-17T22:30:58.032Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/categories)

Name,rich text description,sort order; no parent or location control visible; no save.

[Screenshot](../06_SCREENSHOTS/S066.jpg) · [AX evidence](../07_EVIDENCE/S066.txt)

## S067 — Permission matrix — role overview

Module: Organization and access · Captured: 2026-10-17T22:31:09.348Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/roles-permissions-managements/matrix)

System Defined matrix,CompanyOwner12,FacilityManager8,Technician3,User1; fourpermission groups.

[Screenshot](../06_SCREENSHOTS/S067.jpg) · [AX evidence](../07_EVIDENCE/S067.txt)

## S068 — Permission matrix — expanded definitions

Module: Organization and access · Captured: 2026-10-17T22:31:22.397Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/roles-permissions-managements/matrix)

12permission rows across4roles; execute vsmanage distinction; no checkbox/action changed.

[Screenshot](../06_SCREENSHOTS/S068.jpg) · [AX evidence](../07_EVIDENCE/S068.txt)

## S069 — Role registry

Module: Organization and access · Captured: 2026-10-17T22:31:31.561Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/roles-permissions-managements/roles)

System roles,active,usercounts,permissionchips; no edits.

[Screenshot](../06_SCREENSHOTS/S069.jpg) · [AX evidence](../07_EVIDENCE/S069.txt)

## S070 — Create role form

Module: Organization and access · Captured: 2026-10-17T22:31:37.979Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/roles-permissions-managements/roles)

Name/code/active/description/labels/permission multiselect; no role or permission changes.

[Screenshot](../06_SCREENSHOTS/S070.jpg) · [AX evidence](../07_EVIDENCE/S070.txt)

## S071 — User directory and location assignments

Module: Organization and access · Captured: 2026-10-17T22:31:48.290Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/users/list)

Role/location chips,status,created,date; blank display names and null null action labels. Contains trial-account identifiers; keep local.

[Screenshot](../06_SCREENSHOTS/S071.jpg) · [AX evidence](../07_EVIDENCE/S071.txt)

## S072 — User onboarding — per-location roles

Module: Organization and access · Captured: 2026-10-17T22:31:52.245Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/users/list)

Personal fields/password/active/ownership; mandatory at least one location-role assignment,optional team. No data entered or user created.

[Screenshot](../06_SCREENSHOTS/S072.jpg) · [AX evidence](../07_EVIDENCE/S072.txt)

## S073 — Team registry

Module: Organization and access · Captured: 2026-10-17T22:32:03.284Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/user-groups/list)

Location,manager,member count,date; UI alternates Teams/UserGroups.

[Screenshot](../06_SCREENSHOTS/S073.jpg) · [AX evidence](../07_EVIDENCE/S073.txt)

## S074 — Team creation form

Module: Organization and access · Captured: 2026-10-17T22:32:08.683Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/user-groups/list)

Required name/location/manager,description; no users in location message initially; no creation.

[Screenshot](../06_SCREENSHOTS/S074.jpg) · [AX evidence](../07_EVIDENCE/S074.txt)

## S075 — Account settings — general

Module: Settings · Captured: 2026-10-17T22:32:20.392Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/settings/company)

Six configuration sections;language/timezone/companysize; says auto-synced yet SaveChanges exists. No input touched.

[Screenshot](../06_SCREENSHOTS/S075.jpg) · [AX evidence](../07_EVIDENCE/S075.txt)

## S076 — Feature flags catalog — product claims

Module: Settings · Captured: 2026-10-17T22:32:27.418Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/settings/features)

14 flags all enabled; includes API/webhooks,native mobile,RAG AI,notifications. Claims only,not runtime verification. No toggles.

[Screenshot](../06_SCREENSHOTS/S076.jpg) · [AX evidence](../07_EVIDENCE/S076.txt)

## S077 — Public request settings — disabled

Module: Settings · Captured: 2026-10-17T22:32:32.664Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/settings/public-requests)

Disabled public intake,untranslated labels; did not enable to expose further fields.

[Screenshot](../06_SCREENSHOTS/S077.jpg) · [AX evidence](../07_EVIDENCE/S077.txt)

## S078 — Security settings affordances

Module: Settings · Captured: 2026-10-17T22:32:36.581Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/settings/security)

MFA,passwordpolicy,auditlogging,loginnotifications; current UI state only,not implementation test. No changes.

[Screenshot](../06_SCREENSHOTS/S078.jpg) · [AX evidence](../07_EVIDENCE/S078.txt)

## S079 — Notification channels — coming-soon contradiction

Module: Settings · Captured: 2026-10-17T22:32:40.520Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/settings/notifications)

Push blocked in browser;email and SMS explicitly Coming Soon despite flag catalog claiming omnichannel. No permissions requested.

[Screenshot](../06_SCREENSHOTS/S079.jpg) · [AX evidence](../07_EVIDENCE/S079.txt)

## S080 — Appearance customization — unswitched

Module: Settings · Captured: 2026-10-17T22:32:45.188Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/settings/appearance)

Branding,theme,navorientation,width,sidebar/topbar; explicit instant autosave so no choices changed.

[Screenshot](../06_SCREENSHOTS/S080.jpg) · [AX evidence](../07_EVIDENCE/S080.txt)

## S081 — Company AI assistant — offline

Module: AI and communication · Captured: 2026-10-17T22:32:54.380Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/utilities/company-ai-chat)

Location context,Synced,FullScan button,serviceoffline,greeting; no scans/messages sent.

[Screenshot](../06_SCREENSHOTS/S081.jpg) · [AX evidence](../07_EVIDENCE/S081.txt)

## S082 — Floating AI chat panel

Module: AI and communication · Captured: 2026-10-17T22:33:01.002Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/utilities/company-ai-chat)

Greeting,composer,disabled empty send,clear,fullassistant link; no send or clear.

[Screenshot](../06_SCREENSHOTS/S082.jpg) · [AX evidence](../07_EVIDENCE/S082.txt)

## S083 — Location file library — endpoint failure

Module: AI and communication · Captured: 2026-10-17T22:33:08.761Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/utilities/file-manager)

View-only manager library,resource categories;storage browse GET NotFound,empty result unreliable.

[Screenshot](../06_SCREENSHOTS/S083.jpg) · [AX evidence](../07_EVIDENCE/S083.txt)

## S084 — Location chat workspace

Module: AI and communication · Captured: 2026-10-17T22:33:16.992Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/chat)

Locationteam,presence,transmissionlog,composer; no messages/files sent;live labels not delivery proof.

[Screenshot](../06_SCREENSHOTS/S084.jpg) · [AX evidence](../07_EVIDENCE/S084.txt)

## S085 — Project list — empty

Module: Projects invoices and email · Captured: 2026-10-17T22:33:23.754Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/projects/list)

Columnsproject,due,status,team,action; paginationvisible no rows.

[Screenshot](../06_SCREENSHOTS/S085.jpg) · [AX evidence](../07_EVIDENCE/S085.txt)

## S086 — Project creation form

Module: Projects invoices and email · Captured: 2026-10-17T22:33:30.829Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/projects/create)

Name,image,description,assignees,attachments,status,visibility,due date; no values entered/published.

[Screenshot](../06_SCREENSHOTS/S086.jpg) · [AX evidence](../07_EVIDENCE/S086.txt)

## S087 — Project overview — apparent template content

Module: Projects invoices and email · Captured: 2026-10-17T22:33:38.420Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/projects/overview)

Generic dashboardUI project,2019 dates,lorem-like descriptions,admin ZIPs; not credible facility project execution evidence.

[Screenshot](../06_SCREENSHOTS/S087.jpg) · [AX evidence](../07_EVIDENCE/S087.txt)

## S088 — Invoice list — empty

Module: Projects invoices and email · Captured: 2026-10-17T22:33:46.222Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/invoices/list)

List heading and LoadMore; no visible invoice records.

[Screenshot](../06_SCREENSHOTS/S088.jpg) · [AX evidence](../07_EVIDENCE/S088.txt)

## S089 — Invoice detail — apparent static template

Module: Projects invoices and email · Captured: 2026-10-17T22:33:55.812Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/invoices/detail)

2019 sample order/admin-dashboard products,shipping,Send; not supplierinvoice/POmatching evidence. No Send.

[Screenshot](../06_SCREENSHOTS/S089.jpg) · [AX evidence](../07_EVIDENCE/S089.txt)

## S090 — Email center — apparent sample shell

Module: Projects invoices and email · Captured: 2026-10-17T22:34:11.068Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/email/inbox)

Inbox18badge but showing1–15of0,emptylist,samplechat/labels; no messages opened/composed.

[Screenshot](../06_SCREENSHOTS/S090.jpg) · [AX evidence](../07_EVIDENCE/S090.txt)

## S091 — New asset — metadata and acquisition fields

Module: Assets · Captured: 2026-10-17T22:34:35.885Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/assets/list)

Three tabs,image,category/tags/parentasset text fields,name/type/status,serial/manufacturer/model,purchaseprice/date/warranty,richtext; no create.

[Screenshot](../06_SCREENSHOTS/S091.jpg) · [AX evidence](../07_EVIDENCE/S091.txt)

## S092 — Workflow-linked work order drawer — successful recheck

Module: Full work-order records · Captured: 2026-10-18T08:35:52.062Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/my-tasks)

Recheck corrects S014 ambiguous failed opening. UnknownStatus,WorkflowRelated+HasRules but contextStandalone; package name.

[Screenshot](../06_SCREENSHOTS/S092.jpg) · [AX evidence](../07_EVIDENCE/S092.txt)

## S093 — Full work-order overview

Module: Full work-order records · Captured: 2026-10-18T08:36:05.804Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/work-orders/working-item-61b197a8-262c-4beb-87c2-16e0944f857c)

Separate full record page,5tabs,statusmanagement,assets3,SOP0%,workflow context correctly named unlike drawer.

[Screenshot](../06_SCREENSHOTS/S093.jpg) · [AX evidence](../07_EVIDENCE/S093.txt)

## S094 — Work-order cost/time — empty data

Module: Full work-order records · Captured: 2026-10-18T08:36:10.702Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/work-orders/working-item-61b197a8-262c-4beb-87c2-16e0944f857c)

Costtotal0,estimated/actual0h,Editaffordances; no dataentry verified.

[Screenshot](../06_SCREENSHOTS/S094.jpg) · [AX evidence](../07_EVIDENCE/S094.txt)

## S095 — Work-order assets — three related cards

Module: Full work-order records · Captured: 2026-10-18T08:36:17.525Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/work-orders/working-item-61b197a8-262c-4beb-87c2-16e0944f857c)

Threeactualassetcards,status/location/QR,TrackAsset navigation; multi-asset relationship observed.

[Screenshot](../06_SCREENSHOTS/S095.jpg) · [AX evidence](../07_EVIDENCE/S095.txt)

## S096 — Work-order SOP — empty attachment state

Module: Full work-order records · Captured: 2026-10-18T08:36:23.729Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/work-orders/working-item-61b197a8-262c-4beb-87c2-16e0944f857c)

NoSOPattached and AttachSOP; no attachment persisted.

[Screenshot](../06_SCREENSHOTS/S096.jpg) · [AX evidence](../07_EVIDENCE/S096.txt)

## S097 — Work-order history — empty

Module: Full work-order records · Captured: 2026-10-18T08:36:32.835Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/work-orders/working-item-61b197a8-262c-4beb-87c2-16e0944f857c)

Historytab loads to nohistory,not proofauditnotimplemented.

[Screenshot](../06_SCREENSHOTS/S097.jpg) · [AX evidence](../07_EVIDENCE/S097.txt)

## S098 — Status action on workflow-linked record — no visible dialog

Module: Full work-order records · Captured: 2026-10-18T08:36:47.428Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/work-orders/working-item-61b197a8-262c-4beb-87c2-16e0944f857c)

Clicked ChangeStatus,settled DOM unchanged,no status changed. Bounded unknown-status record observation.

[Screenshot](../06_SCREENSHOTS/S098.jpg) · [AX evidence](../07_EVIDENCE/S098.txt)

## S099 — 390px responsive record — capture after reflow

Module: Responsive web · Captured: 2026-10-18T08:37:10.765Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/work-orders/working-item-61b197a8-262c-4beb-87c2-16e0944f857c)

An immediate inline observation after resize was clipped, but this later saved screenshot had already reflowed. S101 is the deliberate settled recheck; topbar clipping and icon-only tabs remain.

**Capture correction:** The earlier immediate inline observation was transitional; this saved screenshot already reflowed. S101 is the deliberate settled recheck.

[Screenshot](../06_SCREENSHOTS/S099.jpg) · [AX evidence](../07_EVIDENCE/S099.txt)

## S100 — 390px task list — settled responsive layout

Module: Responsive web · Captured: 2026-10-18T08:37:25.309Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/my-tasks)

Content reflows fullwidth,verticalstatstack/tallfilters push tablebelowfold;topbarstillclipped.

[Screenshot](../06_SCREENSHOTS/S100.jpg) · [AX evidence](../07_EVIDENCE/S100.txt)

## S101 — 390px record — settled responsive layout

Module: Responsive web · Captured: 2026-10-18T08:37:40.910Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/work-orders/working-item-61b197a8-262c-4beb-87c2-16e0944f857c)

Corrects S099 transient clipping;contentnowfullwidth;icons-onlytabs noARIA/title,topbarclipped,untranslatedstatuslabeloverflows.

[Screenshot](../06_SCREENSHOTS/S101.jpg) · [AX evidence](../07_EVIDENCE/S101.txt)

## S102 — Workflow creation — four-section wizard

Module: Workflow setup · Captured: 2026-10-18T08:37:57.197Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/workflows/create)

Identity,packages,executionlogic,automation;name/category/ownerrequired,description/image;65%completionbeforeinput is weak feedback.

[Screenshot](../06_SCREENSHOTS/S102.jpg) · [AX evidence](../07_EVIDENCE/S102.txt)

## S103 — Workflow execution logic — strategies and triggers

Module: Workflow setup · Captured: 2026-10-18T08:38:13.610Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/workflows/create)

ParallelIndependent/SequentialDependency,manual/date/cron,activestatus; choicesnotchangednor executionverified.

[Screenshot](../06_SCREENSHOTS/S103.jpg) · [AX evidence](../07_EVIDENCE/S103.txt)

## S104 — Workflow package actions — no visible detail expansion

Module: Workflow setup · Captured: 2026-10-18T08:39:27.021Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/workflows)

ViewDetails and packageEdit yielded no new dialog/page in settledDOM; boundedactionfeedbackfailure,not proofpackageabsent.

[Screenshot](../06_SCREENSHOTS/S104.jpg) · [AX evidence](../07_EVIDENCE/S104.txt)

## S105 — Asset creation — location tree

Module: Asset setup · Captured: 2026-10-18T08:39:51.291Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/assets/list)

MainOfficeBranch/Site selectedbydefault;guidance selectsub-locationyetassetwillbesavedhere; no create.

[Screenshot](../06_SCREENSHOTS/S105.jpg) · [AX evidence](../07_EVIDENCE/S105.txt)

## S106 — Asset creation lifecycle — unsaved metrics

Module: Asset setup · Captured: 2026-10-18T08:39:57.786Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/assets/list)

Planned,0days,0transitions,newtimestamps,changestatusdisabled; thesearepre-saveformvalues.

[Screenshot](../06_SCREENSHOTS/S106.jpg) · [AX evidence](../07_EVIDENCE/S106.txt)

## S107 — Business Hub — menu inventory with clipped placement

Module: Navigation · Captured: 2026-10-18T08:45:00.218Z · full AX snapshot

Source: [SentrixFm - Business Process Management](https://sentrixfm.com/manager/business/operations/my-tasks)

AX confirms three business groups and quick actions. Saved screenshot places the menu at lower right and clips it beyond the viewport; not a clean full-menu layout reference.

**Capture correction:** Menu inventory is confirmed in AX; the screenshot shows clipped lower-right placement, so it is not a clean full-menu layout reference.

[Screenshot](../06_SCREENSHOTS/S107.jpg) · [AX evidence](../07_EVIDENCE/S107.txt)
