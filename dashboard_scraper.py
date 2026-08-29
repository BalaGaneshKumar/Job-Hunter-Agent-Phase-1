"""
dashboard_scraper.py — Scraper tab HTML + JS (Request, Workflow, Log sub-tabs)
Imported by dashboard_server.py
"""
from dashboard_ui import esc
from dashboard_workflows import STATUS_LEGEND

def build_scraper_html():
    # Status legend table
    legend_rows = ''.join(
        '<tr><td>' + sym + '</td><td><b>' + esc(name) + '</b></td><td style="color:#666;font-size:12px;">' + esc(desc) + '</td></tr>'
        for sym, name, desc in STATUS_LEGEND
    )

    legend_strip = ''.join(
        '<span style="white-space:nowrap;"><b>' + sym + '</b> ' + esc(name) + '</span>'
        for sym, name, desc in STATUS_LEGEND
    )

    return '''
<!-- SCRAPER -->
<style>
.switch-btn{padding:5px 14px;border:none;border-radius:14px;cursor:pointer;font-size:12px;font-weight:bold;transition:background .15s;}
.switch-on{background:#27ae60;color:white;}
.switch-off{background:#bbb;color:white;}
.log-table{width:100%;border-collapse:collapse;font-size:12px;}
.log-table td{padding:6px 10px;border-bottom:1px solid #f0f0f0;vertical-align:top;font-family:monospace;}
.log-table td.log-date{color:#888;white-space:nowrap;}
.log-table td.log-wfid{color:#3498db;white-space:nowrap;}
.log-table td.log-msg{word-break:break-all;}
</style>
<div id="page-scraper" class="page">
  <div class="sub-nav">
    <button class="active" onclick="showSubPage(\'request\',this)">&#128228; Request</button>
    <button onclick="showSubPage(\'workflow\',this)">&#9881; Workflow</button>
    <button onclick="showSubPage(\'log\',this)">&#128203; Log</button>
  </div>

  <!-- REQUEST -->
  <div id="sub-request" class="sub-page active">
    <div style="display:flex;justify-content:flex-end;margin-bottom:8px;">
      <button onclick="checkRunningWorkflow()" style="padding:5px 14px;background:#3498db;color:white;border:none;border-radius:5px;cursor:pointer;font-size:12px;">&#128260; Refresh</button>
    </div>
    <div id="running_warning" class="running-warning">&#9888; Workflow <b id="running_wf_id"></b> is running. New requests will be queued.</div>
    <div class="req-section">
      <h3>1. Select Stage(s) &amp; Portal(s)</h3>
      <div style="display:flex;gap:16px;flex-wrap:wrap;">
        <div style="flex:1;min-width:220px;">
          <div style="font-weight:bold;color:#2c3e50;margin-bottom:8px;">Stage(s)</div>
          <div class="scraper-options">
            <div class="scraper-option" id="opt-stage-counter" onclick="toggleStage(\'Counter\')">&#128202; Counter</div>
            <div class="scraper-option" id="opt-stage-scraper" onclick="toggleStage(\'Scraper\')">&#127760; Scraper</div>
            <div class="scraper-option" id="opt-stage-validator" onclick="toggleStage(\'Validator\')">&#128269; Validator</div>
          </div>
        </div>
        <div style="flex:1;min-width:220px;">
          <div style="font-weight:bold;color:#2c3e50;margin-bottom:8px;">Portal(s)</div>
          <div class="scraper-options">
            <div class="scraper-option" id="opt-portal-nk" onclick="togglePortal(\'NK\')">&#128269; Portal B</div>
            <div class="scraper-option" id="opt-portal-li" onclick="togglePortal(\'LI\')">&#128309; Portal A</div>
            <div class="scraper-option" id="opt-portal-in" onclick="togglePortal(\'IN\')">&#128188; Portal C</div>
          </div>
          <div style="font-size:11px;color:#999;margin-top:6px;">Runs in order: Portal B &#8594; Portal A &#8594; Portal C. Selecting all 3 portals = Default (All).</div>
        </div>
      </div>
    </div>
    <div class="req-section">
      <h3>2. Locations <span style="font-size:12px;color:#999;font-weight:normal;">(click to select/deselect &#8226; &#10005; to delete permanently &#8226; validator: leave empty for all)</span>
        <button onclick="selectAllLocations()" style="margin-left:10px;padding:4px 12px;background:#3498db;color:white;border:none;border-radius:5px;cursor:pointer;font-size:11px;font-weight:bold;">Select All</button>
        <button onclick="deselectAllLocations()" style="margin-left:4px;padding:4px 12px;background:#95a5a6;color:white;border:none;border-radius:5px;cursor:pointer;font-size:11px;font-weight:bold;">Clear</button>
      </h3>
      <div class="tag-list" id="loc_tags"></div>
      <div class="extra-input">
        <input type="text" id="loc_input" placeholder="Add location..." onkeydown="if(event.key===\'Enter\')addLocation()">
        <button onclick="addLocation()">+ Add &amp; Save</button>
      </div>
    </div>
    <div id="scraper_only_sections" style="display:none;">
    <div class="req-section">
      <h3>3. Keywords <span style="font-size:12px;color:#999;font-weight:normal;">(click to select/deselect &#8226; &#10005; to delete permanently)</span>
        <button onclick="selectAllKeywords()" style="margin-left:10px;padding:4px 12px;background:#3498db;color:white;border:none;border-radius:5px;cursor:pointer;font-size:11px;font-weight:bold;">Select All</button>
        <button onclick="deselectAllKeywords()" style="margin-left:4px;padding:4px 12px;background:#95a5a6;color:white;border:none;border-radius:5px;cursor:pointer;font-size:11px;font-weight:bold;">Clear</button>
      </h3>
      <div class="tag-list" id="kw_tags"></div>
      <div class="extra-input">
        <input type="text" id="kw_input" placeholder="Add keyword..." onkeydown="if(event.key===\'Enter\')addKeyword()">
        <button onclick="addKeyword()">+ Add &amp; Save</button>
      </div>
    </div>
    <div class="req-section">
      <h3>4. Blacklist Keywords <span style="font-size:12px;color:#999;font-weight:normal;">(&#10005; to delete permanently)</span></h3>
      <div id="bl_kw_tags"></div>
      <div class="extra-input">
        <input type="text" id="bl_input" placeholder="Add blacklist keyword..." onkeydown="if(event.key===\'Enter\')addBlacklist()">
        <button onclick="addBlacklist()">+ Add &amp; Save</button>
      </div>
    </div>
    </div>
    <button class="btn-submit" id="btn_submit" disabled onclick="submitRequest()">&#128640; Submit</button>
    <div id="submit_msg" style="margin-top:10px;font-size:13px;"></div>
  </div>

  <!-- WORKFLOW -->
  <div id="sub-workflow" class="sub-page">
    <div class="wf-table-wrap">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-wrap:wrap;gap:10px;">
        <b style="color:#2c3e50;white-space:nowrap;">Workflows</b>
        <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap;font-size:12px;color:#666;">''' + legend_strip + '''</div>
        <div style="display:flex;align-items:center;gap:8px;">
          <button id="wf_auto_toggle" onclick="toggleAutoRefresh(\'wf\')" class="switch-btn switch-off">Auto Refresh: OFF</button>
          <button onclick="loadWorkflows()" style="padding:5px 14px;background:#3498db;color:white;border:none;border-radius:5px;cursor:pointer;font-size:12px;">&#128260; Refresh</button>
        </div>
      </div>
      <table>
        <thead><tr>
          <th onclick="sortWF(\'status\')">Status</th>
          <th onclick="sortWF(\'id\')">Workflow ID</th>
          <th onclick="sortWF(\'type\')">Type</th>
          <th onclick="sortWF(\'scraper\')">Scraper</th>
          <th onclick="sortWF(\'stage\')">Current Stage</th>
          <th onclick="sortWF(\'start_date\')">Start Date</th>
          <th onclick="sortWF(\'updated_date\')">Updated</th>
        </tr></thead>
        <tbody id="wf_tbody"></tbody>
      </table>
      <div class="pagination" id="wf_pagination"></div>
    </div>
  </div>

  <!-- LOG -->
  <div id="sub-log" class="sub-page">
    <div class="log-wrap">
      <div style="display:flex;gap:10px;align-items:center;margin-bottom:12px;flex-wrap:wrap;">
        <input type="text" id="log_filter_id" placeholder="Filter by Workflow ID..." style="padding:7px 12px;border:1px solid #ddd;border-radius:6px;font-size:13px;width:260px;">
        <select id="log_per_page" onchange="loadLogs(1)" style="padding:7px 10px;border:1px solid #ddd;border-radius:6px;font-size:13px;">
          <option value="50">50 per page</option>
          <option value="100">100 per page</option>
        </select>
        <button onclick="loadLogs(1)" style="padding:7px 14px;background:#3498db;color:white;border:none;border-radius:5px;cursor:pointer;font-size:12px;">&#128269; Filter</button>
        <button onclick="document.getElementById(\'log_filter_id\').value=\'\';loadLogs(1);" style="padding:7px 14px;background:#95a5a6;color:white;border:none;border-radius:5px;cursor:pointer;font-size:12px;">&#10005; Clear</button>
        <button onclick="loadLogs(logPage)" style="padding:7px 14px;background:#3498db;color:white;border:none;border-radius:5px;cursor:pointer;font-size:12px;">&#128260; Refresh</button>
        <button id="log_auto_toggle" onclick="toggleAutoRefresh(\'log\')" class="switch-btn switch-off">Auto Refresh: OFF</button>
        <span style="font-size:12px;color:#aaa;" id="log_count"></span>
      </div>
      <div id="log_container"></div>
      <div class="pagination" id="log_pagination"></div>
    </div>
  </div>
</div>
'''

