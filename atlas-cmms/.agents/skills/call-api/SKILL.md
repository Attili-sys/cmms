---
name: call-api
description: Use when the app must talk to another system — "call the X API", "fetch from our CMS",
  "use the partner's API", "pull data from another app", "get the weather / the scores" — or when an outside call hangs, times out or fails. Who may
  call THIS app (a service account, `access`) is `add-auth`; storing the key is `add-secret`.
---

## Files

| | |
|---|---|
| the Stack table's *a call outside* (AGENTS.md) | every outside call — it carries the timeout |
| `src/lib/` | the function that calls, one per outside system — never in a route or a page |
| `score.yaml` | the key's name under a `secret` (`add-secret`); the other side's URL as a plain variable |
| `src/api/client` (a pair's web app) | the client `canvas api pull` makes — the only way to the pair's API |

## Choosing

| The other side is | Do |
|---|---|
| **the API of this pair** — a web app over a Python API, one folder (ADR-40) | `service` — below. Already wired by `canvas app create <name> --stack next --api python` |
| **another app of ours**, any other | a service account: `canvas sa create <name> --secret <KEY>` in this app's folder, the other app's public URL — `add-auth`'s *Machine callers* |
| **an outside API** — a partner, a SaaS, a public feed | *a call outside*, its key a `secret` — below |
| **a third party pushing to us** — a webhook | not on Canvas: a sandbox has no public address. Poll their API instead (`add-job`'s schedule); an internal system calls us as a service account (`add-auth`) |

`service` is not a general link between two apps. The app it names must be `scope: internal-cluster`
and `auth: sso` (no address of its own); the app that declares it keeps no `postgres`, `llm`,
`volume` or `email`, no `access` of its own, and declares one `service` at most; a member links
only to an app of their own (an owner of the team, any two). `canvas deploy` refuses anything else. Two apps that each keep their own data talk through a service account.

## What to do — the pair's API

1. `score.yaml` of the web app, as `canvas app create` wrote it — the platform sets `API_URL` and
   lets only this app in:
   ```yaml
     api:
       type: service
       params: {app: notes-api}
   ```
2. Call it only through `client` from `@/api/client`; `canvas api pull` makes it from the API's
   contract. `canvas validate` refuses `serviceUrl(`, `API_URL` or `api(` written by hand:
   ```ts
   const { data, error } = await client.GET("/api/notes");
   ```
   The person crosses with the call: the API's own `access` and rules decide, once, for both.

## What to do — an outside API

1. **The key** is a `secret` (`add-secret`), read where it is used. The base URL is a plain variable.
2. **One function in `src/lib/`** per thing the app asks, through *a call outside* — it has a 10 s
   timeout. Pass a longer one only for a call known to be slow, never none:
   ```python
   def scores(day: str) -> list[dict]:
       with http.client() as c:
           r = c.get(f"{envs.SCORES_URL}/v1/scores", params={"day": day},
                     headers={"authorization": f"Bearer {envs.secret('SCORES_KEY')}"})
       r.raise_for_status()
       return r.json()["items"]
   ```
   ```ts
   export async function scores(day: string) {
     const r = await call(`${setting("SCORES_URL")}/v1/scores?day=${encodeURIComponent(day)}`, {
       headers: { authorization: `Bearer ${secret("SCORES_KEY")}` },
     });
     if (!r.ok) throw new Error(`scores answered ${r.status}`);
     return (await r.json()).items;
   }
   ```
   (`SCORES_URL`: a plain variable in score.yaml — Python adds it to `src/envs.py`, Next reads it with `setting()`.)
3. **Retry only what is safe to repeat** — a GET, or a POST the other side dedupes by an id you
   send. Twice at most, a second apart, and only on a timeout, a lost connection, 429 or 5xx. Never
   retry a 4xx: it will say the same thing again.
4. **When it fails**, the person is told in a sentence — a `notice` on the page, a 502 with a
   `detail` from the endpoint — and the error is logged (AGENTS.md's *Log*) with the status, never
   the key. Never a stack trace, never a blank page.
5. **Slow or limited** (a quota, a per-minute cap): keep the answer for a while (`add-cache`), and
   fetch on a schedule in background work rather than on every page view.
6. **A test** replaces the call — `monkeypatch.setattr(http, "client", lambda: httpx.Client(transport=httpx.MockTransport(handler)))`,
   or `vi.spyOn(globalThis, "fetch")`: one for the answer, one for a failure. Tests never reach the real API.

## What NOT to do

- Do not call anything without the timeout *a call outside* carries — no bare `httpx`, `requests`
  or `fetch`.
- Do not put a key in the URL, in code, or in a log line. A key in a query string ends up in logs.
- Do not reach another app at its in-cluster address (`svc.cluster.local`): the platform blocks it
  for an `auth: sso` app. A pair's API through `client`; any other through its public URL and a service account.
- Do not retry a POST that creates something unless the other side dedupes it.
- Do not call an outside API from the browser: the key would be in the page. Call it from the server.
