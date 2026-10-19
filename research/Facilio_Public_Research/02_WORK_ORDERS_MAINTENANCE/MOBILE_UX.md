# Mobile and offline reference

Public documentation checked 2026-10-17. Older guides use WorkQ; newer offline pages mention Workstation. Do not assume identical app generations, editions or interfaces. Source capsules in this folder include the detailed mobile guide pages and their original images.

| Interaction | Public evidence | Atlas design question |
|---|---|---|
| Technician navigation and tasks | [Mobile overview](https://facilio.com/help/docs/mobile-guide/overview/) | Does the technician start with assigned work and the information needed on site? |
| Prepare a record offline | [Offline configuration](https://facilio.com/help/docs/mobile-guide/Working-Offline/Managing-Offline-Mode/Configuring-Offline-Mode/) | Can users deliberately download/remove work and recognize availability/connectivity? |
| Work while disconnected | [Offline WO module](https://facilio.com/help/docs/mobile-guide/Working-Offline-in-Facilio/Offline-for-Work-Order-Module/) | Which actions are local, queued, unavailable or dependent on online automation? |
| Inspection evidence offline | [Offline inspection](https://facilio.com/help/docs/mobile-guide/Working-Offline-in-Facilio/Offline-for-Inspection/) | Can users answer checklists and add findings without suggesting that a pending score is final? |
| Extension placement | [Connected Apps](https://facilio.com/developers/docs/connected-apps/index/) | Which widgets and record actions are supported on mobile, and how does capability differ from desktop? |
| Voice and context assistance | [Technician Co-Pilot](https://facilio.com/help/docs/ai-guide/technician-co-pilot/) | Can a user review the transcribed input and proposed update before it changes a record? |

The work-order offline guide explicitly constrains custom workflows/stateflows, Connected Apps, custom buttons and other operations, with automation/SLA processing resuming online. The inspection guide permits answering checklists, creating an inspection from a template and adding findings; it excludes template creation and immediate scoring. Synchronization and scoring occur after reconnection.

These are documented limitations, not observations of synchronization correctness. Conflict resolution, attachment upload retry, simultaneous edits, notification behavior, device encryption and actual offline performance remain untested. For an Atlas prototype, communicate queued changes, last successful synchronization, rejected changes and actions requiring a connection. Those are design recommendations.
