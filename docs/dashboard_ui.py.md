# dashboard_ui.py

**Role:** Shared CSS, HTML page wrapper, and small utility helpers used across all dashboard tab modules.

## Functions
- `esc(s)` — HTML-escapes a string for safe interpolation.
- `html_page(title, body, extra_head='')` — wraps a tab's body HTML in the full page shell (nav, header, shared `CSS`).
- `render_pagination_js()` — shared pagination-control JS snippet.

## Used by
`dashboard_jobs.py`, `dashboard_scraper.py`, `dashboard_detail.py`, `dashboard_server.py`
