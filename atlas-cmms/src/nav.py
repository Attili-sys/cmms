"""The app's pages, in the order the header shows them — yours to change.

One line per page: its label, and its path in src/views.py. With one page there is no navigation;
from two, the header shows them all and marks the one you are on (the platform's page shell, ajnkit-core's platform/shell.html).
A third item names a rule (score.yaml access.rules): the page is in the menu only of who it lets in —
("Questions", "/questions", "admin"). The `add-page` skill adds the line when it adds a page.
"""

PAGES: list[tuple[str, ...]] = [
    ("Home", "/"),
]
