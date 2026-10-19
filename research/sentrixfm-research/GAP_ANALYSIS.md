# Gap analysis: what should change in Atlas

18 October 2026, Asia/Qatar. Based on authenticated Sentrix manager UI observations and a focused current Atlas source inspection. Sentrix is a reference, not an enterprise-correctness benchmark. Broader Atlas audit findings from the earlier report require revalidation on the current branch.

| Opportunity | Sentrix publicly visible to this trial account | Atlas evidence / skeptical decision | Priority |
|---|---|---|---|
| Enterprise command center | Strategic/local dashboards, but inconsistent scopes and unfinished financial data | Build an actionable exception queue on trustworthy metrics and drill-down first | P1 after core reliability |
| Portfolio hierarchy | Generic parent/child levels, main/current location; Branch/Site label | Atlas already has parentLocation. Add typed levels, subtree roll-ups and clear scope; do not rebuild the tree | P1 |
| Site-scoped roles | User onboarding assigns a role per location | Atlas's inspected User has one Role and Location. Add scoped membership and enforce it across all retrieval/mutation paths | P0 foundation |
| Asset 360 | Metadata, QR, work/PPM/docs/history tabs; history failed | Reuse rich Asset relationships and add a coherent projection/timeline. Verify actual data before displaying health metrics | P1 |
| Work-order lifecycle | Quality/client approval affordances, full record and state card; transitions untested | Current Atlas changeStatus lacks an explicit transition allow-list in the inspected method. Fix service contracts and required evidence | P0 |
| PPM | Recurrence/date/timezone UI and generation explanation | Existing Atlas Schedule/generation code is reusable. Verify idempotency, DST, restart and completion chains before UI expansion | P0 |
| Vendor portal | No dedicated portal demonstrated in inspected navigation | Atlas has vendor master data. Add contacts/compliance/assignment first; portal only after site/job scoping | P2 |
| SLA engine | Percentage displayed; no policy/timer/escalation configuration observed | Design explicit event-based clocks, calendars, pause rules, escalation and audit; do not infer parity from an SLA card | P1 after events/scope |
| Contracts | No contract lifecycle demonstrated | Scope contracts to real operational obligations and existing ERP ownership; avoid speculative broad module | P2/need-driven |
| Procurement | Empty stock/requisition setup; invoice appears sample template | Atlas has PO/vendor foundations. Correct ledger and partial receiving before PR/RFQ/three-way matching | P0 integrity; P2 breadth |
| Inspections | Scheduled inspection list; SOP builder/field palette | Extend Atlas tasks/checklists to versioned templates, typed answers, scoring and corrective links | P1 |
| No-code automation | Process canvas, packages, trigger/strategy choices; execution unproven | Atlas has condition/action rules with TODO branches. Finish supported rules; process orchestration is a separate design | P0 fixes; P2 canvas |
| Custom modules/forms | SOP form builder; no general module platform observed | Existing Atlas CustomField is useful. Add server validation/help/typed rules before custom-object architecture | P1 fields; P2 modules |
| Role-specific layouts | Drawer/full page and different manager surfaces, no layout editor demonstrated | Ship deliberate manager/dispatcher/technician defaults first; defer a builder | P1 UX |
| Dashboards | Several chart/KPI surfaces and failed report action | One metric dictionary and one scoped query contract for counts/list/export. Show unavailable separately from zero | P1 |
| Integrations | API/webhook flag; no successful connector setup inspected | Reuse existing Atlas foundations after current re-audit; scoped keys, reliable event delivery and diagnostics | P1 foundations; P2 connectors |
| AI copilot | Service offline, Synced label, empty chat | Start later with permission-scoped retrieval/citations. No operational dependency on AI; writes use normal governed actions | P3 |
| Mobile execution | Native mobile flag only; responsive web has specific usability issues | Retain Expo and verify an offline outbox with visible sync errors; improve web mobile labels/task access | P1 field needs |

P0 = correctness/security/reliability foundations; P1 = core CAFM differentiation and daily UX; P2 = deeper capabilities after validated demand; P3 = optional intelligence layer. These are dependency priorities, not delivery dates.

Read [Atlas comparison and roadmap](05_ATLAS_UPGRADE_MAP/ATLAS_COMPARISON_AND_ROADMAP.md) for current-source boundaries, phased acceptance criteria and the first design sprint. Read [UI/UX blueprint](03_UI_UX/UI_UX_BLUEPRINT.md) for concrete component behavior. Build around real end-to-end journeys, not feature-count parity.
