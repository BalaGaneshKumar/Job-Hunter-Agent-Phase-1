"""
scraper.py — Scraper entry point.

Launched by the dashboard as:
    python scraper.py
with WF_ID and WF_PORTAL environment variables set ('AL', 'NK', 'LI', or
'IN' — same meaning as Counter/Validator: AL = all three portals in
order, one portal code = that portal only).

This file didn't exist before — the dashboard previously had to invoke
scraper_portal_b.py / scraper_portal_a.py / scraper_portal_c.py directly per
portal. This is the new single mount point; dashboard_workflows.py's
Scraper launch needs to point at this file going forward.

Holds only what's genuinely shared across all three portal scrapers
(is_blacklisted / format_duration / print_progress / load_config /
flush_jobs_to_excel — identical, or identical but for a log tag, in all
three) plus the WF_PORTAL dispatch below. Mirrors the counter_*.py /
validator_*.py split already used by job_counter.py and validator.py.

Each portal's real scrape loop (scrape_portal_b / scrape_portal_a /
scrape_portal_c) and its own orchestrator (run_portal_b_scraper /
run_portal_a_scraper / run_portal_c_scraper) stay in scraper_portal_b.py /
scraper_portal_a.py / scraper_portal_c.py — those files import the helpers
below from here. The run_*_scraper imports are done lazily, inside
main(), rather than at module load — same reason scrape_portal_b() already
does `from job_counter import get_total_jobs_portal_b` inside the loop
instead of at the top: it avoids a circular import, since the portal
files need to import back from this file.
"""

import os
from datetime import datetime

from workflow_tracker import log_info, get_config_path
from tracker import batch_write_jobs, load_existing_jobs
from search_state import get_saved_jobs, clear_saved_jobs


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def is_blacklisted(title, blacklist):
    title_lower = title.lower()
    for word in blacklist:
        if word.lower() in title_lower:
            return True, word
    return False, None


def format_duration(seconds):
    hours   = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs    = seconds % 60
    if hours > 0:
        return str(hours) + 'h ' + str(minutes) + 'm ' + str(secs) + 's'
    return str(minutes) + 'm ' + str(secs) + 's'


def print_progress(tag, start_time, jobs_found, total_expected):
    """tag is the portal's log prefix, e.g. '[NK]', '[LI]', '[IN]'."""
    elapsed     = (datetime.now() - start_time).total_seconds()
    elapsed_hr  = int(elapsed // 3600)
    elapsed_min = int((elapsed % 3600) // 60)
    if jobs_found > 0:
        rate              = elapsed / jobs_found
        remaining_jobs    = total_expected - jobs_found
        remaining_seconds = remaining_jobs * rate
        rem_hr  = int(remaining_seconds // 3600)
        rem_min = int((remaining_seconds % 3600) // 60)
        remaining_str = str(rem_hr) + 'h ' + str(rem_min) + 'm'
        rate_str      = str(round(rate)) + 's/job'
    else:
        remaining_str = 'calculating...'
        rate_str      = 'N/A'
    log_info(tag + ' Progress — Runtime: ' + str(elapsed_hr) + 'h ' + str(elapsed_min) + 'm' + ' | Jobs: ' + str(jobs_found) + '/' + str(total_expected) + ' | Rate: ' + rate_str + ' | Remaining: ~' + remaining_str)


def load_config():
    cfg_path = get_config_path()
    import json
    with open(cfg_path, 'r') as f:
        return json.load(f)


def flush_jobs_to_excel(tag):
    """tag is the portal's log prefix, e.g. '[NK]', '[LI]', '[IN]'."""
    jobs = get_saved_jobs()
    if not jobs:
        return 0
    existing_urls, existing_pairs = load_existing_jobs()
    written_urls  = set()
    written_pairs = set()
    clean_jobs = []
    for job in jobs:
        url  = job['url']
        pair = (job.get('company', '').strip().lower(), job.get('title', '').strip().lower())
        if url in existing_urls or url in written_urls:
            continue
        if pair[0] and pair[1] and pair[0] != 'unknown' and (pair in existing_pairs or pair in written_pairs):
            continue
        clean_jobs.append(job)
        written_urls.add(url)
        written_pairs.add(pair)
    count = batch_write_jobs(clean_jobs)
    clear_saved_jobs()
    log_info(tag + ' Flushed ' + str(count) + ' jobs to scraper_jobs.xlsx.')
    return count


# ---------------------------------------------------------------------------
# Main — WF_PORTAL dispatch (AL = all three, in Portal B -> Portal A -> Portal C
# order, matching dashboard_scraper.py's stated run order)
# ---------------------------------------------------------------------------

def main():
    # Local imports — see module docstring: importing these at module load
    # would be circular, since scraper_portal_b.py/scraper_portal_a.py/
    # scraper_portal_c.py import the helpers above from this file.
    #
    # NOTE: each import moved under its own run_x check below (was
    # previously unconditional here) — scraper_portal_b.py / scraper_portal_a.py
    # / scraper_portal_c.py had their scraping code replaced with
    # "# code were deleted due to legal issue" (see README limitations),
    # so an unconditional import here would crash main() regardless of
    # which portal was requested.

    portal       = os.environ.get('WF_PORTAL', 'AL').upper()
    run_portal_b   = portal in ('NK', 'AL')
    run_portal_a = portal in ('LI', 'AL')
    run_portal_c   = portal in ('IN', 'AL')

    if os.path.exists('STOP'):
        os.remove('STOP')
        log_info('[Scraper] Removed leftover STOP flag')

    if run_portal_b:
        from scraper_portal_b import run_portal_b_scraper
        log_info('[Scraper] Portal B stage started')
        run_portal_b_scraper()
        if os.path.exists('STOP'):
            log_info('[Scraper] STOP flag detected — halting before next portal')
            return

    if run_portal_a:
        from scraper_portal_a import run_portal_a_scraper
        log_info('[Scraper] Portal A stage started')
        run_portal_a_scraper()
        if os.path.exists('STOP'):
            log_info('[Scraper] STOP flag detected — halting before next portal')
            return

    if run_portal_c:
        from scraper_portal_c import run_portal_c_scraper
        log_info('[Scraper] Portal C stage started')
        run_portal_c_scraper()

    log_info('[Scraper] All requested portals finished')


if __name__ == '__main__':
    main()
