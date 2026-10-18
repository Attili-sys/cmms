---
name: ask-data
description: >-
  Use when people should ask questions of the app's own rows in plain words: "how many orders
  last week", "which region sold most", "ask the database", "chat with our data", "text to SQL",
  "natural-language query", "an AI analyst", "a chatbot that answers from our tables". For what
  the app's text SAYS — documents, articles — it is `add-rag`.
---

Code: `ajnkit-chat`, `ajnkit-llm`.

## Files

| | |
|---|---|
| `score.yaml` | `postgres` (`request-database`) and `llm` (`request-llm`) |
| `src/lib/` | the questions the model may ask — as functions, or one `run_sql` — and `ask()` |

## Choosing

The model never gets the database. It gets **tools**, and the app runs them:

| The data | Give the model |
|---|---|
| what the app already offers — and so already guards | **the app's own API**: `api_tools(request, app)` (Python, every GET under `/api`, from its OpenAPI) or `apiTools(request, [routes])` (Next) — called **as the person asking**, so every guard applies. A question the app has no endpoint for is a new endpoint (`build-feature`), which the pages can use too |
| anything a person may see only part of, with no endpoint for it | **named queries**: a few functions you write — `sales_by_region(start, end)` — each applying the caller's scope itself; one only some may use names its rule as the tool's third item, and is offered to them alone. The model picks one and fills its arguments; it cannot reach a row the function does not return |
| every row of every table, readable by everyone who can open the app | **`run_sql`**: the model writes one `SELECT`, the app runs it read-only (below) |

**The bot reaches what the person may, nothing more** — a viewer's chat cannot read an admin's
numbers however the question is put, because the tools run as them and the ones they may not use are
never offered. When unsure, the app's own API; then named queries. They answer the questions people actually ask, and a new question is a new
function. `run_sql` reads **every table the app has** — telling the model "only use these tables" is
a request, not a boundary.

## What to do

1. `postgres` and `llm` in `score.yaml`, as their skills say.
2. Describe the tables for the model in a few lines — each name, its columns, what they mean, the
   units: `sale(day date, region text, amount numeric — QAR, tax included)`. That text is most of
   the answer's quality.
3. The tools. Named queries are ordinary functions on *the database*. `run_sql`, when the Choosing
   table allows it, is exactly this — every line is load-bearing:
   ```python
   def run_sql(sql: str) -> list[dict]:
       with engine.connect() as c, c.begin():
           c.exec_driver_sql("SET TRANSACTION READ ONLY")
           c.exec_driver_sql("SET LOCAL statement_timeout = '5s'")
           cur = c.connection.driver_connection.cursor()
           # prepare=True: Postgres takes exactly one statement. Without it `…; COMMIT; DELETE …` runs.
           cur.execute(f"SELECT * FROM ({sql.strip().rstrip(';')}) AS q LIMIT 200", prepare=True)
           cols = [d.name for d in cur.description]
           return [dict(zip(cols, r)) for r in cur.fetchall()]
   ```
   ```ts
   export async function runSql(sql: string) {
     const c = await db().$client.connect();          // the app's pg Pool (`db` from @/canvas/db)
     try {
       await c.query("BEGIN READ ONLY");
       await c.query("SET LOCAL statement_timeout = '5s'");
       // queryMode "extended": Postgres takes exactly one statement. Without it `…; COMMIT; DELETE …` runs.
       const r = await c.query({ text: `SELECT * FROM (${sql.trim().replace(/;+$/, "")}) AS q LIMIT 200`,
                                 queryMode: "extended" });
       return r.rows;
     } finally { await c.query("ROLLBACK").catch(() => {}); c.release(); }
   }
   ```
4. The answer: `converse()` (*a chat*'s module) runs the model with the tools. The tools are (the function's OpenAI schema, the function); the system prompt holds the
   table description and says: answer from the tool results only, show the numbers, say when the
   data cannot answer, and answer in words unless a chart is asked for or truly clearer.
   ```python
   TOOLS = [({"type": "function", "function": {"name": "sales_by_region", "description": "…",
                                              "parameters": {"type": "object", "properties": {}}}}, sales_by_region)]
   return chat.stream(chat.converse(client(), q.messages(SYSTEM), TOOLS), sources=[{"title": "the sale table"}],
                      followups=lambda said: chat.suggest(client(), q, said))
   ```
   ```ts
   // import { client } from "@ajnkit/llm"; import { type Tool, converse, messages, stream, suggest } from "@ajnkit/chat";
   const TOOLS: Tool[] = [[{ type: "function", function: { name: "sales_by_region", description: "…",
     parameters: { type: "object", properties: {} } } }, salesByRegion]];
   return stream(converse(client(), messages(q, SYSTEM), TOOLS), [{ title: "the sale table" }], (said) => suggest(client(), q, said));
   ```
   It offers the model `CHART_TOOL` and `TABLE_TOOL` too, and draws or tabulates only the rows the
   last tool returned; `charts=False` (Python) or `false` (the
   fifth argument) where an app has no use for one. Show the SQL or the query used under the answer
   (`sources`), so a person can check it. Never write the loop by hand.
5. Tests (*the tests*): each named query on fixture rows; for `run_sql`, that
   `"SELECT 1) x; COMMIT; DELETE FROM t; SELECT * FROM (SELECT 1"` is refused and the rows are still
   there. Then `canvas validate` and `canvas deploy` — there is no database on your computer.

The model: `gemini-flash-lite`; `gemini-flash` only if joins stay wrong once the tables are described.

## What NOT to do

- Do not run the model's SQL any other way than step 3. A read-only transaction alone is not enough:
  a second statement can `COMMIT` and then write.
- Do not use `run_sql` when people may see only some rows: the model can be talked into reading the
  rest. Named queries, with the caller's scope inside each.
- Do not give the model a tool that writes. Asking is reading; a change is a feature with a page
  and a confirm button (`build-feature`).
- Do not send the model thousands of rows — the 200 cap is there; ask it to aggregate instead.
- Do not add LangChain's SQL agent, Vanna or a text-to-SQL service: the loop above is all of it.
- Do not trust the answer as a report: it is a model reading numbers. Show the query and the rows
  it used.
