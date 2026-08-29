"""
workflow_tracker.py — Stage reporter for scrapers and counter
Called by scraper_portal_b.py, scraper_portal_a.py, job_counter.py
to update live stage in workflows.json and log to logs/<WF_ID>.txt
"""

import os
import json
import threading
from datetime import datetime

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
WORKFLOWS_FILE = os.path.join(BASE_DIR, 'workflows.json')
LOGS_DIR       = os.path.join(BASE_DIR, 'logs')

_lock = threading.Lock()


def _get_wf_id():
    return os.environ.get('WF_ID', '')


def _log(wf_id, message):
    if not wf_id:
        return
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file = os.path.join(LOGS_DIR, wf_id + '.txt')
    ts   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = ts + ' | ' + wf_id + ' | ' + message + '\n'
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(line)


def _update_workflows_json(wf_id, stage):
    if not wf_id or not os.path.exists(WORKFLOWS_FILE):
        return
    try:
        with _lock:
            with open(WORKFLOWS_FILE, 'r') as f:
                data = json.load(f)
            for wf in data.get('workflows', []):
                if wf['id'] == wf_id:
                    wf['stage']        = stage
                    wf['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    break
            with open(WORKFLOWS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Stage code generator
# ---------------------------------------------------------------------------

def make_location_code(location):
    """
    Location code — first 2 alphanumeric + last alphanumeric char:
      - Chennai    → CHI
      - Coimbatore → COE

    Extracted from make_stage_code() so callers with no keyword dimension
    (e.g. validator.py, which uses a fixed 'CARSNG' constant instead of a
    keyword) can build a stage code without routing through the keyword
    encoding logic.
    """
    def alnum_only(s):
        return ''.join(c for c in s if c.isalnum())

    loc = alnum_only(location.strip())
    if len(loc) >= 3:
        return (loc[:2] + loc[-1]).upper()
    elif len(loc) == 2:
        return loc.upper() + '0'
    elif len(loc) == 1:
        return loc.upper() + '00'
    else:
        return '000'


def make_stage_code(portal, keyword, location):
    """
    Generate a compact stage code from portal, keyword and location.

    Format: <PORTAL>0<KW_CODE>0<LOC_CODE>

    Keyword code — first 2 alphanumeric chars of each word (max 3 words):
      - Special characters skipped — only alphanumeric chars taken
      - Numbers / alphanumeric short (e.g. L2) → kept as-is
      - Single alphanumeric char word → char + extra 0 separator
      - Missing word slot → 00

    Location code — see make_location_code().

    Examples:
      NK | Technical Support Engineer | Chennai   → NK0TESUEN0CHI
      NK | Cloud Administrator        | Chennai   → NK0CLAD000CHI
      NK | L2 Support Engineer        | Chennai   → NK0L2SUEN0CHI
      NK | &Cloud Support Engineer    | Chennai   → NK0CLSUEN0CHI
    """
    def alnum_only(s):
        return ''.join(c for c in s if c.isalnum())

    portal_tag = portal.upper()

    words    = keyword.strip().split()
    kw_parts = []
    for word in words[:3]:
        clean = alnum_only(word)
        if not clean:
            kw_parts.append('00')  # word was all special chars
        elif any(c.isdigit() for c in clean):
            kw_parts.append(clean.upper())  # e.g. L2
        elif len(clean) == 1:
            kw_parts.append(clean.upper() + '0')  # single letter
        else:
            kw_parts.append(clean[:2].upper())
    # Pad missing word slots
    while len(kw_parts) < 3:
        kw_parts.append('00')
    kw_code = ''.join(kw_parts)

    loc_code = make_location_code(location)

    return portal_tag + '0' + kw_code + '0' + loc_code


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def update_stage(stage, keyword='', location='', portal=''):
    """
    Call this from scraper/counter at each stage transition.
    Updates workflows.json and writes a log line.

    With keyword+location+portal → compact code:
        update_stage('Counting', keyword='Technical Support Engineer', location='Chennai', portal='NK')
        → 'Counting NK0TESUEN0CHI'

    Without keyword/location → plain stage name:
        update_stage('Initialising')
        update_stage('Complete')
    """
    wf_id = _get_wf_id()
    if not wf_id:
        return

    if keyword and location and portal:
        code       = make_stage_code(portal, keyword, location)
        full_stage = stage + ' ' + code
    elif keyword and location:
        full_stage = stage + ' — ' + keyword + ' | ' + location
    elif keyword:
        full_stage = stage + ' — ' + keyword
    elif location:
        full_stage = stage + ' — ' + location
    else:
        full_stage = stage

    _update_workflows_json(wf_id, full_stage)
    _log(wf_id, 'Stage: ' + full_stage)


def log_info(message):
    """Log an informational message to the workflow log."""
    wf_id = _get_wf_id()
    if not wf_id:
        return
    _log(wf_id, message)


def get_config_path():
    """Returns temp config path if set by dashboard, else config.json."""
    temp = os.environ.get('WF_CONFIG', '')
    if temp and os.path.exists(temp):
        return temp
    return os.path.join(BASE_DIR, 'config.json')
