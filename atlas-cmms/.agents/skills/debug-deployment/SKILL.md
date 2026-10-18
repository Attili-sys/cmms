---
name: debug-deployment
description: Use when a deploy failed, an app is unhealthy, or the user asks "why is it not up",
  "what went wrong", "it says degraded".
---

## Files

Edits whatever the evidence points at — usually `score.yaml` or the code that crashes on start;
an adapted app's own `Procfile`. Never a platform file (AGENTS.md §2) — `canvas app update` restores one.

## Choosing

`canvas status` says WHICH stage is wrong; `canvas logs` says why. Pick the logs by the stage:

| `canvas status` shows | Read | What it usually is |
|---|---|---|
| build `failed` at `detect` | `canvas logs --build` | no `Procfile`, or no dependency file a buildpack recognises |
| build `failed` at `build` | `canvas logs --build` | a dependency that will not install |
| deploy `degraded`, restarts > 0 | `canvas logs --previous` | the app crashes on start — the crash is in the instance BEFORE the restart |
| deploy `progressing`, `Synced`, for minutes | `canvas logs` | it starts but does not answer on `route.params.path` |
| deploy not `Synced`, with a message naming a resource (the FIX says Argo could not apply this deploy) | the message | the platform's, not the app's: `report-issue` — unless the message says `exceeded quota` (next row) |
| a message saying `exceeded quota` | the message | the team's quota is used up — a smaller `size`, or an owner asks for more (`onboard-tenant`) |
| `volume … Pending` | — | normal: the disk is made once the app's pod is scheduled. Look at the deploy, not the disk |
| logs say `Read-only file system` | `canvas logs` | it writes outside `/tmp` and the volume — `request-volume` |
| deploy stopped at 62: `secret.missing` | the message | not broken: a key `score.yaml` declares has no value yet, so it built and waits — guide the user to set it (`add-secret`), then deploy again |
| a changed secret, and the app still uses the old one | — | the app reads secrets when it starts: `canvas restart` |

## What to do

1. `canvas status` — exit 80 is its answer (degraded, or the build failed), not an error. The stage, the failed build step, restarts, memory against its limit; its
   `version` line says which build runs (`— rolled back` when not the newest) and whether a newer
   upload is waiting — after a roll back it names the build rolled back from instead, which is not a
   deploy to come — and `folder` whether what you are looking at is what runs
2. The `canvas logs` variant from the table
3. Fix the cause, `canvas deploy` again
4. If the evidence points at Canvas, not the app — a REASON naming the controller or the build
   service, a build step that fails with nothing wrong in the app, an `unmapped.*` diagnosis, a FIX
   saying Argo could not apply this deploy, the same platform error after the fix — tell the user it is the platform's, and `report-issue`: it
   stars the report someone already filed, or files a bug on their yes

## What NOT to do

- Do not report the app's own crash or a missing dependency as a Canvas bug — fix it.
- Do not re-run `deploy` hoping it passes. A build or crash that failed for a reason fails again.
- Do not read `canvas logs` in a restart loop without `--previous` — the current instance has
  usually not logged anything yet.
- Do not try to `kubectl` anything. There is no kubeconfig for tenant namespaces; the CLI is
  the only way in.
