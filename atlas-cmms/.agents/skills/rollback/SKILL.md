---
name: rollback
description: >-
  Use when the user wants to undo a deploy or run another version: "roll it back", "revert",
  "the last deploy broke it", "go back to yesterday's", "roll forward".
---

## Files

Edits nothing. Runs `canvas versions` and `canvas rollback [--to <build>]`.

## Choosing

An app can run any of its **newest build and the three before it** — `canvas versions` lists them,
with which is running. `canvas rollback` runs the one before the running one; `canvas rollback --to
<build>` runs any listed one, **the newest included — that is rolling forward**. It waits for it to be
live. There is no prompt, so tell the user first: the **image** changes, the **schema** and the
**volume's files** do not. If a
migration since then was written by hand (`canvas versions` warns), it may have dropped or renamed
something the older version uses, and it may not start. The next `canvas deploy` builds and runs the
newest code again.

A crash that a fresh start would clear is `canvas restart` — same version, new container — not a
roll back.

## What to do

1. `canvas versions` — pick the build, and read its warning if there is one
2. Say what will change, and anything a migration changed since
3. `canvas rollback --to <build>` (or plain `canvas rollback` for the one before)
4. `canvas status` — confirm the app is Healthy afterwards. Its line `newest build #N is not running`
   is the build you rolled back from — not a deploy to come; `canvas rollback --to N` runs it again

## What NOT to do

- Do not roll back past a destructive migration without telling the user what it means: the image reverts, the schema does not.
- Do not roll back to 'try something' — it is a real deploy.
- Do not use it to undo a schema change. Write the next migration.
