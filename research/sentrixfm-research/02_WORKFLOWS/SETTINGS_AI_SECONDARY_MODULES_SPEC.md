# Settings, AI and secondary modules: observed specification

## Scope and evidence standard

This document analyzes **S075–S090**, captured on 2026-10-17 around 22:32–22:34 UTC, corresponding to **2026-10-18 around 01:32–01:34 in Qatar**. It uses the supplied [manifest](../00_INDEX/EVIDENCE_MANIFEST.json), accessibility snapshots and visually reviewed screenshots. No browser control or network calls were made to prepare the analysis. No settings were changed, flags toggled, permissions requested, scans initiated, messages sent, files uploaded/downloaded, projects created, invoices sent or email composed.

Observed controls and labels establish interface surfaces, not successful integrations or backend behavior. Capability descriptions in settings are **product claims** until independently exercised. “Apparently sample/template content” is an inference from visible dates, generic content and dashboard-product names; it is not a source-code finding. Account identifiers in local screenshots are intentionally omitted from prose. Atlas proposals below are independent recommendations, not verified Sentrix implementation details.

## Six-section settings architecture

ACCOUNT SETTINGS uses a left subsection navigator and a larger configuration panel. The six sections are **General**, **Appearance**, **Feature Flags**, **Notifications**, **Security** and **Public Maintenance Requests**. Section descriptions explain their intent. A shared help area claims settings synchronize across devices and save automatically, although several panels expose explicit Save/Reset actions. Persistence timing was not tested. [S075 snapshot](../07_EVIDENCE/S075.txt)

General shows required Default Language and Timezone, initially **English** and **UTC**. The accessibility tree includes English/Arabic language choices and timezone choices spanning US zones, London, Paris, Dubai and Tokyo. Company Size offers Small 1–10, Medium 11–50, Large 51–200 and Enterprise 200+; Medium is selected. Save Changes and Reset are visible. Company size is described as influencing recommendations/analytics, but no resulting product behavior is demonstrated. [S075](../06_SCREENSHOTS/S075.jpg)

Public Maintenance Requests shows an unchecked enable control, Save and Reset, with extensive untranslated localization keys. It was not enabled to reveal additional configuration. Public intake URLs, anonymous submission, spam controls and routing therefore remain unknown. [S077](../06_SCREENSHOTS/S077.jpg)

Security displays **2FA off**, **Password Policy off**, **Audit Logging on**, and **Login Notifications on**. Save Security Settings and Reset to Defaults are present. These are captured UI states only: no enrollment flow, password rejection, audit record or login notification was tested. The presence of an enabled audit switch must not be described as verified audit coverage or tamper resistance. [S078](../06_SCREENSHOTS/S078.jpg)

Appearance explicitly warns that changes apply and save immediately. The operator consequently made no selection. It offers company-logo upload with advertised 500×500 recommendation, maximum 2MB, JPG/PNG; light/dark themes; vertical/horizontal navigation; fluid/boxed/scrollable width modes; sidebar variants; topbar colors; Reset and Confirm Settings. Several options are only documented in the snapshot below the screenshot viewport. None was tested for rendering, persistence or user-versus-company scope. [S080 screenshot](../06_SCREENSHOTS/S080.jpg), [S080 snapshot](../07_EVIDENCE/S080.txt)

**Atlas lesson:** configuration should state its scope and save behavior per panel. Separate personal layout preferences from organization policy and branding. Show saved/error states explicitly and localize every label before exposing settings to customers. Security options need independently tested enforcement, not reassuring switches alone.

## Fourteen feature flags: claims versus observed availability

Feature Flags Management shows search, category filtering, **14 features available**, and fourteen enabled states across four groups. Reset to Defaults and Save Feature Flags are available but untouched. The [S076 snapshot](../07_EVIDENCE/S076.txt) captures the complete catalog; the [screenshot](../06_SCREENSHOTS/S076.jpg) shows only its upper portion.

| Group | Enabled feature labels |
|---|---|
| Core Management — 5 | User & Role Management; Location Management; Asset Lifecycle Management; Workflow Engineering; Work Order Operations |
| Advanced Operations — 3 | Preventive Maintenance (PPM); Inventory & Consumables; Contextual Team Communication |
| Analytics & Intelligence — 3 | Strategic Reporting; Forensic Analytics Dashboard; Sentrix AI Assistant |
| Enterprise IT Elite — 3 | Enterprise API & Webhooks; Native Mobile Experience; Omni-channel Notifications |

The descriptions advertise sophisticated behavior: process modeling, lifecycle management, scheduling conflict checks, PDF/Excel reporting, realtime analytics, AI retrieval/automation, API/webhooks and native mobile applications. These descriptions were not acceptance-tested in this scope. All flags reading Enabled does not establish working deployment, account entitlement, integration credentials or service health.

The clearest direct contradiction is Notifications. Its dedicated panel marks **email and SMS Coming Soon**, while the enabled omnichannel flag advertises those channels. Push is shown blocked in this browser and its enable action disabled; no browser permission was requested. In-app/push icons imply channel availability but delivery was not tested. Extensive untranslated strings make the exact wording harder to interpret. [S079 screenshot](../06_SCREENSHOTS/S079.jpg), [S079 snapshot](../07_EVIDENCE/S079.txt)

**Atlas lesson:** distinguish entitled, configured, operational, unavailable and planned. A catalog may show a module is included while a separate service is offline, but that distinction must be explicit. Do not make a future channel look usable through an enabled feature switch. Provide actionable dependency checks rather than a universal green state.

## AI assistant: shell present, service offline

