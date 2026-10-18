---
name: apply-update
description: Use when the user says "update canvas" (what the portal's "newer canvas" note gives
  them to say), "update the sandbox", "apply the update", "apply the canvas update", "catch up with canvas", "migrate to the new canvas / to ajnkit", or when canvas prints `updated … to blueprint` or `from blueprint X → Y`. Gets the newest
  canvas, brings the app's assistant files up to it, applies what is new in them to the app's own
  code, and ships it when what the app runs changed — one request, every step.
---

> **An adapted app** (`.canvas/adapted`) gets only the assistant files: apply what changed outside
> AGENTS.md §1–§2 — never the page shell, the components or the blueprint's file map.

## An app made before ajnkit, or with a canvas from before 2026-10-09

**`canvas update` first** (an old canvas without `update`: the install line on the portal's Getting
started page), then `canvas app update`. What may be left:

| You see | Do |
|---|---|
| `ModuleNotFoundError: ajnkit-<name> is not installed — canvas app add <name>` in the tests | the app uses that feature: `canvas app add <name>`, then the tests again |
| `No module named 'src.utils'` (or `src.utils.<x>`) | the platform's modules are imported from ajnkit: `from ajnkit import <x>` — `canvas app update` writes the app's imports so; one it left, write so by hand |
| `kept .canvas/replaced/<file>` | step 1 below |
| the `sdk` line jumped versions | read `packages/CHANGELOG.md`'s **Your app** lines from the app's old version (step 2) |

Then the steps below as for any update — `packages/` changed, so it ships (step 6).

## Files

| What | Where |
|---|---|
| what canvas brought | `AGENTS.md`, `.agents/skills/`, `packages/` (the platform's package, ajnkit, with its `CHANGELOG.md`), `run.py`, CI — `canvas app update` writes them, and the lock (`uv.lock`) |
| what you change to match | the app's own: `score.yaml`, `src/envs.py`, `src/lib/`, `.gitignore`, `README.md` |
| a `needs` line from `canvas app update` or `validate` | a line the platform needs in the app's own file (`src/app.py`) — add it as it says, then run the tests |

## What to do

0. **Get the newest canvas**, when the user said to update canvas: `canvas update`. Already the
   newest says so; go on. Run in the app's folder, it brings the files up as well (step 1).
1. **Bring the files up.** First `git status`: uncommitted changes to the files it replaces
   (AGENTS.md, the skills, the core) are someone's work — ask the user to commit them (or commit
   with their OK). Then `canvas app update` — "already up to date" after step 0 is fine. Read
   AGENTS.md and the skills again now: they may be new.
   **A `kept .canvas/replaced/<file>` line** means that platform file had the app's own changes —
   a test database in `tests/conftest.py`, say. Compare the copy with the new file, move what is the
   app's into its own files (fixtures → `tests/fixtures.py`, code → `src/lib/`), run the tests, then
   delete the copy. Never paste it back over the platform's file: the next update replaces it again.
2. **Read what changed**: `git diff` on what it listed (AGENTS.md and the skills above all), and — when
   an `sdk` line said the platform's package moved — `packages/CHANGELOG.md` from the version the app
   had: a line under **Your app** is a change to make in the app's own code; the rest needs nothing. Make a
   short list of the new or changed rules — where something lives now, a name, a default, a step.
