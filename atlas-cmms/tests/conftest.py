"""What the platform injects, for tests: `src/envs.py` reads PORT at import, and the platform always
sets it, so a test run sets it too — `uv run pytest` works with nothing exported.

This file is the platform's: `canvas app update` replaces it whole. The app's own fixtures — a test
database, sample data, a signed-in client — go in tests/fixtures.py, which is the app's and loaded
here, so an update never takes them away."""

import importlib.util
import os
from pathlib import Path

os.environ.setdefault("PORT", "8080")

# By its path, not `import tests.fixtures`: a package named `tests` elsewhere on the path would win.
_mine = Path(__file__).with_name("fixtures.py")
if _mine.is_file():
    _spec = importlib.util.spec_from_file_location("app_fixtures", _mine)
    _module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_module)
    globals().update({k: v for k, v in vars(_module).items() if not k.startswith("_")})


def _serve() -> None:
    """The app as run.py serves it — the platform's styles and scripts, its uploads, the access checks —
    so a test sees what a visitor does, whatever src/app.py has (ajnkit.web.platform). Imported here,
    after PORT is set: src/envs.py reads it at import."""
    from ajnkit import web

    try:
        from src.app import app
    except ImportError as e:     # a feature's module without its package: says `canvas app add <it>`
        web.missing(e)
        raise

    web.platform(app)


_serve()
