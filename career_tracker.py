import os
import csv
from workflow_tracker import log_info
CAREER_APPS_CSV  = 'career_apps.csv'
CAREER_SITES_CSV = 'career_sites.csv'

APP_COLUMNS  = ['company', 'link', 'credential', 'credtype', 'passhint', 'role', 'location', 'date', 'stage', 'substage', 'ghostedsub', 'jobid', 'notes']
SITE_COLUMNS = ['name', 'url', 'cred', 'notes']

# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
def load_career_apps():
    if not os.path.exists(CAREER_APPS_CSV):
        return []
    try:
        with open(CAREER_APPS_CSV, 'r', encoding='utf-8', newline='') as f:
            return list(csv.DictReader(f))
    except Exception as e:
        log_info('[CareerTracker] Apps read error: ' + str(e)[:50])
        return []

def load_career_sites():
    if not os.path.exists(CAREER_SITES_CSV):
        return []
    try:
        with open(CAREER_SITES_CSV, 'r', encoding='utf-8', newline='') as f:
            return list(csv.DictReader(f))
    except Exception as e:
        log_info('[CareerTracker] Sites read error: ' + str(e)[:50])
        return []

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
def save_career_apps(rows):
    try:
        with open(CAREER_APPS_CSV, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=APP_COLUMNS, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(rows)
        return True
    except Exception as e:
        log_info('[CareerTracker] Apps write error: ' + str(e)[:50])
        return False

def save_career_sites(rows):
    try:
        with open(CAREER_SITES_CSV, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=SITE_COLUMNS, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(rows)
        return True
    except Exception as e:
        log_info('[CareerTracker] Sites write error: ' + str(e)[:50])
        return False
