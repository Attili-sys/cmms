---
name: describe-app
description: Use after a new app's first feature (not straight after `canvas init`) and at the end of every
  `build-feature`; when score.yaml lacks `canvas.dev/title` or `canvas.dev/tags`; when the user renames,
  describes or tags the app ("call it…", "tag it sport", "not ai"); and once per app before a deploy, to
  ask for an icon and cover. Writes the title, description, category and tags the portal shows and
  filters by. Who sees it and opens it is share-app.
---

## Files

| What | Where |
|---|---|
| the title, description, category and tags | `score.yaml`, under `metadata.annotations` |
| the categories and tags there are | `.canvas/contracts/score-extensions.schema.json` — `$defs/category`, `$defs/tag` |
| the icon and the cover picture | `src/static/icon.png`, `src/static/cover.jpg` — named in `score.yaml` as `canvas.dev/icon`, `canvas.dev/cover` |
| the same words for people reading the repo | `README.md` — its `#` heading and first line |

```yaml
metadata:
  name: motion-graphics                 # the address — never changed by this skill
  annotations:
    canvas.dev/title: Motion Graphics Studio
    canvas.dev/description: Turns a short script into an animated explainer for social posts.
    canvas.dev/category: graphics
    canvas.dev/tags: short-form, social, ai
```

The portal shows them to the team and filters by category and tag. `name` is only the address (`<name>--<team>.<base>`); the title is free text and need not match it.
A shorter address (`<name>.<base>`, beside that one) is `canvas domain request <name> "<why>"` — a platform admin approves it. Not a line in score.yaml, and no build. The app keeps the address it was made with.

## What to do

1. **Work out what the app is for**, from the user's own words in this conversation first, then
   `README.md`, then `src/lib/` and the app's pages — what a person does with it.
2. **Work out all four** — the tags as surely as the title; an app is never left without them:
   - the **title** — 2 to 5 words, what people would call it: "Expense Approvals", not
     `expense-app`, not "AI-Powered Expense Platform". Up to 60 characters
   - the **description** — one sentence: what it does, and for whom. Plain words, up to 280
     characters. "Lets the newsroom check a clip's rights before it airs."
   - the **category** — exactly one from `$defs/category`, each with what it covers: what the app
     is *for* in the newsroom (a subtitle checker is `video`, not `editorial`). Unsure between two:
     the one whose people use it
   - the **tags** — **always one to three** from `$defs/tag`, the three that say most: its coverage
     (`sport`), language (`arabic`), format (`podcast`) or craft (`subtitles`, `ai`). Only what is
     true of it — but something always is: an app that calls a model is `ai`, one that shows
     numbers is `dashboard` or `charts`, a step in a process is `workflow`. A tag the list lacks is
     not invented — pick the nearest, and tell the user it can be added to the platform's list
3. **Ask when it is not clear — and only then.**
   - What the app is for — still unclear from what it does, or a slug like `test01`: one question,
     with three titles to pick from:
     > What will this app do? Some names, if one fits: **Clip Rights Check**, **Rights Desk**,
     > **Clearance Board** — or tell me your own.
   - Which tags — the purpose is clear, but more than three fit as well as each other, or none fits well: one question,
     offering the likeliest few to pick from: "Tag it **video**, **rights** or **verification**?"
   Anything the user has said about it — "it's for the sports desk", "tag it arabic", "not ai" —
   decides it over your own reading, now and at every later re-check.
4. **Otherwise write all four — no yes needed.** Then say what you wrote, in one line: "Titled it
   **Clip Rights Check** — *Lets the newsroom check a clip's rights before it airs.* · video ·
   rights, verification". The user changes any of it by saying so.
5. Uncomment `annotations:` if it is still a comment; keep the keys and any others already there.
6. Set the README's heading to the title and its first line to the description.
7. `canvas validate`, then the change ships with the next `canvas deploy` — the portal shows it once
   the source is uploaded.

**At the end of every `build-feature`** — re-evaluate, do not assume. Read the title, description and
tags against the app as it now is, with the feature just added, changed, expanded or removed:

| The change | Then |
|---|---|
| a fix, a tweak, a page for the same job | all still true — say nothing, change nothing |
| it does more, or for more people — "now also exports to PDF", "now for the whole newsroom" | a new description that covers it, still one sentence, and any tag it now earns (`arabic` once it handles Arabic) — at three already, it replaces the one that says least |
| its main job moved — a notes app that became a task tracker | a new title and category as well |
| a feature the description or a tag names is gone | them without it |
| it has no tags | its one to three, now |

Write it, then say it in one line, "Title → …, description → …, tags → …". Wanting to list each feature means the sentence is too narrow, not too
short: say the job they share.

## The pictures: an icon and a cover

The portal shows a **cover** on the app's card and its page, and an **icon** beside its name. With
neither, it draws a cover from the app's name — that is fine, and nothing waits for one.

**Ask once per app, before a deploy**, when `score.yaml` names neither `canvas.dev/icon` nor `canvas.dev/cover` and
`.canvas/pictures-asked` does not exist. Then write that file (`asked <date>`), whatever the answer:
it is what makes it once — never again, on later deploys or in a new conversation, unless the user
brings it up.
> Do you have an icon and a cover picture for it? Give me the files, or I'll leave the one the
> portal draws — you can add them any time.

| They | Then |
|---|---|
| give a file | copy it to `src/static/icon.png` (square, 512×512, at most 100 KB) or `src/static/cover.jpg` (**1600×600**, at most 300 KB) — keep its own type: `.png`, `.jpg` or `.webp` — and name it in `score.yaml`. Not that shape: crop it to it, with their OK |
| say no, later, or nothing | deploy as it is; do not ask again |
| ask you to make one | read `pictures.md` beside this skill, make it in that house style at that size, show it, and write it only on a yes |

**Where a cover is seen**: on the app's card at about 2:1, and across its page as a wide band — so
of a 1600×600 cover, only the **centre 1200×240** is always seen. Put what matters there (the
subject, any words); the rest is background that may be cut. `canvas validate` checks the real
size: a cover 2:1 to 3.2:1 and at least 1200 wide, an icon square and at least 256.

## What NOT to do

- Do not change `metadata.name` — it is the URL, and renaming it is a new app.
- Do not write marketing copy, emoji, or a list of features. One sentence says what it is.
- Do not use a category or tag outside the contract's list — `canvas validate` refuses it, and a
  filter would never find the app.
- Do not describe what the code does not do yet — not the plan, the app as it is.
- Do not put a person's name, a secret or a customer's data in either: the whole team sees them.
- **Do not make a picture by default** — no icon, no cover, unless the user asks for one. With
  none, the portal's drawn cover is the answer.
- Do not take a picture from the web or a search result: a newsroom shows only what it owns or has
  licensed. Ask before using one with a recognisable person in it.
- Do not use SVG for either: it can carry script, and the portal shows it to everyone.
