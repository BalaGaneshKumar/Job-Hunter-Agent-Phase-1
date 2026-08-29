"""
dashboard_workflows.py — Workflow management, subprocess runner, logging, config helpers
Imported by dashboard_server.py
"""

import os
import json
import string
import threading
import subprocess
import time
from datetime import datetime

# Imported lazily (inside functions) where used, to avoid a hard
# dependency on selenium/validator.py at module import time for code
# paths that don't need it (e.g. simple workflow CRUD).

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
WORKFLOWS_FILE = os.path.join(BASE_DIR, 'workflows.json')
LOGS_DIR       = os.path.join(BASE_DIR, 'logs')
CONFIG_FILE    = os.path.join(BASE_DIR, 'config.json')
STOP_FILE      = os.path.join(BASE_DIR, 'STOP')
JOBS_CSV       = os.path.join(BASE_DIR, 'jobs.csv')
BLACKLIST_CSV  = os.path.join(BASE_DIR, 'blacklist.csv')
PROFILE_JSON   = os.path.join(BASE_DIR, 'profile.json')

os.makedirs(LOGS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------
def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=4)

# ---------------------------------------------------------------------------
# Workflow ID + storage
# ---------------------------------------------------------------------------
_wf_lock = threading.Lock()

def load_workflows():
    defaults = {
        'counter_CTR_NK': 0, 'counter_CTR_LI': 0, 'counter_CTR_AL': 0,
        'counter_SCR_NK': 0, 'counter_SCR_LI': 0, 'counter_SCR_AL': 0,
        'workflows': []
    }
    if not os.path.exists(WORKFLOWS_FILE):
        return defaults.copy()
    try:
        with open(WORKFLOWS_FILE, 'r') as f:
            data = json.load(f)
        for key in defaults:
            if key not in data:
                data[key] = defaults[key]
        return data
    except Exception:
        return defaults.copy()

