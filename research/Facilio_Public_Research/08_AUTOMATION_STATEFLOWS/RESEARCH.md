# Automation and stateflows: product research

Research date: **2026-10-17**. Evidence is public, static documentation. No Facilio tenant, transition, script, scheduler or API was executed. Product behavior below is documented behavior, not runtime verification. Atlas opportunities are proposals; the existing Atlas repository was not inspected.

## Observed public model

Facilio separates event-driven automation from modeled record lifecycles. [Configuring Workflow Parameters](https://facilio.com/help/docs/admin-guide/automations/managing-workflows/working-with-workflows/configuring-workflow-parameters/) describes rules for system and custom modules: choose a triggering activity, define criteria, then attach actions. Documented action families include field changes, status changes and script execution. This suggests that routine reactions to record events need not be expressed as a whole lifecycle diagram.

[Stateflows: Basic Components](https://facilio.com/help/docs/admin-guide/process-management/stateflows/basic-components/) distinguishes a process definition, its states and the transitions connecting them. [Stateflow Overview](https://facilio.com/help/docs/admin-guide/process-management/stateflows/overview/) describes configurable state properties/timers and applicability to operational contexts such as teams, buildings and asset categories.

[Adding a Stateflow](https://facilio.com/help/docs/admin-guide/process-management/stateflows/managing-stateflows/adding-a-stateflow/) shows a module-scoped visual builder: establish the initial state and applicability, place existing states on the canvas, and define transitions. Transition labels become actions in the operational interface. Priority settings distinguish highlighted and secondary actions. The screenshot sequence is useful because it links the administrator’s process diagram to the technician’s visible next action.

[Stateflow Transition Properties](https://facilio.com/help/docs/admin-guide/process-management/stateflows/managing-stateflows/configuring-stateflow-transition-properties/) documents manual, timed and condition-driven transitions. The same page covers permissions, location restrictions, mandatory asset QR/barcode checks, transition-specific forms, related-record creation, confirmations and validations. It also lists actions after execution. Mandatory scanning is documented as restricting the transition to mobile. These are precise public clues about field-work verification, rather than evidence of any tenant’s configuration.

## Atlas implementation opportunities — inference

Start with a transition service shared by the web and mobile interfaces. A process definition should declare allowed source/destination states, permission policy, required inputs and side effects. The interface can then render available actions from that definition. This is preferable to scattering status-changing buttons across separate screens because every client needs the same operational rules.

Keep three concepts distinct in the proposed design: a record’s lifecycle, a rule reacting to an event, and an approval decision. They interact, but a simple priority-based notification should not require editing a lifecycle canvas. Likewise, an approval should preserve who decided, why, and under which policy revision.

Before adding a graphical editor, implement a small number of complete workflows: service request to work order; vendor quote approval; work execution to evidence review and closure. Expose transition history, validation failures and pending responsibilities clearly. This would create immediate operational value while supplying a stable foundation for later administrator tooling.

For enterprise use, design idempotent side effects, auditable process revisions, timer pause rules, business calendars, retries and migration behavior for records already in progress. These are Atlas engineering recommendations, not verified details of Facilio’s implementation. Test time-sensitive cases explicitly: reassignment during escalation, repeated requests, failed notifications, reopened work and changed SLA policy.

## Open questions

- How does Facilio version stateflow definitions and handle existing records after edits?
- Are timers based on elapsed time, working calendars or configurable pauses in every context?
- What transaction/retry guarantees exist between transitions and external actions?
- How do approval processes interact with stateflows, and what varies by edition?

## REA analysis prompts

1. From the builder screenshots, identify the minimum process schema needed to reproduce the interaction independently.
2. Map each administrator option to an operator-visible result, required evidence and error state.
3. Sketch an Atlas transition drawer showing required form fields, responsible role and resulting state.
4. Separate directly pictured controls from inferred behavior; record missing cases instead of inventing them.
