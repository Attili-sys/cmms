---
name: share-app
description: >-
  Use when the user wants to change who sees the app listed or who may open it: "make it private",
  "just for me", "hide it", "share it with the team", "let Finance see it", "share it with Sara",
  "show it to everyone", "who can see it?" — with `canvas share`. Restricting a page or an action to
  some people is add-auth's rules.
---

## Who sees it listed

**A new app is private**: its `score.yaml` starts with `canvas.dev/visibility: private`, which keeps
it off the team's page for everyone but its owner, the team's owners and the platform's admins.
Leave it so. An app without the line (made before this) is listed for the team; do not change it
unasked.

**Who sees it and who opens it is `canvas share`** — never edit those lines by hand. It writes
score.yaml, keeping every comment, and changes the running app at once: the same build, no upload,
no deploy. `canvas share` alone says how it is shared now.

| They say | Run |
|---|---|
| "make it private", "just for me", "hide it", "keep it to myself" | `canvas share private` — listed for them, and only they open it. It asks before taking away anyone else named; without a terminal it stops (exit 23): ask the user, then `--yes` |
| "share it with the team", "my team", "my colleagues" | `canvas share team` — listed for the team, and only the team's people open it: its groups `canvas-<team>-owners`, `canvas-<team>-members` (and the team's Entra owners group, if it has one), written to `access.read`. Say it is shared with the team — not a list of everyone's names: the portal's app page shows each group as one chip with how many are in it (`members · 7`), which opens to who is in it now. It asks before taking away anyone else named; without a terminal it stops (exit 23): ask the user, then `--yes` |
| "grant access to everyone", "show it to everyone", "the whole company", "make it public", "anyone can open it" | `canvas share everyone` — listed for the team, and anyone at the company who signs in opens it, whoever `share with` named before. Not the Hall: that is listed for the whole company, and an admin approves it |
| "just the owners", "only the members", "the owners and Sara" | `canvas share with owners` or `canvas share with members` — the team's own group (`canvas-<team>-owners` / `-members`; owners are never in the members group, so `members` lets in the owners too), kept up as people join and leave; it mixes with names (`canvas share with owners Sara`). |
| "share it with Sara", "let Finance see it", "the team and Sara" | `canvas share with <name, email or Entra group>…` — listed for the team, and they and the user open it. A name is someone in the team (`canvas team members --json`); one two people have is asked about, never guessed, and one nobody has is taken as a group — it says so on a `group` line: if a person was meant, ask for their email |

**A person's email is never guessed** from their name (`momin@`, `sara.k@`): a wrong one locks
them out, or lets someone else in. Pass the name and let `canvas share with` find the email in the
team (`canvas team members --json` lists it); for someone outside the team, ask the user. It stops
(exit 23) on an email no one in the team has that looks made from a name — `momin@aljazeera.net is
nobody in <team> — Momin Bannani is bannanim@aljazeera.net`: use the email it names. `--yes` keeps
the one written, only when the user says it is someone else. A `team` line means the names are
everyone in the team: ask whether they meant the team (`canvas share team`, which keeps up as people
join and leave) or just these people.

Not deployed yet, it is written to score.yaml and goes live with the first deploy — it says so. It
needs the company sign-in in front (`auth: sso`) to let only some people in; with `auth: none` it
says so, and that is `add-auth`.
