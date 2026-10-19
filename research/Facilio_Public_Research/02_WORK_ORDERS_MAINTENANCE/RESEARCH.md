# Maintenance execution and field work

Research date: **2026-10-17**. Evidence is public documentation and published interface images, not a hands-on trial. The Atlas installation and codebase were not inspected; upgrade suggestions below are hypotheses to validate.

## Supported workflows and interaction patterns

[Managing Work Orders](https://facilio.com/help/docs/user-guide/facilio-modules/maintenance-management/handling-maintenance/managing-work-orders/) documents a meaningful separation between authorization, execution, resolution and closure. A request can require approval before execution. The operational sequence is assignment, starting work, completing all tasks, resolving and finally closing; closed work can be reopened. Its screenshots expose a detail workspace with summary, tasks, time information, history and related records. A downtime-reporting action connects maintenance execution to the affected asset. Study how stage-dependent actions, task progress and supporting evidence share the workspace.

[Configuring Planned Maintenance](https://facilio.com/help/docs/user-guide/facilio-modules/maintenance-management/handling-maintenance/configuring-planned-maintenance/) shows a three-stage configuration: basic scope and work details, planner configuration, then publication. A planner combines recurring triggers with selected assets, technicians and job plans. Recurrence supports execution windows, repeat intervals and skipped cycles. Published configuration produces work orders; the template retains summary, planner and scheduler views. This suggests a reusable scheduling object rather than individually duplicated recurring tickets.

[Configuring Job Plan](https://facilio.com/help/docs/user-guide/facilio-modules/maintenance-management/handling-maintenance/configuring-job-plan/) documents sections and tasks, text/number/option inputs, and mandatory photographs for all or selected conditions. Its detail view includes planned labor, items, tools and services. Revision, cloning and version history are visible concepts. This is useful evidence for keeping procedure design separate from procedure execution.

[Accessing Resource Planner](https://facilio.com/help/docs/user-guide/facilio-modules/maintenance-management/handling-maintenance/accessing-resource-planner/) demonstrates assigned/unassigned scheduling, date-granularity switching, task detail inspection and drag-and-drop reassignment across staff and times. The [FSM work-order guide](https://facilio.com/help/docs/field-service-management/services/handling-services/managing-work-orders/) is a distinct variant: appointments, resource-bearing tasks and planned-versus-actual consumption deserve separate analysis.

## Mobile and disconnected execution

The [offline work-order guide](https://facilio.com/help/docs/mobile-guide/Working-Offline-in-Facilio/Offline-for-Work-Order-Module/) explicitly limits disconnected behavior. Core field updates synchronize after reconnection; workflows, stateflows, notifications and SLA escalations wait for connectivity. Connected Apps/custom buttons, downtime reporting and printing/downloading are unsupported offline. This is a boundary reference, not proof of unrestricted offline parity. Older [manual offline configuration](https://facilio.com/help/docs/mobile-guide/Working-Offline/Managing-Offline-Mode/Configuring-Offline-Mode/) uses swipe actions and record indicators; newer documentation describes another provisioning model. Confirm the intended app/version before reproducing either interaction.

## Hypothetical Atlas opportunities and unknowns

First assess whether Atlas already distinguishes approval, execution and acceptance; then consider a coherent job workspace, versioned procedures, resource planning and explicit offline status. Prioritize completion evidence and auditability before adding decorative dashboards. Public guides establish intended interactions, but do not verify responsiveness, concurrency, bulk-operation performance, tenant-specific configuration or exact availability by subscription. Compare the ordinary maintenance and FSM variants before selecting a target model.
