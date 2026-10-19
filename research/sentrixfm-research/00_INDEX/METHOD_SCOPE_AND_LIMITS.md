# Method, scope and limits

## Identity and dates

- Target supplied by user: `https://sentrixfm.com/manager/business/operations/my-tasks`.
- Authenticated Chrome trial account, manager interface, visible branding demo, footer SentrixFm v1.2.
- Local research date: **18 October 2026, Asia/Qatar**. The first capture block has UTC timestamps on 17 October late evening; the continuation has UTC timestamps on 18 October morning. The manifest preserves exact timestamps rather than rewriting them to a single acquisition time.
- Evidence IDs S001–S107 identify UI states, not independent modules or successful features. Every ID has a source URL, descriptive research title, timestamp, screenshot and accessibility snapshot path.

## What was actually used

Browser interaction used Codex's existing Chrome computer-use connection and its supported Playwright locator interface. Visible DOM text, accessibility trees, screenshots, measured computed styles and the page's observed asset inventory supplied evidence. Native index/coordinate clicks were used only from fresh observed states where semantic selection was insufficient. No off-UI authenticated HTTP calls, credential/cookie extraction, storage reads or hidden application-state inspection were performed.

The REA skill supplied an evidence-led method. Initially no REA tools were connected to this chat. Later, the user explicitly requested Codex setup: REA 6.5.0 diagnostics found Cursor aligned and Codex missing; the scoped setup added Codex's REA registration with a backup. An isolated stdio MCP readiness check then initialized server `rea` version 6.5.0, listed 207 tools and successfully called `binary_session`. **That is tool-readiness evidence, not a REA analysis of SentrixFM.** No browser CDP target was bound to REA, no JavaScript source tree was analyzed by REA, and no REA runtime-capture Evidence record is claimed for the site.

There was no separately installed Playwright MCP server in this chat. The requested installation of unpinned `@playwright/mcp@latest` was rejected by automatic approval review as unnecessary alongside existing controls. It was not retried through another installation route. A separate debugging profile/CDP session was not launched; the browser work used the already signed-in Chrome connection and one dedicated research tab. Current browser interaction nevertheless used the documented Playwright interface successfully.

Atlas discovery used codebase-memory-mcp; fifteen selected snippets were checked against the current checkout and matched. The full Atlas application was not started or tested in this pass. The earlier audit remains a separate historical source.

## Read-only action boundary

Performed: navigation, expand/collapse, open/close drawers and forms, switch tabs/view modes, inspect filters/dropdowns, generate one read-only report, explicitly Load one dashboard, temporary viewport override, draft-only SOP field/rule exploration and cancellation, one workflow reload to recover an incomplete render.

Not performed: Create/Save/Update/Run Now/Force Sync/Verify, status or role changes, security/appearance toggles, invitations, new users, public intake enablement, uploads, deletes, financial actions, chat/AI/email sends, scans or browser permission grants. No credentials were entered by the agent. The temporary viewport was reset and the agent-created research tab closed. The original user tab was left open; its interrupted blank asset-creation form was not saved or changed.

Opening a record can cause normal server access telemetry; this was not an assertion that HTTP GET has no side effects. The research avoided intentional business-record mutations.

## Evidence interpretation

| Label | Meaning |
|---|---|
| Observed | Visible page/DOM/screenshot or an interaction outcome in this session |
| Configurable / claimed | UI option, explanatory text, feature flag or marketing-like label; execution not established |
| Inferred | A proposed relationship or likely implementation explanation derived from observations |
| Unknown / untested | Requires further read-only inspection, documentation, authorized test data or source/runtime access |
| Proposed | A recommendation for Atlas, never a claim about SentrixFM |

Screenshots contain ordinary trial/account context and should remain part of the user's private research collection. The prose avoids repeating account contact identifiers. This is distinct from the previous public Facilio research folder. No archive is published to a public destination.

## Capture-quality limitations and corrections

Some early accessibility files are **diff snapshots**, containing only changes since a previous observation. Their filenames are preserved; the manifest labels `snapshot_kind`. Read them with adjacent states and the corresponding screenshot. S033 onward use full snapshots. A diff-only snapshot is not a complete DOM inventory of the page.

- S014's unsuccessful/ambiguous drawer opening is superseded by successful S092 and full record S093.
- S016 captured a menu animation; S107 confirms the Business Hub menu inventory in AX but its screenshot shows clipped lower-right placement. S017 has residual overlay; use S015/S018 for reporting controls.
- S019's title describes generation, but its screenshot had already reached the same Not Found result as S020. There is no successful generated report in this collection.
- S032 shows the fading asset-history dialog; S033 is the settled asset overview.
- S044's first AX state showed Create enabled; later settled DOM disabled it. Do not label this a validation bypass.
- An immediate inline resize observation caught transitional clipping; saved S099 had already reflowed. S101 is the deliberate settled narrow record; S100 is the settled narrow task list. Root/body widths were 390, so clipping does not prove document-wide horizontal overflow.
- S062's sparse shell, S064's empty filter and S104's non-expanding package actions are bounded observations. They do not prove a feature is globally absent.

Reload/render timing can alter an apparent failure. Preserve these corrections when producing summaries or feeding this collection to another agent.

## Coverage not established

No exhaustive endpoint/API schema, proprietary backend source, tenant-isolation proof, task completion/approval, actual PPM occurrence generation, stock receipt/issue, filled inspection results, persisted SOP versioning, sequential workflow execution, integration delivery, AI answer quality, native mobile/offline operation, load testing, keyboard/screen-reader testing or edition comparison was performed. No public-portal settings were enabled to inspect hidden options. Those items are deliberately retained as open questions.

Broad manager navigation was covered, but **not every possible state of every accessible feature**: soft-service duplicates, all calendar modes, all form-type inspectors, every asset/location branch, permission catalog standalone page, project-grid variant, record edit variants and hidden/disabled settings remain unsampled or partial. A read-only inspection cannot establish all business behavior.

No attempt was made to bypass authentication, account permissions, technical restrictions or browser safety. Navigation was sequential and bounded, with no bulk authenticated crawler or guessed endpoint sweep.
