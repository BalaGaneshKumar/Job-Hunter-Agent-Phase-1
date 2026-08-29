# dashboard_career.py

def build_career_html():
    return '''
<style>
''' + build_career_css() + '''
</style>
<div id="page-career" class="page">
<div class="career-wrap">

  <div class="cr-tab-bar">
    <button class="cr-tab-btn cr-active" onclick="crSwitchTab(\'applications\', this)">&#128193; Applications</button>
    <button class="cr-tab-btn" onclick="crSwitchTab(\'jobsites\', this)">&#127760; Job Sites</button>
  </div>

  <!-- APPLICATIONS -->
  <div id="cr-tab-applications" class="cr-tab-panel cr-panel-active">
    <div class="cr-stats-row" id="cr-app-stats"></div>
    <div class="cr-card">
      <h2 class="cr-section-title">Applications <span class="cr-pill" id="cr-app-count">0</span></h2>
      <div class="cr-toolbar">
        <input type="text" id="cr-app-search" placeholder="Search company or role&#8230;" oninput="crRenderApps()">
        <select id="cr-app-filter-stage" onchange="crRenderApps()">
          <option value="">All stages</option>
          <option>Applied</option><option>In Progress</option><option>Interview</option>
          <option>Offer</option><option>Rejected</option><option>Closed</option>
          <option>Ghosted</option><option>Withdrawn</option><option>NA</option>
        </select>
        <select id="cr-app-sort" onchange="crRenderApps()">
          <option value="default">Sort: Default</option>
          <option value="company_asc">Company A&#8594;Z</option>
          <option value="company_desc">Company Z&#8594;A</option>
          <option value="date_asc">Date Oldest</option>
          <option value="date_desc">Date Newest</option>
          <option value="stage">Stage</option>
        </select>
        <button class="cr-btn-add" onclick="crOpenAppModal()">&#43; Add application</button>
        <button class="cr-fab-add" onclick="crOpenAppModal()" title="Add application">&#43;</button>
      </div>
      <div class="cr-tbl-wrap">
        <table class="cr-table">
          <thead><tr>
            <th>Company</th>
            <th>Credential</th>
            <th>Role</th>
            <th>Location</th>
            <th>Applied</th>
            <th>Stage</th>
            <th>Actions</th>
          </tr></thead>
          <tbody id="cr-app-tbody"></tbody>
        </table>
        <div id="cr-app-empty" class="cr-empty" style="display:none">
          <div class="cr-empty-icon">&#128203;</div>No applications yet.
        </div>
      </div>
    </div>
  </div>

  <!-- JOB SITES -->
  <div id="cr-tab-jobsites" class="cr-tab-panel">
    <div class="cr-card">
      <h2 class="cr-section-title">Job Sites <span class="cr-pill" id="cr-site-count">0</span></h2>
      <div class="cr-toolbar">
        <input type="text" id="cr-site-search" placeholder="Search site&#8230;" oninput="crRenderSites()">
        <button class="cr-btn-add" onclick="crOpenSiteModal()">&#43; Add site</button>
      </div>
      <div class="cr-tbl-wrap">
        <table class="cr-table">
          <thead><tr>
            <th>Site</th><th>Credential hint</th><th>Notes</th><th>Actions</th>
          </tr></thead>
          <tbody id="cr-site-tbody"></tbody>
        </table>
        <div id="cr-site-empty" class="cr-empty" style="display:none">
          <div class="cr-empty-icon">&#127760;</div>No job sites saved yet.
        </div>
      </div>
    </div>
  </div>

</div><!-- /.career-wrap -->

</div><!-- /#page-career -->

<!-- URL DUPLICATE POPUP -->
<div class="cr-popup" id="cr-url-popup" style="display:none">
  <p id="cr-url-popup-msg"></p>
  <button class="cr-popup-ok" onclick="crUrlPopupOk()">OK</button>
</div>
<div id="cr-popup-overlay" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.3);z-index:1099;"></div>

<!-- APPLICATION MODAL -->
<div class="cr-modal-overlay" id="cr-app-modal">
  <div class="cr-modal">
    <button class="cr-modal-x" onclick="crCloseModal('cr-app-modal')" aria-label="Close">&times;</button>
    <h3 id="cr-app-modal-title">Add application</h3>

    <!-- Row 1: Company + Job link + Credential -->
    <div class="cr-form-row-3">
      <div class="cr-form-row">
        <label>Company *</label>
        <input id="cr-af-company" type="text" placeholder="e.g. Google"
          onblur="crCheckCompanyName()"
          onfocus="crCompanyFocused=true"
          oninput="crCompanyChanged=true">
      </div>
      <div class="cr-form-row">
        <label>Job link</label>
        <input id="cr-af-link" type="url" placeholder="https://&#8230;"
          onfocus="crCheckCompanyName()"
          onblur="crCheckUrl()">
      </div>
      <div class="cr-form-row">
        <label>Credential status</label>
        <select id="cr-af-cred" onchange="crCheckCredSub()">
          <option value="">-- Select --</option>
          <option>Registered</option>
          <option>Not Registered</option>
          <option>Registered Incomplete</option>
          <option>Mailed</option>
        </select>
      </div>
    </div>

    <!-- Credential sub-type (shown when Registered) -->
    <div class="cr-substage-row" id="cr-af-credtype-row">
      <div class="cr-form-row">
        <label>Credential detail</label>
        <select id="cr-af-credtype" onchange="crCheckCredSub()">
          <option value="">-- Select --</option>
          <option>With Password</option>
          <option>Via Google</option>
          <option>Via Portal A</option>
          <option>Via Greenhouse</option>
          <option>Via Talent500</option>
          <option>Via Instahyre</option>
          <option>Via Portal B</option>
          <option>No Password / OTP Login</option>
          <option>Unable to check / Open</option>
          <option>Applied Directly</option>
        </select>
      </div>
      <div class="cr-form-row" id="cr-af-credpass-row" style="display:none">
        <label>Password hint</label>
        <input id="cr-af-credpass" type="text" placeholder="e.g. Ba**10*****@">
      </div>
    </div>

    <hr class="cr-modal-divider">

    <!-- Row 2: Role + Location -->
    <div class="cr-form-row-2">
      <div class="cr-form-row">
        <label>Role *</label>
        <input id="cr-af-role" type="text" placeholder="e.g. Software Engineer"
          onfocus="crCheckUrl()">
      </div>
      <div class="cr-form-row">
        <label>Location</label>
        <input id="cr-af-location" type="text" placeholder="e.g. Bangalore / Remote">
      </div>
    </div>

    <!-- Row 3: Applied date + Stage -->
    <div class="cr-form-row-2">
      <div class="cr-form-row">
        <label>Applied date</label>
        <input id="cr-af-date" type="date">
      </div>
      <div class="cr-form-row">
        <label>Stage</label>
        <select id="cr-af-stage" onchange="crCheckStageSub()">
          <option value="">-- Select --</option>
          <option>Applied</option><option>In Progress</option><option>Interview</option>
          <option>Offer</option><option>Rejected</option><option>Closed</option>
          <option>Ghosted</option><option>Withdrawn</option><option>NA</option>
        </select>
      </div>
    </div>

    <!-- Sub-stage (shown when In Progress) -->
    <div class="cr-substage-row" id="cr-af-substage-row">
      <div class="cr-form-row">
        <label>Sub-stage</label>
        <select id="cr-af-substage">
          <option value="">-- Select --</option>
          <option>Screening Pending</option>
          <option>Screening</option>
          <option>Review</option>
          <option>Under Consideration</option>
          <option>In Progress</option>
          <option>Closed</option>
        </select>

      </div>
    </div>

    <!-- Sub-stage (shown when Ghosted) -->
    <div class="cr-substage-row" id="cr-af-ghosted-row">
      <div class="cr-form-row">
        <label>Last known stage before ghosting</label>
        <select id="cr-af-ghosted-sub">
          <option value="">-- Select --</option>
          <option>Applied</option>
          <option>In Progress</option>
          <option>Screening Pending</option>
          <option>Screening</option>
          <option>Review</option>
          <option>Under Consideration</option>
          <option>Closed</option>
        </select>

      </div>
    </div>

    <!-- Job ID / Notes full width -->
    <div class="cr-form-row">
      <label>Job ID / Notes</label>
      <textarea id="cr-af-notes" placeholder="Job ID, notes, remarks&#8230;"></textarea>
    </div>

    <div class="cr-modal-actions">
      <button class="cr-btn-cancel" onclick="crCloseModal(\'cr-app-modal\')">Cancel</button>
      <button class="cr-btn-save" onclick="crSaveApp()">Save</button>
    </div>
  </div>
</div>

<!-- SITE MODAL -->
<div class="cr-modal-overlay" id="cr-site-modal">
  <div class="cr-modal">
    <h3 id="cr-site-modal-title">Add job site</h3>
    <div class="cr-form-row-2">
      <div class="cr-form-row"><label>Site name *</label><input id="cr-sf-name" type="text" placeholder="e.g. Portal A"></div>
      <div class="cr-form-row"><label>Site URL</label><input id="cr-sf-url" type="url" placeholder="https://&#8230;"></div>
    </div>
    <div class="cr-form-row"><label>Credential hint</label><input id="cr-sf-cred" type="text" placeholder="e.g. RWG, R Ba**10*****@"></div>
    <div class="cr-form-row"><label>Notes</label><input id="cr-sf-notes" type="text" placeholder="Optional&#8230;"></div>
    <div class="cr-modal-actions">
      <button class="cr-btn-cancel" onclick="crCloseModal(\'cr-site-modal\')">Cancel</button>
      <button class="cr-btn-save" onclick="crSaveSite()">Save</button>
    </div>
  </div>
</div>
'''


