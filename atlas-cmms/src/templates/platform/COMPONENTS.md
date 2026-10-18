# The components — every app's, shipped by canvas

`platform/ui.html`, in ajnkit-core (`uv run python -c "import ajnkit; print(*ajnkit.__path__)"`), holds them; `canvas app update` brings new ones and fixes. **Build
every page from these**. Each is a Jinja macro:

```jinja
{% extends "base.html" %}
{% from "platform/ui.html" import page_header, card, table, link_button %}
{% block content %}
  {% call page_header("Notes", "Everything the desk wrote down today.") %}{{ link_button("New note", "/notes/new", "primary") }}{% endcall %}
  {{ table([("title", "Title"), ("by", "By")], notes, empty_text="No notes yet") }}
{% endblock %}
```

**Ours, and yours.** `src/templates/platform/` is ours: never edit it — `canvas app update` replaces
it, and every other page uses it. Start from ours: one that does the job is used as it is. When one
does not fit a page — it must look or behave differently there — make your own in
`src/templates/components.html` (a copy of ours as a start, under a name of its own) and import yours
in that page instead. Ours stays as it is everywhere else.

One you need that is missing goes in `src/templates/components.html` too, built
from these and extracted on its third use (AGENTS.md §5) — and say it might belong here.

**Colours and spacing** are Tailwind's utilities (`mt-4`, `grid-cols-2`, `md:flex`) and the house colours,
`src/static/platform/theme.css` — `bg-surface`, `text-ink`, `text-muted`, `border-rule`, `bg-structure`,
`text-pos`, `text-neg` and the rest it defines: never a colour name of your own (`text-strong`,
`bg-primary` are nobody's). `src/static/app.css` is made from your pages (src/static/README.md).

The page itself — header, your pages, who is signed in and Sign out, the footer — is the shell
(`platform/shell.html`), which `base.html` brings: a page never draws any of it.
An Arabic app sets the page's language and direction there, in `base.html`:
`{% block lang %}ar{% endblock %}{% block dir %}rtl{% endblock %}`.

## Actions

| Component | For | Call |
|---|---|---|
| `button` | an action: submit a form, or post by itself (HTMX). `kind` primary (one per view), secondary, danger | `{{ button("Save") }}` · `{{ button("Delete", kind="danger", post="/notes/3/delete", confirm="Delete this note?") }}` |
| `link_button` | going to another page, looking like a button | `{{ link_button("New note", "/notes/new", "primary") }}` |
| `icon_button` | a small square action with a name for screen readers | `{{ icon_button("×", "Close") }}` |

## Layout

| Component | For | Call |
|---|---|---|
| `page_header` | the top of every page: title, one line, its actions on the right | `{% call page_header("Notes", "All of them") %}…actions…{% endcall %}` |
| `card` | a white box for one thing — a form, a list, a summary | `{% call card("Today") %}…{% endcall %}` |
| `section` | a titled part of a page, without a box | `{% call section("Settings") %}…{% endcall %}` |
| `grid` | cards side by side, as many as fit | `{% call grid() %}{{ stat(…) }}{{ stat(…) }}{% endcall %}` |
| `tabs` | sections of one page, each its own address | `{{ tabs([("open", "Open", "?tab=open"), ("done", "Done", "?tab=done")], tab) }}` |

## Forms

| Component | For | Call |
|---|---|---|
| `form` | a form that posts to the app (without a full reload, through the shell's hx-boost); `upload=True` for a file | `{% call form("/notes") %}…fields…{{ button("Save") }}{% endcall %}` |
| `field` | a labelled input, its hint — or the view's error | `{{ field("email", "Email", type="email", required=True, error=errors.email) }}` |
| `select` | one choice from a list | `{{ select("team", "Team", [("a", "Alpha"), ("b", "Beta")], selected=team) }}` |
| `textarea` | several lines of text | `{{ textarea("body", "Note", rows=5) }}` |
| `choice` | one answer of a few, each shown in full — a quiz question, a poll, a rating. Each question its own `name`, so each is answered apart; never raw `<input type="radio">` | `{{ choice("q-" ~ q.id, q.text, [("A", "kubelet"), ("B", "etcd")], required=True) }}` |
| `checkbox` | a yes or no | `{{ checkbox("notify", "Email me when it is done") }}` |
| `file_input` | a file to upload — the view saves it to the volume, `envs.DATA_DIR`. `large=True`: to 2 GB, sent in pieces before the form, which carries the kept name — the view takes it with `media.uploaded(form["clip"])` | `{{ file_input("clip", "Video", accept="video/*") }}` |

## Data

| Component | For | Call |
|---|---|---|
| `table` | rows of things; says `empty_text` when there are none. A cell's own markup: `{% call(row, key) table(cols, rows) %}…{% endcall %}` — the call draws **every** cell, so it ends `{% else %}{{ row[key] }}{% endif %}` for the columns it leaves as they are | `{{ table([("title", "Title")], notes, empty_text="No notes yet") }}` |
| `stat` | one number and what it is | `{{ stat("Open orders", 12, "3 since this morning") }}` |
| `badge` | a small label — a tag, a kind, a count; `tone` neutral, good, warn, bad | `{{ badge("draft") }}` |
| `pill` | a state, with its dot | `{{ pill("Done", "good") }}` |

## Feedback

| Component | For | Call |
|---|---|---|
| `notice` | what an action did, or why it did not, at the top of the page it came back to | `{{ notice(done) }}` · `{{ notice(error, "error") }}` |
| `empty` | nothing yet — and what to do about it | `{% call empty("No notes yet", "Write the first one.") %}{{ link_button(…) }}{% endcall %}` |
| `spinner` | shown while an HTMX request runs (`hx-indicator="#id"`) | `{{ spinner("saving") }}` |
| `confirm` | asking before something that cannot be undone. `cancel` names its Cancel button — an Arabic app: `cancel="إلغاء"` | `{% call confirm("delete-3", "Delete this note?") %}…the form that deletes…{% endcall %}`, opened by a button with `data-dialog-open="delete-3"` — never an `onclick` |

## Chat

| Component | For | Call |
|---|---|---|
| `chat` | a conversation with the app — a model answering from its data — as Messenger draws one: a round button at the bottom corner opens a window docked there, which minimises, maximises and closes; the whole screen on a phone. The answer streams in from `post`, the app's endpoint (`ajnkit.chat` `stream()`), with any chart the app drew from its rows (`plot()`: bar, line, pie or heat map) or table (`table()`, drawn from Markdown); the conversation stays in the person's tab and goes with each message; questions to ask next, as chips under the answer, from `stream(…, followups=…)`; with `speak` and `listen` routes, Listen on each answer, a microphone in send's place (held or tapped) and Talk, a conversation by voice. Talk's face is the app's choice, `avatar="khatam"`: `anchor`, a presenter (the default), `anchor-woman` or `anchor-bun` (with `voice="female"` for `speak`), `qalam`, `khatam` or `onair`. One a page, in the shell's `docked` block — `base.html`'s for every page. Mark its routes `@access.asks` — `post`, `speak` and `listen` — so everyone who may view the app may chat and talk, not only who may change it. `words={…}` names the window's own labels in an Arabic app (`arabic`). | `{% block docked %}{{ chat("/api/ask", "Ask the notes", "Answers from what the desk wrote", suggestions=["Summarise today"]) }}{% endblock %}` |

## Navigation

| Component | For | Call |
|---|---|---|
| `breadcrumbs` | where this page sits, for a page inside another | `{{ breadcrumbs([("Notes", "/notes"), ("Today", "")]) }}` |
| `pager` | previous and next, for a long list the view pages | `{{ pager(page, pages, "?page={n}") }}` |

The app's own pages, in the header, are `src/nav.py` — not a component: one line per page.
