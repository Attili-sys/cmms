---
name: arabic
description: Use when the app is in Arabic, or in Arabic and English — "make it Arabic", "RTL",
  "right to left", "bilingual", "an English/Arabic toggle", "Arabic search doesn't find it", "the
  numbers should be Arabic", "answer in Arabic" — or when Arabic text shows reversed, misaligned or
  unfound. A single page's layout is `add-page`; the model itself is `request-llm`.
---

## Files

| | |
|---|---|
| `base.html` (Python) / `src/app/layout.tsx` (Next) | the page's language and direction — the shell takes both |
| `src/lib/words.py` / `src/lib/words.ts` | every UI string, one small dict per language — a bilingual app only |
| `src/lib/` | the normalising function search uses, beside the query |

## Choosing

| The app is | Do |
|---|---|
| **Arabic only** | the shell in `ar` / `rtl`, every string written in Arabic in the page — no dict |
| **English, with Arabic content** (headlines, pasted articles) | keep `en` / `ltr`; each piece of content gets `dir="auto"` |
| **Both, switchable** | one dict per language, the choice in a cookie; ask first — it doubles every string |
| **Digits** | Western (`0-9`) unless the user asks for Arabic-Indic (`٠-٩`). One per app, everywhere |
| **Dates** | Gregorian. Hijri only when asked — then both, Hijri beside the Gregorian |

## What to do

1. **Direction.** An Arabic app sets it once, and the shell (header, menu, footer) mirrors with it:
   - Python, `base.html`: `{% block lang %}ar{% endblock %}{% block dir %}rtl{% endblock %}`
   - Next, `layout.tsx`: `<Shell lang="ar" dir="rtl">`
2. **Logical CSS only**: `ms-` `me-` `ps-` `pe-` `start-` `end-` `text-start` `text-end`
   `border-s` `rounded-e` — never `ml-` `mr-` `pl-` `pr-` `left-` `right-` `text-left`. An arrow
   that means "next" flips: `rtl:rotate-180`.
3. **Mixed text.** Anything whose language you do not know — a title, a name, a comment — gets
   `dir="auto"`. A name or a number set inside a sentence of the other direction is wrapped in
   `<bdi>`, so `محمد (3)` does not become `(3) محمد`. Inputs that take either: `dir="auto"` too.
4. **Font.** The shell's stack ends in `system-ui`, which draws Arabic on every OS — enough. A face
   of the app's own (IBM Plex Sans Arabic, Noto Naskh Arabic) is served by the app — the browser
   loads fonts only from it: a `.woff2` under `src/static/` with `@font-face` in `tw.css`, or
   `next/font/local` in `layout.tsx`. Never Google Fonts.
5. **Numbers and dates**, formatted in the view:
   ```python
   ARABIC_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")   # only if the app chose them
   MONTHS = ("يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر")
   f"{d.day} {MONTHS[d.month - 1]} {d.year}"
   ```
   ```ts
   new Intl.DateTimeFormat("ar-u-nu-latn", { dateStyle: "long" }).format(d);   // 8 أكتوبر 2026
   new Intl.NumberFormat("ar-u-nu-latn").format(n);   // "ar-EG" for ٠-٩; Hijri: "ar-u-ca-islamic-umalqura"
   ```
   A country tag (`ar-EG`, `ar-SA`) brings Arabic-Indic digits with it: say `-u-nu-latn` to keep `0-9`.
6. **Two languages**: the strings in `words.py` / `words.ts` — `{"en": {"save": "Save note"}, "ar":
   {"save": "حفظ الملاحظة"}}` — and a `t(key)` that falls back to English. The language comes from a
   cookie a link in the page sets, and sets `lang` and `dir` with it. No i18n library, no
   translation files. The data itself is stored once, in the language it was written in.
7. **Search.** Normalise the text and the query the same way, in one function in `src/lib/`:
   `أ إ آ ٱ → ا`, `ى → ي`, `ة → ه`, drop the tashkeel (`U+064B–U+0652`, `U+0670`) and the tatweel
   (`ـ`). Keep the normalised copy in a column of its own beside the original, and search it with
   `ILIKE` — enough for a few thousand rows. Larger: Postgres has an Arabic stemmer,
   `to_tsvector('arabic', search)` with a GIN index, so `مكتبة` finds `المكتبات`; it does not fold
   `ى`/`ي`, so normalise first anyway (`request-database`).
8. **The model.** Its system prompt says *answer in the language of the question*; write the
   prompt in English, the examples in both. Speech reads Arabic from the text (`request-llm`). The
   chat's own labels: its `words=` in the app's language (COMPONENTS.md).
9. **Look at it** right to left, in light and dark, on a phone width: the header, a form, a table,
   a number column.

## What NOT to do

- Do not add an i18n framework (`next-intl`, `babel`, gettext) or a translation service for the UI.
- Do not use left/right utilities, or `float`, or `absolute left-0`: an RTL page mirrors them wrong.
- Do not reverse Arabic strings or insert direction marks by hand to "fix" order — use `dir` and `<bdi>`.
- Do not mix Western and Arabic-Indic digits in one app.
- Do not edit the shell or the platform's components for direction or words: the shell's own
  labels (Sign out, the pager's Previous/Next) are English today — tell the user, and `report-issue`.
- Do not machine-translate the UI at runtime. The strings are written once, by you, and checked by
  the user.
