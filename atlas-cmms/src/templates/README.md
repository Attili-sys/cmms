# templates/

Jinja pages. `base.html` loads Tailwind and HTMX; everything else extends it.

**HTMX partials return HTML, not JSON.** An endpoint that a page swaps into itself belongs in
`views.py` and returns a fragment template. `api.py` is for callers that are not this app's pages.

**Read-only at runtime.** Templates ship in the image and are never written to.
