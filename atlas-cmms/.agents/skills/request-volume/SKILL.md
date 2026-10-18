---
name: request-volume
description: Use when the app must keep files across a restart — "storage", "a disk", "a PVC",
  "persistent storage", "save uploads", "keep this file", images, photos, videos, audio, clips,
  thumbnails, generated media, "a SQLite database", "a local index", "a working directory",
  "increase the volume", "more disk space", "the disk is full" — or when it tries to write to disk
  and gets "Read-only file system". Not the `postgres` database's space, which is `request-database`.
---

Code: `ajnkit-media`.

## Files

| | |
|---|---|
| `score.yaml` | declare `volume` — one per app — and mount it at **`/data`** under `containers.app.volumes` |
| AGENTS.md's Stack table | *the volume's folder* — `DATA_DIR`, read once, like every other variable |

## Choosing

Three places to put a file, and most apps only need the first:

| The file is | Use |
|---|---|
| scratch, for one request | **`/tmp`** — already there, 512Mi on disk, gone on restart. Nothing to declare |
| **media — images, photos, videos, audio, thumbnails**, uploaded or generated | **`volume`**, through *uploads* (`ajnkit-media`); the database keeps the name. The form is the shipped one with a file input (`COMPONENTS.md`) |
| state one app keeps across restarts — a SQLite file, an index, a working folder | **`volume`** |
| read by anything else — another app, a person, a job | **`bucket`** — not available yet; say so |

A volume is **one disk for one pod**: a restart keeps it; a new version waits for the old one to stop
(`Recreate`), so a deploy has a few seconds of downtime. It is **deleted with the app**, and there is
**no backup**. Say both to the user before they keep anything that matters in it. Data you query is
`postgres` (`request-database`), not a file.

## What to do

0. Uploads, in a Python or adapted app: `canvas app add media` once (not for files the app only writes).
1. Uncomment the three marked lines in `score.yaml` — `DATA_DIR`, `volumes` and the `data` resource —
   so it reads:
   ```yaml
   containers:
     app:
       variables:
         DATA_DIR: /data                 # where the app finds it
       volumes:
         /data:
           source: ${resources.data}
   resources:
     data:
       type: volume
       params: {size: 1Gi}               # 1Gi to 10Gi is yours; counts against the team's storage quota
   ```
   Mount it at `/data`. The platform takes another absolute path of its own (not `/`, `/tmp` or
   `/workspace`, which is the app itself) — use one only when the user asks, and say why in a comment.
2. Use `DATA_DIR`, as *the volume's folder* says: a `data/` folder next to the code on your computer
   (`.gitignore` leaves it out), the disk on the platform.
3. `canvas validate`, then `canvas deploy`. `canvas status` shows the volume: `Pending` until the app's pod is first scheduled — normal — then `Bound`.

## "Increase the volume to 10 GiB" — more space, up to 10Gi

The portal's "More space" dialog gives the user this sentence when the size needs no approval. Do
it all, and ask them nothing more:

1. In `score.yaml`, set the `volume` resource's `params: {size: <it>Gi}` (10Gi at most here)
2. `canvas validate`, then `canvas deploy` — the disk grows; the app restarts once (a few seconds)
3. Say it is done, and the new size: `canvas status` shows the volume

A smaller size than it has is not a change — a volume only grows; say so and leave it.

## More than 10Gi — or it is filling up

The app's page in the portal shows how full the disk is (Health → Disk; amber from 80%). Up to
10Gi, raise `size` and deploy (above). More, up to 100Gi, is approved first: send the user to the
app's page → **Resources → Request more space**, with the size and why — the one step that is theirs. One of the team's owners
approves it, if the team's storage quota has room, and the disk grows **at once** — no deploy.
Then set `size` in `score.yaml` to match, so the file says what the app has.

## What NOT to do

- Do not write anywhere else: the root filesystem is read-only, and only `/tmp` and the volume take files.
- Do not mount it somewhere other than `/data`, or name the variable other than `DATA_DIR`, unless asked.
- Do not build a path to it by hand (`"/data/" + name`): from `DATA_DIR`, as *the volume's folder*
  says, so the same code runs on your computer.
- Do not keep a second copy of data that belongs in `postgres`.
- Do not put images, videos or audio in `postgres` (`bytea`, base64 in `jsonb`) or in `/tmp`: they
  belong on the volume — the database keeps their path and what they are. Video is big: size the
  volume for it, and ask for more early (the Disk tile shows how full it is).
- Over 250 MB, or a connection that drops: `large=True` (`ajnkit-media`) — never your own chunking
  or a raised body limit.
- Never save or serve an upload with your own code (`open()`, `FileResponse`, the uploader's name) —
  `ajnkit-media`. Another kind than image, video or audio (a PDF): ask the user first.
- Do not set `size` over 10Gi before it is approved: `canvas deploy` stops with where to ask.
