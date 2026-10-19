# Coverage matrix

This matrix is deliberately bounded. “Inspected” means visible states were examined, not that every action or backend contract works. A form inspection is not a successful creation test.

| Area | Status | Evidence | Still open |
|---|---|---|---|
| Sidebar/global hub/location selector | Inspected | S001,S015–S016,S107; navigation JSON | Global search, localization switch, alternate account personas |
| My Tasks/work-order registry | Deep UI inspection | S001–S014,S092–S098 | Bulk actions, all pages, actual completion/approval |
| Hard/soft service split | Navigation mapped; hard sample + mixed tasks inspected | S043,S048; navigation JSON | Soft-specific duplicate views not exhaustively sampled |
| Kanban | UI inspected | S004 | Drag mutation deliberately untested, pagination semantics unknown |
| Calendar | Initial UI inspected | S005 | All modes/event scheduling and date semantics |
| Work-order create | All six tab families inspected | S006–S012 | Persistence/server validation, all dropdown choices |
| Full work-order detail | All five tabs inspected on workflow-linked task | S093–S098 | Populated cost/SOP/history, normal-status menu |
| PPM | List + key creation tabs | S043–S047 | Actual occurrence generation, detail, all scheduling selectors |
| Inspections | List + detail | S048–S049 | Filled inspection execution, evidence/score/corrective results |
| SOP | Empty library + builder/types/text inspector/validation | S050–S054 | Other field inspectors, populated instances, publish/version behavior |
| Workflows | List/grid,2canvases,task inspector,export menu,create/logic | S055–S061,S102–S104 | Runtime execution, dependencies, scheduling, export contents |
| Maintenance Packages | Nested composition inspected; route/actions problematic | S056,S060,S062,S104 | Independent registry and executable rules |
| Locations | Hierarchy/detail/edit | S027–S029 | Full expansion/map variants, typed schema, manager role inheritance |
| Assets | Registry/detail/all related-tab families/create fields | S030–S037,S091,S105–S106 | All tree/status cases; populated history; server lifecycle |
| Inventory stores | Empty registry + create form | S038–S039 | Populated stores, balance/movement behavior |
| Consumables/requisitions | Empty registries + item setup | S040–S042 | Issue/return/receiving/approval and reorder behavior |
| Maintenance requests | Empty queue/statuses/filter | S063–S064 | Existing record detail, requester/public form |
| Categories | Registry/create drawer | S065–S066 | Parent relationships, deactivation semantics |
| Roles/matrix | Four roles,12permissions,create form | S067–S070 | Standalone catalog, actual enforcement, custom-role persistence |
| Users/teams | Registry/create forms | S071–S074 | Role-in-location enforcement, team hierarchy/runtime assignment |
| General/appearance settings | Read-only sections | S075,S080 | Save behavior, theme variants not switched |
| Feature flags | Catalog inspected | S076 | Implementation not proven by enabled flags |
| Public request settings | Disabled state inspected | S077 | Hidden configuration deliberately not enabled |
| Security settings | Affordances inspected | S078 | No MFA enrollment or policy enforcement test |
| Notifications | Channels/status inspected | S079 | Delivery; email/SMS explicitly Coming Soon |
| AI | Full/floating entry UI | S081–S082 | Offline service, no queries/scans performed |
| File library | Failure state inspected | S083 | Resource retrieval failed; empty count not authoritative |
| Location chat | Shell/presence/composer | S084 | No transmission or delivery test |
| Projects | List/create/overview | S085–S087 | Overview appears template; actual project lifecycle unproven |
| Invoices | List/detail | S088–S089 | Detail appears template; no procurement chain demonstrated |
| Email center | Inbox shell | S090 | Messages deliberately not opened/sent; count inconsistency |
| Responsive web | 390px task/detail, default desktop restored | S099–S101; metrics JSON | Keyboard/screen-reader and real devices not tested |
| Frontend architecture | DOM/style/asset inventory | design tokens,asset inventory | Source bundles not decompiled; backend unknown |
| APIs | Literal UI error paths only | S020,S083 | No endpoint schema/network-body capture |
| Atlas | Focused graph/source inspection,15spans matched | graph evidence + source verification | Fresh full audit/tests/runtime required before implementation |
| REA | Codex registration + stdio readiness verified | tooling diagnostics | Active-chat tool loading/site runtime capture pending |
| Standalone Playwright MCP/CDP | Not configured/launched | tooling status | Installation rejected by auto-review; explicit approval needed if desired |

No dedicated vendor, contract, RFQ, invoice-matching, general custom-module builder or integration-configuration workflow was demonstrated in the inspected manager navigation. This is a bounded negative observation, not proof those capabilities do not exist in other roles, editions, routes or releases.
