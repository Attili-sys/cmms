---
name: request-email
description: >-
  Use when the app should email people: "send an email", "notify me when…", "email the team",
  "send a receipt / a reminder / a digest", "alert someone", "send a confirmation", or when the
  user names SMTP, SendGrid, Mailgun, Outlook or Gmail for the app — or when a send was refused
  (email.recipient, email.limit, EmailRefused).
---

Code: `ajnkit-email`.

## Files

| | |
|---|---|
| `score.yaml` | the `email` resource — `notify: {type: email}`, no params |
| *email* (AGENTS.md's Stack table) | `send(to, subject, text)` — the platform's; do not edit, do not wrap in a second helper |

## What is permitted, what is not

The platform enforces these — the app cannot change them, so design within them.

| Permitted | Not permitted |
|---|---|
| Email **people in the app's Canvas team** — its owners and members (`canvas team members`) | Anyone else — a customer, a distribution list, another team — **until a platform admin approves the app** (`canvas email request`, below) |
| **20 recipients an hour**, per app, rolling — one email to 5 people counts 5 | More, in any form: a loop, a retry, splitting into many sends. The 21st is refused with when there is room |
| Up to **20 recipients in one email** (`to` is a list) | Cc, Bcc, or recipients hidden from each other — every recipient sees the others |
| **Plain text in**: a one-line subject (≤200 characters), a body (≤65,536 characters). The platform sends it in Canvas's own layout — the app's title, the text in paragraphs (a blank line starts one), `https://` links clickable, an *Open <app>* button | Your own HTML, styling, attachments, images, calendar invites — markup in the text arrives as text |
| The sender's **name** — it is the app's title, `canvas.dev/title` in `score.yaml` (`describe-app`) | The sender's **address**: every app sends from `CanvasTheSandbox@mailer.aljazeera.net`, so the name is how people tell apps apart |
| Replies — they go to the **app's owner** | Choosing `Reply-To`, or sending as a person |
| Sending from the deployed app | Sending from your computer — locally `send()` only logs the message |

## Ask first

Before writing code, ask the user — the answers decide the design:

1. **Who receives it?** Only people in their team, or customers, a distribution list, anyone who
   fills a form? Outside the team needs an admin's approval (below) — say so now, not after the deploy.
2. **How often?** 20 an hour is enough for "a job finished" or "a request needs your approval". It is
   not enough for one email per event, per row, or per user action at any volume — then propose a
   digest (one email listing what happened) or a page the people check instead.

## What to do

0. Python or adapted app: `canvas app add email` once.
1. Declare it in `score.yaml`:
   ```yaml
   resources:
     notify:
       type: email
   ```
2. Send from the code that knows something happened — in `src/lib/` or *background work*, not in a page:
   ```python
   from ajnkit.email import EmailRefused, send

   try:
       send(["sahar@aljazeera.net"], "Import finished", f"{count} rows imported into {name}.")
   except EmailRefused as e:
       log.warning("email not sent: %s", e)
   ```
   ```ts
   import { log } from "@ajnkit/core";
   import { EmailRefused, send } from "@ajnkit/email";

   try {
     await send(["sahar@aljazeera.net"], "Import finished", `${count} rows imported into ${name}.`);
   } catch (e) {
     if (!(e instanceof EmailRefused)) throw e;
     log.warn("email not sent", { reason: e.message });
   }
   ```
   **A refused email must not fail the user's request**: the work happened, only the telling did not.
   Log it, and show it on a page if the user would want to know.
3. Test it with `send` replaced (`ajnkit-email`) — never a real send from a test.
4. On your computer nothing is sent: `send()` logs the message. Show the user that line.
5. The sender's name is the app's title: check `canvas.dev/title` in `score.yaml` says what people
   should see in their inbox — "Visitor desk", not "my-app-v2" (`describe-app`).
6. `canvas validate`, then `canvas deploy` — the first deploy gives the app its token.

## Someone outside the team

Only when the user confirms the app must email people outside their team:

```
canvas email request "<who it writes to, and why>"
```

Run from the app's folder, by the app's owner or a team owner, after the first deploy. Write the
reason for the admin who reads it — who the recipients are and what they get, e.g. *"Sends a receipt
to each person who submits the visitor form — one email per submission."* Then tell the user a
platform admin decides it; until then the app writes to its team only. Approval can be withdrawn.

## When a send is refused

`ajnkit-email`'s table says what each refusal means; say it to the user in plain words.

## What NOT to do

- Do not add an SMTP server, password, `smtplib`, or a mail SDK (SendGrid, Mailgun, Graph). The
  platform sends; an app with its own mail credential bypasses who-may-receive and the limit.
- Do not put addresses or a password in `score.yaml` or `variables`.
- Do not email from a loop over rows or users; one message to many recipients, or a digest.
- Do not run `canvas email request` without the user's yes: it asks an admin to let the app write to
  anyone, and it is the user's call.
