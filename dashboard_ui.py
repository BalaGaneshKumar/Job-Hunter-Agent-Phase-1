"""
dashboard_ui.py — Shared CSS, HTML page wrapper, and escape helper
Imported by dashboard_jobs.py, dashboard_scraper.py, dashboard_detail.py
"""

# ---------------------------------------------------------------------------
# Shared CSS
# ---------------------------------------------------------------------------
CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Arial, sans-serif; background: #f0f2f5; }
.header { background: #2c3e50; color: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
.header h1 { font-size: 20px; }
.nav { display: flex; gap: 5px; flex-wrap: wrap; }
.nav button { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: bold; background: #3d5166; color: white; }
.nav button.active { background: #3498db; }
.status-bar { background: #1a252f; padding: 7px 20px; font-size: 12px; color: #aaa; }
.page { display: none; padding: 20px; }
.page.active { display: block; }
.stats { display: flex; gap: 12px; margin-bottom: 15px; flex-wrap: wrap; }
.stat-card { background: white; padding: 12px 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.08); min-width: 80px; }
.stat-card h2 { font-size: 28px; color: #2c3e50; }
.stat-card p { font-size: 12px; color: #666; margin-top: 3px; }
.filters { display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap; align-items: center; }
.filters select, .filters input { padding: 8px 12px; border-radius: 6px; border: 1px solid #ddd; font-size: 14px; }
.job-count-label { font-size: 13px; color: #666; font-weight: bold; margin-left: 5px; }
/* #jobs_container grid rule removed — superseded by .jobs-list (single-column list) */
.job-card { background: white; border-radius: 10px; padding: 12px 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.08); }
.job-card h3 { font-size: 14px; color: #2c3e50; margin-bottom: 5px; }
.job-desc { font-size: 12px; color: #555; margin-top: 8px; background: #f9f9f9; padding: 10px; border-radius: 6px; border-left: 3px solid #3498db; white-space: pre-wrap; line-height: 1.8; display: none; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 20px; font-size: 11px; font-weight: bold; margin-right: 4px; }
.badge-portal_b { background: #fff3e0; color: #e65100; }
.badge-portal_a { background: #e3f2fd; color: #1565c0; }
.badge-portal_c { background: #e8f0fe; color: #2557a7; }
.badge-internal { background: #e0f7ea; color: #1b7a43; }
.badge-external { background: #fdeaea; color: #a13a3a; }
.status-new { background: #e3f2fd; color: #1565c0; }
.status-blacklist { background: #ffebee; color: #c62828; }
.undo-bar { display:none; position:sticky; top:0; z-index:999; background:#2c3e50; color:white; padding:10px 20px; align-items:center; gap:12px; font-size:13px; flex-wrap:wrap; }
.undo-bar button { padding:5px 14px; background:#e74c3c; color:white; border:none; border-radius:5px; cursor:pointer; font-size:12px; font-weight:bold; }
.status-approved { background: #e8f5e9; color: #2e7d32; }
.status-rejected { background: #ffebee; color: #c62828; }
.status-applied { background: #f3e5f5; color: #6a1b9a; }
.status-hold { background: #fff8e1; color: #f57f17; }
.actions { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; }
.btn { padding: 6px 12px; border: none; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: bold; transition: transform 0.08s ease, filter 0.08s ease; }
.btn:active { transform: scale(0.93); filter: brightness(0.85); }
.btn:disabled:active { transform: none; filter: none; }
@keyframes flashOk { 0% { box-shadow: 0 0 0 3px rgba(46,204,113,0.6); } 100% { box-shadow: 0 2px 5px rgba(0,0,0,0.08); } }
.flash-ok { animation: flashOk 0.5s ease; }
.btn-approve { background: #4caf50; color: white; }
.btn-reject { background: #f44336; color: white; }
.btn-hold-job { background: #ff9800; color: white; }
.btn-applied { background: #9b59b6; color: white; }
.btn-link { background: #2196f3; color: white; text-decoration: none; display: inline-block; text-align: center; padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: bold; }
.btn-desc { background: #ecf0f1; color: #555; }
.no-jobs { text-align: center; padding: 40px; color: #999; font-size: 16px; }
.pagination { display: flex; gap: 6px; justify-content: center; margin-top: 14px; align-items: center; flex-wrap: wrap; }
.pagination button { padding: 6px 12px; border: 1px solid #ddd; border-radius: 5px; cursor: pointer; background: white; font-size: 13px; }
.pagination button.active-page { background: #3498db; color: white; border-color: #3498db; }
.pagination button:disabled { opacity: 0.4; cursor: not-allowed; }
.section-title { font-size: 16px; font-weight: bold; color: #2c3e50; margin: 20px 0 10px; padding-bottom: 5px; border-bottom: 2px solid #3498db; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 15px; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-group label { font-size: 12px; color: #666; font-weight: bold; }
.form-group input, .form-group select, .form-group textarea { padding: 8px 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }
.form-group textarea { resize: vertical; min-height: 80px; }
.btn-save { background: #2ecc71; color: white; padding: 10px 25px; border: none; border-radius: 8px; font-size: 14px; font-weight: bold; cursor: pointer; margin-top: 10px; }
.save-msg { color: #2ecc71; font-weight: bold; margin-left: 10px; font-size: 13px; }
.full-width { grid-column: 1 / -1; }
.sub-nav { display: flex; gap: 4px; margin-bottom: 20px; border-bottom: 2px solid #ddd; }
.sub-nav button { padding: 8px 18px; border: none; border-radius: 6px 6px 0 0; cursor: pointer; font-size: 13px; font-weight: bold; background: #ecf0f1; color: #555; border-bottom: 2px solid transparent; margin-bottom: -2px; }
.sub-nav button.active { background: white; color: #2c3e50; border-bottom: 2px solid #3498db; }
.sub-page { display: none; }
.sub-page.active { display: block; }
.req-section { background: white; border-radius: 10px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 5px rgba(0,0,0,0.08); }
.req-section h3 { font-size: 15px; color: #2c3e50; margin-bottom: 14px; font-weight: bold; }
.scraper-options { display: flex; gap: 12px; flex-wrap: wrap; }
.scraper-option { display: flex; align-items: center; gap: 8px; padding: 10px 18px; border: 2px solid #ddd; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: bold; color: #555; }
.scraper-option.selected { border-color: #3498db; background: #e8f4fd; color: #2980b9; }
.tag-list { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }
.tag { display: inline-flex; align-items: center; gap: 5px; padding: 5px 12px; background: #e8f4fd; border: 1px solid #3498db; border-radius: 20px; font-size: 13px; color: #2980b9; cursor: pointer; user-select: none; }
.tag.selected { background: #3498db; color: white; }
.tag .remove-btn { background: none; border: none; cursor: pointer; font-size: 13px; color: inherit; padding: 0; line-height: 1; margin-left: 2px; }
.extra-input { display: flex; gap: 8px; margin-top: 8px; }
.extra-input input { flex: 1; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }
.extra-input button { padding: 8px 16px; background: #3498db; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: bold; }
.btn-submit { padding: 12px 32px; background: #2ecc71; color: white; border: none; border-radius: 8px; font-size: 15px; font-weight: bold; cursor: pointer; margin-top: 10px; }
.btn-submit:disabled { background: #bdc3c7; cursor: not-allowed; }
.running-warning { background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 12px 16px; font-size: 13px; color: #856404; margin-bottom: 16px; display: none; }
.wf-table-wrap { background: white; border-radius: 10px; padding: 16px; box-shadow: 0 2px 5px rgba(0,0,0,0.08); overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { background: #2c3e50; color: white; padding: 10px 12px; text-align: left; cursor: pointer; white-space: nowrap; }
th:hover { background: #3d5166; }
td { padding: 9px 12px; border-bottom: 1px solid #f0f0f0; vertical-align: middle; }
tr:hover td { background: #f8f9fa; }
tr.pinned td { background: #fffde7; }
.wf-id-link { color: #2980b9; text-decoration: none; font-weight: bold; font-family: monospace; font-size: 12px; }
.wf-id-link:hover { text-decoration: underline; }
.log-entry { font-family: monospace; font-size: 12px; padding: 5px 8px; border-bottom: 1px solid #f0f0f0; word-break: break-all; }
.log-entry:nth-child(even) { background: #f8f9fa; }
.log-wrap { background: white; border-radius: 10px; padding: 16px; box-shadow: 0 2px 5px rgba(0,0,0,0.08); }
.bl-tag { display: inline-flex; align-items: center; gap: 5px; padding: 4px 10px; background: #ffebee; border: 1px solid #f44336; border-radius: 20px; font-size: 12px; color: #c62828; margin: 3px; }
.bl-tag .remove-btn { background: none; border: none; cursor: pointer; font-size: 12px; color: #c62828; padding: 0; }
.legend-table { width: auto; margin-bottom: 16px; font-size: 13px; border-collapse: collapse; }
.legend-table td { padding: 5px 12px; border-bottom: 1px solid #f0f0f0; }
.legend-table td:first-child { font-size: 18px; text-align: center; }

/* Filter breakdown row (Jobs tab header) — plain text columns, no bar */
.segbar-wrap { background: white; border-radius: 10px; padding: 14px 18px; box-shadow: 0 2px 5px rgba(0,0,0,0.08); margin-bottom: 14px; display: flex; gap: 32px; flex-wrap: wrap; align-items: flex-start; }
.segbar-group { min-width: 160px; }
.segbar-firstcol { min-width: 140px; }
.segbar-title { font-size: 13px; font-weight: bold; color: #2c3e50; margin-bottom: 4px; min-height: 16px; }
.segbar-total { font-size: 12px; color: #666; }
.segbar-dim-label { font-size: 11px; font-weight: bold; color: #999; text-transform: uppercase; letter-spacing: 0.3px; margin-bottom: 6px; }
.seg-legend { display: flex; flex-wrap: wrap; gap: 6px 16px; }
.seg-legend-item { font-size: 13px; color: #333; cursor: pointer; white-space: nowrap; }
.seg-legend-item.dimmed { opacity: 0.4; }
.seg-count { font-weight: bold; color: #2c3e50; margin-left: 4px; }

/* Split view (list + detail) — both columns stretch to equal height, so
   whichever is naturally taller (usually the 20-row list) sets the height
   for the other. */
.jobs-split { display: grid; grid-template-columns: minmax(0,1fr) minmax(0,1.3fr); gap: 14px; align-items: stretch; }
.jobs-list-col { min-width: 0; display: flex; flex-direction: column; }
.jobs-list { flex: 1; display: flex; flex-direction: column; background: white; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.08); overflow: hidden; }
.job-row { display: flex; flex-direction: column; gap: 5px; padding: 10px 18px; border-bottom: 1px solid #f0f0f0; cursor: pointer; }
.job-row:last-child { border-bottom: none; }
.job-row:hover { background: #f8f9fa; }
.job-row.selected { background: #e8f4fd; }
.job-row-title { font-size: 14px; font-weight: bold; color: #2c3e50; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.job-row-sub { font-size: 12px; color: #777; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.job-row-badges { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.job-detail-panel { background: white; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.08); padding: 18px 20px; min-height: 200px; display: flex; flex-direction: column; position: sticky; top: calc(16px + var(--undo-offset, 0px)); max-height: calc(100vh - 32px - var(--undo-offset, 0px)); }
.job-detail-empty { color: #999; text-align: center; padding: 60px 20px; font-size: 14px; margin: auto; }
.job-detail-title { font-size: 17px; font-weight: bold; color: #2c3e50; margin-bottom: 6px; flex-shrink: 0; }
.job-detail-meta { font-size: 13px; color: #666; margin-bottom: 10px; line-height: 1.6; flex-shrink: 0; }
.job-detail-badges { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; margin-bottom: 12px; flex-shrink: 0; }
.job-detail-panel .actions { flex-shrink: 0; margin-bottom: 4px; }
.job-detail-desc-label { font-size: 12px; font-weight: bold; color: #2c3e50; margin: 14px 0 6px; flex-shrink: 0; }
.job-detail-desc { font-size: 13px; color: #444; background: #f9f9f9; padding: 14px 16px; border-radius: 6px; border-left: 3px solid #3498db; white-space: pre-wrap; line-height: 1.8; flex: 1; min-height: 0; overflow-y: auto; }
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def esc(s):
    return str(s or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;').replace("'","&#39;")

def html_page(title, body, extra_head=''):
    return ('<!DOCTYPE html><html><head><meta charset="UTF-8"><title>' + title +
            '</title>' + extra_head + '<style>' + CSS + '</style></head><body>' +
            body + '</body></html>')

def render_pagination_js():
    """Returns the shared JS pagination function."""
    return """
function renderPagination(containerId, cur, total, onPage) {
  const c = document.getElementById(containerId);
  if(total <= 1) { c.innerHTML = ''; return; }
  let h = '<button ' + (cur===1?'disabled':'') + ' onclick="('+onPage.toString()+')('+(cur-1)+')">&#8249;</button>';
  const s = Math.max(1,cur-2), e = Math.min(total,cur+2);
  if(s>1) h += '<button onclick="('+onPage.toString()+')(1)">1</button>'+(s>2?'<span>&#8230;</span>':'');
  for(let p=s;p<=e;p++) h += '<button class="'+(p===cur?'active-page':'')+'" onclick="('+onPage.toString()+')('+p+')">'+p+'</button>';
  if(e<total) h += (e<total-1?'<span>&#8230;</span>':'')+'<button onclick="('+onPage.toString()+')('+total+')">'+total+'</button>';
  h += '<button '+(cur===total?'disabled':'')+' onclick="('+onPage.toString()+')('+(cur+1)+')">&#8250;</button>';
  c.innerHTML = h;
}
"""
