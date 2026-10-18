---
name: add-auth
description: Use when the user wants an app to require login, says "lock this down", asks who can
  reach their app, or wants to know who is calling — and when something that is not a person must
  call an app's API — another app, an outside system, a script, in either direction. The platform
  signs people and service accounts in for the app — the app does not do OIDC itself.
---

Code: `ajnkit-core`.

## Sign-in, on or off

**On in a new app**: every request needs a company sign-in (Authentik, the same account as the
portal), and the platform tells the app who is calling. It is one line in `score.yaml`:

```yaml
resources:
  www:
    type: route
    params:
      auth: sso            # none: no sign-in
```

"Turn sign-in off" (or on) is that line, then `canvas deploy` (or auto-deploy). Off needs no
`access` left: a new app opens only for its maker, so first `canvas share everyone` — `canvas validate`
refuses `access` without `auth: sso`. Off, the app is open
to everyone on the corporate network — never the internet — and nobody is known. Say so before
turning it off: anyone on the network can then use it, and anything it shows.

## The API docs, without the sign-in

A Python app only — a Next.js app has no API docs yet, and `canvas validate` refuses this there.
With `auth: sso`, `/api/docs` needs a sign-in like everything else. To let anyone on the company
network read the docs, add `docs: public` beside `auth` and deploy:

```yaml
    params:
      auth: sso
      docs: public         # /api/docs, /api/redoc, /api/openapi.json — nothing else
```

Only those docs pages open; every endpoint stays behind the sign-in, so "Try it out" works only
for someone signed in. The docs list every endpoint the app has — ask the user before turning it on.

## Who is calling

*Who is calling* (AGENTS.md's Stack table) gives `email`, `name` and `groups`: real under
`auth: sso`, absent and **forgeable** under `auth: none` — never decide anything on them there.

## Only some people or groups

The platform lets any employee sign in. **Who may open it** — `access.read` — is `canvas share`
(below), never written by hand. Beside it, by hand, who may also change things and who never:

```yaml
    params:
      auth: sso
      access:
        read: ["Innovation and R&D"]         # `canvas share with "Innovation and R&D"` writes this
        write: ["someone@aljazeera.net"]     # may also POST/PUT/PATCH/DELETE; absent: same as read
        deny: ["contractor@aljazeera.net"]   # never, whatever read and write say
```

No `access`: anyone who signs in. **"Make it private"**, "share it with the team", "everyone" or
"with Finance" is `canvas share private | team | everyone | with <who…>` — never by hand (`share-app`); it changes the
running app at once, without a build. `canvas deploy` refuses `access` without `auth: sso` before it uploads anything. It is
enforced on every request — nothing to write. Writers can always read.

## Only some people on one page — a rule

"Only Finance should see the dashboard", "the export is for Ann", "admins only on /settings": a
**rule**. Write WHO in `score.yaml`, under the route's `access.rules`, and only the rule's NAME in the
code. `score.yaml` is the one place people are written: the platform hands the rules to the app,
and the portal shows them on the app's page — so what it shows is what the app enforces.

```yaml
    params:
      auth: sso
      access:
        rules:
          dashboard: ["Finance", "ann@aljazeera.net"]   # a name, then who: Entra groups or emails
```

```python
from ajnkit.rbac import require

@router.get("/dashboard")
@require("dashboard")
def dashboard(request: Request): ...    # @require below the route decorator; a view under it takes the Request, or every call fails

# or once for a page, its htmx partials and its /api twin:
router = APIRouter(prefix="/dashboard", dependencies=[Depends(require("dashboard"))])
```

**Each role sees its own menu.** A page only a rule may open is only in that rule's menu — name the
rule as the third item of its line in `src/nav.py`, and the header shows it to who the rule lets in:

```python
PAGES = [("Take a test", "/"), ("Questions", "/questions", "admin"), ("Results", "/results", "admin")]
```

A Python app only: a Next.js app's `src/nav.ts` takes a label and a path, and its menu is the same for
everyone — the page's own `permit("admin")` keeps it closed, and a person the rule leaves out who
follows the link gets the 403 page. Never filter `PAGES` yourself in a Next app.

Anything else a role alone may see — a button, a column — is `allowed(who, "admin")` (`from
ajnkit.rbac import allowed`, `who = caller(request.headers)` from `ajnkit.identity`), passed to the template; never an
email compared in code. Who is in the rule stays score.yaml's.
```tsx
import { permit } from "@ajnkit/core";

export default async function Dashboard() {
  await permit("dashboard");          // first, before anything is read
  …
}
```

Who goes in a rule is written by hand, so look each person up: their email from
`canvas team members --json`, or from the user — **never guessed from a name** (`momin@` is
nobody; Momin Bannani is `bannanim@`), as a wrong one locks them out. The whole team is its groups,
`canvas-<team>-owners` and `canvas-<team>-members`, which keep up as people join and leave.

Every time the user asks for something like this, **record it as a rule** — a new name, or more
people on an existing one — never as a list of groups or emails in the code. A rule's name is lowercase
letters, numbers and hyphens; say which page it guards in a comment beside it if the name does not.

`canvas validate` and `canvas deploy` refuse a rule the code names (*a rule*) that `score.yaml` does
not declare, before anything is uploaded. On your computer a guarded page refuses everyone.
A page that tells someone they may not see it uses the notice component, as an error, inside the
shell like any page — never a page of its own making (a Next app's `permit` shows the platform's own
403 page by itself). Sign out is the shell's, under their name.

## Machine callers — a service account

Something that is not a person — another app, an outside system, a script — cannot follow a sign-in
redirect. It gets a **service account** instead, and the app keeps `auth: sso`: a caller is never a
reason to turn sign-in off.

**Being called.** Whoever runs the caller makes the account in their team, and you list it in this
app's `access` like a person — with an `access` block, it reaches nothing until you do (an app with
none lets in anyone signed in, a service account included):

