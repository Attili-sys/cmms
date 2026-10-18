---
name: request-database
description: >-
  Use when the user needs to store data: "I need a database", "add postgres",
  "save this", "persist it", or changes what is stored — a new table, a new field — or the
  database needs more space: "increase the database", "the database is full".
---

## Files

| | |
|---|---|
| `score.yaml` | declare `postgres` — one per app |
| *the schema* (AGENTS.md's Stack table) | the only definition |
| `db/migrations/` | **generated** by `canvas db revision`, applied by the platform in order |
| `db/schema.json` (`db/drizzle/meta/` in a Next.js app) | the schema as of the last revision — written by `canvas db revision`, never by hand |
| *the database* | connection only; read its comment first |

## Choosing

| The data is | Use |
|---|---|
| relational, or documents you query | **`postgres`** — `jsonb` covers document shapes |
| a file someone uploads or downloads — **images, videos, audio** above all | **`volume`** today (`request-volume`); a `bucket` once it exists |
| throwaway, hot, reconstructable | in the process, until `cache` exists — `add-cache` |

## What to do

1. Declare it in `score.yaml`:
   ```yaml
   resources:
     db:
       type: postgres
       params: {size: 1Gi}      # 1Gi to 10Gi; more, to 100Gi, a team owner approves; counts against the team's storage quota
   ```
   The platform sets `DATABASE_URL`; the app already reads it. Do not add it to `variables`.
2. Define the schema in *the schema* (replace the example table).
3. `canvas db revision "<what changed>"` — writes the next `db/migrations/NNN_*.sql` and updates its
   record of the schema (above). No database is needed: it compares the schema with that record.
4. **Read the generated SQL**, then `canvas validate` and `canvas deploy`. The platform applies the
   pending migrations, each in its own transaction, before the new version starts; if one fails,
   the running version keeps serving and `canvas status` names the file.

## "Increase the database to 10 GiB" — more space, up to 10Gi

The portal's "Request more space" dialog gives the user this sentence when the size needs no
approval. Do it all, and ask them nothing more:

1. In `score.yaml`, set the `postgres` resource's `params: {size: <it>Gi}` (10Gi at most here)
2. `canvas validate`, then `canvas deploy` — the disk grows in place and keeps its data
3. Say it is done, and the new size: `canvas status` shows the database

A smaller size than it has is not a change — a database disk only grows; say so and leave it.

## More than 10Gi — or it is filling up

The app's page in the portal shows how full it is (Resources → Database). Up to 10Gi, raise `size`
and deploy (above). More, up to 100Gi, is approved first: send the user to the app's page →
**Resources → Database → Request more space**, with the size and why — the one step that is theirs.
One of the team's owners approves it, if the team's storage quota has room, and the disk grows
**at once** — no deploy. Leave `size` in `score.yaml` as it is: `canvas validate` takes at most 10Gi
for `postgres`.

**An app on its own stack** (adapted as it is, with neither `src/models.py` nor `src/db/schema.ts`):
`canvas db revision` has no schema to read. Write each `db/migrations/NNN_name.sql` by hand, additive only (a new
table, column or index), and never edit one that has run; there is nothing to `--record`.

## When it refuses

`canvas db revision` writes only what keeps the previous version of the app runnable, so a roll back
stays safe: a new table; a new column, with its UNIQUE and FOREIGN KEY when the column has no
default (`server_default` in SQLAlchemy, `.default()` in Drizzle); a new or moved index (a unique one only on new columns); a `server_default` set
(`ALTER COLUMN … SET DEFAULT`); an index removed (`DROP INDEX`). It refuses, and says why:

| Refused | Why | Do |
|---|---|---|
| a column or table that is gone (a drop or a rename) | a one-way door: the previous version can no longer run, so a roll back breaks the app | tell the user what it costs; if they agree, write the SQL (`ALTER TABLE … RENAME COLUMN …`) as the next `db/migrations/NNN_*.sql`, then `canvas db revision --record` |
| a changed type, or a column made `NOT NULL` | may not convert the rows already there, or they may hold NULL | the same: by hand, deliberately, then `--record` |
| a new `NOT NULL` column with no `server_default` | rows already in the table would have no value | give it a `server_default`, or make it nullable |
| a UNIQUE, FOREIGN KEY or CHECK on a column already there, or an index made unique | rows already there may break it, and the deploy fails; an older version may write what it forbids | by hand, after checking the rows, then `--record` |
| a UNIQUE or FOREIGN KEY on a new column with a `server_default` | the default fills every row with one value, which may break it | drop the default, or write it by hand |
| a `server_default` taken away, or a constraint taken away | an older version may insert relying on it; Postgres named the constraint | by hand, then `--record` |

## What NOT to do

- Do not create tables at startup, call `create_all`, run `drizzle-kit push` or `migrate`, or use any
  ORM's auto-migrate.
- Do not edit a migration that has already run — the platform refuses it. Add the next file.
- Do not write migration SQL for an additive change by hand — `canvas db revision` writes it from
  the schema, so the two cannot disagree.
- Do not reach for MongoDB. Document data is `postgres` with a `jsonb` column.
- Do not promise the data is kept (AGENTS.md §9).
