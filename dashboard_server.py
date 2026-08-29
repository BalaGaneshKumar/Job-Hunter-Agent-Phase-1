"""
dashboard_server.py — Job Hunter Agent Dashboard Server
Run: python dashboard_server.py
Open: http://localhost:8080
"""

import json
import signal
import os
import csv
import datetime
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from career_tracker import load_career_apps, load_career_sites, save_career_apps, save_career_sites

# ---------------------------------------------------------------------------
# Import all modules
# ---------------------------------------------------------------------------
from dashboard_workflows import (
    load_config, save_config, load_workflows, read_all_logs, read_workflow_log,
    get_workflow, get_running_workflow, update_workflow, add_workflow_record,
    create_workflow_record, generate_workflow_id, log_workflow,
    run_single_workflow, run_validator_workflow, enqueue_request,
    clear_old_waiting_workflows,
    read_file_text, read_profile,
    STATUS_INPROGRESS, STATUS_RETRY, STATUS_HOLD, STATUS_FAILED,
    STATUS_WAITING, STATUS_CANCELLED,
    JOBS_CSV, BLACKLIST_CSV, PROFILE_JSON, STOP_FILE, BASE_DIR
)
from dashboard_ui import esc, html_page, CSS
from dashboard_jobs import build_jobs_html, build_jobs_js
from dashboard_scraper import build_scraper_html, build_scraper_js
from dashboard_detail import build_workflow_detail_html
from dashboard_career import build_career_html, build_career_js
from dashboard_backup import run_onedrive_backup

# ---------------------------------------------------------------------------
# Main dashboard HTML builder
# ---------------------------------------------------------------------------
def build_dashboard_html(active_tab='jobs', subtab=None):
    cfg       = load_config()
    keywords  = cfg.get('candidate', {}).get('role_keywords', [])
    locations = cfg.get('candidate', {}).get('locations', [])
    blacklist = cfg.get('blacklist', [])
    profile   = read_profile()

    kw_json   = json.dumps(keywords)
    loc_json  = json.dumps(locations)
    bl_json   = json.dumps(blacklist)
    prof_json = json.dumps(profile)

    body = '''
<div class="header">
  <h1>🌌 Bala's Solaris</h1>
  <button id="onedrive_btn" onclick="oneDriveBackup()" style="padding:8px 16px;border:none;border-radius:6px;cursor:pointer;font-size:13px;font-weight:bold;background:#0078d4;color:white;">☁️ One Drive Uploader</button>
  <div class="nav">
    <button class="''' + ('active' if active_tab!='scraper' else '') + '''" onclick="showPage(\'jobs\',this)">🪐 Job Odyssey</button>
    <button onclick="showPage(\'career\',this)">🚀 Career Voyager</button>
    <button onclick="showPage(\'profile\',this)">⭐ Profile Nexus</button>
    <button class="''' + ('active' if active_tab=='scraper' else '') + '''" onclick="showPage(\'scraper\',this)">🌀 Scraper Abyss</button>
  </div>
</div>
<div id="undo_bar" class="undo-bar"><span id="undo_msg"></span><button onclick="undoStatus()">&#8617; Undo</button><button onclick="hideUndoBar()" style="background:#555;">&#10005;</button></div><div class="status-bar" id="status_bar">Loading jobs.csv...</div>
''' + build_jobs_html(cfg, kw_json, loc_json, bl_json, prof_json, locations) + '''
''' + build_scraper_html() + '''
''' + build_career_html() + '''
<script>
''' + build_jobs_js(kw_json, loc_json, bl_json, prof_json) + '''
''' + build_scraper_js() + '''
''' + build_career_js() + '''
async function oneDriveBackup(){
  const btn = document.getElementById('onedrive_btn');
  const orig = btn.textContent;
  btn.disabled = true; btn.textContent = '⏳ Backing up...';
  try{
    const r = await fetch('/api/onedrive-backup', {method:'POST'});
    const d = await r.json();
    if(d.ok){
      const c = d.counts || {};
      const summary = Object.keys(c).map(k=>k+': '+c[k]).join(', ');
      document.getElementById('status_bar').textContent = '✅ Backed up to ' + d.path + ' (' + summary + ')';
    } else {
      document.getElementById('status_bar').textContent = '⚠️ Backup failed: ' + (d.error||'unknown error');
    }
  } catch(e){
    document.getElementById('status_bar').textContent = '⚠️ Backup failed: could not reach server';
  } finally {
    btn.disabled = false; btn.textContent = orig;
  }
}
var INITIAL_SUBTAB = ''' + json.dumps(subtab or '') + ''';
function renderPagination(containerId,cur,total,onPage){
  const c=document.getElementById(containerId);
  if(total<=1){c.innerHTML='';return;}
  let h='<button '+(cur===1?'disabled':'')+' onclick="('+onPage.toString()+')('+(cur-1)+')">&#8249;</button>';
  const s=Math.max(1,cur-2),e=Math.min(total,cur+2);
  if(s>1)h+='<button onclick="('+onPage.toString()+')(1)">1</button>'+(s>2?'<span>&#8230;</span>':'');
  for(let p=s;p<=e;p++)h+='<button class="'+(p===cur?'active-page':'')+'" onclick="('+onPage.toString()+')('+p+')">'+p+'</button>';
  if(e<total)h+=(e<total-1?'<span>&#8230;</span>':'')+'<button onclick="('+onPage.toString()+')('+total+')">'+total+'</button>';
  h+='<button '+(cur===total?'disabled':'')+' onclick="('+onPage.toString()+')('+(cur+1)+')">&#8250;</button>';
  c.innerHTML=h;
}
</script>
'''
    return html_page("Bala's Solaris", body)

