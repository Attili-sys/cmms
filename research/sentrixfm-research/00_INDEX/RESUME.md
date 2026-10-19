# Resume checkpoint

Status: first substantial manager-UI research pass and planning package prepared; not a claim of exhaustive runtime or backend coverage. Date: 18 October 2026, Asia/Qatar.

## Completed

- 107 UI evidence states, with source URLs, timestamps, screenshots and AX snapshots.
- Work orders: table/filter/Kanban/calendar/create tabs, standalone and workflow-linked drawers, full record and related tabs.
- Dashboard/reporting: command center, operations, financials, location dashboard, report types and failed generation.
- Locations, assets, stores, consumables and requisitions; empty/setup/detail states.
- PPM recurrence/timezone/lifecycle; inspections and SOP builder, types and field validation.
- Workflow registry/grid, two BPMN canvases, task inspector, export menu, workflow creation/strategy.
- Request queue, categories, roles/matrix, users/location-role assignments and teams.
- Settings, AI, file library, chat, projects, invoices and inbox shell.
- Narrow-screen task list/record inspection and measured design tokens.
- Fifteen Atlas source spans verified against the current checkout; focused reuse/upgrade plan.
- Codex-only REA registration and stdio server readiness verification; Cursor preserved.

## Current external state

No business records or account settings intentionally saved/changed. No messages sent. The SOP draft field and validation rule were cancelled without Update/Save. Temporary viewport override reset. Agent-created research tab closed. Original user tab remains open on assets/list, with a blank creation modal from the interrupted inspection; it was not saved. Do not discard a future user draft without checking its state.

## Remaining tooling

- Codex must reconnect to expose REA's newly registered tools in the active chat.
- Standalone Playwright MCP installation was rejected by automatic approval review; it remains pending explicit user approval if still desired. Existing browser controls already perform Playwright interactions.
- No dedicated raw CDP debugging profile was launched; no REA site runtime capture was taken.

## Next read-only targets, ranked

1. Open a normal pending work order's full page and inspect its status menu/validation explanations without applying a transition. Compare with Unknown Status behavior S098.
2. Revisit Maintenance Packages route via normal navigation after the shell fully settles; inspect package execution-rule views if available. Recheck S062/S104 rather than asserting absence.
3. Inspect a populated SOP instance/result only if one already exists; expand remaining field-type inspectors without persisting a template.
4. Read existing PPM detail and recurrence selectors for all schedule semantics. Do not Run Now or Force Sync.
5. Inspect remaining location/asset tree paths and their role context, keeping selections local to views.
6. Inspect standalone permission catalog and any integration page exposed by legitimate navigation. Do not guess admin routes or grant access.
7. If REA is connected and a user-authorized isolated browser target is available, capture passive value-free API shapes and bundle/component identity with credential exclusions. Avoid whole-body HAR capture or session export.
8. Test keyboard navigation and additional responsive widths with explicit scope; distinguish emulated web from native app testing.

Business mutation tests (completion, approval, stock movement, automation execution, persistent validation and offline writes) require a separate explicitly disposable test-data plan. They were excluded from this pass.

## Atlas next work

Use the roadmap, not an automatic implementation loop. Repository path is `/Users/attiliab/Documents/GitHub/cmms`, current inspected HEAD `8b29331dd18396cb73f314cd4c6c268a4ee92c07`, branch unrestricted-selfhosted. Preserve untracked `.claude/` and separate `cmms/`. Consult repository AGENTS.md. Prefer graph tools; verify freshness before relying on a snippet. Do not repeat historical test results as newly executed checks.

No Atlas implementation is authorized by this research request.
