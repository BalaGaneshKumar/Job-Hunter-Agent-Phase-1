"""
dashboard_detail.py — Workflow detail page HTML
Imported by dashboard_server.py
"""
from dashboard_ui import esc, html_page
from dashboard_workflows import (
    get_workflow, read_workflow_log,
    STATUS_SYMBOL, STATUS_LEGEND,
    STATUS_WAITING, STATUS_INPROGRESS, STATUS_HOLD,
    STATUS_RETRY, STATUS_FAILED, STATUS_CANCELLED
)


def build_workflow_detail_html(wf_id):
    wf = get_workflow(wf_id)
    if not wf:
        return html_page('Not Found',
            '<div style="padding:40px;text-align:center;color:#999;">Workflow not found: ' + wf_id + '</div>')

    status  = wf['status']
    symbol  = STATUS_SYMBOL.get(status, '?')
    portal  = wf.get('portal', 'AL')
    keywords  = wf.get('keywords', [])
    locations = wf.get('locations', [])
    should_refresh = status in (STATUS_INPROGRESS, STATUS_RETRY)

    # Action buttons
    def action_btn(label, action, color):
        return ('<button onclick="wfAction(\'' + action + '\')" style="background:' + color +
                ';color:white;border:none;padding:9px 20px;border-radius:7px;font-size:13px;'
                'font-weight:bold;cursor:pointer;margin-right:6px;">' + label + '</button>')

    buttons = ''
    if status in (STATUS_INPROGRESS, STATUS_RETRY):
        buttons += action_btn('&#9208; Hold',   'hold',   '#ff9800')
        buttons += action_btn('&#128128; Revoke', 'revoke', '#e74c3c')
    if status in (STATUS_HOLD, STATUS_FAILED):
        buttons += action_btn('&#128260; Retry',  'retry',  '#3498db')
        buttons += action_btn('&#128257; Reset',  'reset',  '#8e44ad')
    if status not in ('Complete', STATUS_CANCELLED):
        buttons += action_btn('&#128683; Cancel', 'cancel', '#95a5a6')

    # Build stage list from the snapshot taken once at creation time
    # (see _compute_scraper_counter_planned_stages / _compute_validator_
    # planned_stages in dashboard_workflows.py) — never recomputed live
    # from 'keywords'/'locations' here, so it can't shrink or change if
    # those mutable fields are ever touched after creation (e.g. by a
    # Retry/Reset action). Same design for Counter, Scraper, and Validator.
    is_validator = (wf['type'] == 'Validator')
    if wf['type'] == 'Counter':
        stages = ['Initialising', 'Connecting to Browser']
        stages.extend(wf.get('planned_stages', []))
        stages.append('Complete')
    elif is_validator:
        stages = ['Create Order', 'Connecting to Browser']
        stages.extend(wf.get('planned_stages', []))
        stages.append('Complete')
    else:
        stages = ['Initialising', 'Connecting to Browser', 'Loading Saved State']
        stages.extend(wf.get('planned_stages', []))
        stages.append('Complete')

    # Match current stage
    current_stage = wf.get('stage', '')
    found_current = False
    stage_rows    = ''
    for s in stages:
        if s == current_stage:
            if status == STATUS_HOLD:
                icon = '⏸'
            elif status == STATUS_FAILED:
                icon = '❌'
            elif status == STATUS_CANCELLED:
                icon = '🚫'
            else:
                icon = STATUS_SYMBOL.get(status, '&#128993;')
            color = '#fffde7'
            found_current = True
        elif not found_current:
            icon  = '&#10003;'
            color = '#f0fff0'
        else:
            icon  = '&#9203;' if status not in (STATUS_HOLD, STATUS_FAILED, STATUS_CANCELLED) else '&#9203;'
            color = '#f8f9fa'
        stage_rows += ('<tr style="background:' + color + ';">'
                      '<td style="padding:10px 14px;font-size:18px;">' + icon + '</td>'
                      '<td style="padding:10px 14px;font-size:13px;font-family:monospace;">' + esc(s) + '</td>'
                      '</tr>')
    stage_panel_html = '<table style="width:100%;border-collapse:collapse;">' + stage_rows + '</table>'

    if is_validator:
        kw_loc_html = ''
    else:
        kw_loc_html = (
            '<div style="font-size:13px;color:#666;margin-bottom:5px;">Keywords: <b>' + esc(', '.join(keywords)) + '</b></div>'
            '<div style="font-size:13px;color:#666;margin-bottom:5px;">Locations: <b>' + esc(', '.join(locations)) + '</b></div>'
        )

    # Status legend
    legend_rows = ''.join(
        '<tr><td style="font-size:16px;padding:3px 10px;">' + sym + '</td>'
        '<td style="padding:3px 10px;font-weight:bold;font-size:12px;">' + esc(name) + '</td>'
        '<td style="padding:3px 10px;color:#666;font-size:12px;">' + esc(desc) + '</td></tr>'
        for sym, name, desc in STATUS_LEGEND
    )

    # Logs
    log_entries = read_workflow_log(wf_id)
    import re as _re
    _DATE_RE = _re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')
    _WFID_RE = _re.compile(r'WFI[A-Z]{8}\d{4}')

    def _parse(line):
        dm = _DATE_RE.match(line)
        date = dm.group(1) if dm else ''
        rest = line[len(dm.group(0)):] if dm else line
        wm = _WFID_RE.search(rest)
        if wm: rest = rest[rest.index(wm.group(0)) + len(wm.group(0)):]
        return date, rest.lstrip(' |')

    log_rows = ''.join(
        '<tr><td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-family:monospace;'
        'font-size:12px;color:#888;white-space:nowrap;vertical-align:top;">' + esc(d) +
        '</td><td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-family:monospace;'
        'font-size:12px;word-break:break-all;vertical-align:top;">' + esc(m) + '</td></tr>'
        for d, m in (_parse(e) for e in reversed(log_entries))
    )
    log_html = (
        '<table style="width:100%;border-collapse:collapse;">'
        '<thead><tr style="background:#2c3e50;">'
        '<th style="text-align:left;padding:8px 10px;color:white;font-weight:bold;font-size:12px;">Date</th>'
        '<th style="text-align:left;padding:8px 10px;color:white;font-weight:bold;font-size:12px;">Message</th>'
        '</tr></thead><tbody>' + log_rows + '</tbody></table>'
    ) if log_entries else '<div style="padding:20px;text-align:center;color:#999;">No log entries yet.</div>'

    refresh_js = '''
// Save scroll before unload
window.addEventListener('beforeunload', function(){
  sessionStorage.setItem('wf_scroll', window.scrollY);
  const st = document.getElementById('stages_scroll');
  if(st) sessionStorage.setItem('wf_stages_scroll', st.scrollTop);
  const lg = document.getElementById('logs_scroll');
  if(lg) sessionStorage.setItem('wf_logs_scroll', lg.scrollTop);
});
window.addEventListener('load', function(){
  const s = sessionStorage.getItem('wf_scroll');
  if(s) window.scrollTo(0, parseInt(s));
  const st = document.getElementById('stages_scroll');
  if(st){ const ss=sessionStorage.getItem('wf_stages_scroll'); if(ss) st.scrollTop=parseInt(ss); }
  const lg = document.getElementById('logs_scroll');
  if(lg){ const ls=sessionStorage.getItem('wf_logs_scroll'); if(ls) lg.scrollTop=parseInt(ls); }
});
''' if should_refresh else ''

    auto_refresh_js = '''
let _detailAutoOn = false;
let _detailTimer  = null;
const TERMINAL_ST = new Set(['Complete','Failed','Cancelled','Hold']);
const ST_SYMBOL   = {'Waiting':'⏳','In Progress':'🟡','Hold':'⏸','Retry':'🔄','Complete':'✅','Failed':'❌','Cancelled':'🚫'};
const D_DATE_RE   = /^(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2})/;
const D_WFID_RE   = /WFI[A-Z]{8}\\d{4}/;
const ALL_STAGES  = ''' + '[' + ','.join('"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"' for s in stages) + ']' + ''';
const IS_VALIDATOR = ''' + ('true' if is_validator else 'false') + ''';

function _parseLog(line){
  const dm=line.match(D_DATE_RE); const date=dm?dm[1]:'';
  let rest=dm?line.slice(dm[0].length):line;
  const wm=rest.match(D_WFID_RE); if(wm) rest=rest.slice(rest.indexOf(wm[0])+wm[0].length);
  return {date, msg:rest.replace(/^[\\s|]+/,'')};
}
function _esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function _buildLogTable(entries){
  if(!entries.length) return '<div style="padding:20px;text-align:center;color:#999;">No log entries yet.</div>';
  const hdr='<thead><tr style="background:#2c3e50;"><th style="text-align:left;padding:8px 10px;color:white;font-weight:bold;font-size:12px;">Date</th><th style="text-align:left;padding:8px 10px;color:white;font-weight:bold;font-size:12px;">Message</th></tr></thead>';
  const rows=entries.map(e=>{const p=_parseLog(e);
    return '<tr><td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-family:monospace;font-size:12px;color:#888;white-space:nowrap;vertical-align:top;">'+_esc(p.date)+'</td><td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-family:monospace;font-size:12px;word-break:break-all;vertical-align:top;">'+_esc(p.msg)+'</td></tr>';
  }).join('');
  return '<table style="width:100%;border-collapse:collapse;">'+hdr+'<tbody>'+rows+'</tbody></table>';
}
function _buildStagesTable(currentStage, status){
  let found=false;
  const rows=ALL_STAGES.map(s=>{
    let icon,color;
    if(s===currentStage){
      if(status==='Hold')          icon='⏸';
      else if(status==='Failed')   icon='❌';
      else if(status==='Cancelled')icon='🚫';
      else                         icon=ST_SYMBOL[status]||'🟡';
      color='#fffde7'; found=true;
    } else if(!found){
      icon='✓'; color='#f0fff0';
    } else {
      icon='⏳'; color='#f8f9fa';
    }
    return '<tr style="background:'+color+';"><td style="padding:10px 14px;font-size:18px;">'+icon+'</td>'
          +'<td style="padding:10px 14px;font-size:13px;font-family:monospace;">'+_esc(s)+'</td></tr>';
  }).join('');
  return '<table style="width:100%;border-collapse:collapse;">'+rows+'</table>';
}
function _actionBtn(label, action, color){
  return '<button onclick="wfAction(\\'' + action + '\\')" style="background:'+color+';color:white;border:none;padding:9px 20px;border-radius:7px;font-size:13px;font-weight:bold;cursor:pointer;margin-right:6px;">'+label+'</button>';
}
function _buildActionButtons(status){
  let html='';
  if(status==='In Progress'||status==='Retry'){
    html+=_actionBtn('&#9208; Hold','hold','#ff9800');
    html+=_actionBtn('&#128128; Revoke','revoke','#e74c3c');
  }
  if(status==='Hold'||status==='Failed'){
    html+=_actionBtn('&#128260; Retry','retry','#3498db');
    html+=_actionBtn('&#128257; Reset','reset','#8e44ad');
  }
  if(status!=='Complete'&&status!=='Cancelled'){
    html+=_actionBtn('&#128683; Cancel','cancel','#95a5a6');
  }
  return html;
}
async function partialRefresh(){
  try{
    const r=await fetch('/api/workflow-status/''' + wf_id + '''');
    const d=await r.json(); if(d.error) return;
    // Update status badge
    const bdEl=document.getElementById('detail_status_badge');
    if(bdEl) bdEl.textContent=(ST_SYMBOL[d.status]||'?')+' '+d.status;
    // Update stage text
    const stEl=document.getElementById('detail_stage'); if(stEl) stEl.textContent=d.stage;
    // Update updated date
    const upEl=document.getElementById('detail_updated'); if(upEl) upEl.textContent=d.updated_date;
    // Update stages table
    const stagesEl=document.getElementById('stages_scroll');
    if(stagesEl) stagesEl.innerHTML=_buildStagesTable(d.stage, d.status);
    // Update logs
    const lgEl=document.getElementById('logs_scroll');
    if(lgEl) lgEl.innerHTML=_buildLogTable(d.log_entries);
    // Update the "(N entries)" count label above the log table
    const cntEl=document.getElementById('logs_entries_count');
    if(cntEl) cntEl.textContent='('+d.log_entries.length+' entries — newest first)';
    // Update action buttons (Hold/Revoke/Retry/Reset/Cancel) — these depend
    // on status and previously only rendered once at initial page load, so
    // a Waiting -> In Progress transition mid-poll left stale buttons until
    // a full page reload.
    const actEl=document.getElementById('detail_action_buttons');
    if(actEl) actEl.innerHTML=_buildActionButtons(d.status);
    // Stop auto-refresh when truly terminal (Hold counts as terminal)
    if(TERMINAL_ST.has(d.status)){
      _detailAutoOn=false; clearInterval(_detailTimer);
      const btn=document.getElementById('detail_auto_toggle');
      if(btn){btn.textContent='Auto Refresh: OFF';btn.style.background='#bbb';}
    }
  }catch(e){}
}
function toggleDetailAuto(){
  _detailAutoOn=!_detailAutoOn;
  const btn=document.getElementById('detail_auto_toggle');
  if(_detailAutoOn){
    btn.textContent='Auto Refresh: ON'; btn.style.background='#27ae60';
    _detailTimer=setInterval(partialRefresh,5000);
  }else{
    btn.textContent='Auto Refresh: OFF'; btn.style.background='#bbb';
    clearInterval(_detailTimer);
  }
}
toggleDetailAuto();  // on by default — same toggle the button uses, just fired once on page load
'''

    body = ('''
<div style="background:#2c3e50;color:white;padding:15px 24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
  <div>
    <a href="/scraper/workflow" style="color:#aaa;text-decoration:none;font-size:13px;">&#8592; Back to Scraper</a>
    <h1 style="font-size:18px;margin-top:4px;">''' + symbol + ' ' + esc(wf_id) + '''</h1>
  </div>
  <div style="font-size:13px;color:#aaa;"><span id="detail_status_badge">''' + symbol + ' ' + esc(status) + '''</span> | ''' + esc(wf.get('type','')) + ' | ' + esc(wf.get('scraper','')) + '''</div>
</div>
<div style="padding:20px;max-width:960px;margin:0 auto;">

  <!-- Info + Buttons -->
  <div style="background:white;border-radius:10px;padding:18px;margin-bottom:16px;box-shadow:0 2px 5px rgba(0,0,0,0.08);">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:10px;">
      <div>
        ''' + kw_loc_html + '''
        <div style="font-size:13px;color:#666;margin-bottom:5px;">Stage: <b style="font-family:monospace;" id="detail_stage">''' + esc(current_stage) + '''</b></div>
        <div style="font-size:12px;color:#999;">Started: ''' + esc(wf.get('start_date','')) + ''' &nbsp;|&nbsp; Updated: <span id="detail_updated">''' + esc(wf.get('updated_date','')) + '''</span></div>
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;">
        <span id="detail_action_buttons">''' + buttons + '''</span>
        <button onclick="location.reload()" style="background:#3498db;color:white;border:none;padding:9px 16px;border-radius:7px;font-size:13px;font-weight:bold;cursor:pointer;">&#128260; Refresh</button>
        <button id="detail_auto_toggle" onclick="toggleDetailAuto()" style="padding:9px 16px;border-radius:7px;border:none;font-size:13px;font-weight:bold;cursor:pointer;background:#bbb;color:white;">Auto Refresh: OFF</button>
      </div>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px;">
    <!-- Stages -->
    <div style="background:white;border-radius:10px;padding:18px;box-shadow:0 2px 5px rgba(0,0,0,0.08);">
      <div style="font-size:15px;font-weight:bold;color:#2c3e50;margin-bottom:12px;border-bottom:2px solid #3498db;padding-bottom:6px;">Stages</div>
      <div id="stages_scroll" style="max-height:400px;overflow-y:auto;">
        ''' + stage_panel_html + '''
      </div>
    </div>
    <!-- Status Legend -->
    <div style="background:white;border-radius:10px;padding:18px;box-shadow:0 2px 5px rgba(0,0,0,0.08);">
      <div style="font-size:15px;font-weight:bold;color:#2c3e50;margin-bottom:12px;border-bottom:2px solid #3498db;padding-bottom:6px;">Status Legend</div>
      <table style="border-collapse:collapse;">''' + legend_rows + '''</table>
    </div>
  </div>

  <!-- Logs -->
  <div style="background:white;border-radius:10px;padding:18px;box-shadow:0 2px 5px rgba(0,0,0,0.08);">
    <div style="font-size:15px;font-weight:bold;color:#2c3e50;margin-bottom:12px;border-bottom:2px solid #3498db;padding-bottom:6px;">
      Logs <span id="logs_entries_count" style="font-size:12px;font-weight:normal;color:#999;">(''' + str(len(log_entries)) + ''' entries — newest first)</span>
    </div>
    <div id="logs_scroll" style="max-height:500px;overflow-y:auto;border:1px solid #f0f0f0;border-radius:6px;">''' + log_html + '''</div>
  </div>
</div>
<script>
function wfAction(action){
  const msgs={
    hold:'Hold this workflow? Scraper will finish current job then stop.',
    retry:'Retry this workflow from last saved point?',
    cancel:'Cancel this workflow? If it is currently running, the process will be stopped immediately.',
    revoke:'Force kill this workflow immediately? Current job may not be saved!',
    reset:'Reset this workflow? Pending jobs will be flushed and all pages reset to 1. Press Retry after to restart from beginning.'
  };
  if(!confirm(msgs[action]||'Are you sure?'))return;
  const endpoint = action==='reset' ? '/api/reset-workflow' : '/api/workflow-action';
  fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({id:"''' + wf_id + '''",action:action})})
  .then(r=>r.json())
  .then(d=>{
    if(d.ok){
      if(action==='hold'){
        // Don't reload — keep auto-refresh running so we can see when it actually holds
        if(!_detailAutoOn){
          _detailAutoOn=true;
          const btn=document.getElementById('detail_auto_toggle');
          if(btn){btn.textContent='Auto Refresh: ON';btn.style.background='#27ae60';}
          _detailTimer=setInterval(partialRefresh,5000);
        }
        partialRefresh();
      } else {
        location.reload();
      }
    } else {
      alert('Error: '+d.error);
    }
  })
  .catch(e=>alert('Browser is busy, please try again in a moment.'));
}
''' + refresh_js + auto_refresh_js + '''
</script>''')

    return html_page('Workflow — ' + wf_id, body)