# ---------------------------------------------------------------------------
# HTTP Handler
# ---------------------------------------------------------------------------
class DashboardHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        if args and str(args[1]) not in ('200', '304'):
            print('[Server] ' + format % args, flush=True)

    def send_json(self, data, code=200):
        try:
            body = json.dumps(data).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(body))
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError):
            pass  # Browser closed connection — ignore silently

    def send_html(self, html, code=200):
        try:
            body = html.encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(body))
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError):
            pass

    def read_body(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            if not length:
                return {}
            raw = self.rfile.read(length)
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            self.send_json({'ok': False, 'error': 'Browser is busy, please try again in a moment.'}, 503)
            return None
        except Exception:
            return {}

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path
        qs     = parse_qs(parsed.query)

        if path in ('/', '/dashboard'):
            self.send_html(build_dashboard_html('jobs'))

        elif path in ('/scraper', '/scraper/workflow'):
            self.send_html(build_dashboard_html('scraper', subtab='workflow'))

        elif path == '/scraper/request':
            self.send_html(build_dashboard_html('scraper', subtab='request'))

        elif path == '/scraper/log':
            self.send_html(build_dashboard_html('scraper', subtab='log'))

        elif path == '/career':
            self.send_html(build_dashboard_html('career'))

        elif path == '/profile':
            self.send_html(build_dashboard_html('profile'))

        elif path.startswith('/workflow/'):
            wf_id = path.split('/')[-1].strip()
            self.send_html(build_workflow_detail_html(wf_id))

        elif path == '/api/workflows':
            page     = int(qs.get('page', ['1'])[0])
            sort_col = qs.get('sort', ['start_date'])[0]
            sort_dir = int(qs.get('dir', ['-1'])[0])
            data     = load_workflows()
            wfs      = data.get('workflows', [])
            running  = [w for w in wfs if w['status'] in (STATUS_INPROGRESS, STATUS_RETRY)]
            others   = [w for w in wfs if w['status'] not in (STATUS_INPROGRESS, STATUS_RETRY)]
            try:
                others.sort(key=lambda w: w.get(sort_col, ''), reverse=(sort_dir == -1))
            except Exception:
                pass
            sorted_wfs = running + others
            total = len(sorted_wfs)
            paged = sorted_wfs[(page - 1) * 20: page * 20]
            self.send_json({'workflows': paged, 'total': total})

        elif path == '/api/logs':
            page      = int(qs.get('page', ['1'])[0])
            filter_id = qs.get('filter', [''])[0]
            per_page  = int(qs.get('per_page', ['50'])[0])
            entries, total = read_all_logs(page=page, per_page=per_page, filter_id=filter_id)
            self.send_json({'entries': entries, 'total': total})

        elif path == '/api/running-workflow':
            wf = get_running_workflow()
            self.send_json({'running': bool(wf), 'id': wf['id'] if wf else ''})

        elif path.startswith('/api/workflow-status/'):
            wf_id_req = path[len('/api/workflow-status/'):]
            wf_req    = get_workflow(wf_id_req)
            if not wf_req:
                self.send_json({'error': 'not found'})
            else:
                # Use the same uncapped single-workflow reader as the initial
                # page load — read_all_logs() is for the cross-workflow
                # global Logs tab and was truncating this to 100 entries,
                # silently hiding everything older on every auto-refresh.
                log_entries = list(reversed(read_workflow_log(wf_id_req)))

                response = {
                    'status':       wf_req.get('status', ''),
                    'stage':        wf_req.get('stage', ''),
                    'updated_date': wf_req.get('updated_date', ''),
                    'log_entries':  log_entries
                }

                self.send_json(response)

        elif path == '/api/jobs-csv':
            content = read_file_text(JOBS_CSV)
            if content:
                self.send_json({'content': content})
            else:
                self.send_json({'error': 'jobs.csv not found'})

        elif path == '/api/blacklist-csv':
            content = read_file_text(BLACKLIST_CSV)
            if content:
                self.send_json({'content': content})
            else:
                self.send_json({'error': 'blacklist.csv not found'})

        elif path == '/api/career-load':
            self.send_json({
                'apps':  load_career_apps(),
                'sites': load_career_sites()
            })

        else:
            self.send_html('<h1>404</h1>', 404)

    def do_POST(self):
        path = urlparse(self.path).path
        body = self.read_body()
        if body is None:
            return  # read_body already sent 503

        if path == '/api/submit':
            stages    = body.get('stages', [])
            portals   = body.get('portals', [])
            keywords  = body.get('keywords', [])
            locations = body.get('locations', [])

            valid_stages  = {'Counter', 'Scraper', 'Validator'}
            valid_portals = {'NK', 'LI', 'IN'}
            stages  = [s for s in stages if s in valid_stages]
            portals = [p for p in portals if p in valid_portals]

            if not stages:
                self.send_json({'ok': False, 'error': 'Select at least one of Counter/Scraper/Validator.'})
                return
            if not portals:
                self.send_json({'ok': False, 'error': 'Select at least one portal.'})
                return
            if not locations:
                self.send_json({'ok': False, 'error': 'Select at least one location.'})
                return
            needs_keywords = ('Counter' in stages) or ('Scraper' in stages)
            if needs_keywords and not keywords:
                self.send_json({'ok': False, 'error': 'Select at least one keyword.'})
                return

            # enqueue_request() creates all rows in strict portal-major
            # order (Portal B: Counter->Scraper->Validator, then Portal A,
            # then Portal C — only for the stages actually selected), clears
            # any leftover Waiting rows from a prior submission, and starts
            # the first one immediately if nothing is currently running.
            created_ids = enqueue_request(stages, portals, keywords, locations)
            self.send_json({'ok': True, 'workflow_ids': created_ids})

        elif path == '/api/workflow-action':
            wf_id  = body.get('id', '')
            action = body.get('action', '')
            wf     = get_workflow(wf_id)
            if not wf:
                self.send_json({'ok': False, 'error': 'Workflow not found'})
                return

            if action == 'hold':
                with open(STOP_FILE, 'w') as f:
                    f.write('HOLD')
                log_workflow(wf_id, 'User pressed Hold')
                log_workflow(wf_id, 'Hold requested — STOP flag written')
                self.send_json({'ok': True})

            elif action == 'retry':
                if wf['status'] not in (STATUS_HOLD, STATUS_FAILED):
                    self.send_json({'ok': False, 'error': 'Can only retry Hold or Failed workflows'})
                    return
                running = get_running_workflow()
                if running and running['id'] != wf_id:
                    self.send_json({'ok': False, 'error': 'Another workflow is running: ' + running['id']})
                    return
                update_workflow(wf_id, status=STATUS_RETRY, stage='Initialising')
                log_workflow(wf_id, 'User pressed Retry')
                log_workflow(wf_id, 'Retry initiated')
                if wf.get('type') == 'Validator':
                    run_validator_workflow(wf_id)
                else:
                    run_single_workflow(wf_id)
                self.send_json({'ok': True})

            elif action == 'cancel':
                if wf['status'] in (STATUS_CANCELLED, 'Complete'):
                    self.send_json({'ok': False, 'error': 'Workflow is already ' + wf['status'] + '.'})
                    return

                if wf['status'] in (STATUS_INPROGRESS, STATUS_RETRY):
                    # Something's actually running — kill it first, same
                    # mechanism as Revoke, before marking Cancelled.
                    from dashboard_workflows import _active_process, _process_lock
                    with _process_lock:
                        if _active_process:
                            try:
                                _active_process.kill()
                                log_workflow(wf_id, 'Cancelled while running — process killed (PID ' + str(_active_process.pid) + ')')
                            except Exception as e:
                                log_workflow(wf_id, 'Cancel (kill) error: ' + str(e))
                        elif wf.get('pid'):
                            try:
                                subprocess.call('taskkill /F /T /PID ' + str(wf['pid']), shell=True,
                                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                log_workflow(wf_id, 'Cancelled while running — killed by stored PID ' + str(wf['pid']))
                            except Exception as e:
                                log_workflow(wf_id, 'Cancel (kill by PID) error: ' + str(e))
                        import dashboard_workflows
                        dashboard_workflows._active_process = None

                update_workflow(wf_id, status=STATUS_CANCELLED, stage='Cancelled')
                log_workflow(wf_id, 'User pressed Cancel')
                log_workflow(wf_id, 'Workflow cancelled by user')

                # Cancel is the "stop everything" action (Hold is the
                # graceful pause, Revoke is the emergency kill for the
                # active one) — so it also clears out the rest of the
                # queue behind it, not just this one row.
                clear_old_waiting_workflows()
                log_workflow(wf_id, 'Remaining queued workflows also cancelled')

                self.send_json({'ok': True})

            elif action == 'revoke':
                if wf['status'] not in (STATUS_INPROGRESS, STATUS_RETRY):
                    self.send_json({'ok': False, 'error': 'Can only revoke In Progress workflows'})
                    return
                from dashboard_workflows import _active_process, _process_lock
                with _process_lock:
                    if _active_process:
                        try:
                            _active_process.kill()
                            log_workflow(wf_id, 'User pressed Revoke')
                            log_workflow(wf_id, 'Revoked — process killed (PID ' + str(_active_process.pid) + ')')
                        except Exception as e:
                            log_workflow(wf_id, 'Revoke error: ' + str(e))
                    elif wf.get('pid'):
                        # Dashboard was restarted — no in-memory handle. Fall back to the
                        # PID stored in workflows.json. /T kills the whole process tree
                        # (python.exe + its Edge child), not just the top process.
                        try:
                            subprocess.call('taskkill /F /T /PID ' + str(wf['pid']), shell=True,
                                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            log_workflow(wf_id, 'User pressed Revoke')
                            log_workflow(wf_id, 'Revoked — killed by stored PID ' + str(wf['pid']) + ' (no active process handle, likely dashboard restart)')
                        except Exception as e:
                            log_workflow(wf_id, 'Revoke by PID error: ' + str(e))
                    import dashboard_workflows
                    dashboard_workflows._active_process = None
                update_workflow(wf_id, status=STATUS_FAILED, stage='Failed — Revoked')
                self.send_json({'ok': True})

            else:
                self.send_json({'ok': False, 'error': 'Unknown action: ' + action})

        elif path == '/api/save-profile':
            try:
                with open(PROFILE_JSON, 'w') as f:
                    json.dump(body, f, indent=4)
                self.send_json({'ok': True})
            except Exception as e:
                self.send_json({'ok': False, 'error': str(e)})

        elif path == '/api/save-jobs':
            try:
                with open(JOBS_CSV, 'w', encoding='utf-8', newline='') as f:
                    f.write(body.get('csv', ''))
                self.send_json({'ok': True})
            except Exception as e:
                self.send_json({'ok': False, 'error': str(e)})

        elif path == '/api/update-job-status':
            # Merge-on-save: re-reads jobs.csv fresh (picking up anything a
            # background scraper/validator run appended in the meantime),
            # updates only the row matching this URL, and writes the rest of
            # the file back untouched. This avoids the full-file-replace risk
            # of /api/save-jobs silently dropping rows a background job added
            # after the browser last loaded its copy.
            try:
                url = body.get('url', '').strip()
                new_status = body.get('status', '')
                if not url:
                    self.send_json({'ok': False, 'error': 'No URL provided'})
                    return
                if not os.path.exists(JOBS_CSV):
                    self.send_json({'ok': False, 'error': 'jobs.csv not found'})
                    return
                with open(JOBS_CSV, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.DictReader(f)
                    fieldnames = reader.fieldnames
                    rows = list(reader)
                matched = 0
                for row in rows:
                    if row.get('URL', '').strip() == url:
                        row['Status'] = new_status
                        matched += 1
                if not matched:
                    self.send_json({'ok': False, 'error': 'No job found with that URL — it may have been removed since this page loaded.'})
                    return
                with open(JOBS_CSV, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
                self.send_json({'ok': True, 'matched': matched})
            except Exception as e:
                self.send_json({'ok': False, 'error': str(e)})

        elif path == '/api/save-config':
            try:
                cfg = load_config()
                cfg['candidate']['role_keywords'] = body.get('role_keywords', cfg['candidate']['role_keywords'])
                cfg['candidate']['locations']     = body.get('locations', cfg['candidate']['locations'])
                cfg['blacklist']                  = body.get('blacklist', cfg.get('blacklist', []))
                save_config(cfg)
                self.send_json({'ok': True})
            except Exception as e:
                self.send_json({'ok': False, 'error': str(e)})

        elif path == '/api/reform-job':
            try:
                url = body.get('url', '').strip()
                title = body.get('title', '')
                company = body.get('company', '')
                portal = body.get('portal', '')
                if not url:
                    self.send_json({'ok': False, 'error': 'No URL provided'})
                    return
                COLUMNS = ['Job ID','Job Title','Company','Portal','Location','URL','Status','Applied Date','Last Checked','Description','Notes']
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                new_row = {'Job ID': '', 'Job Title': title, 'Company': company,
                           'Portal': portal, 'Location': '', 'URL': url,
                           'Status': 'Scraped', 'Applied Date': '', 'Last Checked': now,
                           'Description': '', 'Notes': 'Reformed from blacklist'}
                existing = {}
                if os.path.exists(JOBS_CSV):
                    with open(JOBS_CSV, 'r', encoding='utf-8', newline='') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            existing[row.get('URL','').strip()] = row
                if url not in existing:
                    existing[url] = new_row
                    with open(JOBS_CSV, 'w', encoding='utf-8', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=COLUMNS)
                        writer.writeheader()
                        writer.writerows(existing.values())
                self.send_json({'ok': True})
            except Exception as e:
                self.send_json({'ok': False, 'error': str(e)})

        elif path == '/api/reset-workflow':
            wf_id = body.get('id', '')
            wf    = get_workflow(wf_id)
            if not wf:
                self.send_json({'ok': False, 'error': 'Workflow not found'})
                return
            try:
                import sys
                sys.path.insert(0, BASE_DIR)
                from search_state import (
                    load_search_state, save_search_state,
                    get_saved_jobs, clear_saved_jobs
                )
                from tracker import batch_write_jobs, initialize_scraper_excel, sync_to_master
                log_workflow(wf_id, 'User pressed Reset')

                wf_type = wf.get('type', '')

                # Validator never touches jobs.csv mid-run — every job's
                # result is written to a staging file
                # (jobs_validating.<wf_id>.csv, same naming convention as
                # validator.py's staging_path()) and only merged into
                # jobs.csv when the run reaches Complete. So Reset is just
                # deleting that staging file: jobs.csv is already untouched
                # by construction, and the next Retry rebuilds its working
                # set from jobs.csv from scratch regardless of whether a
                # stale staging file exists.
                if wf_type == 'Validator':
                    staging_file = os.path.join(BASE_DIR, 'jobs_validating.' + wf_id + '.csv')
                    if os.path.exists(staging_file):
                        os.remove(staging_file)
                        log_workflow(wf_id, 'Reset — validator staging file cleared, jobs.csv untouched')
                    else:
                        log_workflow(wf_id, 'Reset — no staging file to clear, jobs.csv untouched')
                    self.send_json({'ok': True})
                    return

                # Only Scraper stages jobs into search_state's pending list —
                # Counter never flushes anything, it just resets its own
                # counted/total_jobs/estimated_seconds fields below (not
                # page/completed — those belong to Scraper).
                if wf_type == 'Scraper':
                    pending = get_saved_jobs()
                    if pending:
                        initialize_scraper_excel()
                        written = batch_write_jobs(pending)
                        clear_saved_jobs()
                        sync_to_master()
                        log_workflow(wf_id, 'Reset — flushed ' + str(written) + ' pending jobs to Excel and synced')
                    else:
                        log_workflow(wf_id, 'Reset — no pending jobs to flush')

                # Reset pages for this workflow's portal + keywords + locations
                portal    = wf.get('portal', '').upper()
                keywords  = wf.get('keywords', [])
                locations = wf.get('locations', [])
                portals   = []
                if portal == 'NK':
                    portals = ['portal_b']
                elif portal == 'LI':
                    portals = ['portal_a']
                elif portal == 'IN':
                    portals = ['portal_c']
                else:
                    portals = ['portal_b', 'portal_a', 'portal_c']
                state = load_search_state()
                reset_count = 0
                for p in portals:
                    for kw in keywords:
                        for loc in locations:
                            key = kw + '||' + loc
                            entry = state.get(p, {}).get(key)
                            if entry is None:
                                continue
                            if wf_type == 'Counter':
                                entry['counted']           = False
                                entry['total_jobs']        = 0
                                entry['estimated_seconds'] = 0
                            else:
                                entry['page']      = 1
                                entry['completed'] = False
                            reset_count += 1
                save_search_state(state)
                if wf_type == 'Counter':
                    log_workflow(wf_id, 'Reset — ' + str(reset_count) + ' keyword/location counts cleared (counted/total_jobs/estimated_seconds)')
                else:
                    log_workflow(wf_id, 'Reset — ' + str(reset_count) + ' keyword/location pages reset to 1, completed flags cleared')
                log_workflow(wf_id, 'Reset complete — press Retry to restart from beginning')
                self.send_json({'ok': True})
            except Exception as e:
                log_workflow(wf_id, 'Reset error: ' + str(e))
                self.send_json({'ok': False, 'error': str(e)})

        elif path == '/api/onedrive-backup':
            result = run_onedrive_backup()
            self.send_json(result)

        elif path == '/api/career-save':
            try:
                ok_a = save_career_apps(body.get('apps', []))
                ok_s = save_career_sites(body.get('sites', []))
                self.send_json({'ok': ok_a and ok_s})
            except Exception as e:
                self.send_json({'ok': False, 'error': str(e)[:50]})
        else:
            self.send_json({'ok': False, 'error': 'Unknown endpoint'}, 404)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    port   = 8080
    server = HTTPServer(('localhost', port), DashboardHandler)

    print('=' * 45, flush=True)
    print('  Job Hunter Dashboard', flush=True)
    print('  http://localhost:' + str(port), flush=True)
    print('  Press Ctrl+C to stop', flush=True)
    print('=' * 45, flush=True)

    def handle_sigint(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, handle_sigint)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n[Server] Stopped.', flush=True)
    finally:
        server.server_close()
