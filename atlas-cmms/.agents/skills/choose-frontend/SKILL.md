---
name: choose-frontend
description: Use once, before an app's first page — when it has no pages yet and needs a user
  interface — or when the user asks for React, Next.js or a SPA. Every page after the first is
  `add-page`, not this.
---

> Adapted or ported app: AGENTS.md §1 first.

## Files

| | |
|---|---|
| `platform/shell.html` (in ajnkit-core) | **the page shell — the platform's.** Never edit it |
| `platform/ui.html` (in ajnkit-core) | **the components — the platform's**, shipped by canvas: buttons, cards, tables, forms, notices… Listed, with a call each, in `src/templates/platform/COMPONENTS.md` |
| `src/templates/base.html` | every page extends it; it brings the shell. Yours: add to `<head>` here |
| `src/templates/<page>.html` | a page: `content` only, built from the components |
| `src/templates/components.html` | your own components, when one is missing — built from the platform's |
| `src/nav.py` | the app's pages, in the header's order — one line each |
| `src/views.py` | the routes; `from ajnkit.web import templates` |
| `src/static/tw.css` | Tailwind source — edit this; `app.css` is generated from it |

## Choosing

**Jinja, with HTMX, inside the platform's shell.** It behaves like a single-page app — the shell's
`hx-boost` swaps each page without a full reload — and stays one Python process. A React UI is the
other stack — `canvas app create --stack next` — chosen when the app is made, not added to this one;
a separate SPA is not available. Say so plainly when asked, and build it this way.

| The page needs | Use |
|---|---|
| a list, a form, a summary | **the components** — `table`, `form` + `field`, `card`, `stat` (`COMPONENTS.md`) |
| to update part of a page without a reload | **HTMX** — `hx-get`, `hx-post` into a partial (below) |
| a toggle, tabs, a dialog | **the components** — `tabs`, `confirm`; `<details>` for a fold |

## What to do

1. A page: `add-page` — its route, its template from the components, its line in `src/nav.py`.
2. Build from the components: `{% from "platform/ui.html" import page_header, card, table %}`.
   **Look in `COMPONENTS.md` first**, and use ours as it is when it does the job.
3. **Ours, and yours.** Never edit the shell or the components (`canvas app update` replaces them).
   One that must differ on a page: a copy under a new name in `src/templates/components.html`,
   imported there. A missing one goes there too — tell the user it may belong in the shared set.
4. The house colours work in your own markup too: `bg-structure`, `text-muted`, `border-rule`.
   An app's own colours change in one place — a `:root { --color-structure: …; }` block at the end
   of `tw.css` — and the shell, components and pages follow.
   **Every page is light and dark** — the reader's OS, or what they chose in the footer: each house
   colour holds both values, so a page drawn only in them needs nothing more. A colour of the app's
   own holds both too: `--color-structure: light-dark(#7A2C20, #A04A38)` (the example is in
   `tw.css`). Its dark value is a mid-tone that white text reads on (4.5:1 or more), never a
   pastel: a pastel button glares on a dark page. Text on `bg-structure` is `text-on-structure`, on
   `bg-neg` `text-on-neg` — never `text-white`.
5. Regenerate CSS after using a new utility class in your templates:
   `tailwindcss -i src/static/tw.css -o src/static/app.css --minify` (the Tailwind CLI: `brew install
   tailwindcss` on a Mac, or its standalone download) — the components' styles are
   already shipped (ajnkit-core's `static/platform/platform.css`).

## HTMX: three patterns, and the trap

| Want | Do |
|---|---|
| A part that keeps itself current | The partial's own root carries `hx-get` (its URL), `hx-trigger="every 15s"` and `hx-swap="outerHTML"`; the view returns that same partial. Each refresh replaces it, so the server picks the next interval from the state — `every 3s` while something is still moving |
| Other places that show the same state | Carry them in that refresh: `<span hx-swap-oob="innerHTML:[data-x='…']">`. A selector, not an id, when the same thing is drawn twice (a desktop and a phone menu). Send only what the page has — an out-of-band swap with no target is an error in the console |
| Load a part on a click | `hx-get` and `hx-target` on the link, its `href` the same page rendered whole — so it also works without JavaScript |

**`hx-swap` and `hx-target` are inherited.** A link inside a part that swaps `outerHTML` swaps
`outerHTML` too, and replaces its target instead of filling it. Set both on the link itself.

## A page that works

The components carry the look; these carry the rest. Each is one line to check before shipping.

| | Rule |
|---|---|
| **Every state** | A page shows each of its states: loading, empty (`empty`, with the one action that fills it), error (`notice(error, "error")`, saying what to do next) and full. Never a blank region |
| **One main action** | One `primary` per view. Order: `page_header`, then `notice`, then what the person came for, then the rest |
| **Forms** | Validate in the view; give each problem back in its field's `error=` and one `notice` at the top, with what was typed kept. Never disable Save to block an incomplete form — let it submit and say what is missing |
| **Words** | A button is a verb and its object, in sentence case: *Save note*, *Delete story* — never *OK*, *Submit*, *Yes*. A confirm repeats the action. One word for one thing across the app. No "click here" |
| **Table or cards** | Things compared on the same fields: `table`. A few things, each read alone: `card`s in a `grid`. On a phone, a table of more than five columns drops the minor ones |
| **Numbers and dates** | Format them in the view, for the reader: `12 Oct 2026, 14:05`, or *in 3 hours* with the exact time in `title`. Digits for counts, a space before units (`10 MB`), `tabular-nums` on a column of figures |
| **Arabic** | Text that may be Arabic — a headline, a pasted article — gets `dir="auto"`. An Arabic app sets `{% block lang %}ar{% endblock %}{% block dir %}rtl{% endblock %}` in `base.html`. Spacing uses start/end, never left/right: `ms-` `me-` `ps-` `pe-` `text-start` |
| **HTMX swaps** | A part that changes in place is announced: it sits in an element with `aria-live="polite"`, or returns a `notice` (already announced). A request that can take over a second has a `spinner`, and its button keeps its label |
| **Nothing jumps** | Reserve the space for what loads later: an image has `width` and `height`; an `every Ns` partial keeps its shape |
| **Spacing** | The components' own. Groups are `section`s or `card`s, never extra margins |
| **Works in dark** | Switch the footer to dark and look: cards stand apart from the page, an inset (`bg-sunken`) sits darker than its card, muted text is dimmer than body, and no button glares. Looking right in light does not mean it does in dark |

## What NOT to do

- Do not draw a header, a footer, a nav or a user menu in a page — the shell has them.
- Do not widen a page past the shell yourself: `{% block width %}wide{% endblock %}` widens the
  header, the page and the footer together (`add-page`).
- Do not add a bundler, a second CSS framework, or a script from a CDN.
- Do not use `ml-`, `mr-`, `left-`, `right-` or `text-left`: an Arabic page mirrors them wrong.
- Do not use `white`, `black`, `gray-*` or a hex colour: a dark screen does not change them.

