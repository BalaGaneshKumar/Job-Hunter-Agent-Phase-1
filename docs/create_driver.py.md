# create_driver.py

**Role:** Generic Selenium Edge driver factory (used by Portal B/Portal A flows that don't need the Anti-bot CMD-launch path).

## Functions
- `sync_profile_data(profile_path, profile_dir='Default')` — copies cookies/session data into the automation profile.
- `load_browser_config()` — reads driver-related config.
- `create_driver(use_profile=False)` — launches Selenium's own Edge instance directly (via `webdriver_manager`), with anti-detection tweaks (`STEALTH_JS`: hides `navigator.webdriver`, spoofs plugins/languages, patches `permissions.query`).

## Notes
- Hardcoded to Windows Edge path (`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`) — Windows-only tool.
- Contrast with `portal_c_helpers.create_driver_portal_c()`, which uses the CMD-launch + attach flow from `antibot_helpers.py` instead.

## Depends on
`selenium`, `webdriver_manager`

## Used by
`scraper_portal_b.py`, `scraper_portal_a.py`, `job_counter.py`
