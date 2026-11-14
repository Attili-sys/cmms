# Open issues

Reviewed on 2026-11-05 after the Python migration sign-off (`955ea8d3`, Canvas build `#17`). These are known residuals, not deployment blockers.

## 1. Required cost checks only additional-cost rows

The work-order completion guard for `completeCost` requires at least one `AdditionalCost` row. Labor cost or parts cost alone does not satisfy it, so a completed job with real cost but no additional-cost entry is still rejected.

## 2. Required tasks pass when a work order has no tasks

The `completeTasks` guard rejects a work order only when an existing task has an empty value. A work order with zero tasks can still be completed while that requirement is turned on.

## 3. Customer report email still needs Canvas approval

Work-order report email sends through Canvas email. Recipients inside the Canvas team can receive it. Customers, contractors, and anyone else outside the team are refused until a platform administrator approves external email with `canvas email request`. That approval has not been requested.

## 4. Calendar generation walks every preventive-maintenance schedule

Each calendar request calculates future preventive-maintenance occurrences in the request, up to 400 per schedule. The current data volume is fine. A large schedule history will make that page slower.
