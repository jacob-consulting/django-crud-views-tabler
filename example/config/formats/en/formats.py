# The demo's date formats (FORMAT_MODULE_PATH in settings.py), as the hand-written pages use them: "05 Jan 2026".
# Without this, every `|date` without an argument (object detail pages, tables) prints Django's "Jan. 5, 2026".
DATE_FORMAT = "d M Y"
DATETIME_FORMAT = "d M Y H:i"