Company AI Assistant shows Main Office context, **Synced**, a tooltip claiming its index is up to date, and **Full Scan** for reindexing. The conversation header simultaneously says **AI service currently offline**. A greeting and timestamp are displayed, with clear-chat and composer controls; the empty send action is disabled. Full Scan, clear and send were not used. No generated answer, retrieval citation, task action or permission-aware knowledge result was observed. [S081](../06_SCREENSHOTS/S081.jpg), [S081 snapshot](../07_EVIDENCE/S081.txt)

The floating assistant opens over the same page with a green status dot, Synced badge, greeting, composer, clear/close controls and **Open Full Assistant**. The underlying full-page offline message remains visible. Index freshness and inference-service availability could be separate states, but the UI does not explain that distinction. A greeting is not proof of an AI response. [S082](../06_SCREENSHOTS/S082.jpg)

**Atlas recommendation:** show separate service availability, index coverage/freshness and conversation state. For an initial copilot, prioritize permission-scoped search with sources and clear limitations. Any later write action should use the same authorized business actions as the normal interface, with explicit review where needed. Test unavailable-model and stale-index paths before adding agentic branding. These behaviors were not demonstrated by this trial.

## File library and location communication

File Manager opens a location-oriented library with search, resource categories, file metadata columns and a view-only manager-mode message. Its resource grouping includes location, work-order, asset, PPM, SOP-template and company-setting content. However, entry automatically produces **Not Found / Cannot GET** for a storage-browse route. A centered OK modal and top-right toast duplicate the failure. [S083](../06_SCREENSHOTS/S083.jpg), [S083 snapshot](../07_EVIDENCE/S083.txt)

An empty-results message is visible underneath, but the failed browse means it cannot reliably establish that no files exist. The view-only label is an interface claim, not tested server-side immutability. The displayed route is error evidence only; it was not separately requested. No preview, download, upload or permission check occurred.

Location Chat offers a Communication Hub for Main Office, labels **Live Stream Active**, **Online Presence** and **Connected Hub**, a location-team area, transmission log, Compact control, Clear Hub Data, composer, Add Intelligence, Upload Evidence and an initially disabled Send. No message/file was sent or data cleared. The live labels do not prove transport connectivity, recipient scope, delivery, retention or presence accuracy. [S084 screenshot](../06_SCREENSHOTS/S084.jpg), [S084 snapshot](../07_EVIDENCE/S084.txt)

**Atlas lesson:** distinguish loading failure from empty data. Communications should show sent/delivered/failed status, intended audience and auditable attachment references. A facility chat can be useful when tied to records and shifts, but a decorative command-center label is less valuable than reliable delivery and search.

## Projects and invoices: apparent template surfaces

Projects List contains search and columns for project, due date, status, team and action, but no rows. Previous/1/Next pagination remains visible. Create Project exposes name, image, description, assignees, attachment drop area, status, visibility and due date. The snapshot lists status choices **Completed / Inprogress / Delay** and visibility **Private / Public / Team**. No values or files were entered, and Create Project was not clicked. These visibility labels do not establish access enforcement. [S085](../06_SCREENSHOTS/S085.jpg), [S086](../06_SCREENSHOTS/S086.jpg)

Project Overview shows a dashboard-UI project, generic prose, frontend/UI/backend team labels, and **September–October 2019** dates. Its attached-file names reference admin/landing/logo ZIP packages, with generic comments. This strongly suggests sample/template content rather than evidence of facility capital works or maintenance-project execution. It does not prove that no real project implementation exists elsewhere. No attachments or comments were opened or changed. [S087 screenshot](../06_SCREENSHOTS/S087.jpg), [S087 snapshot](../07_EVIDENCE/S087.txt)

Invoice List shows a heading and Load more without captured records. Invoice Detail independently shows a sample-looking order, billing/shipping information, masked payment method, **October 16, 2019**, admin-dashboard/landing-template products and shipping totals. Print and Send controls appear in the snapshot, but neither was used. This does not demonstrate supplier invoices, purchase orders, receipt matching, approvals, tax treatment or payment integration. [S088](../06_SCREENSHOTS/S088.jpg), [S089](../06_SCREENSHOTS/S089.jpg)

**Atlas recommendation:** avoid shipping disconnected template pages as enterprise modules. If projects or commercial workflows are priorities, build one credible data-linked journey with consistent list/detail navigation. For facility procurement, use domain-specific commitments, receipts and approvals; a generic ecommerce order printout is insufficient reference evidence.

## Email center and final implementation lessons

Inbox shows Compose, standard mailbox folders, generic labels/chat entries and toolbar actions. Its Inbox badge reads **18** while the empty message area says **Showing 1–15 of 0**. No message was opened, composed or sent; no mailbox connection, synchronization or delivery was verified. These inconsistencies and generic side content suggest a sample shell or incomplete binding, without establishing the underlying cause. [S090](../06_SCREENSHOTS/S090.jpg), [S090 snapshot](../07_EVIDENCE/S090.txt)

For Atlas, the cross-module requirement is truthful product state. Proposed acceptance criteria: feature catalogs match released capabilities; outages are distinguished from configuration problems; counts reconcile with records; failed loads never become authoritative empty states; settings use consistent save semantics; AI availability is separate from index status; and sample content cannot be mistaken for customer records. Test secondary modules through real authorized workflows before presenting them as enterprise coverage.

REA should first map the six settings sections, then annotate each claim with supporting, contradictory or missing execution evidence. Reconstruct the offline AI, notification availability and file-error states faithfully. Treat project/invoice screens as layout references with low domain-evidence value. Unresolved questions include every untested save operation, API/mobile availability, notification delivery, AI retrieval, chat transport, file authorization and commercial persistence. This evidence establishes product surfaces and notable gaps, not an operational platform guarantee.