3. **Apply each one that touches this app**, and only those. Read the app first: a rule about a
   resource it does not declare does not apply. For example:

   | What canvas brought | What it means for this app |
   |---|---|
   | files live at `/data`, read as `envs.DATA_DIR` | an app with a volume: mount it at `/data`, add `DATA_DIR` to `src/envs.py`, `/data/` to `.gitignore`, use `envs.DATA_DIR / name` |
   | `.gitignore` leaves out `/data/`, the volume's folder at the root only | a `data/` line in `.gitignore`: make it `/data/` — `data/` leaves out every folder named data (`src/static/data`, `src/lib/data`), which then never ships; `git status` now shows those files: they are the app's, commit them |
   | a secret read with `envs.secret("KEY")` where it is used | every app whose `src/envs.py` has no `def secret(`, a secret or not yet — AGENTS.md and the skills now say `envs.secret(…)`, which otherwise raises `AttributeError`: copy `secret()` and `secret_file()` from the blueprint's `src/envs.py` (*The blueprint's lines*, below; `import os` and `from pathlib import Path` with them). A secret it reads at import (`os.environ["KEY"]`): read it with them where it is used |
   | the skills' folder is `.agents/` | `src/static/tw.css` has `@source not "../../.agent";`: make it `"../../.agents"`, or Tailwind puts the skills' pages' classes in `app.css` — then regenerate `app.css` |
   | ruff checks likely bugs and security, named (`[tool.ruff.lint] select`) | `pyproject.toml` has no `[tool.ruff.lint]` with a `select`: add the blueprint's (*The blueprint's lines*, below), its `per-file-ignores` with it, then `uv run ruff check .` and fix what it names — an `S` line is a security finding: fix it, never ignore it without the user |
   | the readiness probe answers without a thread (`async def healthz`) | `src/views.py` has `def healthz()`: make it `async def healthz()` — it does no I/O, so a busy app never makes the probe wait |
   | apps say what they are (`describe-app`) | no `canvas.dev/title` in `score.yaml`: run `describe-app` |
   | an icon and a cover, asked for once | neither in `score.yaml` and no `.canvas/pictures-asked`: ask now (`describe-app`, "The pictures") |
   | the page shell and the components (`templates/platform/`) | `base.html` becomes `{% extends "platform/shell.html" %}`; `views.py` takes `from ajnkit.web import templates` instead of its own `Jinja2Templates`; add `src/nav.py` (one line per page) and the two `PLATFORM_*_URL` lines to `src/envs.py`; `tw.css` imports `./platform/theme.css`; then remove each page's own header, footer and menu, and move its hand-written buttons, tables and fields to the components (`COMPONENTS.md`) |
   | every page light and dark, by the reader's OS or their choice in the footer (`theme.css`) | a house colour redefined in `tw.css` (`:root { --color-structure: … }`, or a `prefers-color-scheme` block beside it): it shows on a dark screen too, under dark text — make it one `light-dark(<light>, <dark>)` value (the example is in `tw.css`), a media block's value as the dark one, and say so. `text-white` on `bg-structure`/`bg-neg` in its own pages: `text-on-structure`/`text-on-neg`. Other literal colours (`white`, `black`, `gray-*`, `bg-[#…]`) in its own pages: tell the user, they stay one colour on a dark screen. Then regenerate `app.css` |
   | a page can be wide, header and footer with it (`{% block width %}wide{% endblock %}`) | a page that widened itself — a `max-w-*`, `w-screen` or negative margin around its content, or a rule on `main` in `tw.css`: remove it, give the page `{% block width %}wide{% endblock %}`, then regenerate `app.css` |
   | a skill renamed or a step moved | nothing in the code; the assistant follows the new one from now on |

4. `uv run pytest`, then `canvas validate`. Fix what they name.
5. **Tell the user in a few lines**: the canvas it moved to, the rules that applied and what you
   changed for each, and the ones that did not apply (one line).
6. **Ship it only if what the app runs changed.** Look at what changed — the files `canvas app
   update` listed, and the ones you changed in step 3:

   | Changed | Then |
   |---|---|
   | only the assistant's files — `AGENTS.md`, `CLAUDE.md`, `.agents/`, `.claude/`, `.canvas/` | **do not deploy**: the app runs exactly as before. Say so — "nothing the app runs changed, so I did not deploy" — and that the portal's "newer canvas" note stays until its next deploy |
   | anything else — the app's own code from step 3, or a platform file it runs (`packages/`, `src/templates/platform/`, `src/static/platform/`, `run.py`, `Procfile`, `pyproject.toml`, `score.yaml`) | ship it as any change ships (`deploy`): with `auto_deploy`, deploy; otherwise ask. The deploy clears the portal's "newer canvas" note: it records the canvas that shipped it |
7. With the user's OK, commit: the files canvas brought and your changes, one commit,
   "canvas: blueprint <version>".

## The blueprint's lines

What the rows above copy, as the blueprint has them. `src/envs.py`:

```python
def secret(key: str) -> str:
    """A `secret` score.yaml declares. The platform sets it once the user has (`canvas secret set`);
    not set is an error that says so, never a quiet None. On your computer, the same name in your shell."""
    if not (value := os.environ.get(key)):
        raise RuntimeError(f"the secret {key} is not set — `canvas secret set {key}`, and declare it in score.yaml")
    return value


def secret_file(key: str) -> str:
    """A secret whose value is a file (score.yaml `files:`) — azure.json, a PEM: its contents."""
    if not (path := os.environ.get(f"{key}_FILE")):
        raise RuntimeError(f"the secret file {key} is not set — declare it under a secret's files in score.yaml")
    return Path(path).read_text()
```

`pyproject.toml`, under its `[tool.ruff]`:

```toml
[tool.ruff.lint]
# Named, so every ruff version checks the same: errors (F, E9), likely bugs (B), security (S — an
# injection, a hard-coded secret, a shell call) and what blocks the server inside `async def` (ASYNC).
select = ["E9", "F", "B", "S", "ASYNC"]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101"]    # pytest's assert
"run.py" = ["S104"]     # a container listens on every address
```

## What NOT to do

- Do not undo or edit what `canvas app update` wrote — `packages/`, `uv.lock`'s ajnkit, `run.py`, the skills are the
  platform's (AGENTS.md §2). A change you need there is the platform's to make.
- Do not apply a rule the app has no use for, or rewrite working code to look like the blueprint's.
- Do not run `canvas update` (canvas itself) unless the user asked to update canvas: it replaces
  the program. Asked only to apply an update, say a newer canvas is out instead.
- Do not deploy what fails its tests or `canvas validate`.
