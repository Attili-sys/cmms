---
name: ajnkit-email
description: >-
  Reference for the platform's email — ajnkit-email (Python, `from ajnkit.email import send`) or
  @ajnkit/email (Next.js, `send` from `@ajnkit/email`). Use when writing code that sends an
  email or handles EmailRefused. Setting email up, and who it may go to, is request-email.
---

```python
from ajnkit.email import EmailRefused, send

try:
    left = send(["sahar@aljazeera.net"], "The rota for next week", body)
except EmailRefused as e:
    return {"error": str(e)}
```

| | |
|---|---|
| To | the app's team only; anyone else after an admin approves (`canvas email request "<why>"`) |
| Limits | 20 recipients an hour, a 254-character address, a 200-character subject, 65,536 characters of plain text |
| Look | Canvas's layout, under the app's name — no HTML of the app's own |
| On your computer | checked, then logged — not sent |

`EmailRefused` is a sentence for the person: show it, log it, and act on what it says.
Never resend when the reason says the message may already have been sent.

`send` blocks up to 30 s: Python, from a plain `def` route. Never SMTP, a password or a mail SDK.
In a test, replace `send` where the app imports it — not the settings, which it reads from the
environment.
