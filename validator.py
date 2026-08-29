"""
validator.py — Job Link Validator

Launched by dashboard_workflows.run_validator_sequence() as:
    python validator.py
with WF_ID and WF_PORTAL environment variables set ('AL', 'NK', or 'LI' —
same meaning as Counter/Scraper: AL = both portals, NK/LI = one only).

Purpose: for every jobs.csv row with Status in ('Scraped', 'Eligible') and
a blank 'Internal/External' column, opens the job's URL and:
  - expired-marker present   -> Status = 'Ineligible'
  - Internal apply-button    -> Internal/External = 'Internal'
  - External apply-button    -> Internal/External = 'External'
  - none of the above        -> nothing written, logged as 'Not defined'
                                 (row stays untouched, picked up again on
                                 the next Validator run automatically)

Portal-unique eligibility checks (check_portal_b / check_portal_a /
check_portal_c) live in validator_portal_b.py / validator_portal_a.py /
validator_portal_c.py — mirrors the counter_portal_b.py / counter_portal_a.py
/ counter_portal_c.py split already used by job_counter.py. This file keeps
only what's shared across portals: jobs.csv I/O, bucket building, and the
Validator's main() orchestration.

4 stages only, reported via workflow_tracker.update_stage():
    Create Order -> Connecting to Browser -> Cycle <bucket> -> Complete

No keyword dimension. Jobs are grouped into (Portal, Location) buckets and
processed in alphabetical (Portal, Location) order. The Cycle stage code
uses a fixed 'CARSNG' (Career Screening) constant in place of a keyword,
e.g.:
    Cycle NK0CARSNG0COE
    Cycle LI0CARSNG0CHI
"""

import os
import csv
import time
import random
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from create_driver import create_driver
from workflow_tracker import update_stage, log_info, make_location_code

# NOTE: portal-specific imports (portal_c_helpers, antibot_helpers,
# validator_portal_b, validator_portal_a, validator_portal_c) moved from
# module level into main() below — those modules had their scraping/
# eligibility-check code replaced with
# "# code were deleted due to legal issue" (see README limitations), so
# an unconditional import here would crash on `import validator` even
# when just loading this file, let alone running it.

JOBS_CSV  = 'jobs.csv'
STOP_FILE = 'STOP'


def staging_path(wf_id):
    """jobs.csv is never written to mid-run — every job's result is saved
    here instead, and only merged into jobs.csv once the run reaches
    'Complete'. This exact naming convention (jobs_validating.<wf_id>.csv,
    same directory as jobs.csv) is duplicated in dashboard_server.py's
    /api/reset-workflow, which deletes this file on Reset — if this
    changes, that must change too."""
    return 'jobs_validating.' + wf_id + '.csv'

# Must match tracker.py's COLUMNS exactly (post patch_tracker_add_internal_external.py)
COLUMNS = [
    'Job ID', 'Job Title', 'Company', 'Portal', 'Location',
    'URL', 'Status', 'Internal/External', 'Applied Date', 'Last Checked',
    'Description', 'Notes'
]

PORTAL_CODE = {'PortalB': 'NK', 'PortalA': 'LI', 'PortalC': 'IN'}


