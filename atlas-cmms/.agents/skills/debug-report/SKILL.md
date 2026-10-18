---
name: debug-report
description: Use when the user says something in the running app is broken or wrong — "the button does
  nothing", "search finds nothing", "it shows an error", "the score is always 0", "X is missing". Says how
  to check it first and say back what you found before changing code, and when to stop. A deploy that
  failed or an app that is not up is debug-deployment.
---

**Check it first, say what you found, then change it.** A fix written from the description alone changes
code that may not be the reason, and the report comes back; and the person should hear whether they are
right before anything changes.

## The steps

1. **See it happen.** Open the page they named as them (Studio: `try_app`, with `phone` when it is about
   a phone or "mobile"; an API route: `fetch_app`; a laptop: the browser at a phone's width, `curl`).
   Read the app's log for the error behind it (`canvas logs`; Studio: `app_logs`).
2. **Read the code behind it** — the view, the API route, the function in `src/lib/` — and what it
   calls in ajnkit (`packages/`; Studio: `read_package` or `explore`). Do not guess how a call works.
3. **One cause, in one sentence, naming the line** — "`search()` in src/lib/articles.py:42 compares
   with `==`, so a word inside a title never matches". If you cannot name the line, read more; do not
   change code yet.
4. **Say it back before you change anything.** Plainly: whether they are right ("You are right: on a
   phone the table runs off the edge" — or "I could not see it: the page fits at a phone's width"),
   where it happens, and the change you would make, as they will see it. Studio: `propose_fix`, then
   stop — nothing is changed until they say Fix it. Elsewhere: say it in a few lines and wait for their
   go-ahead, unless they already asked you to fix it.
5. **The smallest change that removes that cause** — the one they agreed to. Nothing else in the same
   change: no tidying, no second idea.
6. **See it again** (step 1) once it is deployed. Fixed: say what was wrong and what they can do now.

## When to stop

Three fixes that did not change what they see: stop. Say what you looked at, what you tried and what
you saw each time, and what you would need to know — a cause you cannot find from the code is often
data (an empty table, a value typed differently) or a person's access, which the user can check.

If after step 2 nothing is wrong, say what you looked at, what it does now, and what they should try,
in their words. Never answer a report with "it is already built".
