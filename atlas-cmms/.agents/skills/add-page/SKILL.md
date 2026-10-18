---
name: add-page
description: Use when the user wants a new page or screen — "add a page", "a settings page", "a
  dashboard", "a page for …", "another tab in the menu" — and for the page step of every
  `build-feature`. Adds the route, the page from the shipped components, and its line in the header.
---

Code: `ajnkit-core`.

> **An adapted app** (`.canvas/adapted`) keeps its own layout and conventions: the paths and steps
> here are the blueprint's — follow the app's own instead (AGENTS.md §1).
> **A ported app** (`.canvas/ported`, or `.canvas/legacy/`) keeps the old app's look: its pages are
> not moved into the page shell or the components unless the user asks (AGENTS.md §1).

## Files

| What | Where |
|---|---|
| the route | `src/views.py` — `templates.TemplateResponse(request, "<page>.html", {...})` |
| the page | `src/templates/<page>.html`, extending `base.html` |
| its place in the header | `src/nav.py` — one line: `("Label", "/path")`, or `("Label", "/path", "rule")` for a page only that rule may open (add-auth) |
| what it shows | from `src/lib/` — the same function the feature's endpoint calls (`build-feature`) |
| the components | `platform/ui.html` (ajnkit-core's — read it at `$(uv run python -c 'import ajnkit; print(*ajnkit.__path__)')/templates/platform/ui.html`), listed in `src/templates/platform/COMPONENTS.md` |

## What to do

1. **The route** in `src/views.py`: its data from the feature's `src/lib/` function, never from
   `/api`. Errors and outcomes go to the page as `done` / `error` for `notice`.
2. **The page** — `src/templates/<page>.html`:

   ```jinja
   {% extends "base.html" %}
   {% from "platform/ui.html" import page_header, table, link_button, notice %}
   {% block content %}
     {% call page_header("Orders", "Everything placed this week.") %}{{ link_button("New order", "/orders/new", "primary") }}{% endcall %}
     {{ notice(done) }}
     {{ table([("id", "Order"), ("by", "By")], orders, empty_text="No orders yet") }}
   {% endblock %}
   ```

   It names itself for the browser's tab — `{% block title %}Orders · {{ about().title }}{% endblock %}` —
   and starts with `page_header`; a list is `table`, a form is `form` + `field`, nothing yet is
   `empty`, numbers are `stat` in a `grid` — whatever `COMPONENTS.md` has, before any markup of
   your own.
   A page that needs the whole screen — a workspace, an editor, side-by-side panes — adds
   `{% block width %}wide{% endblock %}`, and the header and footer widen with it. Pages for reading
   (a list, a form, a detail) keep the default.
3. **The header**: add its line to `src/nav.py` — in the order the user would look for it. The
   header shows the pages once there are two, and marks the one you are on. A page inside another
   (an order's detail) gets no line: it uses `breadcrumbs`.
4. **Check it against "A page that works"** (`choose-frontend`): its empty and error states, its
   button words, its dates — and look at it in dark too (the footer's switch).
5. **A test**: the page answers 200 and shows its title (`tests/`).
6. `uv run pytest`, `canvas validate`, then ship it as `build-feature` says.

## A list with search, filters and pages

Everything that shapes the list is in the query string, so a link — or Back — gives the same view:

```python
@router.get("/orders", response_class=HTMLResponse)
def orders(request: Request, db: Annotated[Session, Depends(session)], q: str = "", status: str = "", page: int = Query(1, ge=1)):
    rows, pages = lib.orders.find(db, q, status, page)       # in lib: .where(Order.title.ilike(f"%{q}%")) if q,
    return templates.TemplateResponse(request, "orders.html",  # .limit(PER_PAGE).offset((page - 1) * PER_PAGE)
                                      {"orders": rows, "q": q, "status": status, "page": page, "pages": pages})
```
```jinja
<form method="get" action="/orders" hx-get="/orders" hx-trigger="input changed delay:300ms"
      hx-target="#results" hx-select="#results" hx-swap="outerHTML" hx-push-url="true" class="mb-4 grid gap-3 sm:grid-cols-2">
  {{ field("q", "Search", value=q) }}{{ select("status", "Status", [("", "Any"), ("open", "Open")], selected=status) }}
</form>
<div id="results" aria-live="polite">
  {{ table([("id", "Order"), ("title", "Title")], orders, empty_text="No orders match") }}
  {{ pager(page, pages, "?" ~ {"q": q, "status": status} | urlencode ~ "&page={n}") }}
</div>
```

The page renders whole; htmx swaps only `#results`, and without JavaScript the form still works.
`ILIKE` is enough for a few thousand rows — a bound parameter, never formatted into the SQL; past
that, full-text search (`request-database`; Arabic: `arabic`). Twenty-five a page.

## A chart

COMPONENTS.md has no chart for a page. The platform's charts are the chat's — `chat.plot()` draws
one in an answer from rows (`ajnkit-chat`); `chart()` in ajnkit-core's `static/platform/chat.js` is the
chat's own, not for pages. So, simplest first:

| To show | Use |
|---|---|
| a few numbers | `stat` in a `grid` |
| a few values compared | a `table` with a bar in a cell: `<div class="h-2 rounded bg-structure" style="inline-size: {{ pct }}%">` — `pct` from the view |
| a trend, many points, hover | ask first: one library, its file saved under `src/static/` (no CDN), started from a script file of the app's |

## What NOT to do

- Do not draw a header, a footer, a nav or a menu in the page — the shell (`base.html`) has them.
- Do not make a page that does not extend `base.html`: it would lose the header, Sign out and the footer.
- Do not add a second menu or a sidebar of your own: the pages are `src/nav.py`.
- Do not make a chat page — bubbles, a message box — of your own: a chat is the platform's chat
  component, docked over every page (`add-chat`).
- Do not widen a page yourself (a `max-w-*`, `w-screen` or negative margin around the content, a
  rule on `main`): the header and footer stay narrow above it. `width` widens all three.
- Do not edit `src/templates/platform/` or the platform's package (`packages/`). One of ours that does not fit this page: your own in
  `src/templates/components.html`, imported here instead (`choose-frontend`, "Ours, and yours").
- More than five or six top-level pages: ask whether some are inside others (`breadcrumbs`, `tabs`).
