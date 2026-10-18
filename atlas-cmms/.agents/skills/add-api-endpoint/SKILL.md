---
name: add-api-endpoint
description: Use for the API step of every feature (`build-feature`), or when the user asks for an
  endpoint, a JSON route, or "an API for…".
---

## Files

| | |
|---|---|
| `src/lib/<feature>.py` | the logic the endpoint runs — write it first |
| `src/api.py` | the endpoint: Pydantic models in and out, a docstring, a status code for each failure |
| `src/app.py` | nothing — the router is already mounted at `/api` |
| `tests/` | the endpoint through `TestClient`: success, and each refusal |
| `/api/docs` | generated from the models and docstrings — check it reads right |

## Choosing

Every feature has an endpoint, even when a page is all that was asked for: the page in `views.py`
and the endpoint here both call the same `lib/` function, so they cannot disagree.

| Who calls it | Today |
|---|---|
| this app's pages | they don't — a view calls `lib/` directly |
| a person's browser, or the Swagger page | works; with `auth: sso` they are signed in, and `ajnkit.identity` says who |
| a script, another app, an internal system | with `auth: sso`, as a **service account** — `canvas sa create`, then listed in `access` like a person (`add-auth`, "Machine callers"). Never open the app with `auth: none` for it |

```python
# src/api.py — `from typing import Annotated`, `from ajnkit.db import session`, `from src.lib import notes`
class NoteIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)

class NoteOut(BaseModel):
    id: int
    text: str

@router.post("/notes", response_model=NoteOut, status_code=201)
def add_note(body: NoteIn, db: Annotated[Session, Depends(session)]) -> NoteOut:   # Annotated, as FastAPI asks
    """Keep a note."""
    return notes.add(db, body.text)          # src/lib/notes.py does the work
```

## What to do

1. The `lib/` function, if it is not there yet
2. Request and response models, then the handler — thin: validate, call `lib/`, return
3. A test per outcome; `uv run pytest`
4. Open `/api/docs` locally (`local-run`) and check the endpoint is described as intended

## What NOT to do

- Do not put logic in the handler. It belongs in `lib/`, where the view uses it too.
- Do not return bare dicts — a response model is what documents it and keeps it stable.
- Do not add a second listening port. One container, one port.
- Do not leave an endpoint open that returns data without saying so: `/api/docs` advertises it to
  everyone who can reach the app, "Try it out" included.