def build_scraper_js():
    return '''
// ── Scraper state ──────────────────────────────────────────────────────────────
let selectedStages   = new Set();   // 'Counter' | 'Scraper' | 'Validator'
let selectedPortals  = new Set();   // 'NK' | 'LI' | 'IN'
let selectedKeywords  = new Set();
let selectedLocations = new Set();
let wfPage    = 1;
let wfSortCol = 'start_date';
let wfSortDir = -1;
let logPage   = 1;
let _wfTimer  = null;
let _logTimer = null;

const STATUS_SYMBOL = {
  'Waiting':'⏳','In Progress':'🟡','Hold':'⏸','Retry':'🔄',
  'Complete':'✅','Failed':'❌','Cancelled':'🚫'
};

// ── Request Tab ────────────────────────────────────────────────────────────────
function initRequestTab(){
  renderKwTags();renderLocTags();renderBlTags();checkSubmitEnabled();checkRunningWorkflow();
  updateScraperOnlyVisibility();
}
function updateScraperOnlyVisibility(){
  const needsKeywords = selectedStages.has('Counter') || selectedStages.has('Scraper');
  document.getElementById('scraper_only_sections').style.display = needsKeywords ? 'block' : 'none';
}
function renderKwTags(){
  const c=document.getElementById('kw_tags');c.innerHTML='';
  CONFIG_KEYWORDS.forEach(kw=>{
    const tag=document.createElement('div');
    tag.className='tag'+(selectedKeywords.has(kw)?' selected':'');
    tag.onclick=()=>toggleKeyword(kw);
    const btn=document.createElement('button');
    btn.className='remove-btn';btn.title='Delete permanently';btn.innerHTML='&#10005;';
    btn.onclick=function(e){e.stopPropagation();removeKeyword(kw);};
    tag.appendChild(document.createTextNode(escHtml(kw)+' '));
    tag.appendChild(btn);
    c.appendChild(tag);
  });
}
function renderLocTags(){
  const c=document.getElementById('loc_tags');c.innerHTML='';
  CONFIG_LOCATIONS.forEach(loc=>{
    const tag=document.createElement('div');
    tag.className='tag'+(selectedLocations.has(loc)?' selected':'');
    tag.onclick=()=>toggleLocation(loc);
    const btnL=document.createElement('button');
    btnL.className='remove-btn';btnL.title='Delete permanently';btnL.innerHTML='&#10005;';
    btnL.onclick=function(e){e.stopPropagation();removeLocation(loc);};
    tag.appendChild(document.createTextNode(escHtml(loc)+' '));
    tag.appendChild(btnL);
    c.appendChild(tag);
  });
}
function renderBlTags(){
  const c=document.getElementById('bl_kw_tags');c.innerHTML='';
  CONFIG_BLACKLIST.forEach(kw=>{
    const tag=document.createElement('span');
    tag.className='bl-tag';
    const btnB=document.createElement('button');
    btnB.className='remove-btn';btnB.innerHTML='&#10005;';
    btnB.onclick=function(){removeBlacklist(kw);};
    tag.appendChild(document.createTextNode(escHtml(kw)+' '));
    tag.appendChild(btnB);
    c.appendChild(tag);
  });
}
function toggleKeyword(kw){if(selectedKeywords.has(kw))selectedKeywords.delete(kw);else selectedKeywords.add(kw);renderKwTags();checkSubmitEnabled();}
function toggleLocation(loc){if(selectedLocations.has(loc))selectedLocations.delete(loc);else selectedLocations.add(loc);renderLocTags();checkSubmitEnabled();}
function selectAllKeywords(){CONFIG_KEYWORDS.forEach(kw=>selectedKeywords.add(kw));renderKwTags();checkSubmitEnabled();}
function deselectAllKeywords(){selectedKeywords.clear();renderKwTags();checkSubmitEnabled();}
function selectAllLocations(){CONFIG_LOCATIONS.forEach(loc=>selectedLocations.add(loc));renderLocTags();checkSubmitEnabled();}
function deselectAllLocations(){selectedLocations.clear();renderLocTags();checkSubmitEnabled();}
function toggleStage(stage){
  if(selectedStages.has(stage)) selectedStages.delete(stage);
  else selectedStages.add(stage);
  const el=document.getElementById('opt-stage-'+stage.toLowerCase());
  el.classList.toggle('selected', selectedStages.has(stage));
  updateScraperOnlyVisibility();
  checkSubmitEnabled();
}
function togglePortal(code){
  if(selectedPortals.has(code)) selectedPortals.delete(code);
  else selectedPortals.add(code);
  const idMap={'NK':'nk','LI':'li','IN':'in'};
  const el=document.getElementById('opt-portal-'+idMap[code]);
  el.classList.toggle('selected', selectedPortals.has(code));
  checkSubmitEnabled();
}
async function addKeyword(){
  const val=document.getElementById('kw_input').value.trim();if(!val)return;
  if(!CONFIG_KEYWORDS.includes(val))CONFIG_KEYWORDS.push(val);
  selectedKeywords.add(val);
  document.getElementById('kw_input').value='';
  await saveConfigToServer();renderKwTags();checkSubmitEnabled();
}
async function addLocation(){
  const val=document.getElementById('loc_input').value.trim();if(!val)return;
  if(!CONFIG_LOCATIONS.includes(val))CONFIG_LOCATIONS.push(val);
  selectedLocations.add(val);
  document.getElementById('loc_input').value='';
  await saveConfigToServer();renderLocTags();checkSubmitEnabled();
}
async function addBlacklist(){
  const val=document.getElementById('bl_input').value.trim().toLowerCase();if(!val)return;
  if(!CONFIG_BLACKLIST.includes(val))CONFIG_BLACKLIST.push(val);
  document.getElementById('bl_input').value='';
  await saveConfigToServer();renderBlTags();
}
async function removeKeyword(kw){
  if(!confirm('Permanently delete keyword "'+kw+'" from config.json?'))return;
  CONFIG_KEYWORDS=CONFIG_KEYWORDS.filter(k=>k!==kw);selectedKeywords.delete(kw);
  await saveConfigToServer();renderKwTags();checkSubmitEnabled();
}
async function removeLocation(loc){
  if(!confirm('Permanently delete location "'+loc+'" from config.json?'))return;
  CONFIG_LOCATIONS=CONFIG_LOCATIONS.filter(l=>l!==loc);selectedLocations.delete(loc);
  await saveConfigToServer();renderLocTags();checkSubmitEnabled();
}
async function removeBlacklist(kw){
  if(!confirm('Permanently delete "'+kw+'" from blacklist?'))return;
  CONFIG_BLACKLIST=CONFIG_BLACKLIST.filter(k=>k!==kw);
  await saveConfigToServer();renderBlTags();
}
async function saveConfigToServer(){
  try {
    await fetch('/api/save-config',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({role_keywords:CONFIG_KEYWORDS,locations:CONFIG_LOCATIONS,blacklist:CONFIG_BLACKLIST})});
  } catch(e){ alert('Browser is busy, please try again in a moment.'); }
}
function checkSubmitEnabled(){
  const needsKeywords = selectedStages.has('Counter') || selectedStages.has('Scraper');
  const ok = selectedStages.size>0 && selectedPortals.size>0 && selectedLocations.size>0
             && (!needsKeywords || selectedKeywords.size>0);
  document.getElementById('btn_submit').disabled=!ok;
}
async function checkRunningWorkflow(){
  try{
    const r=await fetch('/api/running-workflow');const d=await r.json();
    const warn=document.getElementById('running_warning');
    if(d.running){
      warn.style.display='block';
      document.getElementById('running_wf_id').textContent=d.id;
      warn.innerHTML='&#9888; Workflow <b>'+d.id+'</b> is running. Your request will be queued and start automatically once it finishes.';
    } else {
      warn.style.display='none';
    }
    checkSubmitEnabled();
  }catch(e){}
}
async function submitRequest(){
  const payload = {
    stages: [...selectedStages],
    portals: [...selectedPortals],
    keywords: [...selectedKeywords],
    locations: [...selectedLocations]
  };
  try {
    const r=await fetch('/api/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const d=await r.json();
    const msg=document.getElementById('submit_msg');
    if(d.ok){
      msg.style.color='#27ae60';msg.textContent='&#10003; Workflows queued: '+d.workflow_ids.join(', ');
      selectedStages.clear();selectedPortals.clear();selectedKeywords.clear();selectedLocations.clear();
      document.querySelectorAll('.scraper-option').forEach(o=>o.classList.remove('selected'));
      updateScraperOnlyVisibility();
      initRequestTab();
      setTimeout(()=>{document.querySelectorAll('.sub-nav button')[1].click();},1000);
    }else{msg.style.color='#e74c3c';msg.textContent='&#10007; '+d.error;}
  } catch(e){ alert('Browser is busy, please try again in a moment.'); }
}

// ── Workflow table ─────────────────────────────────────────────────────────────
async function loadWorkflows(){
  try{
    const r=await fetch('/api/workflows?page='+wfPage+'&sort='+wfSortCol+'&dir='+wfSortDir);
    const d=await r.json();renderWorkflowTable(d.workflows,d.total);
  }catch(e){}
}
function renderWorkflowTable(wfs,total){
  const tbody=document.getElementById('wf_tbody');
  if(!wfs.length){
    tbody.innerHTML='<tr><td colspan="7" style="text-align:center;color:#999;padding:30px;">No workflows yet.</td></tr>';
    document.getElementById('wf_pagination').innerHTML='';return;
  }
  tbody.innerHTML=wfs.map(wf=>`<tr class="${wf.status==='In Progress'||wf.status==='Retry'?'pinned':''}">
    <td style="font-size:18px;">${STATUS_SYMBOL[wf.status]||'?'}</td>
    <td><a class="wf-id-link" href="/workflow/${escHtml(wf.id)}" target="_blank">${escHtml(wf.id)}</a></td>
    <td>${escHtml(wf.type)}</td>
    <td>${escHtml(wf.scraper)}</td>
    <td><span style="font-family:monospace;font-size:12px;">${escHtml(wf.stage||'')}</span></td>
    <td style="font-size:12px;color:#666;">${escHtml(wf.start_date)}</td>
    <td style="font-size:12px;color:#666;">${escHtml(wf.updated_date)}</td>
  </tr>`).join('');
  renderPagination('wf_pagination',wfPage,Math.ceil(total/20),p=>{wfPage=p;loadWorkflows();});
}
function sortWF(col){if(wfSortCol===col)wfSortDir*=-1;else{wfSortCol=col;wfSortDir=-1;}loadWorkflows();}

// ── Shared log line parser ─────────────────────────────────────────────────────
// Date: yyyy-mm-dd hh:mm:ss   |   Workflow ID: WFI + 11 uppercase letters + 4 digits
const LOG_DATE_RE = /^(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2})/;
const LOG_WFID_RE = /(WFI[A-Z]{8}\\d{4})/;
function parseLogLine(line){
  const dm = line.match(LOG_DATE_RE);
  const date = dm ? dm[1] : \'\';
  let rest = dm ? line.slice(dm[0].length) : line;
  const wm = rest.match(LOG_WFID_RE);
  const wfid = wm ? wm[1] : \'\';
  if(wm) rest = rest.slice(rest.indexOf(wm[1]) + wm[1].length);
  const msg = rest.replace(/^[\\s|]+/, \'\');
  return {date, wfid, msg};
}
function renderLogTable(entries, showWfId){
  if(!entries.length) return \'<div style="text-align:center;padding:30px;color:#999;">No log entries found.</div>\';
  const hdr = \'<thead><tr style="background:#2c3e50;">\'
    + \'<th style="text-align:left;padding:8px 10px;color:white;font-weight:bold;">Date</th>\'
    + (showWfId ? \'<th style="text-align:left;padding:8px 10px;color:white;font-weight:bold;">Workflow ID</th>\' : \'\')
    + \'<th style="text-align:left;padding:8px 10px;color:white;font-weight:bold;">Message</th>\'
    + \'</tr></thead>\';
  const rows = entries.map(e=>{
    const p = parseLogLine(e);
    return '<tr><td class="log-date">'+escHtml(p.date)+'</td>'
      + (showWfId ? '<td class="log-wfid">'+escHtml(p.wfid)+'</td>' : '')
      + '<td class="log-msg">'+escHtml(p.msg)+'</td></tr>';
  }).join('');
  return '<table class="log-table">'+hdr+'<tbody>'+rows+'</tbody></table>';
}

// ── Log tab ────────────────────────────────────────────────────────────────────
async function loadLogs(page){
  logPage=page||logPage;
  const filterId=document.getElementById('log_filter_id').value.trim();
  const perPage=document.getElementById('log_per_page').value;
  try{
    const r=await fetch('/api/logs?page='+logPage+'&filter='+encodeURIComponent(filterId)+'&per_page='+perPage);
    const d=await r.json();
    document.getElementById('log_count').textContent=d.total+' entries';
    document.getElementById('log_container').innerHTML=renderLogTable(d.entries, true);
    renderPagination('log_pagination',logPage,Math.ceil(d.total/parseInt(perPage)),p=>loadLogs(p));
  }catch(e){}
}

// ── Auto-refresh (independent per-tab toggles) ─────────────────────────────────
let _wfAutoOn=false, _logAutoOn=false;
function toggleAutoRefresh(which){
  if(which==='wf'){
    _wfAutoOn=!_wfAutoOn;
    const btn=document.getElementById('wf_auto_toggle');
    if(_wfAutoOn){btn.textContent='Auto Refresh: ON';btn.className='switch-btn switch-on';_wfTimer=setInterval(loadWorkflows,5000);}
    else{btn.textContent='Auto Refresh: OFF';btn.className='switch-btn switch-off';clearInterval(_wfTimer);}
  }else if(which==='log'){
    _logAutoOn=!_logAutoOn;
    const btn=document.getElementById('log_auto_toggle');
    if(_logAutoOn){btn.textContent='Auto Refresh: ON';btn.className='switch-btn switch-on';_logTimer=setInterval(()=>loadLogs(logPage),5000);}
    else{btn.textContent='Auto Refresh: OFF';btn.className='switch-btn switch-off';clearInterval(_logTimer);}
  }
}
function startAutoRefresh(){
  // Auto-start both tabs' refresh — called by showPage() (outside this
  // file) whenever the Scraper tab becomes visible. Not called again
  // here: toggleAutoRefresh() toggles rather than sets, so calling this
  // twice (once here, once from showPage) cancelled itself back to OFF.
  toggleAutoRefresh('wf');
  toggleAutoRefresh('log');
}
'''
