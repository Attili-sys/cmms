---
name: add-job
description: >-
  Use when work should happen outside the request, or on a timer: "in the background", "send it
  later", "a queue", "a job", "job status", "retry if it fails", "every night", "every hour",
  "schedule", "cron", "a worker", "Celery", "BullMQ" — or when a request takes too long and should
  answer first and finish after. Something slow that only needs to be remembered is `add-cache`.
---

## Files

| | |
|---|---|
| `score.yaml` | `postgres` — `request-database` — for a job or a schedule; nothing for work after the response |
| *the schema* (AGENTS.md's Stack table) | one `job` table |
| *background work* (the Stack table) | the loop: `src/tasks.py` in a Python app, `src/lib/jobs.ts` in a Next.js app |
| `src/app.py` / `src/instrumentation.ts` | starts the loop with the app |
| `src/lib/` | what each job does — a plain function, the same one a page or a test can call |

## Choosing

**Auto-deploy restarts the app on every change**: anything only in memory is lost.

| The work | Use |
|---|---|
| a few seconds, fine to lose — a log line, a notification, a cache warmed | **after the response**: `BackgroundTasks` in Python, `after()` in Next.js |
| must happen, even across a restart — an email, an import, a report, a model call that costs | **a job**: a row in the `job` table, worked by the loop |
| someone waits for the result — "Generate report" | a job; the page shows its row's `status` and `error`, refreshed every few seconds |
| at a time — "every night at 7", "every hour" | **a schedule**: the same loop adds the job when it is due |
| longer than ten minutes | a job that does one part and enqueues the next — see What NOT to do |

What a restart or a deploy does to each:

| | On a restart |
|---|---|
| after the response | finished if it takes under ~30 s from the stop signal; otherwise **lost**, never retried |
| a job | **kept**. One cut off mid-run runs again ten minutes later — so it must be safe to run twice |
| a schedule | kept. A run missed while the app was down runs once when it is back |
| a timer or a thread of your own (`setInterval`, `sleep` in a loop) | **lost**, and a missed run never happens — do not use one |

## What to do

### After the response

```python
from fastapi import BackgroundTasks

@router.post("/notes")
def add(note: NoteIn, background: BackgroundTasks, db: Annotated[Session, Depends(session)]):
    saved = lib.notes.add(db, note)
    background.add_task(lib.notes.notify, saved.id)    # runs once the answer is sent
    return saved
```
```ts
import { after } from "next/server";

export async function POST(request: Request) {
  const saved = await addNote(await request.json());
  after(() => notify(saved.id));                     // runs once the answer is sent
  return Response.json(saved);
}
```
`after()` works the same in a server action. That is all — no table, no loop.

### A job, or a schedule

1. `postgres` in `score.yaml` (`request-database`), then the table in *the schema*:
   ```python
   from sqlalchemy import Index, text
   from sqlalchemy.dialects.postgresql import JSONB

   class Job(Base):
       __tablename__ = "job"
       id: Mapped[int] = mapped_column(primary_key=True)
       kind: Mapped[str]                                     # which handler runs it
       key: Mapped[str | None] = mapped_column(unique=True)  # the same key twice is one job
       payload: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'"))
       run_at: Mapped[datetime] = mapped_column(server_default=func.now())
       status: Mapped[str] = mapped_column(server_default="pending")   # pending, running, done, failed
       attempts: Mapped[int] = mapped_column(server_default="0")
       started_at: Mapped[datetime | None]
       error: Mapped[str | None]
       __table_args__ = (Index("ix_job_due", "status", "run_at"),)
   ```
   ```ts
   import { index, integer, jsonb, pgTable, serial, text, timestamp } from "drizzle-orm/pg-core";

   export const job = pgTable("job", {
     id: serial("id").primaryKey(),
     kind: text("kind").notNull(),                         // which handler runs it
     key: text("key").unique(),                            // the same key twice is one job
     payload: jsonb("payload").notNull().default({}),
     runAt: timestamp("run_at").notNull().defaultNow(),
     status: text("status").notNull().default("pending"),  // pending, running, done, failed
     attempts: integer("attempts").notNull().default(0),
     startedAt: timestamp("started_at"),
     error: text("error"),
   }, (t) => [index("job_due").on(t.status, t.runAt)]);
   ```
   `canvas db revision "add job"`.

2. The loop, in *background work*. `HANDLERS` and `SCHEDULE` are the only lines that change from app
   to app; each handler is a function of `src/lib/` taking the payload.
   ```python
   """Background work that must not be lost — the add-job skill."""

   import json
   import threading
   from datetime import UTC, datetime, timedelta

   from sqlalchemy import text

   from src.lib import reports
   from ajnkit.db import SessionLocal
   from ajnkit.logger import log

   HANDLERS = {"report": reports.build, "digest": reports.digest}   # a kind → what does it
   SCHEDULE = {"digest": "04:00"}                  # a kind → when, every day, in UTC (07:00 in Doha)
   ATTEMPTS = 3
   stop = threading.Event()

   CLAIM = """
   UPDATE job SET status = 'running', attempts = attempts + 1, started_at = now()
   WHERE id = (SELECT id FROM job
               WHERE run_at <= now() AND attempts < :attempts
                 AND (status = 'pending' OR (status = 'running' AND started_at < now() - interval '10 minutes'))
               ORDER BY run_at LIMIT 1 FOR UPDATE SKIP LOCKED)
   RETURNING id, kind, payload"""
   DONE = "UPDATE job SET status = 'done', error = NULL WHERE id = :id"
   FAILED = """
   UPDATE job SET error = :error, run_at = now() + attempts * interval '1 minute',
     status = CASE WHEN attempts >= :attempts THEN 'failed' ELSE 'pending' END
   WHERE id = :id"""
   ENQUEUE = """
   INSERT INTO job (kind, key, payload, run_at) VALUES (:kind, :key, CAST(:payload AS jsonb), :run_at)
   ON CONFLICT (key) DO NOTHING"""


   def enqueue(db, kind: str, payload: dict | None = None, key: str | None = None,
               run_at: datetime | None = None) -> None:
       """Add a job; the caller commits — with the rows it is about, so neither exists without the other."""
       db.execute(text(ENQUEUE), {"kind": kind, "key": key, "payload": json.dumps(payload or {}),
                                  "run_at": run_at or datetime.now(UTC)})


   def schedule(db) -> None:
       now = datetime.now(UTC)
       for kind, at in SCHEDULE.items():
           hour, minute = map(int, at.split(":"))
           due = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
           if due > now:
               due -= timedelta(days=1)          # today's is not due yet: yesterday's, if it never ran
           enqueue(db, kind, key=f"{kind}:{due:%Y-%m-%d}", run_at=due)


   def run(job) -> None:
       try:
           HANDLERS[job.kind](job.payload)
           sql, args = DONE, {"id": job.id}
       except Exception as e:
           log.exception("job %s (%s) failed", job.id, job.kind)
           sql, args = FAILED, {"id": job.id, "error": str(e)[:500], "attempts": ATTEMPTS}
       with SessionLocal() as db:
           db.execute(text(sql), args)
           db.commit()


   def work() -> None:
       """The loop — started with the app (src/app.py), until it stops."""
       while not stop.is_set():
           try:
               with SessionLocal() as db:
                   schedule(db)
                   job = db.execute(text(CLAIM), {"attempts": ATTEMPTS}).first()
                   db.commit()
               if job:
                   run(job)
                   continue                      # straight to the next one
           except Exception:
               log.exception("jobs: the loop failed; trying again")
           stop.wait(5)
   ```
   ```ts
   import { sql } from "drizzle-orm";

   import { env, log } from "@ajnkit/core";
   import { db } from "@/canvas/db";
   import { buildReport, sendDigest } from "@/lib/reports";

   type Handler = (payload: Record<string, unknown>) => Promise<void>;
   const HANDLERS: Record<string, Handler> = { report: buildReport, digest: sendDigest };  // a kind → what does it
   const SCHEDULE: Record<string, string> = { digest: "04:00" };   // a kind → when, every day, in UTC (07:00 in Doha)
   const ATTEMPTS = 3;

   export async function enqueue(kind: string, payload: object = {}, key: string | null = null, runAt = new Date()) {
     await db().execute(sql`INSERT INTO job (kind, key, payload, run_at)
       VALUES (${kind}, ${key}, ${JSON.stringify(payload)}::jsonb, ${runAt.toISOString()}::timestamptz)
       ON CONFLICT (key) DO NOTHING`);
   }

   async function schedule() {
     const now = new Date();
     for (const [kind, at] of Object.entries(SCHEDULE)) {
       const [hour, minute] = at.split(":").map(Number);
       const due = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), hour, minute));
       if (due > now) due.setUTCDate(due.getUTCDate() - 1);   // today's is not due yet: yesterday's, if it never ran
       await enqueue(kind, {}, `${kind}:${due.toISOString().slice(0, 10)}`, due);
     }
   }

   async function run(job: { id: number; kind: string; payload: Record<string, unknown> }) {
     try {
       await HANDLERS[job.kind](job.payload);
       await db().execute(sql`UPDATE job SET status = 'done', error = NULL WHERE id = ${job.id}`);
     } catch (error) {
       log.error(`job ${job.id} (${job.kind}) failed`, { error });
       await db().execute(sql`UPDATE job SET error = ${String(error).slice(0, 500)},
         run_at = now() + attempts * interval '1 minute',
         status = CASE WHEN attempts >= ${ATTEMPTS} THEN 'failed' ELSE 'pending' END
         WHERE id = ${job.id}`);
     }
   }

   async function work() {
     for (;;) {
       try {
         await schedule();
         const { rows: [job] } = await db().execute(sql`
           UPDATE job SET status = 'running', attempts = attempts + 1, started_at = now()
           WHERE id = (SELECT id FROM job
                       WHERE run_at <= now() AND attempts < ${ATTEMPTS}
                         AND (status = 'pending' OR (status = 'running' AND started_at < now() - interval '10 minutes'))
                       ORDER BY run_at LIMIT 1 FOR UPDATE SKIP LOCKED)
           RETURNING id, kind, payload`);
         if (job) {
           await run(job as Parameters<typeof run>[0]);
           continue;                                          // straight to the next one
         }
       } catch (error) {
         log.error("jobs: the loop failed; trying again", { error });
       }
       await new Promise((done) => setTimeout(done, 5_000));
     }
   }

   let started = false;

   /** The loop — started with the app (src/instrumentation.ts), once. */
   export function start() {
     if (started || !env.DATABASE_URL) return;
     started = true;
     void work();
   }
   ```

3. Start it with the app — with no `DATABASE_URL` (your computer, the tests, `next build`) it does
   not start:
   ```python
   # src/app.py
   import threading
   from contextlib import asynccontextmanager

   from src import envs, tasks

   @asynccontextmanager
   async def lifespan(app: FastAPI):
       if envs.DATABASE_URL:
           threading.Thread(target=tasks.work, daemon=True).start()
       yield
       tasks.stop.set()

   app = FastAPI(lifespan=lifespan, docs_url=…)       # the arguments it already has, unchanged
   ```
   ```ts
   // src/instrumentation.ts — Next.js calls register() once, when the server starts
   export async function register() {
     if (process.env.NEXT_RUNTIME === "nodejs") (await import("@/lib/jobs")).start();
   }
   ```
   (`NEXT_RUNTIME` is Next's, not `env`.)

4. Enqueue where the work starts — a route, an action, another job:
   ```python
   tasks.enqueue(db, "report", {"month": "2026-09"}, key="report:2026-09")
   db.commit()
   ```
   ```ts
   await enqueue("report", { month: "2026-09" }, "report:2026-09");
   ```
   A `key` makes asking twice one job — a double click, a retried request. Leave it out when every
   call is new work.

5. Every hour instead of every day: the key is the hour — `f"{kind}:{now:%Y-%m-%d %H}"`,
   `` `${kind}:${now.toISOString().slice(0, 13)}` `` — and `run_at` now. The times are UTC because
   the app's clock is; say what that is where the user is (Doha is UTC+3, all year).

6. Tests (*the tests*) call each handler directly, as a plain function — the loop needs the database,
   which is not on your computer. Try the loop itself on the deployed app: enqueue, then read the row.

## What NOT to do

- Do not add Celery, RQ, BullMQ, Redis or a scheduler library: the table and the loop are the whole of it.
- No `worker:` Procfile line, no second app for jobs.
- Do not write a job that breaks when it runs twice — a restart re-runs one that was cut off. Upsert,
  check before sending, or key what it writes.
- Do not let one job run past ten minutes — it would be taken as cut off and run again beside itself.
  Do a part, then `enqueue` the next part.
- Do not hold the claim's transaction open while the job runs: claim, commit, then work — as above.
  Every page waits on the same few connections (`use-database`).
- Do not start the loop at import, or once per request — once, with the app, as in step 3.
- Do not keep `done` rows forever if there are many a day: the loop may `DELETE FROM job WHERE status
  = 'done' AND run_at < now() - interval '30 days'` once a day, as a scheduled job of its own.
