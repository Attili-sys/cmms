"""HTML pages, and HTMX partials. Each page's data comes from its feature's function in src/lib/ —
the same one its endpoint in api.py calls; a view never calls /api (AGENTS.md §2).

`/healthz` lives here and **must keep matching `route.params.path` in
score.yaml** — a mismatch is `probe.path`: the pod never becomes ready, and the deploy
stops at sync. tests/test_health.py catches it in a second instead.

Templates come from src/templates/ — each page extends base.html, which brings the platform's
shell (header, Sign out, footer) — through `ajnkit.web.templates`; assets from src/static/.
Both are read-only at runtime: an upload goes to a `volume`, never to static/.
"""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter()

UI = Path(__file__).resolve().parent / "static" / "ui"


@router.get("/healthz")
async def healthz() -> dict:
    """Readiness. Must match route.params.path in score.yaml. `async`: it does no I/O, so it never
    waits for one of the threads the app's other routes are using."""
    return {"ok": True}


def cmms_page(path: str = "index.html"):
    """The existing CMMS screens. A missing build still answers, so the readiness page stays up."""
    root = UI.resolve()
    candidate = (UI / path).resolve()
    if str(candidate).startswith(str(root)) and candidate.is_file():
        return FileResponse(candidate)
    index = UI / "index.html"
    if index.is_file() and path != "index.html":
        return FileResponse(index)
    return HTMLResponse("<p>Powered by Canvas</p>")


@router.get("/")
def index():
    return cmms_page()
