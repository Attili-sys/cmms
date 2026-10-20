"""HTML pages, and HTMX partials. Each page's data comes from its feature's function in src/lib/ —
the same one its endpoint in api.py calls; a view never calls /api (AGENTS.md §2).

`/healthz` lives here and **must keep matching `route.params.path` in
score.yaml** — a mismatch is `probe.path`: the pod never becomes ready, and the deploy
stops at sync. tests/test_health.py catches it in a second instead.

Templates come from src/templates/ — each page extends base.html, which brings the platform's
shell (header, Sign out, footer) — through `ajnkit.web.templates`; assets from src/static/.
Both are read-only at runtime: an upload goes to a `volume`, never to static/.
"""

import os
from pathlib import Path
import re

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

router = APIRouter()

UI = Path(__file__).resolve().parent / "static" / "ui"
_HASHED_ASSET_RE = re.compile(
    r"^(js|css)/([A-Za-z0-9_-]+)\.[0-9a-f]{6,12}(\.(?:chunk\.)?(?:js|css))$"
)


class ResilientStaticFiles(StaticFiles):
    """Falls back to the active hashed bundle when a browser with a stale pre-no-cache
    index.html requests a superseded main.<old>.js/.css or <chunk>.<old>.chunk.js/.css."""

    def lookup_path(self, path: str) -> tuple[str, os.stat_result | None]:
        full_path, stat_result = super().lookup_path(path)
        if stat_result is not None:
            return full_path, stat_result
        m = _HASHED_ASSET_RE.match(path)
        if m and self.directory:
            subdir, prefix, suffix = m.groups()
            target_dir = Path(self.directory) / subdir
            if target_dir.is_dir():
                matches = sorted(target_dir.glob(f"{prefix}.*{suffix}"))
                if matches:
                    fallback = matches[0].resolve()
                    try:
                        return str(fallback), os.stat(fallback)
                    except OSError:
                        pass
        return full_path, stat_result


@router.get("/healthz")
async def healthz() -> dict:
    """Readiness. Must match route.params.path in score.yaml. `async`: it does no I/O, so it never
    waits for one of the threads the app's other routes are using."""
    return {"ok": True}


NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}


def cmms_page(path: str = "index.html"):
    """The existing CMMS screens. A missing build still answers, so the readiness page stays up."""
    root = UI.resolve()
    candidate = (UI / path).resolve()
    if str(candidate).startswith(str(root)) and candidate.is_file():
        headers = NO_CACHE_HEADERS if candidate.name in {"index.html", "runtime-env.js"} else None
        return FileResponse(candidate, headers=headers)
    index = UI / "index.html"
    if index.is_file() and path != "index.html":
        return FileResponse(index, headers=NO_CACHE_HEADERS)
    return HTMLResponse("<p>Powered by Canvas</p>")


@router.get("/")
def index():
    return cmms_page()
