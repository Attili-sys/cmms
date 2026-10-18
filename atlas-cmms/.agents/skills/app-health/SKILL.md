---
name: app-health
description: >-
  Use when the user asks how the running app is doing or what it costs: "is it healthy", "is it
  up", "what's firing", "what is this costing", "how much AI have we used". A deploy that failed or
  an app that will not start is debug-deployment.
---

## Files

Edits nothing.

## Choosing

Cost figures are **estimated** — a proportional allocator, not a bill. Say so when quoting one.

## What to do

1. `canvas status` for the app — health, the running build, its estimated cost
2. `canvas llm keys` for the user's own AI key: this month's spend against their limit. The app's
   own AI spend, and the team's against its budget, are in the portal (the app's page, and Quotas)
3. The portal's app page for logs and history — there are no per-app alerts yet, so nothing "fires"

## What NOT to do

- Do not page anyone, or send the user to Grafana: consoles are for platform admins.
- Do not present estimated cost as a bill — every currency panel says *estimated*.