# ---------------------------------------------------------------------------
# jobs.csv load / save
# ---------------------------------------------------------------------------
def load_jobs(source_path=JOBS_CSV):
    if not os.path.exists(source_path):
        return {}
    with open(source_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        return {
            row.get('URL', '').strip(): row
            for row in reader
            if row.get('URL', '').strip()
        }


def save_jobs(jobs_by_url, target_path=JOBS_CSV):
    with open(target_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(jobs_by_url.values())


# ---------------------------------------------------------------------------
# Bucket building
# ---------------------------------------------------------------------------
def build_buckets(jobs_by_url, wf_portal, wf_locations=None):
    """Group validator-eligible rows by (Portal, Location), scoped to the
    requested portal ('AL' = both) and optionally a set of locations
    (empty/None = all locations). Returns a list of
    ((portal_name, location), [url, ...]) sorted alphabetically by
    (portal_name, location) — so a third portal or location added later
    slots in without needing any ordering logic changes.

    When wf_locations is given, every requested (portal, location) combo
    gets a bucket even if it has zero matching rows right now — so the
    caller can still show/log that cycle and skip it, instead of it
    silently never existing just because jobs.csv has no data for it yet.
    Falls back to purely data-driven bucketing when wf_locations is empty
    ('leave empty for all'), since there's no fixed location list to
    enumerate against in that case."""
    wanted_portals = None
    if wf_portal == 'NK':
        wanted_portals = {'PortalB'}
    elif wf_portal == 'LI':
        wanted_portals = {'PortalA'}
    elif wf_portal == 'IN':
        wanted_portals = {'PortalC'}
    # 'AL' -> wanted_portals stays None -> all portals included

    wanted_locations = set(wf_locations) if wf_locations else None

    buckets = {}
    for url, row in jobs_by_url.items():
        status = row.get('Status', '')
        label  = (row.get('Internal/External') or '').strip()
        portal = row.get('Portal', '')
        location = row.get('Location', '')

        if status not in ('Scraped', 'Eligible'):
            continue
        if label:
            continue
        if wanted_portals and portal not in wanted_portals:
            continue
        if wanted_locations and location not in wanted_locations:
            continue

        key = (portal, location)
        buckets.setdefault(key, []).append(url)

    if wanted_locations:
        portal_names = wanted_portals if wanted_portals else {'PortalB', 'PortalA', 'PortalC'}
        for portal_name in portal_names:
            for location in wanted_locations:
                buckets.setdefault((portal_name, location), [])

    return sorted(buckets.items(), key=lambda kv: (kv[0][0], kv[0][1]))


def wait_for_page(driver, timeout=8):
    """Best-effort wait for the page body before checking selectors."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
    except Exception:
        pass


def flush_and_cleanup(jobs_by_url, touched_urls, staging_csv):
    """Merge this run's (plus any resumed) touched rows into a fresh read
    of jobs.csv, save, and remove the staging file. Shared by both the
    grand_total==0 shortcut (all work was already done in a prior Hold,
    nothing new to check) and the normal end-of-run path."""
    if not touched_urls:
        if os.path.exists(staging_csv):
            os.remove(staging_csv)
        return
    current = load_jobs()
    for url in touched_urls:
        if url in current and url in jobs_by_url:
            current[url] = jobs_by_url[url]
    save_jobs(current, JOBS_CSV)
    if os.path.exists(staging_csv):
        os.remove(staging_csv)
    log_info('[Validator] Complete — ' + str(len(touched_urls)) + ' rows written to jobs.csv')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # NOTE: portal-specific imports are done per-bucket below (see the
    # "for (portal_name, location), urls in buckets:" loop), not here —
    # each of portal_c_helpers / antibot_helpers / validator_portal_b /
    # validator_portal_a / validator_portal_c had its code replaced with
    # "# code were deleted due to legal issue" (see README limitations),
    # so a portal only fails when a bucket for that portal is actually
    # non-empty and reached, instead of main() crashing outright
    # regardless of which portal was requested.

    wf_id        = os.environ.get('WF_ID', '')
    wf_portal    = os.environ.get('WF_PORTAL', 'AL').upper()
    wf_locations = [l for l in os.environ.get('WF_LOCATIONS', '').split(',') if l]
    staging_csv  = staging_path(wf_id)

    if os.path.exists(STOP_FILE):
        os.remove(STOP_FILE)
        log_info('[Validator] Removed leftover STOP flag')

    update_stage('Create Order')
    log_info('[Validator] Create Order — scanning jobs.csv')

    jobs_by_url  = load_jobs()
    staged       = load_jobs(staging_csv)
    touched_urls = set()

    # Rows already validated in a previous Hold->Retry cycle of THIS
    # workflow (not deleted via Reset) get their result merged in before
    # build_buckets() runs — since their Status/Internal-External no
    # longer match build_buckets()'s "needs validation" filter, they're
    # naturally excluded from this run's working set, so they're never
    # re-checked. Reset deletes the staging file entirely, which is the
    # only way to force a full restart from scratch.
    for url, staged_row in staged.items():
        if url in jobs_by_url:
            jobs_by_url[url] = staged_row
            touched_urls.add(url)

    if touched_urls:
        log_info('[Validator] Resuming — ' + str(len(touched_urls)) + ' already-validated jobs excluded (from a prior Hold)')

    buckets     = build_buckets(jobs_by_url, wf_portal, wf_locations)

    nk_total = sum(len(urls) for (portal, loc), urls in buckets if portal == 'PortalB')
    li_total = sum(len(urls) for (portal, loc), urls in buckets if portal == 'PortalA')
    in_total = sum(len(urls) for (portal, loc), urls in buckets if portal == 'PortalC')
    grand_total = nk_total + li_total + in_total

    log_info(
        '[Validator] Create Order — ' + str(grand_total) + ' jobs found '
        '(Portal B: ' + str(nk_total) + ', Portal A: ' + str(li_total) + ', Portal C: ' + str(in_total) + ')'
    )

    if not buckets:
        log_info('[Validator] Nothing new to validate.')
        flush_and_cleanup(jobs_by_url, touched_urls, staging_csv)
        update_stage('Complete')
        return

    needs_generic_driver = any(portal_name in ('PortalB', 'PortalA') and urls for (portal_name, _), urls in buckets)
    needs_portal_c_driver  = any(portal_name == 'PortalC' and urls for (portal_name, _), urls in buckets)

    driver = None
    portal_c_driver = None
    portal_c_jobs_checked = 0

    if needs_generic_driver:
        update_stage('Connecting to Browser')
        log_info('[Validator] Connecting to Browser')
        driver = create_driver(use_profile=True)

    try:
        for (portal_name, location), urls in buckets:
            if os.path.exists(STOP_FILE):
                log_info('[Validator] STOP flag detected — halting before next bucket')
                break

            # Portal C's driver is separate — CMD-launched + Anti-bot-recovery
            # aware, unlike the direct-launch driver Portal B/Portal A share.
            portal_code = PORTAL_CODE.get(portal_name, '??')
            loc_code    = make_location_code(location)
            stage_label = 'Cycle ' + portal_code + '0CARSNG0' + loc_code

            if not urls:
                update_stage(stage_label)
                log_info(
                    '[Validator] ' + stage_label + ' — 0 jobs (' +
                    portal_name + ' | ' + location + '), skipping'
                )
                continue

            # Per-portal lazy import — see main()'s note above.
            if portal_name == 'PortalC':
                from portal_c_helpers import (
                    PORTAL_C_HOME, PORTAL_C_PROFILE_DIR, PORTAL_C_DEBUG_PORT,
                    PORTAL_C_DOMAIN, PORTAL_C_KEEP_COOKIES,
                    create_driver_portal_c, proactive_clear, verify_login, is_logged_in,
                )
                from antibot_helpers import check_antibot, recover_from_hang, short_err, shutdown_browser
                from validator_portal_c import check_portal_c
            elif portal_name == 'PortalB':
                from validator_portal_b import check_portal_b
            elif portal_name == 'PortalA':
                from validator_portal_a import check_portal_a

            if portal_name == 'PortalC' and portal_c_driver is None:
                update_stage('Connecting to Browser')
                log_info('[Validator] Connecting to Browser (Portal C)')
                portal_c_driver = create_driver_portal_c()

            update_stage(stage_label)
            log_info(
                '[Validator] ' + stage_label + ' — ' + str(len(urls)) +
                ' jobs (' + portal_name + ' | ' + location + ')'
            )

            for url in urls:
                if os.path.exists(STOP_FILE):
                    log_info('[Validator] STOP flag detected — halting mid-bucket')
                    break

                row = jobs_by_url.get(url)
                if not row:
                    continue

                try:
                    if portal_name == 'PortalC':
                        # Proactive cookie/cache clear every 20th job
                        # checked, before the next one starts — Validator
                        # has no keyword/location cycles like Counter/
                        # Scraper, it checks individual job links one by
                        # one, so the schedule is job-count-based instead.
                        if portal_c_jobs_checked > 0 and portal_c_jobs_checked % 20 == 0:
                            portal_c_driver = proactive_clear(
                                portal_c_driver, url, url,
                                reason='job ' + str(portal_c_jobs_checked + 1) + ' (every 20th)'
                            )
                        try:
                            portal_c_driver.get(url)
                        except Exception as get_err:
                            # Session was already dead from a previous job —
                            # this fails BEFORE check_antibot() below ever
                            # gets a chance to run, which is exactly why a
                            # dead driver used to loop forever, failing every
                            # subsequent job identically with no recovery.
                            log_info('[Validator|IN] Driver session dead, attempting recovery: ' + short_err(get_err))
                            portal_c_driver = recover_from_hang(
                                url, PORTAL_C_HOME, PORTAL_C_HOME,
                                PORTAL_C_PROFILE_DIR, PORTAL_C_DEBUG_PORT, driver=portal_c_driver
                            )
                            portal_c_driver.get(url)
                        portal_c_driver, _ = check_antibot(
                            portal_c_driver, url, PORTAL_C_HOME, PORTAL_C_HOME,
                            PORTAL_C_PROFILE_DIR, PORTAL_C_DOMAIN, PORTAL_C_KEEP_COOKIES, PORTAL_C_DEBUG_PORT,
                            login_check_fn=is_logged_in
                        )
                        wait_for_page(portal_c_driver)
                        verify_login(portal_c_driver, '[Validator|IN]')
                        result = check_portal_c(portal_c_driver)
                        portal_c_jobs_checked += 1
                    else:
                        driver.get(url)
                        wait_for_page(driver)
                        if portal_name == 'PortalB':
                            result = check_portal_b(driver)
                        else:
                            result = check_portal_a(driver)

                    if result == 'Ineligible':
                        row['Status']       = 'Ineligible'
                        row['Last Checked'] = datetime.now().strftime('%Y-%m-%d %H:%M')
                        touched_urls.add(url)
                        log_info('[Validator|' + portal_code + '] Ineligible (expired): ' + url)

                    elif result in ('Internal', 'External'):
                        row['Internal/External'] = result
                        row['Last Checked']       = datetime.now().strftime('%Y-%m-%d %H:%M')
                        touched_urls.add(url)
                        log_info('[Validator|' + portal_code + '] ' + result + ': ' + url)

                    else:
                        log_info('[Validator|' + portal_code + '] Not defined — no match found: ' + url)

                    # Save after every job — but only the rows actually
                    # touched so far, not the whole CSV. Untouched rows are
                    # identical to what's already in jobs.csv (nothing here
                    # ever reads the staging file back to resume — see the
                    # Hold/Retry note below), so writing them every job is
                    # pure I/O with no protective value.
                    if touched_urls:
                        save_jobs({u: jobs_by_url[u] for u in touched_urls}, staging_csv)

                except Exception as e:
                    log_info('[Validator|' + portal_code + '] Error checking ' + url + ': ' + str(e)[:100])

                time.sleep(random.uniform(3, 5))

    finally:
        if driver:
            driver.quit()
        if portal_c_driver:
            shutdown_browser(portal_c_driver, PORTAL_C_PROFILE_DIR)

    if os.path.exists(STOP_FILE):
        # dashboard_workflows.run_validator_sequence() detects this file
        # itself (after this subprocess exits) and sets status=Hold —
        # jobs.csv was never opened for writing this run, so it's already
        # untouched; the staging file is left on disk but gets overwritten
        # fresh (or deleted via Reset) rather than resumed from, since
        # every Retry rebuilds its working set from jobs.csv from scratch.
        return

    # Re-read jobs.csv fresh rather than reusing the in-memory jobs_by_url
    # from Create Order — anything hand-edited via the dashboard's CSV
    # editor while this run was in progress must survive; only the rows
    # this run actually touched get overwritten.
    flush_and_cleanup(jobs_by_url, touched_urls, staging_csv)
    update_stage('Complete')


if __name__ == '__main__':
    main()
