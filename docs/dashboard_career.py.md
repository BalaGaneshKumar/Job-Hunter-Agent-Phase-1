# dashboard_career.py

**Role:** HTML/CSS/JS for the dashboard's "Career" tab (Applications + Job Sites sub-tabs).

## Functions
- `build_career_html()` — tab markup (Applications table, Job Sites table).
- `build_career_css()` — tab-scoped styles.
- `build_career_js()` — client-side rendering/filtering/editing logic for the two tables.

## Note
Pure UI generation — no data access itself; data comes from `career_tracker.py` via `dashboard_server.py` API endpoints.

## Used by
`dashboard_server.py`