def save_workflows(data):
    with open(WORKFLOWS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def generate_workflow_id(wf_type, portal):
    with _wf_lock:
        data        = load_workflows()
        counter_key = 'counter_' + wf_type + '_' + portal
        data[counter_key] = data.get(counter_key, 0) + 1
        count   = data[counter_key]
        letters = string.ascii_lowercase
        n  = (count - 1) // 9999      # letter group increments every 9999
        nn = ((count - 1) % 9999) + 1  # NNNN resets to 0001 each group
        c1 = letters[n // (26 * 26) % 26]
        c2 = letters[n // 26 % 26]
        c3 = letters[n % 26]
        wf_id = 'WFI' + wf_type + portal + (c1+c2+c3).upper() + str(nn).zfill(4)
        save_workflows(data)
    return wf_id

# ---------------------------------------------------------------------------
# Status constants
# ---------------------------------------------------------------------------
STATUS_WAITING    = 'Waiting'
STATUS_INPROGRESS = 'In Progress'
STATUS_HOLD       = 'Hold'
STATUS_RETRY      = 'Retry'
STATUS_COMPLETE   = 'Complete'
STATUS_FAILED     = 'Failed'
STATUS_CANCELLED  = 'Cancelled'

STATUS_SYMBOL = {
    STATUS_WAITING: '⏳', STATUS_INPROGRESS: '🟡', STATUS_HOLD: '⏸',
    STATUS_RETRY: '🔄', STATUS_COMPLETE: '✅', STATUS_FAILED: '❌',
    STATUS_CANCELLED: '🚫',
}

STATUS_LEGEND = [
    ('⏳', 'Waiting',     'Created, not yet started'),
    ('🟡', 'In Progress', 'Subprocess actively running'),
    ('⏸', 'Hold',        'Stopped gracefully, resumable'),
    ('🔄', 'Retry',       'Resuming from last saved state'),
    ('✅', 'Complete',    'Finished successfully'),
    ('❌', 'Failed',      'Subprocess exited with error'),
    ('🚫', 'Cancelled',   'Cancelled before starting'),
]

# ---------------------------------------------------------------------------
# Workflow record helpers
# ---------------------------------------------------------------------------
def create_workflow_record(wf_id, wf_type, portal, scraper, keywords, locations, planned_stages=None):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return {
        'id': wf_id, 'type': wf_type, 'portal': portal, 'scraper': scraper,
        'keywords': keywords, 'locations': locations, 'status': STATUS_WAITING,
        'stage': 'Waiting', 'start_date': now, 'updated_date': now, 'pid': None,
        # Computed once, upfront, at creation time — the full planned list
        # of Cycle stages this workflow will go through. Stored permanently
        # so the Stages panel can show the complete picture from the start
        # (not built up piecemeal as it runs) and never goes stale/
        # disappears later regardless of what happens to jobs.csv
        # afterward, since we never recompute it live.
        'planned_stages': planned_stages or [],
    }

def update_workflow(wf_id, **kwargs):
    with _wf_lock:
        data = load_workflows()
        for wf in data['workflows']:
            if wf['id'] == wf_id:
                wf.update(kwargs)
                wf['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                break
        save_workflows(data)

def get_workflow(wf_id):
    data = load_workflows()
    for wf in data['workflows']:
        if wf['id'] == wf_id:
            return wf
    return None

def get_running_workflow():
    data = load_workflows()
    for wf in data['workflows']:
        if wf['status'] in (STATUS_INPROGRESS, STATUS_RETRY):
            return wf
    return None

def get_next_waiting_workflow():
    """Oldest still-Waiting workflow, in the order they were created —
    i.e. the front of the queue."""
    data = load_workflows()
    for wf in data['workflows']:
        if wf['status'] == STATUS_WAITING:
            return wf
    return None

def clear_old_waiting_workflows():
    """A brand-new submission supersedes any not-yet-started rows left
    over from a previous request — mark them Cancelled rather than
    silently deleting, so the history stays visible."""
    data = load_workflows()
    changed = False
    for wf in data['workflows']:
        if wf['status'] == STATUS_WAITING:
            wf['status'] = STATUS_CANCELLED
            wf['stage']  = 'Cancelled (superseded by new request)'
            wf['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            changed = True
    if changed:
        save_workflows(data)

def advance_queue():
    """Starts the next Waiting workflow, but only if nothing is actively
    running right now. A Held workflow does NOT count as running here —
    it simply won't be auto-advanced past by the system; only a fresh
    manual submission can override past a Held one (via
    clear_old_waiting_workflows() + its own immediate start)."""
    if get_running_workflow():
        return
    next_wf = get_next_waiting_workflow()
    if not next_wf:
        return
    if next_wf['type'] == 'Validator':
        run_validator_workflow(next_wf['id'])
    else:
        run_single_workflow(next_wf['id'])

def _compute_validator_planned_stages(portal_code, portal_name, locations):
    """
    Called once, at workflow creation time, to compute the FULL list of
    Cycle stages this Validator run will go through — a snapshot taken
    before any processing happens, so it's still accurate (nothing has
    been validated yet to make jobs.csv stale). Stored permanently on the
    record; never recomputed live afterward, which is what caused cycles
    to appear to "disappear" once their jobs were processed (their
    Internal/External column was no longer blank, so a live recompute at
    display time would show fewer or zero buckets for work already done).
    """
    stages = []
    try:
        from validator import load_jobs, build_buckets, PORTAL_CODE
        from workflow_tracker import make_location_code
        jobs_by_url = load_jobs()
        buckets     = build_buckets(jobs_by_url, portal_code, locations)
        for (b_portal_name, location), urls in buckets:
            p_code   = PORTAL_CODE.get(b_portal_name, portal_code)
            loc_code = make_location_code(location)
            stages.append('Cycle ' + p_code + '0CARSNG0' + loc_code)
        return stages
    except Exception as e:
        # Was previously a bare "return []" that silently discarded every
        # bucket built so far the moment ANY single bucket failed (e.g. one
        # bad location value hitting make_location_code) — that's what made
        # Portal B/Portal A validator runs show zero Cycle stages instead of
        # a partial list, and Portal C show only the buckets processed before
        # its own failure. Log the real cause and keep whatever was
        # successfully built before the failure instead of throwing it away.
        import traceback
        log_workflow('SYSTEM', '_compute_validator_planned_stages failed for portal_code=' +
                      str(portal_code) + ', locations=' + str(locations) + ': ' +
                      str(e) + '\n' + traceback.format_exc())
        return stages

def _compute_scraper_counter_planned_stages(wf_type, portal_code, keywords, locations):
    """
    Computed once, at creation time — same design as
    _compute_validator_planned_stages() above. Stored permanently on the
    record as 'planned_stages' so the Stages panel shows a fixed list that
    can't shrink or change later if 'keywords'/'locations' on the record
    are ever touched (e.g. by a Retry/Reset action), instead of being
    rebuilt live from those mutable fields on every page render.
    """
    from workflow_tracker import make_stage_code
    prefix = 'Counting ' if wf_type == 'Counter' else 'Cycle '
    # 'AL' isn't produced by enqueue_request() today (each row is always a
    # single portal_code — NK, LI, or IN), but handled here for parity with
    # the old live-build logic in dashboard_detail.py, in case anything
    # else ever creates a record with portal='AL'.
    portals_to_build = ['LI', 'NK', 'IN'] if portal_code == 'AL' else [portal_code]
    stages = []
    for p in portals_to_build:
        for kw in keywords:
            for loc in locations:
                stages.append(prefix + make_stage_code(p, kw, loc))
    return stages


def enqueue_request(stages, portals, keywords, locations):
    """
    Creates one workflow row per (portal, stage) combination, in strict
    portal-major order: for each portal (Portal B, then Portal A, then
    Portal C, in that fixed order regardless of selection order), its own
    Counter -> Scraper -> Validator rows (only for the stages actually
    requested). Any previous still-Waiting rows are superseded first.
    Returns the list of created workflow ids.
    """
    PORTAL_ORDER = ['NK', 'LI', 'IN']
    PORTAL_NAME  = {'NK': 'PortalB', 'LI': 'PortalA', 'IN': 'PortalC'}
    STAGE_ORDER  = ['Counter', 'Scraper', 'Validator']

    clear_old_waiting_workflows()

    created_ids = []
    for portal_code in PORTAL_ORDER:
        if portal_code not in portals:
            continue
        portal_name = PORTAL_NAME[portal_code]
        for stage in STAGE_ORDER:
            if stage not in stages:
                continue
            if stage == 'Counter':
                wf_id = generate_workflow_id('CTR', portal_code)
                planned = _compute_scraper_counter_planned_stages('Counter', portal_code, keywords, locations)
                rec = create_workflow_record(wf_id, 'Counter', portal_code, portal_name, keywords, locations,
                                              planned_stages=planned)
            elif stage == 'Scraper':
                wf_id = generate_workflow_id('SCR', portal_code)
                planned = _compute_scraper_counter_planned_stages('Scraper', portal_code, keywords, locations)
                rec = create_workflow_record(wf_id, 'Scraper', portal_code, portal_name, keywords, locations,
                                              planned_stages=planned)
            else:  # Validator — no keywords needed
                wf_id = generate_workflow_id('VAL', portal_code)
                # planned_stages is NOT computed here — at enqueue time,
                # this portal's Scraper (queued ahead of this Validator row)
                # hasn't run yet, so jobs.csv doesn't have its rows yet
                # either. Computing the bucket snapshot now would freeze in
                # whatever was already there (e.g. only one location) and
                # never see locations/rows the Scraper produces afterward.
                # Computed instead in run_validator_workflow(), right before
                # the subprocess actually starts.
                rec = create_workflow_record(wf_id, 'Validator', portal_code, portal_name, [], locations)
            add_workflow_record(rec)
            log_workflow(wf_id, 'Workflow queued — ' + stage + ' | ' + portal_name)
            created_ids.append(wf_id)

    advance_queue()
    return created_ids

def add_workflow_record(record):
    with _wf_lock:
        data = load_workflows()
        data['workflows'].append(record)
        save_workflows(data)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def log_workflow(wf_id, message):
    log_file = os.path.join(LOGS_DIR, wf_id + '.txt')
    ts   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = ts + ' | ' + wf_id + ' | ' + message + '\n'
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(line)

def read_workflow_log(wf_id):
    log_file = os.path.join(LOGS_DIR, wf_id + '.txt')
    if not os.path.exists(log_file):
        return []
    with open(log_file, 'r', encoding='utf-8') as f:
        return [l.rstrip('\n') for l in f.readlines()]

def read_all_logs(page=1, per_page=50, filter_id=''):
    entries = []
    if not os.path.exists(LOGS_DIR):
        return [], 0
    for fname in sorted(os.listdir(LOGS_DIR)):
        if not fname.endswith('.txt') or fname.endswith('_proc.txt'):
            continue
        fpath = os.path.join(LOGS_DIR, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.rstrip('\n')
                    if not line:
                        continue
                    if filter_id and filter_id.upper() not in line.upper():
                        continue
                    entries.append(line)
        except Exception:
            pass
    entries.sort(reverse=True)
    total = len(entries)
    start = (page - 1) * per_page
    return entries[start:start + per_page], total

# ---------------------------------------------------------------------------
# Subprocess runner
# ---------------------------------------------------------------------------
_process_lock   = threading.Lock()
_active_process = None

def kill_edge():
    """Kill only Edge processes running under the Selenium profile —
    never the user's real default Edge session."""
    try:
        subprocess.call(
            'wmic process where "name=\'msedge.exe\' and '
            'commandline like \'%SeleniumEdgeProfile%\'" call terminate',
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(5)
    except Exception:
        pass

def run_single_workflow(wf_id):
    """Runs one Counter or Scraper workflow row. Fully self-contained —
    reads its own keywords/locations/portal from the stored record, so
    it can be started either as part of an initial submission or later
    by advance_queue() picking it up from the queue. Only advances the
    queue on true success (Complete) — Hold and Failed both stop here
    and leave the rest of the queue untouched until the user acts."""
    def _runner():
        global _active_process

        wf = get_workflow(wf_id)
        if not wf or wf['status'] == STATUS_CANCELLED:
            log_workflow(wf_id, 'Skipped — workflow was cancelled')
            return

        keywords  = wf.get('keywords', [])
        locations = wf.get('locations', [])
        wf_type   = wf['type']
        wf_portal = wf['portal']

        if wf_type == 'Counter':
            script = 'job_counter.py'
        else:
            script = 'scraper.py'

        kill_edge()

        temp_cfg = _write_temp_config(keywords, locations)

        update_workflow(wf_id, status=STATUS_INPROGRESS, stage='Initialising')
        log_workflow(wf_id, 'Workflow started — ' + wf_type + ' | ' + wf_portal)
        log_workflow(wf_id, 'Stage: Initialising')
        log_workflow(wf_id, 'Script: ' + script)
        log_workflow(wf_id, 'Keywords: ' + ', '.join(keywords))
        log_workflow(wf_id, 'Locations: ' + ', '.join(locations))

        proc_log = os.path.join(LOGS_DIR, wf_id + '_proc.txt')
        try:
            env = os.environ.copy()
            env['WF_ID']            = wf_id
            env['WF_PORTAL']        = wf_portal
            env['WF_CONFIG']        = temp_cfg
            env['PYTHONIOENCODING'] = 'utf-8'

            with open(proc_log, 'w', encoding='utf-8', errors='replace') as lf:
                proc = subprocess.Popen(
                    ['python', script],
                    stdout=lf,
                    stderr=lf,
                    cwd=BASE_DIR,
                    env=env
                )
                with _process_lock:
                    _active_process = proc
                update_workflow(wf_id, pid=proc.pid, stage='Connecting to Browser')
                log_workflow(wf_id, 'Stage: Connecting to Browser — PID ' + str(proc.pid))
                proc.wait()

            with _process_lock:
                _active_process = None

            # The user may have pressed Cancel/Revoke while we were
            # blocked in proc.wait() — that already set status=Cancelled
            # and killed the process, which is exactly what makes
            # proc.wait() unblock here with a non-zero return code. Don't
            # let this dying process's own completion logic then flip
            # Cancelled back to Complete/Failed/Hold — check first.
            current = get_workflow(wf_id)
            if current and current['status'] == STATUS_CANCELLED:
                log_workflow(wf_id, 'Process exited after user cancellation — status stays Cancelled')
                return

            if os.path.exists(proc_log):
                with open(proc_log, 'r', encoding='utf-8', errors='replace') as lf:
                    lines = lf.readlines()
                errors = [l.strip() for l in lines if 'error' in l.lower() or 'traceback' in l.lower() or 'exception' in l.lower()]
                for err in errors[:10]:
                    log_workflow(wf_id, 'PROC ERROR: ' + err)

            if os.path.exists(STOP_FILE):
                update_workflow(wf_id, status=STATUS_HOLD)
                log_workflow(wf_id, 'Workflow held — STOP flag detected')
                try:
                    os.remove(STOP_FILE)
                except Exception:
                    pass
                return  # Held — queue stays put until user acts

            elif proc.returncode == 0:
                update_workflow(wf_id, status=STATUS_COMPLETE, stage='Complete')
                log_workflow(wf_id, 'Workflow completed successfully')
                advance_queue()
                return

            else:
                if os.path.exists(proc_log):
                    with open(proc_log, 'r', encoding='utf-8', errors='replace') as lf:
                        tail = lf.readlines()[-30:]
                    for line in tail[-10:]:
                        if line.strip():
                            log_workflow(wf_id, 'ERR: ' + line.strip())
                update_workflow(wf_id, status=STATUS_FAILED, stage='Failed')
                log_workflow(wf_id, 'Workflow FAILED — return code ' + str(proc.returncode))
                return  # Failed — queue halts until user Retries/Cancels

        except Exception as e:
            with _process_lock:
                _active_process = None
            current = get_workflow(wf_id)
            if current and current['status'] == STATUS_CANCELLED:
                log_workflow(wf_id, 'Process exited after user cancellation — status stays Cancelled')
                return
            update_workflow(wf_id, status=STATUS_FAILED, stage='Failed')
            log_workflow(wf_id, 'Workflow exception: ' + str(e))
            return
        finally:
            if os.path.exists(temp_cfg):
                try:
                    os.remove(temp_cfg)
                except Exception:
                    pass

    t = threading.Thread(target=_runner, daemon=True)
    t.start()

def run_validator_workflow(wf_id):
    """Runs one Validator workflow row — single subprocess (validator.py),
    no keywords. Fully self-contained, reads its own portal/locations
    from the stored record. Only advances the queue on true success."""
    def _runner():
        global _active_process

        wf = get_workflow(wf_id)
        if not wf or wf['status'] == STATUS_CANCELLED:
            log_workflow(wf_id, 'Skipped — workflow was cancelled')
            return

        portal    = wf['portal']
        locations = wf.get('locations', [])

        # Computed here, not at enqueue time — by now this portal's Scraper
        # (queued ahead of this Validator row) has already finished and
        # flushed jobs.csv, so the snapshot reflects every location that
        # actually has rows, not just whatever existed when the request
        # was first submitted.
        planned_stages = _compute_validator_planned_stages(portal, wf['scraper'], locations)
        update_workflow(wf_id, planned_stages=planned_stages)

        kill_edge()

        update_workflow(wf_id, status=STATUS_INPROGRESS, stage='Initialising')
        log_workflow(wf_id, 'Workflow started — Validator | ' + portal)
        log_workflow(wf_id, 'Stage: Initialising')
        log_workflow(wf_id, 'Script: validator.py')

        proc_log = os.path.join(LOGS_DIR, wf_id + '_proc.txt')
        try:
            env = os.environ.copy()
            env['WF_ID']            = wf_id
            env['WF_PORTAL']        = portal
            env['WF_LOCATIONS']     = ','.join(locations)
            env['PYTHONIOENCODING'] = 'utf-8'

            with open(proc_log, 'w', encoding='utf-8', errors='replace') as lf:
                proc = subprocess.Popen(
                    ['python', 'validator.py'],
                    stdout=lf,
                    stderr=lf,
                    cwd=BASE_DIR,
                    env=env
                )
                with _process_lock:
                    _active_process = proc
                update_workflow(wf_id, pid=proc.pid, stage='Connecting to Browser')
                log_workflow(wf_id, 'Stage: Connecting to Browser — PID ' + str(proc.pid))
                proc.wait()

            with _process_lock:
                _active_process = None

            # The user may have pressed Cancel/Revoke while we were
            # blocked in proc.wait() — that already set status=Cancelled
            # and killed the process, which is exactly what makes
            # proc.wait() unblock here with a non-zero return code. Don't
            # let this dying process's own completion logic then flip
            # Cancelled back to Complete/Failed/Hold — check first.
            current = get_workflow(wf_id)
            if current and current['status'] == STATUS_CANCELLED:
                log_workflow(wf_id, 'Process exited after user cancellation — status stays Cancelled')
                return

            if os.path.exists(proc_log):
                with open(proc_log, 'r', encoding='utf-8', errors='replace') as lf:
                    lines = lf.readlines()
                errors = [l.strip() for l in lines if 'error' in l.lower() or 'traceback' in l.lower() or 'exception' in l.lower()]
                for err in errors[:10]:
                    log_workflow(wf_id, 'PROC ERROR: ' + err)

            if os.path.exists(STOP_FILE):
                update_workflow(wf_id, status=STATUS_HOLD)
                log_workflow(wf_id, 'Workflow held — STOP flag detected')
                try:
                    os.remove(STOP_FILE)
                except Exception:
                    pass
                return  # Held — queue stays put until user acts

            elif proc.returncode == 0:
                update_workflow(wf_id, status=STATUS_COMPLETE, stage='Complete')
                log_workflow(wf_id, 'Workflow completed successfully')
                advance_queue()
                return

            else:
                if os.path.exists(proc_log):
                    with open(proc_log, 'r', encoding='utf-8', errors='replace') as lf:
                        tail = lf.readlines()[-30:]
                    for line in tail[-10:]:
                        if line.strip():
                            log_workflow(wf_id, 'ERR: ' + line.strip())
                update_workflow(wf_id, status=STATUS_FAILED, stage='Failed')
                log_workflow(wf_id, 'Workflow FAILED — return code ' + str(proc.returncode))
                return  # Failed — queue halts until user Retries/Cancels

        except Exception as e:
            with _process_lock:
                _active_process = None
            current = get_workflow(wf_id)
            if current and current['status'] == STATUS_CANCELLED:
                log_workflow(wf_id, 'Process exited after user cancellation — status stays Cancelled')
                return
            update_workflow(wf_id, status=STATUS_FAILED, stage='Failed')
            log_workflow(wf_id, 'Workflow exception: ' + str(e))
            return

    t = threading.Thread(target=_runner, daemon=True)
    t.start()

def _write_temp_config(keywords, locations):
    cfg = load_config()
    cfg['candidate']['role_keywords'] = keywords
    cfg['candidate']['locations']     = locations
    temp_path = os.path.join(BASE_DIR, '_temp_config.json')
    with open(temp_path, 'w') as f:
        json.dump(cfg, f, indent=2)
    return temp_path

# ---------------------------------------------------------------------------
# File readers
# ---------------------------------------------------------------------------
def read_file_text(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None

def read_profile():
    if not os.path.exists(PROFILE_JSON):
        return {}
    try:
        with open(PROFILE_JSON, 'r') as f:
            return json.load(f)
    except Exception:
        return {}
