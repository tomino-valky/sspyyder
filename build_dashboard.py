"""
Pavuk - Dashboard Builder (Glass Lab Design)

Reads JSON data from data/ and generates a self-contained dashboard.html.

USAGE:
    python build_dashboard.py
    start index.html
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path("data")
OUTPUT_FILE = Path("index.html")

SOURCES = {
    "clinicaltrials": ["clinicaltrials.json", "clinicaltrials_test.json"],
    "pubmed": ["pubmed.json", "pubmed_test.json"],
    "biorxiv": ["biorxiv.json", "biorxiv_test.json"],
    "rss": ["rss.json", "rss_test.json"],
    "equine": ["equine.json"],
}


def find_data_files():
    found = {}
    for source, candidates in SOURCES.items():
        for candidate in candidates:
            path = DATA_DIR / candidate
            if path.exists():
                found[source] = path
                break
    for source in SOURCES:
        if source not in found:
            matches = sorted(DATA_DIR.glob(f"{source}_*.json"), reverse=True)
            if matches:
                found[source] = matches[0]
    return found


def load_data(file_map):
    data = {}
    for source, path in file_map.items():
        try:
            with open(path, encoding="utf-8") as f:
                items = json.load(f)
                data[source] = items
                print(f"  + {source}: {len(items)} items from {path.name}")
        except Exception as e:
            print(f"  x {source}: Error reading {path}: {e}")
            data[source] = []
    for source in SOURCES:
        if source not in data:
            data[source] = []
            print(f"  - {source}: no data file found")
    return data


def build_html(data):
    total = sum(len(v) for v in data.values())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    data_json = json.dumps(data, ensure_ascii=False)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pavuk - Neurobiology Research Monitor</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}

:root{{
  --bg-deep:#060a14;
  --bg-surface:rgba(12,18,32,0.85);
  --bg-card:rgba(15,25,50,0.55);
  --bg-card-hover:rgba(20,35,70,0.65);
  --bg-glass:rgba(20,30,60,0.4);
  --border:rgba(100,160,255,0.1);
  --border-glow:rgba(100,160,255,0.25);
  --glow:rgba(80,140,255,0.06);
  --glow-strong:rgba(80,140,255,0.12);
  --text:#e2e8f0;
  --text-secondary:#94a3b8;
  --text-dim:#4b5c78;
  --primary:#5b9aff;
  --primary-soft:rgba(91,154,255,0.15);
  --cyan:#22d3ee;
  --cyan-soft:rgba(34,211,238,0.12);
  --green:#34d399;
  --green-soft:rgba(52,211,153,0.12);
  --amber:#fbbf24;
  --amber-soft:rgba(251,191,36,0.12);
  --red:#f87171;
  --purple:#a78bfa;
  --purple-soft:rgba(167,139,250,0.12);
  --sidebar-w:230px;
}}

html{{height:100%}}
body{{
  font-family:'Inter',system-ui,-apple-system,sans-serif;
  background:var(--bg-deep);
  color:var(--text);
  min-height:100vh;
  display:flex;
  overflow-x:hidden;
  line-height:1.5;
}}

/* ---- Animated background ---- */
body::before{{
  content:'';position:fixed;inset:0;z-index:0;pointer-events:none;
  background:
    radial-gradient(ellipse 800px 600px at 15% 20%, rgba(50,100,200,0.06) 0%, transparent 70%),
    radial-gradient(ellipse 600px 500px at 85% 75%, rgba(30,80,180,0.04) 0%, transparent 70%),
    radial-gradient(ellipse 400px 400px at 50% 50%, rgba(60,120,220,0.03) 0%, transparent 70%);
}}

/* ---- Sidebar ---- */
.sidebar{{
  position:fixed;left:0;top:0;bottom:0;
  width:var(--sidebar-w);
  background:var(--bg-surface);
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  border-right:1px solid var(--border);
  display:flex;flex-direction:column;
  z-index:100;
  padding:0;
}}
.sidebar-brand{{
  padding:28px 24px 20px;
  border-bottom:1px solid var(--border);
}}
.sidebar-logo{{
  display:flex;align-items:center;gap:12px;
}}
.sidebar-logo svg{{width:36px;height:36px;opacity:0.9}}
.sidebar-logo h1{{
  font-size:20px;font-weight:700;letter-spacing:1.5px;
  background:linear-gradient(135deg,var(--primary),var(--cyan));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;
}}
.sidebar-subtitle{{font-size:10px;color:var(--text-dim);letter-spacing:1px;text-transform:uppercase;margin-top:6px}}

.sidebar-nav{{flex:1;padding:16px 12px;display:flex;flex-direction:column;gap:2px}}
.nav-item{{
  display:flex;align-items:center;gap:12px;
  padding:11px 14px;border-radius:10px;
  font-size:13px;font-weight:500;color:var(--text-secondary);
  cursor:pointer;transition:all 0.2s;border:1px solid transparent;
  position:relative;
}}
.nav-item:hover{{color:var(--text);background:var(--glow)}}
.nav-item.active{{
  color:var(--text);
  background:var(--primary-soft);
  border-color:rgba(91,154,255,0.15);
}}
.nav-item.active::before{{
  content:'';position:absolute;left:-12px;top:50%;transform:translateY(-50%);
  width:3px;height:20px;border-radius:0 3px 3px 0;
  background:var(--primary);
}}
.nav-item .nav-icon{{width:18px;text-align:center;font-size:15px}}
.nav-item .nav-count{{
  margin-left:auto;font-size:11px;font-weight:600;
  background:var(--bg-card);padding:2px 8px;border-radius:6px;
  color:var(--text-dim);
}}
.nav-item.active .nav-count{{color:var(--primary);background:var(--primary-soft)}}

.sidebar-footer{{
  padding:16px 20px;border-top:1px solid var(--border);
  font-size:10px;color:var(--text-dim);line-height:1.6;
}}

/* ---- Main ---- */
.main{{
  margin-left:var(--sidebar-w);flex:1;min-height:100vh;
  position:relative;z-index:1;
}}
.main-inner{{max-width:880px;margin:0 auto;padding:32px 36px}}

/* ---- Header ---- */
.header{{margin-bottom:28px}}
.header-row{{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:20px}}
.header h2{{font-size:22px;font-weight:700}}
.header .timestamp{{font-size:11px;color:var(--text-dim)}}

.search-wrap{{position:relative}}
.search-wrap svg{{position:absolute;left:14px;top:50%;transform:translateY(-50%);width:16px;height:16px;color:var(--text-dim)}}
.search-input{{
  width:100%;padding:11px 16px 11px 40px;
  background:var(--bg-card);
  backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);
  border:1px solid var(--border);border-radius:12px;
  color:var(--text);font-size:13px;font-family:inherit;
  outline:none;transition:border-color 0.2s,box-shadow 0.2s;
}}
.search-input::placeholder{{color:var(--text-dim)}}
.search-input:focus{{border-color:var(--border-glow);box-shadow:0 0 20px var(--glow)}}

/* ---- Stats ---- */
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:28px}}
.stat{{
  background:var(--bg-card);
  backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);
  border:1px solid var(--border);border-radius:14px;
  padding:18px 16px;
  cursor:pointer;transition:all 0.25s;
  position:relative;overflow:hidden;
}}
.stat::before{{
  content:'';position:absolute;inset:0;border-radius:14px;
  background:radial-gradient(ellipse at 50% 0%, var(--glow) 0%, transparent 70%);
  opacity:0;transition:opacity 0.3s;
}}
.stat:hover::before,.stat.active::before{{opacity:1}}
.stat:hover,.stat.active{{border-color:var(--border-glow)}}
.stat-icon{{font-size:20px;margin-bottom:8px;position:relative;z-index:1}}
.stat-value{{font-size:28px;font-weight:700;position:relative;z-index:1;letter-spacing:-0.5px}}
.stat-label{{font-size:10px;color:var(--text-dim);text-transform:uppercase;letter-spacing:0.8px;margin-top:2px;position:relative;z-index:1}}

/* ---- Cards ---- */
.card-list{{display:flex;flex-direction:column;gap:10px}}
.card{{
  background:var(--bg-card);
  backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);
  border:1px solid var(--border);border-radius:14px;
  padding:18px 20px;
  transition:all 0.25s;
  position:relative;
}}
.card:hover{{
  border-color:var(--border-glow);
  background:var(--bg-card-hover);
  box-shadow:0 4px 24px var(--glow);
}}
.card-head{{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}}
.card-head-content{{flex:1;min-width:0}}
.card-title{{font-size:14px;font-weight:600;line-height:1.45;color:var(--text)}}
.card-meta{{font-size:12px;color:var(--text-secondary);margin-top:5px}}
.card-badges{{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}}

.badge{{
  display:inline-flex;align-items:center;
  padding:3px 10px;border-radius:8px;
  font-size:10px;font-weight:600;letter-spacing:0.3px;
}}
.badge-green{{background:var(--green-soft);color:var(--green)}}
.badge-amber{{background:var(--amber-soft);color:var(--amber)}}
.badge-blue{{background:var(--primary-soft);color:var(--primary)}}
.badge-cyan{{background:var(--cyan-soft);color:var(--cyan)}}
.badge-purple{{background:var(--purple-soft);color:var(--purple)}}
.badge-dim{{background:rgba(255,255,255,0.04);color:var(--text-dim);font-weight:500}}

.expand-btn{{
  background:none;border:none;color:var(--primary);font-size:12px;font-weight:500;
  cursor:pointer;padding:4px 8px;border-radius:6px;
  transition:background 0.15s;white-space:nowrap;font-family:inherit;
}}
.expand-btn:hover{{background:var(--primary-soft)}}

.expandable{{max-height:0;overflow:hidden;transition:max-height 0.35s ease}}
.expandable.open{{max-height:4000px}}
.card-detail{{
  margin-top:14px;padding-top:14px;border-top:1px solid var(--border);
  font-size:12px;color:var(--text-secondary);line-height:1.7;
}}
.card-detail .field{{margin-bottom:6px}}
.card-detail .field-label{{font-weight:600;color:var(--text)}}
.card-link{{
  display:inline-flex;align-items:center;gap:4px;
  color:var(--primary);text-decoration:none;font-size:12px;font-weight:500;
  margin-top:8px;padding:4px 0;transition:color 0.15s;
}}
.card-link:hover{{color:var(--cyan)}}
.card-link svg{{width:12px;height:12px}}

.empty-state{{
  text-align:center;padding:60px 20px;color:var(--text-dim);
  font-size:14px;
}}

/* ---- Cookie Banner ---- */
.cookie-banner{{
  position:fixed;bottom:20px;left:50%;transform:translateX(-50%);
  width:90%;max-width:600px;background:var(--bg-surface);
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  border:1px solid var(--border);border-radius:16px;
  padding:20px 24px;display:flex;flex-direction:column;gap:16px;
  box-shadow:0 10px 40px rgba(0,0,0,0.5);z-index:9999;
  opacity:0;pointer-events:none;transition:opacity 0.4s, transform 0.4s;
  transform:translate(-50%, 20px);
}}
.cookie-banner.show{{opacity:1;pointer-events:auto;transform:translate(-50%, 0);}}
.cookie-text{{font-size:13px;color:var(--text-secondary);line-height:1.5}}
.cookie-text strong{{color:var(--text)}}
.cookie-btns{{display:flex;gap:10px;justify-content:flex-end}}
.cookie-btn{{
  padding:8px 16px;border-radius:8px;font-size:13px;font-weight:600;
  cursor:pointer;border:none;transition:all 0.2s;
}}
.btn-accept{{background:var(--primary);color:#fff}}
.btn-accept:hover{{background:var(--cyan)}}
.btn-decline{{background:var(--bg-card);color:var(--text);border:1px solid var(--border)}}
.btn-decline:hover{{background:var(--bg-card-hover)}}

/* ---- Responsive ---- */
@media(max-width:900px){{
  :root{{--sidebar-w:0px}}
  .sidebar{{display:none}}
  .main-inner{{padding:20px 16px}}
  .stats{{grid-template-columns:repeat(2,1fr)}}
}}
</style>
</head>
<body>

<!-- Cookie Banner -->
<div class="cookie-banner" id="cookieBanner">
  <div class="cookie-text">
    <strong>We value your privacy</strong><br>
    We use tracking technologies (including cookies) to serve targeted advertisements and analyze site traffic. By clicking "Accept", you consent to our use of these technologies. You can read more in our <a href="privacy.html" style="color:var(--primary)">Privacy Policy</a>.
  </div>
  <div class="cookie-btns">
    <button class="cookie-btn btn-decline" onclick="handleConsent(false)">Decline</button>
    <button class="cookie-btn btn-accept" onclick="handleConsent(true)">Accept & Continue</button>
  </div>
</div>

<!-- Sidebar -->
<nav class="sidebar">
  <div class="sidebar-brand">
    <div class="sidebar-logo">
      <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="20" cy="20" r="3" fill="url(#g1)"/>
        <circle cx="20" cy="20" r="8" stroke="url(#g1)" stroke-width="0.7" opacity="0.6"/>
        <circle cx="20" cy="20" r="14" stroke="url(#g1)" stroke-width="0.5" opacity="0.35"/>
        <circle cx="20" cy="20" r="19" stroke="url(#g1)" stroke-width="0.4" opacity="0.2"/>
        <line x1="20" y1="1" x2="20" y2="39" stroke="url(#g1)" stroke-width="0.4" opacity="0.3"/>
        <line x1="1" y1="20" x2="39" y2="20" stroke="url(#g1)" stroke-width="0.4" opacity="0.3"/>
        <line x1="6" y1="6" x2="34" y2="34" stroke="url(#g1)" stroke-width="0.4" opacity="0.25"/>
        <line x1="34" y1="6" x2="6" y2="34" stroke="url(#g1)" stroke-width="0.4" opacity="0.25"/>
        <defs><linearGradient id="g1" x1="0" y1="0" x2="40" y2="40"><stop stop-color="#5b9aff"/><stop offset="1" stop-color="#22d3ee"/></linearGradient></defs>
      </svg>
      <h1>PAVUK</h1>
    </div>
    <div class="sidebar-subtitle">Neurobiology Monitor</div>
  </div>
  <div class="sidebar-nav" id="nav"></div>
  <div class="sidebar-footer">
    Last updated<br>{now}<br><br>
    <a href="privacy.html" style="color:var(--text-secondary);text-decoration:none;font-weight:500;">Privacy Policy & Terms</a><br><br>
    <span style="opacity:0.6">python build_dashboard.py</span>
  </div>
</nav>

<!-- Main content -->
<main class="main">
  <div class="main-inner">
    <div class="header">
      <div class="header-row">
        <h2 id="page-title">Clinical Trials</h2>
        <span class="timestamp">{total} items collected</span>
      </div>
      <div class="search-wrap">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input type="text" class="search-input" id="search" placeholder="Search trials, papers, preprints...">
      </div>
    </div>
    <div class="stats" id="stats"></div>
    <div class="card-list" id="results"></div>
    <div class="empty-state" id="empty" style="display:none">No results match your search.</div>
  </div>
</main>

<script>
const DATA = {data_json};

const TABS = [
  {{id:'clinicaltrials', icon:'\U0001F3E5', label:'Clinical Trials', title:'Clinical Trials'}},
  {{id:'pubmed', icon:'\U0001F52C', label:'PubMed', title:'PubMed Articles'}},
  {{id:'biorxiv', icon:'\U0001F4C4', label:'bioRxiv', title:'Preprints'}},
  {{id:'rss', icon:'\U0001F4F0', label:'RSS News', title:'Industry News'}},
  {{id:'equine', icon:'\U0001F40E', label:'Equine Science', title:'Equine Science (PubMed)'}},
];

let activeTab='clinicaltrials', searchQuery='';

function esc(s){{if(!s)return'';const d=document.createElement('div');d.textContent=s;return d.innerHTML}}
function stripHtml(s){{const d=document.createElement('div');d.innerHTML=s;return d.textContent||''}}
function toggle(id){{document.getElementById(id)?.classList.toggle('open')}}

function renderNav(){{
  document.getElementById('nav').innerHTML=TABS.map(t=>`
    <div class="nav-item ${{activeTab===t.id?'active':''}}" onclick="switchTab('${{t.id}}')">
      <span class="nav-icon">${{t.icon}}</span>${{t.label}}
      <span class="nav-count">${{DATA[t.id].length}}</span>
    </div>`).join('');
}}

function renderStats(){{
  document.getElementById('stats').innerHTML=TABS.map(t=>`
    <div class="stat ${{activeTab===t.id?'active':''}}" onclick="switchTab('${{t.id}}')">
      <div class="stat-icon">${{t.icon}}</div>
      <div class="stat-value">${{DATA[t.id].length}}</div>
      <div class="stat-label">${{t.label}}</div>
    </div>`).join('');
}}

function switchTab(id){{
  activeTab=id;
  const tab=TABS.find(t=>t.id===id);
  document.getElementById('page-title').textContent=tab?tab.title:id;
  renderNav();renderStats();renderResults();
}}

function renderResults(){{
  const el=document.getElementById('results');
  const emptyEl=document.getElementById('empty');
  const items=DATA[activeTab]||[];
  const q=searchQuery.toLowerCase();
  const filtered=items.filter(it=>!q||JSON.stringify(it).toLowerCase().includes(q));
  if(!filtered.length){{el.innerHTML='';emptyEl.style.display='block';return}}
  emptyEl.style.display='none';
  el.innerHTML=filtered.map((it,i)=>{{
    if(activeTab==='clinicaltrials')return trialCard(it,i);
    if(activeTab==='pubmed')return pubmedCard(it,i);
    if(activeTab==='equine')return pubmedCard(it,i); // Same format as PubMed
    if(activeTab==='biorxiv')return biorxivCard(it,i);
    if(activeTab==='rss')return rssCard(it,i);
    return'';
  }}).join('');
}}

function phaseBadge(p){{
  if(!p)return'';
  const c=p.includes('3')?'badge-green':p.includes('2')?'badge-amber':p.includes('1')?'badge-blue':'badge-purple';
  return`<span class="badge ${{c}}">${{p}}</span>`;
}}
function statusBadge(s){{
  if(!s)return'';
  const c=s==='RECRUITING'?'badge-green':s.includes('NOT_YET')?'badge-amber':'badge-cyan';
  return`<span class="badge ${{c}}">${{s.replace(/_/g,' ')}}</span>`;
}}
const arrow='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 17L17 7M17 7H7M17 7V17"/></svg>';

function trialCard(t,i){{
  const conds=(t.conditions||[]).join(', ');
  const intervs=(t.interventions||[]).map(v=>v.name).filter(Boolean).join(', ');
  return`<div class="card">
    <div class="card-head">
      <div class="card-head-content">
        <div class="card-title">${{esc(t.title)}}</div>
        <div class="card-badges">
          ${{statusBadge(t.status)}}${{phaseBadge(t.phase)}}
          <span class="badge badge-dim">${{t.nct_id}}</span>
          ${{t.study_type?`<span class="badge badge-dim">${{t.study_type}}</span>`:''}}
        </div>
      </div>
      <button class="expand-btn" onclick="toggle('c${{i}}')">Details</button>
    </div>
    <div id="c${{i}}" class="expandable"><div class="card-detail">
      ${{conds?`<div class="field"><span class="field-label">Conditions: </span>${{esc(conds)}}</div>`:''}}
      ${{intervs?`<div class="field"><span class="field-label">Interventions: </span>${{esc(intervs)}}</div>`:''}}
      <div class="field"><span class="field-label">Sponsor: </span>${{esc(t.sponsor||'--')}}</div>
      <div class="field"><span class="field-label">Enrollment: </span>${{t.enrollment||'--'}} participants</div>
      ${{t.start_date?`<div class="field"><span class="field-label">Started: </span>${{t.start_date}}</div>`:''}}
      ${{t.summary?`<div style="margin-top:8px">${{esc(t.summary).substring(0,500)}}${{(t.summary||'').length>500?'...':''}}</div>`:''}}
      <a class="card-link" href="${{t.source_url}}" target="_blank">View on ClinicalTrials.gov ${{arrow}}</a>
    </div></div>
  </div>`;
}}

function pubmedCard(p,i){{
  const auths=Array.isArray(p.authors)?p.authors.slice(0,3).join(', '):(p.authors||'');
  const more=Array.isArray(p.authors)&&p.authors.length>3?` +${{p.authors.length-3}} more`:'';
  const kw=(p.keywords||[]).slice(0,5);
  return`<div class="card">
    <div class="card-head">
      <div class="card-head-content">
        <div class="card-title">${{esc(p.title)}}</div>
        <div class="card-meta">${{esc(auths)}}${{more}}${{p.journal?' &middot; '+esc(p.journal):''}}${{p.pub_date?' &middot; '+p.pub_date:''}}</div>
        ${{kw.length?`<div class="card-badges" style="margin-top:6px">${{kw.map(k=>`<span class="badge badge-dim">${{esc(k)}}</span>`).join('')}}</div>`:''}}
      </div>
      <button class="expand-btn" onclick="toggle('p${{i}}')">Details</button>
    </div>
    <div id="p${{i}}" class="expandable"><div class="card-detail">
      ${{p.abstract?`<div>${{esc(p.abstract).substring(0,600)}}${{(p.abstract||'').length>600?'...':''}}</div>`:'<div style="font-style:italic;color:var(--text-dim)">No abstract available</div>'}}
      ${{p.doi?`<div class="field" style="margin-top:8px"><span class="field-label">DOI: </span>${{esc(p.doi)}}</div>`:''}}
      <a class="card-link" href="${{p.source_url}}" target="_blank">View on PubMed ${{arrow}}</a>
    </div></div>
  </div>`;
}}

function biorxivCard(b,i){{
  return`<div class="card">
    <div class="card-head">
      <div class="card-head-content">
        <div class="card-title">${{esc(b.title)}}</div>
        <div class="card-badges" style="margin-top:6px">
          <span class="badge badge-blue">${{b.category||'preprint'}}</span>
          <span class="badge badge-dim">${{b.pub_date||''}} &middot; ${{b.server||'biorxiv'}}</span>
          ${{b.published_doi?'<span class="badge badge-green">Peer-reviewed</span>':''}}
        </div>
      </div>
      <button class="expand-btn" onclick="toggle('b${{i}}')">Details</button>
    </div>
    <div id="b${{i}}" class="expandable"><div class="card-detail">
      <div class="field"><span class="field-label">Authors: </span>${{esc((b.authors||'').substring(0,200))}}</div>
      ${{b.abstract?`<div style="margin-top:8px">${{esc(b.abstract).substring(0,500)}}${{(b.abstract||'').length>500?'...':''}}</div>`:''}}
      <a class="card-link" href="${{b.source_url}}" target="_blank">View on bioRxiv ${{arrow}}</a>
    </div></div>
  </div>`;
}}

function rssCard(r){{
  const summary=stripHtml(r.summary||'').substring(0,180);
  const date=r.published?new Date(r.published).toLocaleDateString('en-GB',{{day:'numeric',month:'short',year:'numeric'}}):'';
  return`<div class="card">
    <div class="card-head">
      <div class="card-head-content">
        <div class="card-title">${{esc(r.title)}}</div>
        <div class="card-meta">
          <strong>${{esc(r.source_feed||'')}}</strong>
          ${{date?' &middot; '+date:''}}
          ${{r.category?' &middot; '+esc(r.category.substring(0,50)):''}}
        </div>
        ${{summary?`<div style="margin-top:8px;font-size:12px;color:var(--text-secondary);line-height:1.6">${{esc(summary)}}</div>`:''}}
      </div>
      <a class="card-link" href="${{r.link}}" target="_blank" style="white-space:nowrap">Read ${{arrow}}</a>
    </div>
  </div>`;
}}

document.getElementById('search').addEventListener('input',e=>{{searchQuery=e.target.value;renderResults()}});

// ---- Consent Management ----
function initConsent(){{
  const consent = localStorage.getItem('pavuk_cookie_consent');
  if (consent === null) {{
    // Show banner after short delay
    setTimeout(() => document.getElementById('cookieBanner').classList.add('show'), 1000);
  }} else if (consent === 'true') {{
    enableAds();
  }}
}}

function handleConsent(accepted) {{
  localStorage.setItem('pavuk_cookie_consent', accepted ? 'true' : 'false');
  document.getElementById('cookieBanner').classList.remove('show');
  if (accepted) enableAds();
}}

function enableAds() {{
  // NOTE: Insert your actual AdSense or tracking code here!
  console.log("Consent granted: Ad scripts would load here.");
}}

renderNav();renderStats();renderResults();initConsent();
</script>
</body>
</html>'''


def main():
    print("Pavuk Dashboard Builder")
    print("=" * 40)

    if not DATA_DIR.exists():
        print(f"\n[!] Data directory '{DATA_DIR}' not found!")
        print("  Run some spiders first:")
        print("    scrapy crawl clinicaltrials -O data/clinicaltrials.json")
        sys.exit(1)

    print(f"\nLooking for data files in {DATA_DIR}/...")
    file_map = find_data_files()

    if not file_map:
        print("\n[!] No JSON data files found!")
        print("  Run some spiders first:")
        print("    scrapy crawl clinicaltrials -O data/clinicaltrials.json")
        sys.exit(1)

    print("\nLoading data...")
    data = load_data(file_map)
    total = sum(len(v) for v in data.values())

    print(f"\nBuilding dashboard with {total} total items...")
    html = build_html(data)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n[OK] Dashboard saved to: {OUTPUT_FILE.resolve()}")
    print(f"  Open it: start {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
