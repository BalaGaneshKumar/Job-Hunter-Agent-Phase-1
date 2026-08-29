"""
dashboard_jobs.py — Jobs, Blacklist, Profile tab HTML + JS
Imported by dashboard_server.py
"""
import json
from dashboard_ui import esc, html_page
from dashboard_workflows import (
    load_config, read_file_text, read_profile,
    JOBS_CSV, BLACKLIST_CSV, PROFILE_JSON
)

JOBS_PER_PAGE = 20

def build_jobs_html(cfg, kw_json, loc_json, bl_json, prof_json, locations):
    return '''
<!-- JOBS -->
<div id="page-jobs" class="page active">
  <div class="filters">
    <select id="filter_status" onchange="renderJobs(1)"><option value="">All Status</option><option value="Scraped">Scraped</option><option value="Eligible">Eligible</option><option value="Applied">Applied</option><option value="Ineligible">Ineligible</option><option value="Hold">Hold</option><option value="Blacklist">Blacklist</option></select>
    <select id="filter_portal" onchange="renderJobs(1)"><option value="">All Portals</option></select>
    <select id="filter_ie" onchange="renderJobs(1)"><option value="">All Int/Ext</option><option value="Internal">Internal</option><option value="External">External</option><option value="Other">Other</option></select>
    <select id="filter_location" onchange="renderJobs(1)"><option value="">All Locations</option></select>
    <input type="text" id="search" placeholder="Search title..." onkeyup="renderJobs(1)">
    <select id="sort_by" onchange="renderJobs(1)"><option value="">Sort By</option><option value="title_asc">Title A-Z</option><option value="title_desc">Title Z-A</option><option value="company_asc">Company A-Z</option><option value="date_desc">Date Newest</option><option value="date_asc">Date Oldest</option><option value="status">Status</option></select>
    <button class="btn" style="background:#27ae60;color:white;" onclick="reloadJobsCSV()">🔄 Reload</button>
    <span class="job-count-label" id="jobs_count_label"></span>
    <span class="job-count-label" id="jobs_page_label" style="color:#999;"></span>
  </div>

  <div class="segbar-wrap" id="segbar_groups"></div>

  <div class="jobs-split">
    <div class="jobs-list-col">
      <div class="section-title" style="margin:0 0 10px;">Job Card</div>
      <div class="jobs-list" id="jobs_container"></div>
    </div>
    <div class="job-detail-panel" id="job_detail_panel">
      <div class="job-detail-empty">Select a job from the list to see details.</div>
    </div>
  </div>
  <div class="pagination" id="jobs_pagination"></div>
</div>


<!-- PROFILE -->
<div id="page-profile" class="page">
  <div class="section-title">Personal Information</div>
  <div class="form-grid">
    <div class="form-group"><label>First Name</label><input id="firstName" type="text"></div>
    <div class="form-group"><label>Last Name</label><input id="lastName" type="text"></div>
    <div class="form-group"><label>Full Name</label><input id="fullName" type="text"></div>
    <div class="form-group"><label>Legal Name</label><input id="legalName" type="text"></div>
    <div class="form-group"><label>Middle Name</label><input id="middleName" type="text"></div>
    <div class="form-group"><label>Preferred Name</label><input id="preferredName" type="text"></div>
    <div class="form-group"><label>Email</label><input id="email" type="email"></div>
    <div class="form-group"><label>Phone</label><input id="phone" type="text"></div>
    <div class="form-group"><label>Phone Type</label><select id="phoneType"><option>Mobile</option><option>Home</option><option>Work</option></select></div>
    <div class="form-group"><label>Phone Country Code</label><input id="phoneCountry" type="text"></div>
    <div class="form-group"><label>Birthday</label><input id="birthday" type="date"></div>
    <div class="form-group"><label>Location</label><input id="location_p" type="text"></div>
    <div class="form-group"><label>Address</label><input id="address" type="text"></div>
    <div class="form-group"><label>City</label><input id="city" type="text"></div>
    <div class="form-group"><label>State</label><input id="state" type="text"></div>
    <div class="form-group"><label>Country</label><input id="country" type="text"></div>
    <div class="form-group"><label>Postal Code</label><input id="postalCode" type="text"></div>
  </div>
  <div class="section-title">Education</div>
  <div class="form-grid">
    <div class="form-group"><label>School / University</label><input id="school" type="text"></div>
    <div class="form-group"><label>Degree</label><input id="degree" type="text"></div>
    <div class="form-group"><label>Highest Degree</label><select id="highestDegree"><option value="">Select</option><option>High School</option><option>Diploma</option><option>Bachelor</option><option>Master</option><option>PhD</option></select></div>
    <div class="form-group"><label>Graduation Year</label><input id="gradYear" type="text"></div>
    <div class="form-group"><label>GPA / CGPA</label><input id="gpa" type="text"></div>
    <div class="form-group"><label>Field of Study</label><input id="fieldOfStudy" type="text"></div>
  </div>
  <div class="section-title">Experience</div>
  <div class="form-grid">
    <div class="form-group"><label>Currently Employed</label><select id="currentlyEmployed"><option>No</option><option>Yes</option></select></div>
    <div class="form-group"><label>Total Experience (Years)</label><input id="totalExperience" type="text"></div>
    <div class="form-group"><label>Relevant Experience (Years)</label><input id="relevantExperience" type="text"></div>
    <div class="form-group"><label>Notice Period</label><select id="noticePeriod"><option value="">Select</option><option>Immediate</option><option>15 Days</option><option>30 Days</option><option>45 Days</option><option>60 Days</option><option>90 Days</option></select></div>
    <div class="form-group"><label>Current CTC</label><input id="currentCTC" type="text"></div>
    <div class="form-group"><label>Expected CTC — Text</label><input id="expectedCTCText" type="text"></div>
    <div class="form-group"><label>Expected CTC — Number</label><input id="expectedCTCNumber" type="number"></div>
    <div class="form-group"><label>Available From</label><input id="availableFrom" type="date"></div>
    <div class="form-group"><label>Night Shift</label><select id="nightShift"><option>No</option><option>Yes</option></select></div>
  </div>
  <div class="section-title">Work History <button onclick="addJob()" style="background:#3498db;color:white;border:none;padding:4px 12px;border-radius:6px;cursor:pointer;font-size:12px;margin-left:10px;">+ Add Job</button></div>
  <div id="jobs_container_profile"></div>
  <div class="section-title">EEO Information</div>
  <div class="form-grid">
    <div class="form-group"><label>Gender</label><select id="gender"><option value="">Prefer not to say</option><option>Male</option><option>Female</option><option>Non-binary</option></select></div>
    <div class="form-group"><label>Ethnicity</label><input id="ethnicity" type="text"></div>
    <div class="form-group"><label>Hispanic</label><select id="hispanic"><option>No</option><option>Yes</option></select></div>
    <div class="form-group"><label>Veteran Status</label><select id="veteran"><option>No</option><option>Yes</option></select></div>
    <div class="form-group"><label>Disability</label><select id="disability"><option>No</option><option>Yes</option></select></div>
    <div class="form-group"><label>LGBT</label><select id="lgbt"><option>Prefer not to say</option><option>Yes</option><option>No</option></select></div>
  </div>
  <div class="section-title">Work Authorization</div>
  <div class="form-grid">
    <div class="form-group"><label>Work Authorization</label><input id="workAuthorization" type="text"></div>
    <div class="form-group"><label>Work Auth (US)</label><select id="workAuthUS"><option>No</option><option>Yes</option></select></div>
    <div class="form-group"><label>Visa Type</label><input id="visaType" type="text"></div>
    <div class="form-group"><label>Sponsorship Required</label><select id="sponsorship"><option>No</option><option>Yes</option></select></div>
    <div class="form-group"><label>Willing to Relocate</label><select id="relocate"><option>No</option><option>Yes</option></select></div>
    <div class="form-group"><label>Relocate Preference</label><input id="relocatePreference" type="text"></div>
    <div class="form-group"><label>Work Location Preference</label><input id="workLocation" type="text"></div>
  </div>
  <div class="section-title">India Specific</div>
  <div class="form-grid">
    <div class="form-group"><label>PAN Number</label><input id="pan" type="text"></div>
    <div class="form-group"><label>Aadhaar Number</label><input id="aadhaar" type="text"></div>
    <div class="form-group"><label>UAN Number</label><input id="uan" type="text"></div>
    <div class="form-group"><label>ESIC Number</label><input id="esic" type="text"></div>
  </div>
  <div class="section-title">Social &amp; Links</div>
  <div class="form-grid">
    <div class="form-group"><label>Portal A</label><input id="portal_a_p" type="text"></div>
    <div class="form-group"><label>GitHub</label><input id="github" type="text"></div>
    <div class="form-group"><label>Portfolio</label><input id="portfolio" type="text"></div>
    <div class="form-group"><label>Website</label><input id="website" type="text"></div>
    <div class="form-group"><label>Twitter</label><input id="twitter" type="text"></div>
  </div>
  <div class="section-title">Skills &amp; Preferences</div>
  <div class="form-grid">
    <div class="form-group full-width"><label>Skills</label><textarea id="skills"></textarea></div>
    <div class="form-group"><label>Language</label><input id="language" type="text"></div>
    <div class="form-group"><label>Native Language</label><input id="nativeLanguage" type="text"></div>
    <div class="form-group"><label>Employment Type</label><select id="empType"><option>Full Time</option><option>Part Time</option><option>Contract</option><option>Internship</option></select></div>
    <div class="form-group full-width"><label>Professional Summary</label><textarea id="summary"></textarea></div>
  </div>
  <button class="btn-save" onclick="saveProfile()">&#128190; Save profile.json</button>
  <span class="save-msg" id="saveMsg"></span>
</div>
'''


