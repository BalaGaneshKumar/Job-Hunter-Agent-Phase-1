import json
import re

STATE_FILE = 'search_state.json'

DEFAULT_STATE = {'portal_b': {}, 'portal_a': {}, 'portal_c': {}, 'jobs_found': []}

def load_search_state():
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        # Ensure all required keys exist even if file is old/partial
        for key in DEFAULT_STATE:
            if key not in state:
                state[key] = DEFAULT_STATE[key]
        return state
    except Exception:
        return {'portal_b': {}, 'portal_a': {}, 'jobs_found': []}

def save_search_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)

# --- Page tracking ---

def get_page(portal, keyword, location):
    state = load_search_state()
    key   = keyword + '||' + location
    entry = state[portal].get(key, {})
    return entry.get('page', 1)

def save_page(portal, keyword, location, page):
    state = load_search_state()
    key   = keyword + '||' + location
    if key not in state[portal]:
        state[portal][key] = {}
    state[portal][key]['page'] = page
    save_search_state(state)

def reset_portal(portal, keyword, location):
    save_page(portal, keyword, location, 1)

def mark_completed(portal, keyword, location):
    state = load_search_state()
    key   = keyword + '||' + location
    if key not in state[portal]:
        state[portal][key] = {}
    state[portal][key]['page']      = 1
    state[portal][key]['completed'] = True
    save_search_state(state)

def is_completed(portal, keyword, location):
    state = load_search_state()
    key   = keyword + '||' + location
    return state[portal].get(key, {}).get('completed', False)

# --- Job count + timing (set by job_counter.py) ---

def save_job_count(portal, keyword, location, total_jobs, estimated_seconds):
    state = load_search_state()
    key   = keyword + '||' + location
    entry = state[portal].get(key, {})

    entry['total_jobs']        = total_jobs
    entry['estimated_seconds'] = estimated_seconds
    entry['counted']           = True
    # page/completed are owned by the scraper only — counter never touches them
    entry.setdefault('page', 1)
    entry.setdefault('completed', False)

    state[portal][key] = entry
    save_search_state(state)

def is_counted(portal, keyword, location):
    state = load_search_state()
    key   = keyword + '||' + location
    return state[portal].get(key, {}).get('counted', False)

def reset_scraper_flag(portal, keyword, location):
    """Called by counter before it counts a combo — clears scraper's completed
    flag so scraper doesn't stall thinking it's done while counter re-counts."""
    state = load_search_state()
    key   = keyword + '||' + location
    entry = state[portal].get(key, {})
    entry['completed'] = False
    state[portal][key] = entry
    save_search_state(state)

def reset_counter_flag(portal, keyword, location):
    """Called by scraper before it scrapes a combo — clears counter's counted
    flag so counter doesn't stall/skip while scraper starts a fresh pass."""
    state = load_search_state()
    key   = keyword + '||' + location
    entry = state[portal].get(key, {})
    entry['counted'] = False
    state[portal][key] = entry
    save_search_state(state)

def get_job_count(portal, keyword, location):
    state = load_search_state()
    key   = keyword + '||' + location
    entry = state[portal].get(key, {})
    return entry.get('total_jobs', 0), entry.get('estimated_seconds', 0)

def get_total_runtime(portal):
    state   = load_search_state()
    total   = sum(v.get('estimated_seconds', 0) for v in state[portal].values())
    hours   = total // 3600
    minutes = (total % 3600) // 60
    return total, str(hours) + 'h ' + str(minutes) + 'm'

# --- Jobs found buffer ---

def save_job_to_state(job):
    state = load_search_state()
    if 'jobs_found' not in state:
        state['jobs_found'] = []
    existing_urls = {j['url'] for j in state['jobs_found']}
    if job['url'] not in existing_urls:
        state['jobs_found'].append(job)
        save_search_state(state)

def get_saved_jobs():
    state = load_search_state()
    return state.get('jobs_found', [])

def clear_saved_jobs():
    state = load_search_state()
    state['jobs_found'] = []
    save_search_state(state)

def get_total_pages(total_jobs, per_page=25):
    if total_jobs == 0:
        return 1
    return (total_jobs + per_page - 1) // per_page

def estimate_runtime(total_jobs, seconds_per_job=45):
    total_seconds = total_jobs * seconds_per_job
    hours         = total_seconds // 3600
    minutes       = (total_seconds % 3600) // 60
    return str(hours) + 'h ' + str(minutes) + 'm'
