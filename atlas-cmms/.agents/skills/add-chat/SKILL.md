---
name: add-chat
description: >-
  Use when the app should have a chat window: "a chat", "a chatbot", "chat with it", "an assistant
  in the app", "ask it questions", "a voice assistant". Answering from documents is `add-rag`, from
  the app's own rows `ask-data` — both then come here for the window. A model call with no window
  is `request-llm`.
---

Code: `ajnkit-chat`.

## Files

| | |
|---|---|
| `score.yaml` | the `llm` resource (`request-llm`) — with `gemini-flash-lite-tts` in its models for voice |
| `src/lib/` | `assistant` — `answer()`, which yields the reply's text |
| the API | the `ask` route, and `speak` / `listen` for voice |
| the Stack table's *a chat* (AGENTS.md) | the window, once, in the layout, and the functions its routes use |

## Choosing

A chat is the platform's window, docked on every page, each answer streamed.

| Asked for | Add |
|---|---|
| a chat | `answer()`, the `ask` route, the window |
| it uses the app's data | `converse()` instead of `text()`, with the app's read API as tools: `api_tools()` / `apiTools()` (`ask-data`) |
| voice — "read the answers aloud", "let me talk to it", "speech to speech" | the `speak` and `listen` routes, and the TTS model in `llm` |
| charts, tables | `plot()`, `table()` from rows the app read (step 4) |

## What to do

0. Python or adapted app: `canvas app add chat` once.
1. The answer, API first: a function in `src/lib/` that yields its text, and a route that streams it.
   The message arrives with the turns before it, so the model reads the whole conversation:
   ```python
   # src/lib/assistant.py
   def answer(q: chat.Ask) -> Iterator[str]:          # from ajnkit import chat
       reply = client().chat.completions.create(model="gemini-flash-lite", stream=True,
                                                messages=q.messages("You help the desk with …"))
       yield from chat.text(reply)

   # src/api.py
   @router.post("/ask")
   @access.asks                                       # from ajnkit import access
   def ask(q: chat.Ask) -> StreamingResponse:
       """Answer a message, streamed."""
       return chat.stream(assistant.answer(q),
                          followups=lambda said: chat.suggest(client(), q, said))
   ```
   ```ts
   // src/lib/assistant.ts — messages, text, Ask: @ajnkit/chat
   export async function* answer(q: Ask) {
     const reply = await client().chat.completions.create({ model: "gemini-flash-lite", stream: true,
       messages: messages(q, "You help the desk with …") });
     yield* text(reply);
   }

   // src/app/api/ask/route.ts
   export async function POST(request: Request) {
     const q = await read(request);
     return q instanceof Response ? q : stream(answer(q), undefined, (said) => suggest(client(), q, said));
   }
   ```
   Mark `ask`, `speak` and `listen` as asking — `@access.asks`, or their paths in `src/asks.ts` — so
   everyone who may view the app may chat and talk, not only who may change it: none changes anything.
2. Follow-ups: `suggest()` writes two or three next questions from the answer just given, on the
   app's key; a tap asks one. Leave it out where a next question makes no sense — a form's helper,
   a one-shot summary.
3. The window, once, as *a chat* says — its title, a line on what it answers, two or three
   suggestions in the app's own words. In an Arabic app, its words in Arabic too.
   - **Voice**: give it `speak` and `listen` routes, two lines each with `speak()` and `listen()`.
     The window then offers Listen, a microphone and Talk by itself. The voice is a man's, to go with the default face; a woman's is
     `voice="female"` on `speak()`.
   - **Avatar**: the presenter (`anchor`) unless the developer picks another — `anchor-woman` or
     `anchor-bun` (give them the woman's voice), `qalam`, `khatam`, `onair`.
4. Charts and tables, only when they help:
   - A **chart** when the person asks for one ("chart it", "a graph", "a dashboard of…"), or when
     several numbers compare, trend or split. A single number, a yes or no, a short list is words.
     Yield `plot(rows, kind, title, x, y, unit)` among the text: `bar` to compare, `line` over time,
     `pie` for parts of one whole, `heatmap` across two categories (`group=`); limits in `ajnkit-chat`.
   - A **table** of rows is `table(rows, columns, title)` (50 rows).
   - The numbers in both are rows the app read, never numbers the model wrote: give the model
     `CHART_TOOL` / `TABLE_TOOL` and draw what it names (`ask-data`).
5. Sources, when the answer comes from documents: `stream(answer(q), sources)`, each `{"title": …,
   "url": …}` — the window lists them under the answer (`add-rag`).
6. Remembering the person, when they want the chat to know them next time (their language, what they
   follow): `memory_tools` and `remembered`, with a table of the app's own and every query scoped to
   the signed-in person — `ajnkit-chat`'s *Remembering the person*. Say on the page that it remembers.
7. Tests (*the tests*): the route with the model faked — what streams back, line by line. Then
   `review-security`, `canvas validate`, `canvas deploy`.

## What NOT to do

- Do not draw a chat page of your own, or return an answer as one JSON body.
- Do not keep the conversation on the server: it comes with each message, at most 20 turns. What the
  person tells it about themselves is facts, kept per person (step 6) — not the conversation.
- Do not use a browser's own speech engine or an outside speech service — `speak()` and `listen()`.