def build_jobs_js(kw_json, loc_json, bl_json, prof_json):
    return '''
// ── Preloaded data ────────────────────────────────────────────────────────────
let CONFIG_KEYWORDS  = ''' + kw_json + ''';
let CONFIG_LOCATIONS = ''' + loc_json + ''';
let CONFIG_BLACKLIST = ''' + bl_json + ''';
const PROFILE_DATA   = ''' + prof_json + ''';

// ── State ─────────────────────────────────────────────────────────────────────
let jobs         = [];
let csvHeader    = [];
let blacklistJobs = [];
let blHeader     = [];
let jobsPage     = 1;
const JOBS_PER_PAGE = 20;
let _filteredJobs = [];

// ── CSV Parser ─────────────────────────────────────────────────────────────────
function parseCSV(text) {
  text = text.split(String.fromCharCode(13,10)).join(String.fromCharCode(10)).split(String.fromCharCode(13)).join(String.fromCharCode(10));
  const fields = parseCSVAll(text);
  if(!fields.length) return {header:[],rows:[]};
  const header = fields[0];
  const rows = [];
  for(let i=1;i<fields.length;i++){
    const vals=fields[i];
    if(!vals.some(v=>v.trim())) continue;
    const obj={_row:i+1};
    header.forEach((col,ci)=>obj[col]=vals[ci]!==undefined?vals[ci]:'');
    if(obj['Job Title']||obj[header[1]]) rows.push(obj);
  }
  return {header,rows};
}
function parseCSVAll(text){
  const rows=[];let row=[],cur='',inQ=false,i=0;
  while(i<text.length){const ch=text[i];
    if(inQ){if(ch==='"'){if(text[i+1]==='"'){cur+='"';i+=2;continue;}inQ=false;i++;continue;}cur+=ch;i++;continue;}
    if(ch==='"'){inQ=true;i++;continue;}
    if(ch===','){row.push(cur);cur='';i++;continue;}
    if(ch==='\\n'){row.push(cur);cur='';rows.push(row);row=[];i++;continue;}
    cur+=ch;i++;}
  if(cur||row.length){row.push(cur);rows.push(row);}return rows;
}
function toCSV(header,rows){
  const e=v=>{v=String(v===null||v===undefined?'':v);if(v.includes(',')||v.includes('"')||v.includes('\\n'))return'"'+v.replace(/"/g,'""')+'"';return v;};
  return [header.map(e).join(','),...rows.map(r=>header.map(h=>e(r[h]||'')).join(','))].join('\\n');
}
function escHtml(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}

// ── Auto-load ──────────────────────────────────────────────────────────────────
window.onload = async function() {
  fillProfileForm(PROFILE_DATA);
  initRequestTab();
  await reloadJobsCSV();
  await reloadBlacklistCSV();
  // Activate tab from URL path
  const path = window.location.pathname;
  let activeTab = 'jobs';
  if(path.startsWith('/scraper')) activeTab = 'scraper';
  else if(path.startsWith('/career')) activeTab = 'career';
  else if(path.startsWith('/profile')) activeTab = 'profile';
  const btn = [...document.querySelectorAll('.nav button')].find(b=>b.getAttribute('onclick')&&b.getAttribute('onclick').includes("'"+activeTab+"'"));
  showPage(activeTab, btn);
  // Activate sub-tab from INITIAL_SUBTAB (set by server)
  if(activeTab === 'scraper' && typeof INITIAL_SUBTAB !== 'undefined' && INITIAL_SUBTAB){
    const subBtn = [...document.querySelectorAll('.sub-nav button')].find(b=>b.getAttribute('onclick')&&b.getAttribute('onclick').includes("'"+INITIAL_SUBTAB+"'"));
    showSubPage(INITIAL_SUBTAB, subBtn);
  }
};

async function reloadJobsCSV(){
  try {
    const r = await fetch('/api/jobs-csv');
    const d = await r.json();
    if(d.content){
      const parsed = parseCSV(d.content);
      csvHeader = parsed.header; jobs = parsed.rows;
      refreshDynamicFilters();
      renderJobs(1);
      setStatus('✅ Loaded jobs.csv — '+jobs.length+' jobs');
    } else { setStatus('⚠️ ' + (d.error||'jobs.csv not found')); }
  } catch(e) { setStatus('⚠️ Could not load jobs.csv'); }
}

async function reloadBlacklistCSV(){
  try {
    const r = await fetch('/api/blacklist-csv');
    const d = await r.json();
    if(d.content){
      const parsed = parseCSV(d.content);
      blHeader = parsed.header; blacklistJobs = parsed.rows;
      // Merge blacklist into jobs array with Status='Blacklist'
      const existingUrls = new Set(jobs.map(j=>j['URL']));
      const blJobs = blacklistJobs.map((j,i)=>({
        _row: -(i+1),
        'Job Title': j[blHeader[0]]||'',
        'Company':   j[blHeader[1]]||'',
        'Portal':    j[blHeader[2]]||'',
        'URL':       j[blHeader[3]]||'',
        'Status':    'Blacklist',
        'Location':  '',
        'Job ID':    '',
        'Applied Date': '',
        'Description': ''
      })).filter(j=>j['URL']&&!existingUrls.has(j['URL']));
      jobs = jobs.concat(blJobs);
      refreshDynamicFilters();
      renderJobs(jobsPage);
    }
  } catch(e) {}
}

function setStatus(msg){ document.getElementById('status_bar').textContent = msg; }

// ── Page nav ───────────────────────────────────────────────────────────────────
function showPage(name,btn){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nav button').forEach(b=>b.classList.remove('active'));
  document.getElementById('page-'+name).classList.add('active');
  if(btn)btn.classList.add('active');
  if(name==='jobs') renderJobs(1);
  if(name==='scraper'){initRequestTab();loadWorkflows();loadLogs(1);startAutoRefresh();}
  if(name==='career') crLoad();
}
function showSubPage(name,btn){
  document.querySelectorAll('.sub-page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.sub-nav button').forEach(b=>b.classList.remove('active'));
  document.getElementById('sub-'+name).classList.add('active');
  if(btn)btn.classList.add('active');
  if(name==='workflow') loadWorkflows();
  if(name==='log') loadLogs(1);
}

// ── Jobs ───────────────────────────────────────────────────────────────────────
function getStatusClass(s){return{'Scraped':'status-new','Eligible':'status-approved','Ineligible':'status-rejected','Applied':'status-applied','Hold':'status-hold'}[s]||'status-new';}
function displayStatus(s){return s||'Scraped';}

// ── Dynamic Portal / Location values (derived from loaded data, not hardcoded) ───
function getUniqueValues(field){
  const set = new Set();
  jobs.forEach(j=>{ const v=(j[field]||'').trim(); if(v) set.add(v); });
  return [...set].sort((a,b)=>a.localeCompare(b));
}
function refreshDynamicFilters(){
  const portalSel = document.getElementById('filter_portal');
  const locSel = document.getElementById('filter_location');
  const curPortal = portalSel.value, curLoc = locSel.value;
  const portals = getUniqueValues('Portal'), locs = getUniqueValues('Location');
  const hasBlankPortal = jobs.some(j=>!(j['Portal']||'').trim());
  const hasBlankLoc = jobs.some(j=>!(j['Location']||'').trim());
  portalSel.innerHTML = '<option value="">All Portals</option>' + portals.map(p=>'<option'+(p===curPortal?' selected':'')+'>'+escHtml(p)+'</option>').join('')
    + (hasBlankPortal ? '<option'+(curPortal==='Not specified'?' selected':'')+'>Not specified</option>' : '');
  locSel.innerHTML = '<option value="">All Locations</option>' + locs.map(l=>'<option'+(l===curLoc?' selected':'')+'>'+escHtml(l)+'</option>').join('')
    + (hasBlankLoc ? '<option'+(curLoc==='Not specified'?' selected':'')+'>Not specified</option>' : '');
}

// ── Auto-colored portal badges (known portals keep fixed colors; new ones get a
//    consistent generated color the moment they appear, no CSS edits needed) ───
const KNOWN_PORTAL_COLORS = {
  portal_b:   {bg:'#fff3e0', fg:'#e65100'},
  portal_a: {bg:'#e3f2fd', fg:'#1565c0'},
  portal_c:   {bg:'#e8f0fe', fg:'#2557a7'}
};
function portalColorStyle(portal){
  const key = (portal||'').toLowerCase();
  if(KNOWN_PORTAL_COLORS[key]){
    const c = KNOWN_PORTAL_COLORS[key];
    return 'background:'+c.bg+';color:'+c.fg+';';
  }
  let hash = 0;
  for(let i=0;i<key.length;i++){ hash = key.charCodeAt(i) + ((hash<<5)-hash); }
  const hue = Math.abs(hash) % 360;
  return 'background:hsl('+hue+',70%,92%);color:hsl('+hue+',55%,32%);';
}
// Same hue family as the badges above, but a solid/saturated tone instead of
// ── Filter breakdown row (live, filter-driven) ───────────────────────────────────
// Blacklist rows are ordinary jobs with Status='Blacklist' so they already fall
// under Total / the Status breakdown — no separate tab or card needed.
// _segFocus is {dim, label} so a click narrows one specific dimension's
// segment without colliding with same-named labels in a different dimension.
let _segFocus = null;

function renderSegBar(status, portal, ie, location){
  const ALL_STATUSES  = ['Scraped','Eligible','Applied','Ineligible','Hold','Blacklist'];
  const ALL_PORTALS   = getUniqueValues('Portal');
  const ALL_IE        = ['Internal','External','Other'];
  const ALL_LOCATIONS = getUniqueValues('Location');

  // Jobs matching only the currently-specific (non-"All") filters
  const base = jobs.filter(j=>{
    if(status && (j['Status']||'Scraped')!==status) return false;
    if(portal){ if(portal==='Not specified'){ if((j['Portal']||'').trim()) return false; } else if(j['Portal']!==portal) return false; }
    if(ie){
      const jie=j['Internal/External']||'';
      if(ie==='Other'){ if(jie==='Internal'||jie==='External') return false; }
      else if(jie!==ie) return false;
    }
    if(location){ if(location==='Not specified'){ if((j['Location']||'').trim()) return false; } else if(!(j['Location']||'').includes(location)) return false; }
    return true;
  });
  // Single pass over `base` to build frequency tallies, instead of the old
  // approach of re-filtering the whole `base` array once per category (Status,
  // every Portal, every Location...). At 17k+ jobs with dozens of distinct
  // Portals/Locations, that was O(jobs × categories) — this is O(jobs) once,
  // plus cheap lookups after.
  const statusCounts = {}, portalCounts = {}, ieCounts = {Internal:0, External:0, Other:0};
  const rawLocationCounts = {};   // exact raw Location string → count
  let blankPortalCount = 0, blankLocationCount = 0;
  base.forEach(j=>{
    const st = j['Status']||'Scraped';
    statusCounts[st] = (statusCounts[st]||0)+1;

    const po = j['Portal']||'';
    if(!po.trim()) blankPortalCount++; else portalCounts[po] = (portalCounts[po]||0)+1;

    const jie = j['Internal/External']||'';
    ieCounts[jie==='Internal'||jie==='External' ? jie : 'Other']++;

    const loc = (j['Location']||'').trim();
    if(!loc) blankLocationCount++; else rawLocationCounts[loc] = (rawLocationCounts[loc]||0)+1;
  });
  // Location buckets use substring matching (e.g. "Chennai" matches "Chennai,
  // Tamil Nadu" too), so a bucket's count = sum of raw-location tallies that
  // contain it — done once per unique bucket against the small set of unique
  // raw strings actually present, not against every job.
  function locationBucketCount(bucketLabel){
    let total=0;
    for(const raw in rawLocationCounts){ if(raw.includes(bucketLabel)) total += rawLocationCounts[raw]; }
    return total;
  }

  const allAll = !status && !portal && !ie && !location;
  const prefix = [status, portal, ie, location].filter(Boolean).join(' ') || 'All Jobs';

  // Same grouping as the card algorithm: default view breaks down by Status
  // only; once any filter is set, every OTHER filter still on "All" gets its
  // own full breakdown group, shown as its own column — same fixed order
  // (Status, Portal, IE, Location), same fields, same counts.
  const groups = [];
  if(allAll){
    groups.push({dim:'Status', segments: ALL_STATUSES.map(s=>({label:s, value:statusCounts[s]||0}))});
  } else {
    if(!status)  groups.push({dim:'Status',   segments: ALL_STATUSES.map(s=>({label:s, value:statusCounts[s]||0}))});
    if(!portal){
      const portalSegs = ALL_PORTALS.map(p=>({label:p, value:portalCounts[p]||0}));
      portalSegs.push({label:'Not specified', value:blankPortalCount});
      groups.push({dim:'Portal', segments: portalSegs});
    }
    if(!ie)      groups.push({dim:'Int/Ext',  segments: ALL_IE.map(v=>({label:v, value:ieCounts[v]||0}))});
    if(!location){
      const locSegs = ALL_LOCATIONS.map(loc=>({label:loc, value:locationBucketCount(loc)}));
      locSegs.push({label:'Not specified', value:blankLocationCount});
      groups.push({dim:'Location', segments: locSegs});
    }
  }
  groups.forEach(g=>{ g.segments = g.segments.filter(s=>s.value>0); });

  const wrap = document.getElementById('segbar_groups');

  const titleCol = '<div class="segbar-group segbar-firstcol">'
    +'<div class="segbar-title">'+escHtml(prefix)+'</div>'
    +'<div class="segbar-total">'+base.length+' job'+(base.length!==1?'s':'')+'</div>'
    +'</div>';

  const groupCols = groups.map(g=>{
    const legend = g.segments.map(s=>{
      const dimmed = (_segFocus && (_segFocus.dim!==g.dim || _segFocus.label!==s.label)) ? ' dimmed' : '';
      return '<span class="seg-legend-item'+dimmed+'" onclick="toggleSegFocus(&#39;'+escHtml(g.dim)+'&#39;,&#39;'+escHtml(s.label).replace(/'/g,'&#39;')+'&#39;)">'
        +escHtml(s.label)+'<span class="seg-count">'+s.value+'</span></span>';
    }).join('');
    return '<div class="segbar-group">'
      +'<div class="segbar-dim-label">'+escHtml(g.dim)+'</div>'
      +'<div class="seg-legend">'+legend+'</div>'
      +'</div>';
  }).join('');

  wrap.innerHTML = titleCol + groupCols;
}
function toggleSegFocus(dim,label){
  _segFocus = (_segFocus && _segFocus.dim===dim && _segFocus.label===label) ? null : {dim,label};
  renderJobs(jobsPage);
}

let selectedJobRow = null;

function renderJobs(page){
  jobsPage = page || jobsPage;
  const status   = document.getElementById('filter_status').value;
  const portal   = document.getElementById('filter_portal').value;
  const ie       = document.getElementById('filter_ie').value;
  const location = document.getElementById('filter_location').value;
  const search   = document.getElementById('search').value.toLowerCase();

  renderSegBar(status, portal, ie, location);

  // Filter
  _filteredJobs = jobs.filter(j=>{
    if(status&&j['Status']!==status)return false;
    if(portal){ if(portal==='Not specified'){ if((j['Portal']||'').trim())return false; } else if(j['Portal']!==portal)return false; }
    if(ie){const jie=j['Internal/External']||'';if(ie==='Other'){if(jie==='Internal'||jie==='External')return false;}else if(jie!==ie)return false;}
    if(location){ if(location==='Not specified'){ if((j['Location']||'').trim())return false; } else if(!(j['Location']||'').includes(location))return false; }
    if(search&&!(j['Job Title']||'').toLowerCase().includes(search))return false;
    if(_segFocus){
      // Legend click narrows to one segment within its own dimension —
      // dim tells us which field to check, independent of the filter state.
      const {dim, label} = _segFocus;
      if(dim==='Status' && (j['Status']||'Scraped')!==label) return false;
      if(dim==='Portal'){
        const match = label==='Not specified' ? !(j['Portal']||'').trim() : j['Portal']===label;
        if(!match) return false;
      }
      if(dim==='Int/Ext'){
        const jie=j['Internal/External']||'';
        const match = label==='Other' ? (jie!=='Internal'&&jie!=='External') : jie===label;
        if(!match) return false;
      }
      if(dim==='Location'){
        const jloc=(j['Location']||'').trim();
        const match = label==='Not specified' ? !jloc : jloc.includes(label);
        if(!match) return false;
      }
    }
    return true;
  });

  // Sort
  const sb=document.getElementById('sort_by').value;
  if(sb==='title_asc')_filteredJobs.sort((a,b)=>(a['Job Title']||'').localeCompare(b['Job Title']||''));
  else if(sb==='title_desc')_filteredJobs.sort((a,b)=>(b['Job Title']||'').localeCompare(a['Job Title']||''));
  else if(sb==='company_asc')_filteredJobs.sort((a,b)=>(a['Company']||'').localeCompare(b['Company']||''));
  else if(sb==='date_desc')_filteredJobs.sort((a,b)=>(b['Last Checked']||'').localeCompare(a['Last Checked']||''));
  else if(sb==='date_asc')_filteredJobs.sort((a,b)=>(a['Last Checked']||'').localeCompare(b['Last Checked']||''));
  else if(sb==='status'){const o={'Eligible':0,'Scraped':1,'Hold':2,'Applied':3,'Ineligible':4};_filteredJobs.sort((a,b)=>(o[a['Status']]??5)-(o[b['Status']]??5));}

  // Paginate
  const totalPages = Math.ceil(_filteredJobs.length / JOBS_PER_PAGE);
  if(jobsPage > 1 && jobsPage > totalPages) jobsPage = Math.max(1, totalPages);
  const start = (jobsPage-1)*JOBS_PER_PAGE;
  const paged = _filteredJobs.slice(start, start+JOBS_PER_PAGE);
  const pageEnd = Math.min(start + JOBS_PER_PAGE, _filteredJobs.length);
  document.getElementById('jobs_count_label').textContent = pageEnd + ' / ' + _filteredJobs.length + ' jobs shown';
  document.getElementById('jobs_page_label').textContent = '(20 per page)';

  const c = document.getElementById('jobs_container');
  if(!paged.length){
    c.innerHTML='<div class="no-jobs">No jobs found.</div>';
    document.getElementById('jobs_pagination').innerHTML='';
    selectedJobRow = null;
    renderJobDetail(null);
    return;
  }

  // Keep the current selection if it's still on this page; otherwise default
  // to the first row so the detail panel is never empty when jobs exist.
  if(selectedJobRow===null || !paged.some(j=>j._row===selectedJobRow)){
    selectedJobRow = paged[0]._row;
  }

  c.innerHTML = paged.map(job => {
    const isBlacklist = (job['Status']||'').toLowerCase()==='blacklist';
    const selected = job._row===selectedJobRow ? ' selected' : '';
    const ieVal = job['Internal/External'];
    const ieBadge = (ieVal==='Internal'||ieVal==='External')
      ? '<span class="badge badge-'+ieVal.toLowerCase()+'">'+ieVal+'</span>' : '';
    const badges = '<div class="job-row-badges">'
      +'<span class="badge" style="'+portalColorStyle(job['Portal'])+'">'+escHtml(job['Portal'])+'</span>'
      +'<span class="badge '+(isBlacklist?'status-rejected':getStatusClass(job['Status']))+'">'+escHtml(isBlacklist?'Blacklist':job['Status'])+'</span>'
      +ieBadge
      +'</div>';
    return '<div class="job-row'+selected+'" onclick="selectJob('+job._row+')">'
      +'<div class="job-row-title">'+escHtml(job['Job Title'])+'</div>'
      +'<div class="job-row-sub">'+escHtml(job['Company'])+' &middot; '+escHtml(job['Location'])+'</div>'
      +badges
      +'</div>';
  }).join('');

  renderPagination('jobs_pagination', jobsPage, totalPages, p=>renderJobs(p));

  renderJobDetail(jobs.find(j=>j._row===selectedJobRow));
}

function selectJob(row){
  selectedJobRow = row;
  const job = jobs.find(j=>j._row===row);
  renderJobDetail(job);
  document.querySelectorAll('.job-row').forEach(el=>el.classList.remove('selected'));
  const idx = _filteredJobs.findIndex(j=>j._row===row);
  const rows = document.querySelectorAll('.job-row');
  const start = (jobsPage-1)*JOBS_PER_PAGE;
  if(idx>=start && idx<start+JOBS_PER_PAGE) rows[idx-start]?.classList.add('selected');
}

function renderJobDetail(job){
  const panel = document.getElementById('job_detail_panel');
  if(!job){
    panel.innerHTML = '<div class="job-detail-empty">Select a job from the list to see details.</div>';
    return;
  }
  const isBlacklist = (job['Status']||'').toLowerCase()==='blacklist';
  const metaLine = isBlacklist
    ? '&#127962; '+escHtml(job['Company'])+' &nbsp;|&nbsp; &#128205; '+escHtml(job['Location'])
    : '&#127962; '+escHtml(job['Company'])+' &nbsp;|&nbsp; &#128205; '+escHtml(job['Location'])+' &nbsp;|&nbsp; &#128274; '+escHtml(job['Job ID'])+'<br>&#128197; Applied: '+escHtml(job['Applied Date']||'—');
  const ieVal = job['Internal/External'];
  const ieBadge = (ieVal==='Internal'||ieVal==='External')
    ? '<span class="badge badge-'+ieVal.toLowerCase()+'">'+ieVal+'</span>' : '';
  const badges = '<div class="job-detail-badges">'
    +'<span class="badge" style="'+portalColorStyle(job['Portal'])+'">'+escHtml(job['Portal'])+'</span>'
    +'<span class="badge '+(isBlacklist?'status-rejected':getStatusClass(job['Status']))+'">'+escHtml(isBlacklist?'Blacklist':job['Status'])+'</span>'
    +ieBadge
    +'</div>';
  let actions;
  if(isBlacklist){
    actions = '<div class="actions">'
      +'<a class="btn-link" href="'+escHtml(job['URL'])+'" target="_blank">&#128279; Link</a>'
      +'<button class="btn" style="background:#27ae60;color:white;" onclick="reformJob('+job._row+')">&#9851; Reform</button>'
      +'</div>';
  } else {
    const isApproved = job['Status']==='Eligible';
    const isApplied  = job['Status']==='Applied';
    const appliedBtn = isApproved
      ? '<button class="btn btn-applied" onclick="markApplied('+job._row+')">&#10003; Applied</button>' : '';
    actions = '<div class="actions">'
      +'<a class="btn-link" href="'+escHtml(job['URL'])+'" target="_blank">&#128279; View</a>'
      +'<button class="btn btn-approve" onclick="updateStatus('+job._row+',&#39;Eligible&#39;)"'+(isApproved||isApplied?' disabled style="opacity:0.4"':'')+'>&#10003; Eligible</button>'
      +'<button class="btn btn-hold-job" onclick="updateStatus('+job._row+',&#39;Hold&#39;)"'+(job['Status']==='Hold'||isApplied?' disabled style="opacity:0.4"':'')+'>&#9208; Hold</button>'
      +'<button class="btn btn-reject" onclick="updateStatus('+job._row+',&#39;Ineligible&#39;)"'+(job['Status']==='Ineligible'||isApplied?' disabled style="opacity:0.4"':'')+'>&#10007; Ineligible</button>'
      +appliedBtn
      +'</div>';
  }
  panel.innerHTML = '<div class="job-detail-title">'+escHtml(job['Job Title'])+'</div>'
    +'<div class="job-detail-meta">'+metaLine+'</div>'
    +badges
    +actions
    +'<div class="job-detail-desc-label">Description</div>'
    +'<div class="job-detail-desc">'+escHtml(job['Description']||'No description.')+'</div>';
}

let _undoJob = null;
let _undoTimer = null;

// Keeps the detail panel's sticky offset in sync with the undo bar's actual
// rendered height (it can wrap to two lines on narrow screens via flex-wrap,
// so a hardcoded pixel guess would drift out of sync).
function syncUndoOffset(){
  const bar = document.getElementById('undo_bar');
  const h = (bar && bar.style.display!=='none') ? bar.offsetHeight : 0;
  document.documentElement.style.setProperty('--undo-offset', h+'px');
}
window.addEventListener('resize', syncUndoOffset);
function hideUndoBar(){
  document.getElementById('undo_bar').style.display='none';
  syncUndoOffset();
}

function showUndo(job, prevStatus){
  _undoJob = {job, prevStatus};
  const bar = document.getElementById('undo_bar');
  bar.style.display='flex';
  bar.querySelector('#undo_msg').textContent = 'Status changed: "' + (job['Job Title']||'').slice(0,40) + '" @ ' + (job['Company']||'') + ' → ' + job['Status'];
  syncUndoOffset();
  clearTimeout(_undoTimer);
  _undoTimer = setTimeout(()=>{hideUndoBar();_undoJob=null;}, 10000);
}

function undoStatus(){
  if(!_undoJob) return;
  const {job, prevStatus} = _undoJob;
  job['Status'] = prevStatus;
  clearTimeout(_undoTimer);
  hideUndoBar();
  _undoJob = null;
  fetch('/api/update-job-status',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:job['URL'],status:prevStatus})});
  renderJobs(jobsPage);
}

async function updateStatus(row, status){
  const job = jobs.find(j=>j._row===row); if(!job) return;
  const prevStatus = job['Status'];
  job['Status'] = status;
  showUndo(job, prevStatus);
  renderJobs(jobsPage);   // update the screen immediately — don't wait on the network
  const panel = document.getElementById('job_detail_panel');
  panel.classList.remove('flash-ok'); void panel.offsetWidth; panel.classList.add('flash-ok');
  try {
    const r = await fetch('/api/update-job-status',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:job['URL'],status:status})});
    const d = await r.json();
    if(!d.ok){
      job['Status'] = prevStatus;   // roll back — the save didn't actually take
      hideUndoBar();
      renderJobs(jobsPage);
      alert('Could not save status change: '+(d.error||'unknown error'));
    }
  } catch(e) {
    job['Status'] = prevStatus;
    hideUndoBar();
    renderJobs(jobsPage);
    alert('Browser is busy, please try again in a moment.');
  }
}

async function markApplied(row){
  const job = jobs.find(j=>j._row===row); if(!job) return;
  await updateStatus(row, 'Applied');
  if(job['Internal/External'] === 'External'){
    await crOpenAppModalPrefill(job['Company']);
  }
}

async function reformJob(row){
  const job = jobs.find(j=>j._row===row); if(!job) return;
  const prevStatus = job['Status'];
  try {
    const r = await fetch('/api/reform-job',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({url:job['URL'],title:job['Job Title'],company:job['Company'],portal:job['Portal']})});
    const d = await r.json();
    if(d.ok){ job['Status']='Scraped'; showUndo(job, prevStatus); renderJobs(jobsPage); }
    else alert('Reform failed: '+d.error);
  } catch(e){ alert('Browser is busy, please try again in a moment.'); }
}

// renderBlacklist removed — blacklist cards merged into jobs tab
// toggleDesc removed — description is always visible in the detail panel now

// ── Profile ────────────────────────────────────────────────────────────────────
const PF=['firstName','lastName','fullName','legalName','middleName','preferredName','email','phone',
  'phoneType','phoneCountry','birthday','location_p','address','city','state','country','postalCode',
  'school','degree','highestDegree','gradYear','gpa','fieldOfStudy','currentlyEmployed','totalExperience',
  'relevantExperience','noticePeriod','currentCTC','expectedCTCText','expectedCTCNumber','availableFrom',
  'nightShift','gender','ethnicity','hispanic','veteran','disability','lgbt','workAuthorization','workAuthUS',
  'visaType','sponsorship','relocate','relocatePreference','workLocation','pan','aadhaar','uan','esic',
  'portal_a_p','github','portfolio','website','twitter','skills','language','nativeLanguage','empType','summary'];
function fillProfileForm(data){
  PF.forEach(id=>{const el=document.getElementById(id);if(el&&data[id]!==undefined)el.value=data[id];});
  const c=document.getElementById('jobs_container_profile');c.innerHTML='';
  if(data.jobs&&data.jobs.length)data.jobs.forEach((j,i)=>renderJobEntry(j,i));else renderJobEntry({},0);
}
function collectProfile(){
  const p={};PF.forEach(id=>{const el=document.getElementById(id);if(el)p[id]=el.value;});
  const c=document.getElementById('jobs_container_profile');const jj=[];
  for(let i=0;i<c.children.length;i++){
    jj.push({title:document.getElementById('job_title_'+i)?.value||'',
      company:document.getElementById('job_company_'+i)?.value||'',
      startDate:document.getElementById('job_startDate_'+i)?.value||'',
      endDate:document.getElementById('job_endDate_'+i)?.value||'',
      currentlyWorking:document.getElementById('job_cw_'+i)?.value||'No',
      description:document.getElementById('job_desc_'+i)?.value||''});
  }
  p.jobs=jj;return p;
}
function renderJobEntry(job,idx){
  const c=document.getElementById('jobs_container_profile');const d=document.createElement('div');
  d.id='job_'+idx;d.style.cssText='background:white;padding:15px;border-radius:8px;margin-bottom:10px;box-shadow:0 2px 5px rgba(0,0,0,0.08);';
  d.innerHTML=`<div style="display:flex;justify-content:space-between;margin-bottom:10px;"><b>Job #${idx+1}</b>
    <button onclick="removeJob(${idx})" style="background:#e74c3c;color:white;border:none;padding:3px 10px;border-radius:5px;cursor:pointer;font-size:12px;">Remove</button></div>
    <div class="form-grid">
      <div class="form-group"><label>Job Title</label><input id="job_title_${idx}" type="text" value="${escHtml(job.title||'')}"></div>
      <div class="form-group"><label>Company</label><input id="job_company_${idx}" type="text" value="${escHtml(job.company||'')}"></div>
      <div class="form-group"><label>Start Date</label><input id="job_startDate_${idx}" type="month" value="${job.startDate||''}"></div>
      <div class="form-group"><label>End Date</label><input id="job_endDate_${idx}" type="month" value="${job.endDate||''}"></div>
      <div class="form-group"><label>Currently Working</label>
        <select id="job_cw_${idx}"><option value="No" ${job.currentlyWorking!=='Yes'?'selected':''}>No</option><option value="Yes" ${job.currentlyWorking==='Yes'?'selected':''}>Yes</option></select></div>
      <div class="form-group full-width"><label>Description</label><textarea id="job_desc_${idx}">${escHtml(job.description||'')}</textarea></div>
    </div>`;
  c.appendChild(d);
}
function addJob(){const c=document.getElementById('jobs_container_profile');renderJobEntry({},c.children.length);}
function removeJob(idx){const el=document.getElementById('job_'+idx);if(el)el.remove();}
async function saveProfile(){
  try {
    const r=await fetch('/api/save-profile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(collectProfile())});
    const d=await r.json();
    const msg=document.getElementById('saveMsg');
    msg.textContent=d.ok?'&#10003; Saved!':'&#10007; '+d.error;
    setTimeout(()=>msg.textContent='',3000);
  } catch(e) { alert('Browser is busy, please try again in a moment.'); }
}
'''
