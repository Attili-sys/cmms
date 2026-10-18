---
name: add-secret
description: Use when the app needs a credential — an API key, a token, a webhook secret, a Google
  service account, AWS or S3 keys for an outside bucket, a partner's password — or when `canvas deploy`
  says `secret.missing`.
---

## Files

| | |
|---|---|
| `score.yaml` | declare the key **names** under a `secret` resource — never a value |
| the Stack table's *a secret* (AGENTS.md) | how this app reads each one — once, in one place |

## Choosing

1. **Check it really is a credential.** Configuration — a group name, a feature flag, a URL — is a
   plain `containers.app.variables` entry, not a secret
2. **An AI model key is never needed**, for chat or for text to speech: `type: llm` gives the app its
   own (`request-llm`) — not an ElevenLabs, Azure Speech or Google TTS key either
3. Anything else that would let someone act as the app — a key, a token, a password — is a `secret`

## What to do

1. Declare the names in `score.yaml`. One `secret` resource holds them all:
   ```yaml
   resources:
     creds:
       type: secret
       params:
         keys: [PARTNER_API_KEY]
   ```
   Names are `UPPER_SNAKE_CASE`, and not one the platform sets (`DATABASE_URL`, `OPENAI_*`, `PORT`, …).
   **A credential that is a file** — `azure.json`, a Google service-account JSON, a PEM key — goes
   under `files:` instead, never base64'd into a key:
   ```yaml
       params:
         keys: [PARTNER_API_KEY]
         files: [AZURE_CREDENTIALS]
   ```
   The app gets it read-only at `/secrets/AZURE_CREDENTIALS`, and `AZURE_CREDENTIALS_FILE` holds
   that path — hand it to the SDK that wants a path (`AZURE_AUTH_LOCATION`,
   `GOOGLE_APPLICATION_CREDENTIALS`) or open it
2. Read it as the Stack table's *a secret* says — a key by its name, a file by the path the platform
   gives in `<KEY>_FILE` — where the code uses it, never into a constant at import: the tests, and a
   pair's `canvas validate` and `canvas api pull`, import the app with no secret set. A test of code
   that reads one sets it itself (`monkeypatch.setenv`, `vi.stubEnv`)
3. `canvas deploy`. An app is **never deployed without its secrets**: it builds, then waits. Run
   by you (no terminal), it stops with **exit 62** — `secret.missing`, naming each key — and nothing
   is deployed; the old version, if any, keeps running. That is your cue for step 4, not an error
4. **Guide the user to set each value themselves**, and wait for them — either way works, and both are theirs to do:
   - **In the portal:** the app's page → **Settings** → **Secrets** → **Set value** next to the key
   - **In their own terminal:**
     ```
     canvas secret set PARTNER_API_KEY
     ```
     It asks for the value with the input hidden; `canvas secret set PARTNER_API_KEY < key.txt`
     reads a file instead. A secret declared under `files:` is set from the file itself —
     `canvas secret set AZURE_CREDENTIALS --file azure.json`, or the file picker on the page
   Tell them which keys, why the app needs each (what service it is for), and where to get the
   value (the partner's console, Google Cloud, AWS…) if they do not have it. Then **stop and wait**
   for them to say it is done — do not poll, do not deploy around it
5. Once they say it is set, `canvas secret list` to confirm none is `NOT SET`, then `canvas deploy`
   again — the build is kept, so it goes straight to deploying

## Changing or removing one

| The user wants to | They do |
|---|---|
| see which are set | Settings → Secrets, or `canvas secret list` — names, who set each, when; never a value |
| change a value (a rotated key) | **Replace** on Settings → Secrets, or `canvas secret set <KEY>` again — then **restart**: the app reads it only when it starts (`canvas restart`, or Restart now on the page) |
| stop using one | remove it from `score.yaml` and deploy, then **Remove** it on the page or `canvas secret rm <KEY>` |

Only the person who deployed the app, an owner of its team or an admin can set or remove its
secrets, and nobody can read one back. **Taking the app down deletes all of its secrets** — the
value lives nowhere else, so if the app comes back, its owner sets them again.

## What NOT to do

- **Never** handle the value yourself: do not ask the user to paste it into the conversation, do not
  run `canvas secret set` for them, do not pipe a value into it. The prompt stopping you is the point.
- **Never** put a credential in score.yaml, in code, in `.env`, or in any file — not "for now", not
  base64'd. Whatever reaches the repo has leaked and must be rotated.
- Do not log a secret, return it from an endpoint, or show it on a page.
