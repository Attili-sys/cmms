# Inspections, reusable questionnaires and field evidence

Research date: **2026-10-17**. The evidence below comes from public Facilio documentation, with no authenticated trial. Atlas was not inspected; recommendations are opportunities to validate against the actual product.

## Template design and execution are distinct

[Illustrating Inspection Process](https://facilio.com/help/docs/user-guide/facilio-modules/inspection/illustrating-inspection-process/) separates reusable templates from individual inspections. A template defines what to inspect and how an execution is triggered; the execution records the actual assessment. This is a useful architectural distinction for condition checks, compliance rounds and routine logbooks.

[Managing Inspection Template](https://facilio.com/help/docs/user-guide/facilio-modules/inspection/illustrating-inspection-process/managing-inspection-template/) documents a scope covering one or multiple assets/locations, inspector assignment, and manual or scheduled triggers. Recurrence configuration previews upcoming cycles. The questionnaire builder supports drag-and-drop question types, required responses, attachments, pages and reordering. Scoring and response rules are separate configuration areas; documented rule actions include email and script execution. Template views expose completion insights and trigger history. The screenshots are especially useful for understanding how a nontechnical administrator moves between form structure, scoring and behavior rather than putting all settings into one large dialog.

[Managing Inspections](https://facilio.com/help/docs/user-guide/facilio-modules/inspection/illustrating-inspection-process/managing-inspections/) demonstrates the operational flow: a template triggers an inspection, the assigned inspector opens it, conducts the questionnaire, submits answers and closes the activity. Inspection detail shows answers and score alongside notes/documents and history. The conduct action is limited to the assigned inspector. Questionnaire PDF and print actions are documented. This provides evidence for responsibility and traceability, beyond a checklist that anyone can edit without context.

## Mobile and offline evidence

[Offline for Inspection](https://facilio.com/help/docs/mobile-guide/Working-Offline-in-Facilio/Offline-for-Inspection/) explicitly supports answering checklists, creating inspections dynamically from templates and adding findings while disconnected. Creating templates and dynamically calculating scores are unsupported offline. Updates synchronize automatically and scoring occurs after connectivity returns; a notification confirms completion. The broader [Working Offline guide](https://facilio.com/help/docs/mobile-guide/Working-Offline-in-Facilio/) introduces administrator-managed briefcases and automatic record downloads. This suggests a deliberate distribution/synchronization model rather than unlimited offline access to every module.

## Hypothetical Atlas opportunities

First establish whether Atlas's existing procedures already support structured answers, conditional evidence and reusable versions. A possible upgrade would connect a reusable inspection definition, scoped schedule, assigned execution, findings and follow-up maintenance. Operators should be able to tell which answers are saved locally, which have synchronized and whether a score is final. Separate builder permissions from execution permissions. Do not infer that every field, script or automation works offline because basic checklist execution does.

## What remains unknown

Public instructions are strong evidence of intended builder controls and completion flows, but do not verify accessibility, large-form performance, branching-depth limits, scoring edge cases, signature validity, or conflict resolution after simultaneous edits. They also do not establish regulatory certification. Compare screenshots across documentation generations before choosing a visual baseline. For reconstruction, prioritize questionnaire navigation, mandatory evidence, assignment and synchronization feedback; adapt the visual design independently and retain source attribution for reference images.
