---
name: add-cache
description: Use when the user wants something faster or kept for a while — "cache this", "add
  Redis", "it's slow", "rate limit", "remember the last result" — or when you reach for Redis,
  memcached or a cache library. A queue, a job or work in the background is `add-job`.
---

## Not available yet: `cache`

The platform has no `cache` resource (Redis) yet: `canvas validate` refuses `type: cache`. Say so —
and if the user does need Redis itself, `report-issue` stars the demand for it, or files one — then
use what the app already has — **an app is one process**, so most of what Redis does for a
fleet of servers, the process itself or `postgres` does here.

## Choosing

| The need | Use |
|---|---|
| a slow read that is fine to lose on a restart — an outside API, a heavy query | **in the process** — AGENTS.md's Stack table, *a cache in the process* |
| a result that must outlive a restart or a deploy — an expensive AI answer, a report | **a `postgres` table** keyed by the input, read before computing (`request-database`) |
| a rate limit, a counter | a `postgres` row per key and window: `INSERT … ON CONFLICT DO UPDATE` |
| a queue, job status | not a cache: `add-job` |
| sessions, who is signed in | nothing: the platform's sign-in is the session (`add-auth`) |
| state shared with another app of the team | that app's API, through `service` (a pair: `canvas app create --stack next --api python`) |

Auto-deploy restarts the app on every change, so an in-process cache starts empty after each deploy.
For a cache that is fine; if it is not, the data belongs in `postgres`.

## What to do

1. Find what is actually slow — time it in the log — before caching anything
2. Cache in `src/lib/`, on the slow function, so the page and the endpoint both get it — as *a cache
   in the process* says, with an expiry (five minutes, say) and a bound on how much it holds, so it
   cannot grow until the app runs out of memory; a library it needs is *a dependency*
3. A `postgres` table instead when it must survive a restart: *the schema*, then `canvas db revision`
4. A test that the second call does not recompute (`write-tests`); *the tests*, then AGENTS.md §1

## What NOT to do

- Do not declare `type: cache`, add a Redis client, or run Redis beside the app — there is no second
  container.
- Do not cache without a bound — `maxsize` and `ttl`. The app has a 512Mi memory limit, and an
  unbounded dict ends in `OOMKilled`.
- Do not cache what depends on who is calling under a key that leaves the caller out — one person
  would see another's data.
- Do not keep cached query results on the `volume`; a table does that, and is queryable.