def build_career_css():
    return '''
.career-wrap { padding: 24px; max-width: 1400px; margin: 0 auto; }

/* ── Tabs ── */
.cr-tab-bar { display: flex; gap: 6px; margin-bottom: 22px; }
.cr-tab-btn {
  padding: 7px 18px; border-radius: 20px; border: 1.5px solid #d0d3e8;
  background: #fff; font-size: 13px; font-weight: 500; color: #555; cursor: pointer; transition: all 0.15s;
}
.cr-active { background: #3949ab !important; color: #fff !important; border-color: #3949ab !important; }
.cr-tab-btn:hover:not(.cr-active) { background: #eef0fb; }
.cr-tab-panel { display: none; }
.cr-panel-active { display: block !important; }

/* ── Card ── */
.cr-card { background: #fff; border-radius: 14px; border: 1px solid #e4e6f0; padding: 20px 22px; margin-bottom: 24px; }

/* ── Stats ── */
.cr-stats-row { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 22px; }
.cr-stat-box {
  background: #fff; border-radius: 12px; border: 1px solid #e4e6f0;
  padding: 12px 16px; flex: 1; min-width: 90px; text-align: center;
}
.cr-stat-box .sv { font-size: 22px; font-weight: 700; }
.cr-stat-box .sl { font-size: 10px; color: #888; margin-top: 2px; }
.cr-stat-box.c-total .sv       { color: #3949ab; }
.cr-stat-box.c-applied .sv     { color: #1565c0; }
.cr-stat-box.c-inprogress .sv  { color: #0097a7; }
.cr-stat-box.c-interview .sv   { color: #7b1fa2; }
.cr-stat-box.c-offer .sv       { color: #2e7d32; }
.cr-stat-box.c-rejected .sv    { color: #c62828; }
.cr-stat-box.c-closed .sv      { color: #546e7a; }
.cr-stat-box.c-ghosted .sv     { color: #757575; }
.cr-stat-box.c-withdrawn .sv   { color: #880e4f; }
.cr-stat-box.c-na .sv          { color: #999; }

/* ── Section title ── */
.cr-section-title { font-size: 15px; font-weight: 600; color: #1a1a2e; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }
.cr-pill { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 20px; background: #e8eaf6; color: #3949ab; }

/* ── Toolbar ── */
.cr-toolbar { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.cr-toolbar input[type="text"] {
  padding: 7px 12px; border-radius: 8px; border: 1.5px solid #d0d3e8;
  font-size: 13px; width: 200px; outline: none; background: #f5f6fa;
}
.cr-toolbar input:focus { border-color: #3949ab; background: #fff; }
.cr-toolbar select {
  padding: 7px 10px; border-radius: 8px; border: 1.5px solid #d0d3e8;
  font-size: 13px; background: #f5f6fa; outline: none; cursor: pointer;
}
.cr-btn-add {
  margin-left: auto; padding: 7px 16px; background: #3949ab; color: #fff;
  border: none; border-radius: 8px; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: background 0.15s;
}
.cr-btn-add:hover { background: #283593; }
.cr-fab-add {
  position: fixed; bottom: 28px; right: 28px; width: 52px; height: 52px;
  border-radius: 50%; background: #3949ab; color: #fff; border: none;
  font-size: 26px; line-height: 1; cursor: pointer; box-shadow: 0 4px 14px rgba(0,0,0,0.25);
  z-index: 50; display: none;
}
.cr-fab-add.cr-show { display: block; }
.cr-fab-add:hover { background: #283593; }

/* ── Table ── */
.cr-tbl-wrap { overflow-x: auto; }
.cr-table { width: 100%; border-collapse: collapse; font-size: 13px; table-layout: fixed; }
.cr-table th:nth-child(1), .cr-table td:nth-child(1) { width: 30ch; }
.cr-table th:nth-child(2), .cr-table td:nth-child(2) { width: 21ch; }
.cr-table th:nth-child(3), .cr-table td:nth-child(3) { width: 34ch; }
.cr-table th:nth-child(4), .cr-table td:nth-child(4) { width: 23ch; text-align: center; }
.cr-table th:nth-child(5), .cr-table td:nth-child(5) { width: 12ch; white-space: nowrap; }
.cr-table th:nth-child(6), .cr-table td:nth-child(6) { width: 16ch; text-align: center; }
.cr-table th:nth-child(7), .cr-table td:nth-child(7) { width: 122px; text-align: center; }
.cr-table thead tr { background: #f0f1f9; }
.cr-table th {
  padding: 10px 12px; text-align: left; font-weight: 600;
  font-size: 11px; color: #555 !important; text-transform: uppercase;
  letter-spacing: 0.04em; border-bottom: 1.5px solid #e4e6f0; white-space: nowrap;
  background: #f0f1f9 !important; cursor: pointer; border-right: 1px solid #e0e2ee;
}
.cr-table th:last-child { border-right: none; }
.cr-table th:hover { background: #e8eaf6 !important; }
.cr-table td { padding: 10px 12px; border-bottom: 1px solid #f0f1f7; border-right: 1px solid #eceef7; vertical-align: top; word-break: break-word; overflow-wrap: break-word; }
.cr-table td:last-child { border-right: none; }
.cr-table td:nth-child(3), .cr-table th:nth-child(3) { border-right: 2px solid #c7cae2; }
.cr-table tr:hover td { background: #f8f9ff; }
.cr-table tr.cr-notes-row td { background: #fffde7; padding: 10px 16px; font-size: 13px; color: #555; }
.cr-table tr.cr-notes-row:hover td { background: #fffde7; }
.cr-table tr.cr-company-row td { border-top: 2px solid #e4e6f0; }
.cr-group-first-td { vertical-align: top; }
.cr-group-cont-td  { border-bottom: none !important; padding: 0 !important; }

/* ── Company cell ── */
.cr-company-info { display: flex; flex-direction: column; gap: 2px; align-items: center; text-align: center; }
.cr-company-name { font-weight: 600; font-size: 13px; color: #1a1a2e; }
.cr-company-link { font-size: 11px; color: #3949ab; text-decoration: none; }
.cr-company-link:hover { text-decoration: underline; }
.cr-role-count { font-size: 10px; color: #999; }

/* ── Stage badge ── */
.cr-stage-badge {
  display: inline-block; padding: 3px 9px; border-radius: 20px; font-size: 11px; font-weight: 600;
}
.cr-stage-badge.applied     { background: #e3f2fd; color: #1565c0; }
.cr-stage-badge.inprogress  { background: #e0f7fa; color: #00838f; }
.cr-stage-badge.interview   { background: #f3e5f5; color: #6a1b9a; }
.cr-stage-badge.offer       { background: #e8f5e9; color: #2e7d32; }
.cr-stage-badge.rejected    { background: #ffebee; color: #c62828; }
.cr-stage-badge.closed      { background: #eceff1; color: #546e7a; }
.cr-stage-badge.ghosted     { background: #f5f5f5; color: #757575; }
.cr-stage-badge.withdrawn   { background: #fce4ec; color: #880e4f; }
.cr-stage-badge.na          { background: #f5f5f5; color: #999; }
.cr-substage { font-size: 10px; color: #888; margin-top: 3px; }

/* ── Credential badge ── */
.cr-cred-badge {
  display: inline-block; padding: 3px 9px; border-radius: 20px; font-size: 11px; font-weight: 600;
  background: #fff3e0; color: #e65100;
}
.cr-credtype { font-size: 10px; color: #888; margin-top: 3px; }

/* ── Action buttons ── */
.cr-act-btn {
  background: none; border: 1px solid #d0d3e8; border-radius: 6px;
  padding: 4px 7px; font-size: 12px; cursor: pointer; color: #555;
  transition: all 0.12s; margin-right: 3px;
}
.cr-act-btn:hover       { background: #eef0fb; border-color: #3949ab; color: #3949ab; }
.cr-act-btn.del:hover   { background: #ffebee; border-color: #c62828; color: #c62828; }
.cr-act-btn.notes:hover { background: #fffde7; border-color: #f9a825; color: #f9a825; }

/* ── Modal ── */
.cr-modal-overlay {
  display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.45);
  z-index: 999; align-items: center; justify-content: center;
}
.cr-modal-overlay.cr-open { display: flex; }
.cr-modal {
  background: #fff; border-radius: 16px; padding: 28px 32px;
  width: 820px; max-width: 96vw; max-height: 90vh; overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0,0,0,0.18);
  position: relative;
}
.cr-modal-x {
  position: absolute; top: 16px; right: 18px; background: none; border: none;
  font-size: 22px; line-height: 1; color: #888; cursor: pointer; padding: 4px 8px; border-radius: 6px;
}
.cr-modal-x:hover { background: #f0f1f9; color: #1a1a2e; }
.cr-modal h3 { font-size: 16px; font-weight: 700; margin-bottom: 20px; color: #1a1a2e; }
.cr-form-row { margin-bottom: 14px; }
.cr-form-row label { display: block; font-size: 12px; font-weight: 600; color: #555; margin-bottom: 5px; }
.cr-form-row input, .cr-form-row select, .cr-form-row textarea {
  width: 100%; padding: 8px 11px; border-radius: 8px;
  border: 1.5px solid #d0d3e8; font-size: 13px; outline: none; background: #f5f6fa;
  font-family: inherit;
}
.cr-form-row input:focus, .cr-form-row select:focus, .cr-form-row textarea:focus { border-color: #3949ab; background: #fff; }
.cr-form-row input:disabled, .cr-form-row select:disabled { background: #eeeeee; color: #999; cursor: not-allowed; }
.cr-form-row textarea { resize: vertical; min-height: 60px; }
.cr-form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 14px; }
.cr-form-row-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; margin-bottom: 14px; }
.cr-substage-row { display: none; margin-bottom: 14px; }
.cr-substage-row.visible { display: block; }
.cr-modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 22px; }
.cr-btn-cancel {
  padding: 8px 18px; border-radius: 8px; border: 1.5px solid #d0d3e8;
  background: #fff; font-size: 13px; cursor: pointer; color: #555;
}
.cr-btn-save {
  padding: 8px 22px; border-radius: 8px; border: none;
  background: #3949ab; color: #fff; font-size: 13px; font-weight: 600; cursor: pointer;
}
.cr-btn-save:hover { background: #283593; }
.cr-modal-divider { border: none; border-top: 1px solid #e4e6f0; margin: 16px 0; }

/* ── Misc ── */
.cr-empty { text-align: center; padding: 40px 20px; color: #aaa; font-size: 14px; }
.cr-empty-icon { font-size: 36px; margin-bottom: 8px; }
.cr-pw-field { display: flex; align-items: center; gap: 5px; }
.cr-pw-text { font-family: monospace; letter-spacing: 0.08em; font-size: 13px; }
.cr-pw-toggle { background: none; border: none; cursor: pointer; color: #888; font-size: 14px; padding: 0; }
.cr-popup {
  position: fixed; top: 50%; left: 50%; transform: translate(-50%,-50%);
  background: #fff; border-radius: 12px; padding: 24px 28px; z-index: 1100;
  box-shadow: 0 8px 32px rgba(0,0,0,0.22); max-width: 380px; width: 90%; text-align: center;
}
.cr-popup p { font-size: 14px; color: #333; margin-bottom: 18px; line-height: 1.5; }
.cr-popup-ok {
  padding: 8px 24px; background: #3949ab; color: #fff; border: none;
  border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer;
}
'''


