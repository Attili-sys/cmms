---
name: use-database
description: >-
  Use when code reads or writes the database — a route, a page or a job that queries, inserts,
  updates or deletes — and whenever the app is slow, times out, or logs "QueuePool limit … reached",
  "too many connections" or "timeout exceeded when trying to connect". Above all before building
  anything live or many-people-at-once: a game, a race, a party room, presence, a live board, polling
  every second. Declaring the database and changing the schema is `request-database`.
---

## The one rule: a connection is the scarcest thing the app has

One app is one process with **10 database connections** (`ajnkit.db`: 5 + 5; Next.js: `max: 5`),
and up to 40 requests running at once. A request holds a connection from its first query until its
transaction ends. When all 10 are held, every other request waits — 30 s in Python — then fails, the
health check slows, and the app looks down.

So: **few queries per request, a short transaction, no waiting while holding one, and nothing
high-frequency in the database at all.**

## Per request

| Do | Python (SQLAlchemy 2, `ajnkit.db`) | Next.js (Drizzle, `db()`) |
|---|---|---|
| one session per request, passed down — never a new one in a helper | `db: Annotated[Session, Depends(session)]`; `lib.x.add(db, …)` | `db()` is the shared pool: call it, never `new Pool` |
| writes in one transaction, ended at once | `with db.begin(): …` or `db.commit()` right after the last write | `await db().transaction(async (tx) => { … })` |
| done with the database → let go **before** slow work (an AI call, an outside API, a big render) | read, `db.commit()` (it releases the connection; `expire_on_commit=False` keeps the objects readable), then the slow call, then a new short `with db.begin():` for the result | the pool lends per query: never `await` slow work inside `transaction()` |
| a list with its children: one or two queries, never one per row | `select(Room).options(selectinload(Room.players))` — `joinedload` for a single parent | `db().query.room.findMany({ with: { players: true } })` |
| many rows: one statement | `db.execute(insert(Row), [{…}, {…}])`; by id: `db.execute(update(Row), [{"id": 1, …}, …])`; by condition: `update(Row).where(…).values(…)` | `db().insert(row).values([...])`; `update(row).set(…).where(…)` |
| insert or update by key: one statement | `from sqlalchemy.dialects.postgresql import insert` → `insert(Row).values(…).on_conflict_do_update(index_elements=[Row.key], set_={…})` | `.onConflictDoUpdate({ target: row.key, set: { … } })` |
| the row you just wrote: no second query | `db.scalars(insert(Row).returning(Row), rows).all()` | `.returning()` |
| a count, a check: in SQL | `db.scalar(select(func.count()).where(…))`, `exists()` | `count()`, `exists` |
| only the columns and rows needed | `select(Row.id, Row.name).where(…).limit(50)` | `.select({ id: row.id }).limit(50)` |
| background work: its own session | in the task, `with Session(engine) as s, s.begin():` (`engine` from `ajnkit.db`) — never the request's `db`, which is closed by then | `after()` with `db()` |

A streaming answer (SSE, a long poll, a file streamed back) keeps the request's session — and its
connection — until the stream ends: read what it needs, `db.commit()`, then return the stream.

## Live and many-at-once: in memory, not the database

The app is **one** process, so memory is shared by every request — what Redis does for a fleet is a
dict here.

| The data | Where |
|---|---|
| positions, ticks, who is typing or online, a countdown, a live score — changing several times a second | **in memory**: a dict in `src/lib/`, behind a `threading.Lock` (Python), keyed by room; the route reads and writes it without a session |
| what must outlive a restart — the result, the lap time, who won, the room itself | **the database**, written once, when it happens (the race ends), or in one batched insert every few seconds |
| everyone sees the same state | one read from memory per poll; the poll every 1–2 s, not faster; positions sent at most 5 times a second |

A restart (every deploy) empties the memory: a live race ends with it. Say so, and save what matters
at each step that matters.

## The browser side

- Poll no faster than the person can see: 1–2 s for a list, 5 times a second at most for live play.
- On an error — 409, 429, 500, 503, a timeout — **stop or slow down**: wait 1 s, then 2, 4, 8 (plus a
  little random), never retry in a loop.
- A state that will not change (the race is over, the room closed): stop polling.

## Check it

- The log: a `QueuePool limit … reached` or `timeout exceeded when trying to connect` line means
  connections ran out — find what holds them (above), never raise the pool.
- Count the queries one request makes: `echo=True` on a local engine, or the log. More than a few is
  a loop to batch.
- For anything live: think of 6 people at once. Requests a second × queries each must stay well
  under what 10 connections answer, with the slow work outside.

## What NOT to do

- Do not raise the pool, add replicas, or add Redis — the app is one process with a small pool on
  purpose, and the database serves every app of the team. Use less of it.
- Do not open a session or engine of your own (`create_engine`, `Session()`, `new Pool`) — use the
  one the app has.
- Do not query in a loop over rows (`for r in rows: db.get(…)`) — load them together, or join.
- Do not call an AI model, an outside API, or `time.sleep` inside a transaction.
- Do not write to the database on every frame, move, keystroke or heartbeat.
- Do not use the sync session in an `async def` route — it stops every other request (AGENTS.md's
  Stack table, *a route's function*).
