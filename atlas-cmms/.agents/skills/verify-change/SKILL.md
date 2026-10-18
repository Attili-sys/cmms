---
name: verify-change
description: Use after a change is deployed and before saying it is done — "it works", "done", "ready" —
  and whenever the user asks "does it work?", "check it", "look at it". Says how to see the change as
  each of the app's people sees it, and what counts as working.
---

**Done is what you saw, not what you wrote.** `canvas validate` passing and the deploy going live
prove the code runs; they do not prove it does what was asked. Look before you say so.

## What to look at

Every page and API route the change touched, as each kind of person who uses it:

| Who | Why |
|---|---|
| The person you build for (no role) | what they asked for is there, and does what they said |
| Each rule in score.yaml's `access.rules` (an admin, an editor…) | their menu shows their pages, and only theirs (AGENTS.md, `add-auth`) |
| A member (`access.read`) | they are refused what a rule keeps for others — the page and its API route |
| A phone's width, for a new page | nothing cut off, nothing side by side that cannot fit |

| Where you are | How |
|---|---|
| Studio | `try_app` (path, role, phone) for a page, `fetch_app` for an API route; Studio gives you one round for this once the version is live |
| A laptop | the app's URL (`canvas status`) in the browser, signed in as yourself; an API route with `curl` and your session; a role you do not have: ask the user to look |

## What counts as working

- The page shows what was asked, in the user's words — not a placeholder, not "TODO".
- A list that is empty says what to do, with the button to do it for who may.
- An action says what happened (a notice) and where it went.
- A refusal is a plain page, not a 500.

Something is wrong: fix it, deploy again, look again — at most twice, then say in the answer what is
still wrong and why. In the answer, name what you looked at and what you saw ("as an editor, Articles
lists the three drafts"), never "should work".
