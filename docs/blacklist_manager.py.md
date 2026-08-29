# blacklist_manager.py

**Role:** Keyword/URL blacklist store, backed by `blacklist.xlsx`.

## Functions
- `initialize_blacklist()` — creates `blacklist.xlsx` with header row if it doesn't exist.
- `load_existing_blacklist_urls()` — loads all blacklisted URLs into an in-memory cache (loaded once, updated incrementally).
- `add_to_blacklist(job, reason="Blacklisted by keyword")` — appends a job to the blacklist sheet and cache.

## Depends on
`openpyxl`, `workflow_tracker.log_info`

## Used by
`scraper_portal_b.py`, `scraper_portal_a.py` (via `blacklist_manager.add_to_blacklist`)

## Phase 2 note
Flagged for xlsx → SQLite migration (see `storage_migration_handoff.md`).