```yaml
    params:
      auth: sso
      access:
        read: ["Innovation and R&D", "orders-sync--growth@svc.<base>"]
```

`canvas sa create` prints the identity to add. `read` alone lets it change things too, as it does
for people; to keep it to GET, there must be a `write` list — and a `write` list takes changing
things away from everyone only in `read`, so name in it every person who still needs to. Adding
it to an existing list keeps the people already there; an `access.read` that names only the
service account shuts everyone else out.

**Calling another app.** Run in the CALLING app's folder; the credential goes straight into its
secret and is never shown:

```
canvas sa create orders-sync --secret ORDERS_API
```

Declare `ORDERS_API` like any secret (`add-secret`), and the other app's URL —
`https://<app>--<team>.<base>`, as its page in the portal shows it — as a plain variable,
`ORDERS_URL`; read both as *a secret* and *read a setting* say. Always that URL, never the app's in-cluster Service, which
the platform blocks for an `auth: sso` app:

```python
user, password = envs.secret("ORDERS_API").split(":", 1)
with http.client() as c:
    c.post(f"{envs.ORDERS_URL}/api/orders", auth=(user, password), json=order)
```
```ts
await call(`${setting("ORDERS_URL")}/api/orders`, {
  method: "POST",
  headers: { authorization: `Basic ${btoa(secret("ORDERS_API"))}`, "content-type": "application/json" },
  body: JSON.stringify(order),
});
```

**An outside system or a script:** `canvas sa create <name>` without `--secret` shows the password
once, for its owner to keep in that system's own secret store. It sends
`Authorization: Basic <username>:<password>` (`curl -u`). `canvas sa list` shows when each expires;
`canvas sa rotate <name>` makes a new password, and the old one stops within a minute. Rotating and
deleting are for whoever made the account, or an owner of the team.

**A third party's webhook** — GitHub, a SaaS — is not for Canvas: a sandbox has no public address.
Never open the app with `auth: none` for one; poll their API instead (`call-api`).

## What NOT to do

- **Do not implement OIDC in the app.** The platform does it; app-side auth drifts from it.
- **Do not list people in `ALLOWED_GROUPS`-style variables, or in the code.** `access`
  and its `rules` are the one place; the portal reads them.
- **Do not loosen the platform's access or rule checks to make them pass.** Failing closed is the intended behaviour.
- **Do not turn sign-in off so a script or another app can call in.** Give it a service account.
- **Do not print, log or commit a service account's password.** `--secret` keeps it out of sight.
- **Do not put `@require` above the route decorator.** `@router.get` (or post, put, …) comes first and `@require` below it, next to the function. Above, it protects nothing — the route is registered without it — and `canvas validate` refuses the app.
