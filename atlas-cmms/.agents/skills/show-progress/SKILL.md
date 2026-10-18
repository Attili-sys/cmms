---
name: show-progress
description: Use at the start of any work with three or more steps — a feature (build-feature), a
  deploy that needs fixing, an adapt or port, an update (apply-update) — and whenever the user asks
  "show me what you're doing", "keep a board", "what's left". Opens a board beside the conversation
  with every step as done, in progress, pending or blocked, and keeps it current as each step starts
  and lands, so whoever is sitting with you can follow without reading the transcript. Not for a
  one-step change.
---

## Where the board lives

| If you can | The board is |
|---|---|
| publish a live page (Claude: the Artifact tool, with the `db` capability) | **a live board page** — `board.html` beside this file, published once, its rows updated as you go |
| not (Cursor, or anywhere without one) | **your own to-do list** — the same steps and states, in the tool's task list the user already sees |

Never a file in the app's repository: it would change on every step and outlive the work.

## Opening it — before the first step

1. Write the steps down: what the user asked, broken into the pieces you will do, in order, grouped
   by phase when there is more than one ("Build", "Ship"). Five to fifteen rows; a row is a result
   someone can check ("the export endpoint, tested"), not an activity ("work on export").
2. **Live board.** Copy `board.html` to your scratch space, replace `{{TITLE}}` with what this work
   is ("Recipes · CSV export") and `{{WHAT}}` with one line of what it is for, and publish it with
   `capabilities: {db: {}}`. Then write, in one batch:
   - `meta/board` — `{updated: <date>, now: <what you are doing>, decided?: <choices the user made>}`
   - one `tasks/<id>` per step — `{order, phase, title, state, note}`, `state` one of `done`,
     `progress`, `pending`, `blocked`. Number `order` in tens, so a step can go between two later.
3. Give the user the link once, in one line, and say it is private to them until they share it.

## Keeping it current

| When | Write |
|---|---|
| you start a step | its `state: progress`, and `meta/board.now` says what you are doing |
| a step lands | `state: done`, and `note` says **what was verified** — "3 tests pass", "live at <url>" — not "done" |
| something stops you | `state: blocked`, `note` says on what: a question for the user, a failing check, a platform issue (`report-issue`) |
| the user asks for something more mid-work | a new row, `pending` — or `progress` if you take it up now |
| the work is finished | every row `done` or explained, `now` cleared or set to what is next |

Update as each step changes, not in a batch at the end: the board is for someone watching it live.
One write per change; read a row's `version` before you update it.

## What never goes on it

A secret's value, a token, a password, a connection string, or personal data the app holds. The
board is a page others can be given: a step says "set `STRIPE_KEY`", never what it was set to.
