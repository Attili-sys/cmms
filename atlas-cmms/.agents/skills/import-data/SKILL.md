---
name: import-data
description: >-
  Use when data from a file should end up in the app's database: "import this CSV", "load the
  spreadsheet", "upload the Excel", "seed the table", "bring in the list", "migrate our data from the
  sheet", "bulk upload" — or when the user hands over a .csv or .xlsx and asks for it in the app.
  Making the table itself is `request-database`; files people keep as files (images, PDFs, video) are
  `request-volume`.
---

## Files

| | |
|---|---|
| *the schema* (AGENTS.md's Stack table) | the table the rows go into, with a **unique key** column |
| `db/migrations/NNN_seed_<what>.sql` | small, fixed data only — written once, by a script, never edited |
| `src/lib/` | `import_csv` — parse, check, upsert — for anything else |
| *the API* and a page | the endpoint and the upload page that call it, behind a rule (`add-auth`) |

## Choosing

There is **no database on your computer**, and no `canvas` command that runs SQL or opens a shell on
the deployed one. Data reaches it one of two ways: a migration, applied at deploy, or the app itself.

| The data is | Use |
|---|---|
| a short, fixed list the app needs to work — regions, categories, desks; a few hundred rows | **a seed migration** |
| bigger, personal, or changes — staff, contacts, a monthly export | **an import page** in the app |
| re-sent every week or month | the import page; the same file twice updates the rows, never doubles them |
| a live system — another app, an API, a shared sheet | not an import: fetch it (`call-api`), on a schedule if it changes (`add-job`) |

Ask for **CSV UTF-8**. In Excel: *File → Save As → "CSV UTF-8 (Comma delimited)"*. Plain "CSV" from
Excel is not UTF-8 — Arabic arrives as `?` or garbage — and a `.xlsx` needs a library to read (What
NOT to do).

## What to do

1. **Look at the file first** — the header row, ten rows, the row count, and every column that holds
   a date, a number or an ID. Decide, and say:
   - **the key** — the column that names a row (`code`, `email`, `employee_id`): re-importing
     matches on it. No such column: ask; never the row number.
   - **the date format** — `2026-10-08`, `08/10/2026` or `10/08/2026`. Ask when it could be either;
     never a parser that guesses.
   - **IDs and phone numbers are text** — Excel has already dropped leading zeros and turned long
     numbers into `1.23E+15` if the column was not text before it was saved; check, and ask for the
     file again if so.
2. **The table**, in *the schema*, its key `unique`, then `canvas db revision "add <table>"`
   (`request-database`):
   ```python
   class Item(Base):
       __tablename__ = "item"
       id: Mapped[int] = mapped_column(primary_key=True)
       code: Mapped[str] = mapped_column(unique=True)        # the key the file is matched on
       name: Mapped[str]
       starts_on: Mapped[date | None]
       amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
   ```
   ```ts
   export const items = pgTable("items", {
     id: serial("id").primaryKey(),
     code: text("code").notNull().unique(),                // the key the file is matched on
     name: text("name").notNull(),
     startsOn: date("starts_on"),
     amount: numeric("amount", { precision: 12, scale: 2 }),
   });
   ```

### A seed migration — a short, fixed list

3. After the table's migration, write the next `db/migrations/NNN_seed_<what>.sql` **with a short
   script**, never by hand: one `INSERT`, every value quoted (`'` doubled), an empty cell `NULL`:
   ```sql
   -- seed regions, from regions.csv
   INSERT INTO region (code, name) VALUES
     ('doha', 'الدوحة'),
     ('cairo', 'القاهرة')
   ON CONFLICT (code) DO NOTHING;
   ```
   `ON CONFLICT DO NOTHING` so a row someone already added does not fail the deploy. Saved as UTF-8 —
   `canvas validate` refuses anything else. Nothing to `--record`: the schema did not change, and the
   next `canvas db revision` numbers past it.
4. `canvas validate`, `canvas deploy`. The platform runs it once, before the new version starts.

### An import page — anything else

3. `import_csv` in `src/lib/` — decode, find the delimiter, check every row, then upsert them all in
   one transaction, or none:
   ```python
   import csv, io
   from datetime import datetime
   from decimal import Decimal
   from sqlalchemy.dialects.postgresql import insert

   MAX_BYTES, MAX_ROWS, BATCH = 10 << 20, 50_000, 1000
   DATE_FORMAT = "%d/%m/%Y"                       # the file's, as step 1 decided

   def import_csv(db, data: bytes) -> dict:
       try:
           text = data.decode("utf-8-sig")         # -sig: drops the BOM Excel writes first
       except UnicodeDecodeError:
           return {"imported": 0, "errors": ["Not UTF-8 — save it from Excel as “CSV UTF-8” and upload it again."]}
       first = text.partition("\n")[0]
       delimiter = ";" if first.count(";") > first.count(",") else ","    # Excel in some languages writes ;
       rows, errors = {}, []
       for n, r in enumerate(csv.DictReader(io.StringIO(text), delimiter=delimiter), start=2):
           try:
               rows[r["code"].strip()] = {      # by key: the same code twice keeps the last
                   "code": r["code"].strip(), "name": r["name"].strip(),
                   "starts_on": datetime.strptime(d, DATE_FORMAT).date() if (d := r["starts_on"].strip()) else None,
                   "amount": Decimal(a.replace(",", "")) if (a := r["amount"].strip()) else None,
               }
           except (KeyError, ValueError, ArithmeticError) as e:
               errors.append(f"row {n}: {e}")
       if len(rows) > MAX_ROWS:
           errors.insert(0, f"{len(rows)} rows — at most {MAX_ROWS}; split the file")
       if errors:
           return {"imported": 0, "errors": errors[:20]}
       values = list(rows.values())
       for i in range(0, len(values), BATCH):
           stmt = insert(Item).values(values[i:i + BATCH])
           db.execute(stmt.on_conflict_do_update(index_elements=[Item.code],
                      set_={c: stmt.excluded[c] for c in ("name", "starts_on", "amount")}))
       db.commit()
       return {"imported": len(values), "errors": []}
   ```
   ```ts
   import { parse } from "csv-parse/sync";        // npm install csv-parse
   import { sql } from "drizzle-orm";

   export const MAX_BYTES = 10 << 20;
   const MAX_ROWS = 50_000, BATCH = 1000;
   const DATE = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/;  // dd/mm/yyyy — the file's, as step 1 decided

   export async function importCsv(data: ArrayBuffer) {
     let text: string;
     try {
       text = new TextDecoder("utf-8", { fatal: true }).decode(data);
     } catch {
       return { imported: 0, errors: ["Not UTF-8 — save it from Excel as “CSV UTF-8” and upload it again."] };
     }
     const first = text.slice(0, text.indexOf("\n"));
     const delimiter = first.split(";").length > first.split(",").length ? ";" : ",";
     const records: Record<string, string>[] = parse(text, { bom: true, columns: true, delimiter, trim: true, skip_empty_lines: true });
     const rows = new Map<string, typeof items.$inferInsert>(), errors: string[] = [];
     records.forEach((r, i) => {
       const m = DATE.exec(r.starts_on ?? "");
       const amount = (r.amount ?? "").replace(/,/g, "").replace(/[٠-٩]/g, (d) => String(d.charCodeAt(0) - 0x660));
       if (!r.code || !r.name || (r.starts_on && !m) || (amount && Number.isNaN(Number(amount)))) {
         errors.push(`row ${i + 2}: ${JSON.stringify(r)}`);
         return;
       }
       rows.set(r.code, { code: r.code, name: r.name,      // by key: the same code twice keeps the last
         startsOn: m ? `${m[3]}-${m[2].padStart(2, "0")}-${m[1].padStart(2, "0")}` : null,
         amount: amount || null });
     });
     if (rows.size > MAX_ROWS) errors.unshift(`${rows.size} rows — at most ${MAX_ROWS}; split the file`);
     if (errors.length) return { imported: 0, errors: errors.slice(0, 20) };
     const values = [...rows.values()];
     await db().transaction(async (tx) => {
       for (let i = 0; i < values.length; i += BATCH)
         await tx.insert(items).values(values.slice(i, i + BATCH)).onConflictDoUpdate({ target: items.code,
           set: { name: sql`excluded.name`, startsOn: sql`excluded.starts_on`, amount: sql`excluded.amount` } });
     });
     return { imported: values.length, errors: [] };
   }
   ```
   Python's `Decimal` and `int` read Arabic-Indic digits (`١٢`) as they are; JavaScript's `Number`
   does not — hence the replace. Dates as Excel serial numbers (`45938`) mean the column was not
   formatted as a date: ask for the file again rather than converting.
4. **Who may import** — a rule, in `score.yaml` with the owner's email, named in the code
   (`add-auth`):
   ```yaml
         access:
           rules:
             import: ["owner@aljazeera.net"]
   ```
5. **The endpoint and the page.** Python: a page with `form("/import", upload=True)` and
   `file_input("file", "CSV file", accept=".csv,text/csv")`; its view, and its `/api/import` twin
   (`add-api-endpoint`), each `@require("import")`, read the upload with
   `file.file.read(MAX_BYTES + 1)` — over `MAX_BYTES` is refused — and call `import_csv`. Next.js:
   a route, `src/app/api/import/route.ts`:
   ```ts
   export async function POST(request: Request) {
     await permit("import");
     if (Number(request.headers.get("content-length")) > MAX_BYTES)
       return Response.json({ imported: 0, errors: ["Over 10 MB — split the file."] }, { status: 413 });
     return Response.json(await importCsv(await request.arrayBuffer()));
   }
   ```
   and a small client component on the page that sends the file to it —
   `fetch("/api/import", { method: "POST", body: file })` — never in a form post or server action,
   as AGENTS.md's *uploads* says. Show the result in a `Notice`: how many rows, or the first errors
   with their row numbers.
6. Tests (*the tests*) for `import_csv`: a BOM, `;` as the delimiter, an Arabic name, a bad date (its
   row number in the errors, nothing written), and the same file twice (the count does not change).
   The database is not on your computer: the tests that write fake it, as `write-tests` says.
7. `canvas validate`, `canvas deploy`; then the user imports the real file on the deployed app.

## What NOT to do

- Do not put personal data — staff, contacts, salaries — in a migration. It is in git for good, for
  everyone who can read the repository.
- Do not put more than a few hundred rows in a migration. Every migration the app has ever had counts
  against one 1 MiB limit, forever; past it, the app cannot deploy until they are squashed.
- Do not edit a seed migration that has run to change the data — the platform refuses it, and a roll
  back does not take its rows out either. A change is the next migration, or the import page.
- Do not import with plain `INSERT` — the second upload doubles every row. Upsert on the key.
- Do not import some rows and skip the bad ones silently. All or nothing, with the row numbers of
  what was wrong.
- Do not read `.xlsx` unless the user cannot export CSV. If they cannot: `openpyxl` (`read_only=True`)
  or `exceljs` — never the `xlsx` package on npm, which is years out of date with known
  vulnerabilities.
- Do not parse dates with a guessing parser (`dateutil.parser`, `new Date("08/10/2026")`) — 8 October
  becomes 10 August without an error.
- Do not leave the import page open to everyone who can open the app. A rule, as in step 4.