def build_career_js():
    return '''
// ── Career state ──
var crApps        = [];
var crSites       = [];
var crEditAppIdx  = -1;
var crEditSiteIdx = -1;
var crCompanyChanged = false;
var crLockedCompany  = null;  // company name that is currently locked
var crLoaded         = false; // becomes true once career data has been fetched at least once

// ── Load / Save ──
function crLoad() {
  return fetch('/api/career-load')
    .then(function(r){ return r.json(); })
    .then(function(d){ crApps = d.apps||[]; crSites = d.sites||[]; crLoaded = true; crRenderApps(); crRenderSites(); })
    .catch(function(){ crRenderApps(); crRenderSites(); });
}
// Fetches career data if it hasn't been loaded yet in this session — used
// when opening the application modal from the Jobs tab, since that tab
// never triggers the normal crLoad() that runs on visiting the Career tab.
function crEnsureLoaded() {
  if (crLoaded) return Promise.resolve();
  return crLoad();
}
function crSaveToServer() {
  fetch('/api/career-save', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({apps:crApps, sites:crSites})
  }).catch(function(){});
}

// ── Tab switch ──
function crSwitchTab(id, btn) {
  document.querySelectorAll('.cr-tab-panel').forEach(function(p){ p.style.display='none'; p.classList.remove('cr-panel-active'); });
  document.querySelectorAll('.cr-tab-btn').forEach(function(b){ b.classList.remove('cr-active'); });
  var panel = document.getElementById('cr-tab-'+id);
  if (panel) { panel.style.display='block'; panel.classList.add('cr-panel-active'); }
  if (btn) btn.classList.add('cr-active');
}

// ── Logo helpers removed ──

// ── Badge helpers ──
function crStageBadge(s) {
  var cls = (s||'').toLowerCase().replace(' ','').replace('/','');
  if(cls==='inprogress') cls='inprogress';
  return '<span class="cr-stage-badge '+cls+'">'+crEsc(s||'—')+'</span>';
}
function crCredBadge(c) {
  if(!c) return '—';
  return '<span class="cr-cred-badge">'+crEsc(c)+'</span>';
}

// ── Stats ──
function crUpdateStats() {
  var counts = {total:0,applied:0,inprogress:0,interview:0,offer:0,rejected:0,closed:0,ghosted:0,withdrawn:0,na:0};
  // count unique roles (each app entry = 1 role)
  crApps.forEach(function(a){
    counts.total++;
    var s = (a.stage||'').toLowerCase().replace(' ','');
    if(s==='applied')     counts.applied++;
    else if(s==='inprogress') counts.inprogress++;
    else if(s==='interview')  counts.interview++;
    else if(s==='offer')      counts.offer++;
    else if(s==='rejected')   counts.rejected++;
    else if(s==='closed')     counts.closed++;
    else if(s==='ghosted')    counts.ghosted++;
    else if(s==='withdrawn')  counts.withdrawn++;
    else if(s==='na')         counts.na++;
  });
  var el = document.getElementById('cr-app-stats');
  if(!el) return;
  el.innerHTML =
    '<div class="cr-stat-box c-total"><div class="sv">'+counts.total+'</div><div class="sl">Total</div></div>'+
    '<div class="cr-stat-box c-applied"><div class="sv">'+counts.applied+'</div><div class="sl">Applied</div></div>'+
    '<div class="cr-stat-box c-inprogress"><div class="sv">'+counts.inprogress+'</div><div class="sl">In Progress</div></div>'+
    '<div class="cr-stat-box c-interview"><div class="sv">'+counts.interview+'</div><div class="sl">Interview</div></div>'+
    '<div class="cr-stat-box c-offer"><div class="sv">'+counts.offer+'</div><div class="sl">Offer</div></div>'+
    '<div class="cr-stat-box c-rejected"><div class="sv">'+counts.rejected+'</div><div class="sl">Rejected</div></div>'+
    '<div class="cr-stat-box c-closed"><div class="sv">'+counts.closed+'</div><div class="sl">Closed</div></div>'+
    '<div class="cr-stat-box c-ghosted"><div class="sv">'+counts.ghosted+'</div><div class="sl">Ghosted</div></div>'+
    '<div class="cr-stat-box c-withdrawn"><div class="sv">'+counts.withdrawn+'</div><div class="sl">Withdrawn</div></div>'+
    '<div class="cr-stat-box c-na"><div class="sv">'+counts.na+'</div><div class="sl">NA</div></div>';
}

// ── APPLICATIONS RENDER ──
function crWrapAtLimit(text, limit) {
  text = text || '';
  if (text.length <= limit) return crEsc(text);
  var lines = [];
  var rest = text;
  while (rest.length > limit) {
    var slice = rest.slice(0, limit);
    var lastSpace = slice.lastIndexOf(' ');
    if (lastSpace > 0) {
      lines.push(rest.slice(0, lastSpace));
      rest = rest.slice(lastSpace + 1);
    } else {
      lines.push(rest.slice(0, limit));
      rest = rest.slice(limit);
    }
  }
  if (rest) lines.push(rest);
  return lines.map(function(l){ return crEsc(l); }).join('<br>');
}

function crWrapLocation(text) {
  text = text || '';
  if (!text) return '—';
  var parts = text.split(',');
  if (parts.length <= 2) return crEsc(text);
  var lines = [];
  for (var i = 0; i < parts.length; i += 2) {
    var chunk = parts.slice(i, i + 2).join(',').trim();
    if (i + 2 < parts.length) chunk += ',';
    lines.push(chunk);
  }
  return lines.map(function(l){ return crEsc(l); }).join('<br>');
}

function crRenderApps() {
  crUpdateStats();
  var q      = (document.getElementById('cr-app-search')||{value:''}).value.toLowerCase();
  var stFilt = (document.getElementById('cr-app-filter-stage')||{value:''}).value;
  var sort   = (document.getElementById('cr-app-sort')||{value:'default'}).value;

  // Filter
  var filtered = crApps.filter(function(a){
    return (!q || (a.company||'').toLowerCase().includes(q) || (a.role||'').toLowerCase().includes(q))
        && (!stFilt || a.stage === stFilt);
  });

  // Sort
  if (sort === 'company_asc')  filtered.sort(function(a,b){ return (a.company||'').localeCompare(b.company||''); });
  if (sort === 'company_desc') filtered.sort(function(a,b){ return (b.company||'').localeCompare(a.company||''); });
  if (sort === 'date_asc')     filtered.sort(function(a,b){ return (a.date||'') > (b.date||'') ? 1 : -1; });
  if (sort === 'date_desc')    filtered.sort(function(a,b){ return (a.date||'') < (b.date||'') ? 1 : -1; });
  if (sort === 'stage')        filtered.sort(function(a,b){ return (a.stage||'').localeCompare(b.stage||''); });

  var countEl = document.getElementById('cr-app-count');
  if(countEl) countEl.textContent = filtered.length;

  var tbody = document.getElementById('cr-app-tbody');
  var empty = document.getElementById('cr-app-empty');
  if(!filtered.length){ if(tbody) tbody.innerHTML=''; if(empty) empty.style.display='block'; return; }
  if(empty) empty.style.display='none';

  // Group by company (case-insensitive) preserving sort order
  var groups = [];
  var groupMap = {};
  filtered.forEach(function(a){
    var key = (a.company||'').toLowerCase().trim();
    if(!groupMap[key]){ groupMap[key]=[]; groups.push({key:key, company:a.company, rows:[]}); }
    groupMap[key].push(a);
  });
  // attach rows to groups in date order (oldest first); same date = original save order
  groups.forEach(function(g){
    g.rows = groupMap[g.key].slice().sort(function(a,b){
      var da=a.date||'', db=b.date||'';
      if(da!==db) return da>db?1:-1;
      return crApps.indexOf(a)-crApps.indexOf(b);
    });
    var head = g.rows[0];
    g.link = head.link; g.credential = head.credential; g.credtype = head.credtype; g.passhint = head.passhint;
  });

  var html = '';
  groups.forEach(function(g, gi){
    var groupBg = gi % 2 === 0 ? '#ffffff' : '#f7f8fd';
    var roleCount = g.rows.length;
    var companyCellHtml =
      '<div class="cr-company-info">'+
        '<div class="cr-company-name">'+crWrapAtLimit(g.company, 25)+'</div>'+
        (g.link ? '<a class="cr-company-link" href="'+crEsc(g.link)+'" target="_blank">Open &#8599;</a>' : '')+
        (roleCount>1 ? '<div class="cr-role-count">'+roleCount+' roles</div>' : '')+
      '</div>';

    var _credtypeText = g.credtype==='With Password' && g.passhint
      ? 'With Password '+crEsc(g.passhint)
      : crEsc(g.credtype||'');
    var credCellHtml = '<div>'+crCredBadge(g.credential)+'<div class="cr-credtype">'+_credtypeText+'</div></div>';

    g.rows.forEach(function(a, ri){
      var realIdx = crApps.indexOf(a);
      var isFirst  = ri === 0;
      var isLast   = ri === g.rows.length - 1;
      var notesId  = 'cr-notes-'+realIdx;

      // Company cell: show on first row, empty bordered cell on subsequent rows
      var companyTd = isFirst
        ? '<td class="cr-group-first-td">'+companyCellHtml+'</td>'
        : '<td class="cr-group-cont-td"></td>';

      // Credential cell: show on first row only, empty on subsequent
      var credTd = isFirst
        ? '<td class="cr-group-first-td">'+credCellHtml+'</td>'
        : '<td class="cr-group-cont-td"></td>';

      // Bottom border only on last role row of the group
      var rowStyle = isLast ? '' : 'border-bottom:none;';
      var miniBg = ri % 2 === 0 ? groupBg : (gi % 2 === 0 ? '#f2f3fb' : '#eceef8');
      rowStyle += 'background:'+miniBg+';';

      html +=
        '<tr class="'+(isFirst?'cr-company-row':'')+'" style="'+rowStyle+'">'+
          companyTd+
          credTd+
          '<td>'+crWrapAtLimit(a.role, 39)+'</td>'+
          '<td>'+crWrapAtLimit(a.location, 21)+'</td>'+
          '<td>'+(a.date||'—')+'</td>'+
          '<td>'+crStageBadge(a.stage)+(a.stage==='In Progress'&&a.substage?'<div class="cr-substage">'+crEsc(a.substage)+'</div>':'')+(a.stage==='Ghosted'&&a.ghostedsub?'<div class="cr-substage">'+crEsc(a.ghostedsub)+'</div>':'')+'</td>'+
          '<td>'+
            '<button class="cr-act-btn" onclick="crOpenAppModal('+realIdx+')">&#9998;</button>'+
            '<button class="cr-act-btn del" onclick="crDeleteApp('+realIdx+')">&#128465;</button>'+
            '<button class="cr-act-btn notes" onclick="crToggleNotes('+realIdx+',this)">&#128203;</button>'+
          '</td>'+
        '</tr>'+
        '<tr id="'+notesId+'" class="cr-notes-row" style="display:none">'+
          '<td></td><td></td>'+
          '<td colspan="5">'+
            '<b>Job ID / Notes:</b> '+(a.notes ? crEsc(a.notes) : '<em style="color:#bbb">No notes</em>')+
          '</td>'+
        '</tr>';
    });
  });

  if(tbody) tbody.innerHTML = html;
}

function crToggleNotes(idx, btn) {
  var row = document.getElementById('cr-notes-'+idx);
  if(!row) return;
  var visible = row.style.display !== 'none';
  row.style.display = visible ? 'none' : 'table-row';
  btn.style.background = visible ? '' : '#fffde7';
}

function crDeleteApp(i) {
  if(!confirm('Delete this application?')) return;
  crApps.splice(i,1); crSaveToServer(); crRenderApps();
}

// ── Company / URL validation ──
function crFindByCompany(name) {
  var key = (name||'').toLowerCase().trim();
  for(var i=0;i<crApps.length;i++){
    if((crApps[i].company||'').toLowerCase().trim()===key) return crApps[i];
  }
  return null;
}
function crFindByUrl(url) {
  var u = (url||'').trim().toLowerCase();
  if(!u) return null;
  for(var i=0;i<crApps.length;i++){
    if((crApps[i].link||'').trim().toLowerCase()===u) return crApps[i];
  }
  return null;
}
function crLockCompanyFields(app) {
  document.getElementById('cr-af-link').value    = app.link     || '';
  document.getElementById('cr-af-cred').value    = app.credential || '';
  document.getElementById('cr-af-credtype').value = app.credtype  || '';
  document.getElementById('cr-af-credpass').value = app.passhint  || '';
  document.getElementById('cr-af-link').disabled    = true;
  document.getElementById('cr-af-cred').disabled    = true;
  document.getElementById('cr-af-credtype').disabled = true;
  document.getElementById('cr-af-credpass').disabled = true;
  crLockedCompany = (app.company||'').toLowerCase().trim();
  crCheckCredSub();
}
function crUnlockCompanyFields() {
  document.getElementById('cr-af-link').disabled    = false;
  document.getElementById('cr-af-cred').disabled    = false;
  document.getElementById('cr-af-credtype').disabled = false;
  document.getElementById('cr-af-credpass').disabled = false;
  crLockedCompany = null;
}
function crCheckCompanyName() {
  if(crEditAppIdx >= 0) return; // editing — skip
  var name = document.getElementById('cr-af-company').value.trim();
  if(!name){ crUnlockCompanyFields(); return; }
  var existing = crFindByCompany(name);
  if(existing){ crLockCompanyFields(existing); }
  else { crUnlockCompanyFields(); }
}
function crCheckUrl() {
  if(crEditAppIdx >= 0) return; // editing — skip
  var url = document.getElementById('cr-af-link').value.trim();
  if(!url) return;
  var existing = crFindByUrl(url);
  if(!existing) return;
  // check if same company already matched
  var typedName = document.getElementById('cr-af-company').value.trim().toLowerCase();
  if(typedName === (existing.company||'').toLowerCase().trim()) return;
  // URL matched different company — show popup
  document.getElementById('cr-url-popup-msg').textContent =
    'This URL already exists under "'+existing.company+'". Switching to that company.';
  document.getElementById('cr-url-popup').style.display = 'block';
  document.getElementById('cr-popup-overlay').style.display = 'block';
  document.getElementById('cr-af-company').value = existing.company;
  crLockCompanyFields(existing);
}
function crUrlPopupOk() {
  document.getElementById('cr-url-popup').style.display = 'none';
  document.getElementById('cr-popup-overlay').style.display = 'none';
}

// ── Sub-field visibility ──
function crCheckStageSub() {
  var stage = document.getElementById('cr-af-stage').value;
  var ipRow = document.getElementById('cr-af-substage-row');
  var ghRow = document.getElementById('cr-af-ghosted-row');
  if(ipRow) ipRow.classList.toggle('visible', stage==='In Progress');
  if(ghRow) ghRow.classList.toggle('visible', stage==='Ghosted');

}
function crCheckCredSub() {
  var cred = document.getElementById('cr-af-cred').value;
  var row  = document.getElementById('cr-af-credtype-row');
  var passRow = document.getElementById('cr-af-credpass-row');
  if(row) row.classList.toggle('visible', cred==='Registered');
  if(passRow){
    var credtype = document.getElementById('cr-af-credtype').value;
    passRow.style.display = (cred==='Registered' && credtype==='With Password') ? 'block' : 'none';
  }
}

// ── Open App Modal ──
function crOpenAppModal(idx) {
  if(idx===undefined) idx=-1;
  crEditAppIdx = idx;
  var a = idx>=0 ? crApps[idx] : {};
  document.getElementById('cr-app-modal-title').textContent = idx>=0 ? 'Edit application' : 'Add application';

  // reset locks
  crUnlockCompanyFields();
  crLockedCompany = null;

  document.getElementById('cr-af-company').value   = a.company   || '';
  document.getElementById('cr-af-link').value      = a.link      || '';
  document.getElementById('cr-af-cred').value      = a.credential|| '';
  document.getElementById('cr-af-credtype').value  = a.credtype  || '';
  document.getElementById('cr-af-credpass').value  = a.passhint  || '';
  document.getElementById('cr-af-role').value      = a.role      || '';
  document.getElementById('cr-af-location').value  = a.location  || '';
  document.getElementById('cr-af-date').value      = a.date      || '';
  document.getElementById('cr-af-stage').value       = a.stage      || '';
  document.getElementById('cr-af-substage').value    = a.substage   || '';
  document.getElementById('cr-af-ghosted-sub').value = a.ghostedsub || '';
  document.getElementById('cr-af-notes').value     = a.notes     || '';

  // if editing existing, lock company fields if not first entry of company
  if(idx>=0){
    var key = (a.company||'').toLowerCase().trim();
    var sameCompany = crApps.filter(function(x){ return (x.company||'').toLowerCase().trim()===key; });
    sameCompany.sort(function(x,y){
      var dx=x.date||'', dy=y.date||'';
      if(dx!==dy) return dx>dy?1:-1;
      return crApps.indexOf(x)-crApps.indexOf(y);
    });
    if(sameCompany[0] !== a){
      // not the display-sorted first — replicate its link/credential
      // data into the fields (this row's own copy may be blank), then lock
      var first = sameCompany[0];
      document.getElementById('cr-af-link').value     = first.link      || '';
      document.getElementById('cr-af-cred').value      = first.credential|| '';
      document.getElementById('cr-af-credtype').value  = first.credtype  || '';
      document.getElementById('cr-af-credpass').value  = first.passhint  || '';
      document.getElementById('cr-af-link').disabled    = true;
      document.getElementById('cr-af-cred').disabled    = true;
      document.getElementById('cr-af-credtype').disabled = true;
      document.getElementById('cr-af-credpass').disabled = true;
    }
  }

  crCheckStageSub();
  crCheckCredSub();
  document.getElementById('cr-app-modal').classList.add('cr-open');
}

// ── Open App Modal, pre-filled with just a company name (from Job Odyssey) ──
async function crOpenAppModalPrefill(company) {
  await crEnsureLoaded(); // make sure crApps reflects saved data even if Career tab was never opened
  crOpenAppModal(-1); // blank modal, resets locks/edit state
  document.getElementById('cr-af-company').value = company || '';
  // reuse existing link/credential if this company already has an entry
  crCheckCompanyName();
}

// ── Save App ──
function crSaveApp() {
  var company = document.getElementById('cr-af-company').value.trim();
  var role    = document.getElementById('cr-af-role').value.trim();
  if(!company||!role){ alert('Company and role are required.'); return; }

  var credtype = document.getElementById('cr-af-credtype').value;
  var credpass = '';
  if(credtype==='With Password') credpass = (document.getElementById('cr-af-credpass')||{value:''}).value.trim();

  var obj = {
    company:    company,
    link:       document.getElementById('cr-af-link').value.trim(),
    credential: document.getElementById('cr-af-cred').value,
    credtype:   credtype,
    passhint:   credpass,
    role:       role,
    location:   document.getElementById('cr-af-location').value.trim(),
    date:       document.getElementById('cr-af-date').value,
    stage:      document.getElementById('cr-af-stage').value,
    substage:   document.getElementById('cr-af-substage').value,
    notes:      document.getElementById('cr-af-notes').value.trim(),
    ghostedsub: document.getElementById('cr-af-ghosted-sub').value
  };

  // if company locked — sync link+cred to all same-company entries
  if(crLockedCompany){
    crApps.forEach(function(a){
      if((a.company||'').toLowerCase().trim()===crLockedCompany){
        a.link=obj.link; a.credential=obj.credential; a.credtype=obj.credtype; a.passhint=obj.passhint;
      }
    });
  }

  if(crEditAppIdx>=0) crApps[crEditAppIdx]=obj; else crApps.push(obj);
  crSaveToServer(); crCloseModal('cr-app-modal'); crRenderApps();
}

// ── JOB SITES ──
function crRenderSites() {
  var q = (document.getElementById('cr-site-search')||{value:''}).value.toLowerCase();
  var filtered = crSites.filter(function(s){ return !q||(s.name||'').toLowerCase().includes(q); });
  var countEl = document.getElementById('cr-site-count');
  if(countEl) countEl.textContent = filtered.length;
  var tbody = document.getElementById('cr-site-tbody');
  var empty = document.getElementById('cr-site-empty');
  if(!filtered.length){ if(tbody) tbody.innerHTML=''; if(empty) empty.style.display='block'; return; }
  if(empty) empty.style.display='none';
  if(tbody) tbody.innerHTML = filtered.map(function(s){
    var realIdx = crSites.indexOf(s);
    return '<tr>'+
      '<td>'+
        '<div class="cr-company-name">'+crEsc(s.name)+'</div>'+
        (s.url?'<a class="cr-company-link" href="'+crEsc(s.url)+'" target="_blank">Open &#8599;</a>':'')+
      '</td>'+
      '<td>'+crEsc(s.cred||'—')+'</td>'+
      '<td>'+crEsc(s.notes||'—')+'</td>'+
      '<td>'+
        '<button class="cr-act-btn" onclick="crOpenSiteModal('+realIdx+')">&#9998;</button>'+
        '<button class="cr-act-btn del" onclick="crDeleteSite('+realIdx+')">&#128465;</button>'+
      '</td></tr>';
  }).join('');
}

function crOpenSiteModal(idx) {
  if(idx===undefined) idx=-1;
  crEditSiteIdx=idx;
  var s=idx>=0?crSites[idx]:{};
  document.getElementById('cr-site-modal-title').textContent=idx>=0?'Edit site':'Add job site';
  document.getElementById('cr-sf-name').value  = s.name  ||'';
  document.getElementById('cr-sf-url').value   = s.url   ||'';
  document.getElementById('cr-sf-cred').value  = s.cred  ||'';
  document.getElementById('cr-sf-notes').value = s.notes ||'';
  document.getElementById('cr-site-modal').classList.add('cr-open');
}
function crDeleteSite(i) {
  if(!confirm('Delete this site?')) return;
  crSites.splice(i,1); crSaveToServer(); crRenderSites();
}
function crSaveSite() {
  var name=document.getElementById('cr-sf-name').value.trim();
  if(!name){ alert('Site name is required.'); return; }
  var obj={
    name: name,
    url:  document.getElementById('cr-sf-url').value.trim(),
    cred: document.getElementById('cr-sf-cred').value.trim(),
    notes:document.getElementById('cr-sf-notes').value.trim()
  };
  if(crEditSiteIdx>=0) crSites[crEditSiteIdx]=obj; else crSites.unshift(obj);
  crSaveToServer(); crCloseModal('cr-site-modal'); crRenderSites();
}

// ── Modals ──
function crCloseModal(id) {
  document.getElementById(id).classList.remove('cr-open');
  // reset substage/cred rows
  var sr=document.getElementById('cr-af-substage-row'); if(sr) sr.classList.remove('visible');
  var gr=document.getElementById('cr-af-ghosted-row');  if(gr) gr.classList.remove('visible');
  var cr=document.getElementById('cr-af-credtype-row'); if(cr) cr.classList.remove('visible');
  crUnlockCompanyFields();
}
// Outside-click no longer closes modals (prevents accidental data loss)
window.addEventListener('scroll', function(){
  var fab = document.querySelector('.cr-fab-add');
  if(fab) fab.classList.toggle('cr-show', window.scrollY > 200);
});

// ── Utils ──
function crEsc(s){
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
'''

