import os
import time
import json
import random
from create_driver import create_driver
from search_state import (
        get_total_pages, save_job_count, get_total_runtime, is_counted, reset_scraper_flag
)
from workflow_tracker import update_stage, log_info, get_config_path
from datetime import datetime

# NOTE: portal-specific imports (portal_b_helpers, portal_c_helpers,
# antibot_helpers, counter_portal_b, counter_portal_a, counter_portal_c)
# moved from module level into main() below, under each run_x check —
# those modules had their scraping code replaced with
# "# code were deleted due to legal issue" (see README limitations), so
# an unconditional import here would crash main() regardless of WF_PORTAL.


def load_config():
    cfg_path = get_config_path()
    with open(cfg_path, 'r') as f:
        return json.load(f)


def main():
    # Determine which portals to count based on WF_PORTAL env var
    # NK = Portal B only, LI = Portal A only, AL or unset = both
    portal = os.environ.get('WF_PORTAL', 'AL').upper()
    run_portal_b  = portal in ('NK', 'AL')
    run_portal_a = portal in ('LI', 'AL')
    run_portal_c  = portal in ('IN', 'AL')

    config       = load_config()
    keywords     = config['candidate']['role_keywords']
    locations    = config['candidate']['locations']
    max_age_days = config['settings'].get('max_job_age_days', 45)
    nk_experience = config.get('candidate', {}).get('experience_years', 3)

    driver     = create_driver(use_profile=True)
    start_time = datetime.now()

    # -----------------------------------------------------------------------
    # Portal A Counter
    # -----------------------------------------------------------------------
    li_grand_total = 0

    if run_portal_a:
        from counter_portal_a import build_portal_a_url, get_total_jobs_portal_a
        log_info('[Counter] Portal A Job Counter started: ' + start_time.strftime('%Y-%m-%d %H:%M:%S'))

        update_stage('Connecting to Browser')
        log_info('[Counter] Portal A counting started')

        for keyword in keywords:
            for location in locations:
                if os.path.exists('STOP'):
                    log_info('[Counter|LI] STOP flag detected — halting counter')
                    driver.quit()
                    return
                reset_scraper_flag('portal_a', keyword, location)
                if is_counted('portal_a', keyword, location):
                    log_info('[Counter|LI] Skipping (already counted): ' + keyword + ' | ' + location)
                    continue
                log_info('[Counter|LI] Counting: ' + keyword + ' | ' + location)
                search_url = build_portal_a_url(
                    keyword, location, max_age_days, config['settings']['experience_levels']
                )
                driver.get(search_url)
                time.sleep(random.uniform(4, 6))

                total             = get_total_jobs_portal_a(driver)
                pages             = get_total_pages(total)
                estimated_seconds = total * 3

                hours   = estimated_seconds // 3600
                minutes = (estimated_seconds % 3600) // 60

                log_info('[Counter|LI] ' + keyword + ' | ' + location + ' — ' + str(total) + ' jobs, ' + str(pages) + ' pages, est. ' + str(hours) + 'h ' + str(minutes) + 'm')
                log_info('[Counter|LI] ' + keyword + ' | ' + location + ' — ' + str(total) + ' jobs')

                save_job_count('portal_a', keyword, location, total, estimated_seconds)
                update_stage('Counting', keyword=keyword, location=location, portal='LI')
                li_grand_total += total
                time.sleep(random.uniform(3, 5))

        li_total_seconds = li_grand_total * 3
        li_hours   = li_total_seconds // 3600
        li_minutes = (li_total_seconds % 3600) // 60
        li_total_runtime = str(li_hours) + 'h ' + str(li_minutes) + 'm'
        log_info('[Counter|LI] Grand total: ' + str(li_grand_total) + ' jobs | ' + str(get_total_pages(li_grand_total)) + ' pages | est. ' + li_total_runtime)
        log_info('[Counter] Portal A total: ' + str(li_grand_total) + ' jobs — est. ' + li_total_runtime)

    # -----------------------------------------------------------------------
    # Portal B Counter
    # -----------------------------------------------------------------------
    nk_grand_total = 0

    if run_portal_b:
        from portal_b_helpers import verify_experience_filter
        from counter_portal_b import build_portal_b_url, get_total_jobs_portal_b
        log_info('[Counter] Portal B Job Counter started')

        log_info('[Counter] Portal B counting started')

        for keyword in keywords:
            for location in locations:
                if os.path.exists('STOP'):
                    log_info('[Counter|NK] STOP flag detected — halting counter')
                    driver.quit()
                    return
                reset_scraper_flag('portal_b', keyword, location)
                if is_counted('portal_b', keyword, location):
                    log_info('[Counter|NK] Skipping (already counted): ' + keyword + ' | ' + location)
                    continue
                log_info('[Counter|NK] Counting: ' + keyword + ' | ' + location)
                search_url = build_portal_b_url(keyword, location, nk_experience)
                driver.get(search_url)
                time.sleep(random.uniform(4, 6))

                tag = '[NK|' + keyword + '|' + location + ']'
                if not verify_experience_filter(driver, keyword, location, 1, nk_experience, tag):
                    log_info(tag + ' [ExpCheck] Stopping counter — experience filter lost')
                    break

                total             = get_total_jobs_portal_b(driver)
                pages             = get_total_pages(total, per_page=20)
                estimated_seconds = total * 1

                hours   = estimated_seconds // 3600
                minutes = (estimated_seconds % 3600) // 60

                log_info('[Counter|NK] ' + keyword + ' | ' + location + ' — ' + str(total) + ' jobs, ' + str(pages) + ' pages, est. ' + str(hours) + 'h ' + str(minutes) + 'm')
                log_info('[Counter|NK] ' + keyword + ' | ' + location + ' — ' + str(total) + ' jobs')

                save_job_count('portal_b', keyword, location, total, estimated_seconds)
                update_stage('Counting', keyword=keyword, location=location, portal='NK')
                nk_grand_total += total
                time.sleep(random.uniform(3, 5))

        nk_total_seconds = nk_grand_total * 1
        nk_hours   = nk_total_seconds // 3600
        nk_minutes = (nk_total_seconds % 3600) // 60
        nk_total_runtime = str(nk_hours) + 'h ' + str(nk_minutes) + 'm'
        log_info('[Counter|NK] Grand total: ' + str(nk_grand_total) + ' jobs | ' + str(get_total_pages(nk_grand_total, per_page=20)) + ' pages | est. ' + nk_total_runtime)
        log_info('[Counter] Portal B total: ' + str(nk_grand_total) + ' jobs — est. ' + nk_total_runtime)

    # -----------------------------------------------------------------------
    # Portal C Counter
    # -----------------------------------------------------------------------
    in_grand_total = 0
    in_completed_cycles = 0

    if run_portal_c:
        from portal_c_helpers import create_driver_portal_c, PORTAL_C_PROFILE_DIR, build_portal_c_url, proactive_clear
        from antibot_helpers import shutdown_browser
        from counter_portal_c import get_total_jobs_portal_c
        log_info('[Counter] Portal C Job Counter started')
        log_info('[Counter] Portal C counting started')

        # Portal C uses its own dedicated driver (separate profile, CMD-launched
        # + Anti-bot/hang recovery) — never the shared 'driver' above, so
        # its forced kill/relaunch cycles can't disturb Portal B/Portal A.
        portal_c_driver = create_driver_portal_c()

        for keyword in keywords:
            for location in locations:
                if os.path.exists('STOP'):
                    log_info('[Counter|IN] STOP flag detected — halting counter')
                    shutdown_browser(portal_c_driver, PORTAL_C_PROFILE_DIR)
                    driver.quit()
                    return
                reset_scraper_flag('portal_c', keyword, location)
                if is_counted('portal_c', keyword, location):
                    log_info('[Counter|IN] Skipping (already counted): ' + keyword + ' | ' + location)
                    continue

                # Proactive cookie/cache clear every 4th completed cycle,
                # before the next one starts (i.e. before cycle 5, 9, 13,
                # ...) — same recovery pipeline as a Anti-bot-triggered
                # clear, just on a schedule instead of only reacting after
                # Anti-bot is actually hit.
                if in_completed_cycles > 0 and in_completed_cycles % 4 == 0:
                    next_url = build_portal_c_url(keyword, location)
                    portal_c_driver = proactive_clear(
                        portal_c_driver, next_url, next_url,
                        reason='cycle ' + str(in_completed_cycles + 1) + ' (every 4th)'
                    )

                log_info('[Counter|IN] Counting: ' + keyword + ' | ' + location)

                total, pages, portal_c_driver = get_total_jobs_portal_c(portal_c_driver, keyword, location)
                estimated_seconds = total * 4  # Portal C involves per-card detail clicks + recovery overhead

                hours   = estimated_seconds // 3600
                minutes = (estimated_seconds % 3600) // 60

                log_info('[Counter|IN] ' + keyword + ' | ' + location + ' — ' + str(total) + ' jobs, ' + str(pages) + ' pages, est. ' + str(hours) + 'h ' + str(minutes) + 'm')

                save_job_count('portal_c', keyword, location, total, estimated_seconds)
                update_stage('Counting', keyword=keyword, location=location, portal='IN')
                in_grand_total += total
                in_completed_cycles += 1
                time.sleep(random.uniform(3, 5))

        shutdown_browser(portal_c_driver, PORTAL_C_PROFILE_DIR)

        in_total_seconds = in_grand_total * 4
        in_hours   = in_total_seconds // 3600
        in_minutes = (in_total_seconds % 3600) // 60
        in_total_runtime = str(in_hours) + 'h ' + str(in_minutes) + 'm'
        log_info('[Counter|IN] Grand total: ' + str(in_grand_total) + ' jobs | ' + str(get_total_pages(in_grand_total)) + ' pages | est. ' + in_total_runtime)
        log_info('[Counter] Portal C total: ' + str(in_grand_total) + ' jobs — est. ' + in_total_runtime)

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    end_time = datetime.now()
    duration = round((end_time - start_time).total_seconds())

    log_info('[Counter] Summary — Portal A: ' + (str(li_grand_total) + ' jobs' if run_portal_a else 'skipped')
             + ' | Portal B: ' + (str(nk_grand_total) + ' jobs' if run_portal_b else 'skipped')
             + ' | Portal C: ' + (str(in_grand_total) + ' jobs' if run_portal_c else 'skipped')
             + ' | Duration: ' + str(duration // 60) + 'm ' + str(duration % 60) + 's'
             + ' | Finished: ' + end_time.strftime('%Y-%m-%d %H:%M:%S'))

    driver.quit()


if __name__ == '__main__':
    main()
