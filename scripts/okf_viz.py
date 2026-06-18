# scripts/okf_viz.py
"""Render a normalized model as a single self-contained HTML file: an offline
browser for the bundle. Reader-first — search + a directory-grouped concept
list + a reader panel (frontmatter, body, links, backlinks) — plus a "needs
attention" lens that surfaces the same findings `check` reports (orphans, broken
links, stale, uncited, unlisted) and lets you click straight to them. The graph
is a secondary toggle. No external resources, no build step.

All user-supplied text rides in the JSON blob (with `</` neutralized) and is
rendered with textContent, so a concept body can never break out or execute."""
import json, html

_ATTENTION = {"orphan", "broken-link", "stale", "no-citations", "index-drift"}

def render_html(model, name="OKF Bundle", findings=None):
    issues_by_id = {}
    for f in (findings or []):
        if f.get("code") in _ATTENTION:
            issues_by_id.setdefault(f.get("id"), set()).add(f["code"])
    nodes = []
    for cid, f in model["files"].items():
        meta = f.get("meta") or {}
        def _s(key):
            v = meta.get(key)
            return v if isinstance(v, str) else ""
        nodes.append({
            "id": cid, "type": f.get("type", "") or "", "reserved": bool(f.get("reserved")),
            "error": bool(f.get("errors")), "title": _s("title"), "desc": _s("description"),
            "resource": _s("resource"), "body": f.get("body", "") or "",
            "issues": sorted(issues_by_id.get(cid, []))})
    edges = [{"src": l["src"], "dst": l["dst"], "resolved": bool(l.get("resolved"))}
             for l in model["links"] if l.get("dst")]
    data = json.dumps({"nodes": nodes, "edges": edges}, indent=2).replace("</", "<\\/")
    return _TEMPLATE.replace("__TITLE__", html.escape(name)).replace("__DATA__", data)

_TEMPLATE = r"""<!doctype html>
<html><head><meta charset="utf-8"><title>__TITLE__</title>
<style>
 :root{--bg:#0f1115;--panel:#171a21;--line:#2a2f3a;--fg:#e6e6e6;--mut:#9aa4b2;--accent:#88c0d0;--warn:#bf616a}
 *{box-sizing:border-box} body{font-family:system-ui,sans-serif;margin:0;background:var(--bg);color:var(--fg)}
 header{display:flex;gap:12px;align-items:center;padding:10px 16px;background:var(--panel);border-bottom:1px solid var(--line)}
 header .title{font-weight:600} header input{flex:1;max-width:360px;background:var(--bg);border:1px solid var(--line);
   color:var(--fg);border-radius:6px;padding:7px 10px;font-size:14px}
 header button{background:var(--bg);border:1px solid var(--line);color:var(--fg);border-radius:6px;padding:7px 12px;cursor:pointer;font-size:13px}
 #chips{display:flex;flex-wrap:wrap;gap:6px;padding:8px 16px;background:var(--panel);border-bottom:1px solid var(--line)}
 .chip{cursor:pointer;font-size:12px;border:1px solid var(--line);border-radius:12px;padding:2px 10px;color:var(--mut)}
 .chip.on{background:var(--warn);border-color:var(--warn);color:#fff} .chip.clean{color:var(--mut);opacity:.7;cursor:default}
 #wrap{display:flex;height:calc(100vh - 92px)}
 #list{width:340px;overflow:auto;border-right:1px solid var(--line)}
 #list .grp{padding:8px 12px 2px;color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.04em}
 #list .item{padding:5px 12px;cursor:pointer;font-size:14px;display:flex;align-items:center;gap:6px}
 #list .item:hover{background:#1c2330} #list .item.sel{background:#222b3a}
 #list .dot{width:8px;height:8px;border-radius:50%;flex:none;background:transparent}
 #list .item.flag .dot{background:var(--warn)} #list .tt{font-size:11px;color:var(--mut)}
 #main{flex:1;overflow:auto;padding:14px 18px}
 #reader h2{margin:0 0 4px} #reader .meta div{margin:1px 0;color:#cbd3df} #reader .meta b{color:var(--mut)}
 #reader .badges{margin:6px 0} #reader .badge{display:inline-block;font-size:11px;background:var(--warn);color:#fff;border-radius:10px;padding:1px 8px;margin-right:4px}
 ul.lnk{list-style:none;margin:2px 0 10px;padding:0} ul.lnk li{padding:1px 0}
 ul.lnk a{color:var(--accent);text-decoration:none;cursor:pointer} ul.lnk .broken{color:var(--warn)}
 pre.body{white-space:pre-wrap;word-break:break-word;background:#11151c;border:1px solid var(--line);border-radius:6px;padding:10px;font-size:13px}
 .hint{color:var(--mut)} #legend{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:8px}
 .leg{display:inline-flex;align-items:center;gap:4px;font-size:12px} .leg i{width:9px;height:9px;border-radius:50%;display:inline-block}
 svg{width:100%;height:calc(100vh - 150px)} .lbl{font-size:12px;fill:#e6e6e6} text{pointer-events:none}
</style></head>
<body>
<header><span class="title">__TITLE__</span>
 <input id="q" placeholder="Search concepts…">
 <button id="view">Graph view</button></header>
<div id="chips"></div>
<div id="wrap"><div id="list"></div><div id="main"><p class="hint" id="empty">Select a concept to read it.</p></div></div>
<script>
const DATA = __DATA__;
const nodes = DATA.nodes, edges = DATA.edges, byId = {};
nodes.forEach(n => byId[n.id] = n);
const concepts = nodes.filter(n => !n.reserved);

const LABELS = {"orphan":"Orphans","broken-link":"Broken links","stale":"Stale",
                "no-citations":"Uncited","index-drift":"Unlisted"};
const PALETTE = ['#a3be8c','#81a1c1','#b48ead','#ebcb8b','#88c0d0','#d08770','#8fbcbb','#5e81ac','#bf616a','#e5e9f0'];
const types = [...new Set(concepts.filter(n => n.type).map(n => n.type))].sort();
const colorOf = {};
types.forEach((t, i) => colorOf[t] = PALETTE[i - PALETTE.length * Math.floor(i / PALETTE.length)]);
function nodeColor(n){ if(n.error) return '#bf616a'; if(n.reserved) return '#4c566a'; return colorOf[n.type] || '#a3be8c'; }

const out = {}, inn = {};
nodes.forEach(n => { out[n.id] = []; inn[n.id] = []; });
edges.forEach(e => { if(byId[e.src]) out[e.src].push(e); if(byId[e.dst]) inn[e.dst].push(e); });

let activeIssue = null, view = 'reader', selected = null;

function renderChips(){
  const box = document.getElementById('chips'); box.textContent = '';
  const lead = document.createElement('span'); lead.className = 'chip clean'; lead.textContent = 'Needs attention:';
  box.appendChild(lead);
  let any = false;
  Object.keys(LABELS).forEach(code => {
    const n = concepts.filter(c => c.issues.indexOf(code) >= 0).length;
    if(!n) return; any = true;
    const c = document.createElement('span'); c.className = 'chip' + (activeIssue === code ? ' on' : '');
    c.textContent = LABELS[code] + ' ' + n;
    c.addEventListener('click', () => { activeIssue = activeIssue === code ? null : code; renderChips(); renderList(); });
    box.appendChild(c);
  });
  if(!any){ const ok = document.createElement('span'); ok.className = 'chip clean'; ok.textContent = 'all clear'; box.appendChild(ok); }
}

function topdir(id){ const i = id.lastIndexOf('/'); return i < 0 ? '(root)' : id.slice(0, i); }

function renderList(){
  const q = (document.getElementById('q').value || '').toLowerCase();
  const el = document.getElementById('list'); el.textContent = '';
  const rows = concepts
    .filter(n => !activeIssue || n.issues.indexOf(activeIssue) >= 0)
    .filter(n => !q || (n.id + ' ' + (n.title || '') + ' ' + (n.desc || '')).toLowerCase().indexOf(q) >= 0)
    .sort((a, b) => a.id < b.id ? -1 : 1);
  let group = null;
  rows.forEach(n => {
    const g = topdir(n.id);
    if(g !== group){ group = g; const h = document.createElement('div'); h.className = 'grp'; h.textContent = g; el.appendChild(h); }
    const it = document.createElement('div');
    it.className = 'item' + (n.issues.length ? ' flag' : '') + (selected === n.id ? ' sel' : '');
    const dot = document.createElement('span'); dot.className = 'dot'; it.appendChild(dot);
    const t = document.createElement('span'); t.textContent = n.title || n.id; it.appendChild(t);
    if(n.type){ const tt = document.createElement('span'); tt.className = 'tt'; tt.textContent = n.type; it.appendChild(tt); }
    it.addEventListener('click', () => select(n.id));
    el.appendChild(it);
  });
  if(!rows.length){ const p = document.createElement('p'); p.className = 'hint'; p.style.padding = '10px 12px';
    p.textContent = 'No concepts match.'; el.appendChild(p); }
}

function kv(k, v){ const p = document.createElement('div'); const b = document.createElement('b');
  b.textContent = k + ': '; p.appendChild(b); p.appendChild(document.createTextNode(v)); return p; }
function linksBlock(label, ids){
  const w = document.createElement('div'); const b = document.createElement('b');
  b.textContent = label + ' (' + ids.length + ')'; w.appendChild(b);
  const ul = document.createElement('ul'); ul.className = 'lnk';
  ids.forEach(id => { const li = document.createElement('li');
    if(byId[id]){ const a = document.createElement('a'); a.textContent = byId[id].title || id;
      a.addEventListener('click', () => select(id)); li.appendChild(a); }
    else { li.textContent = id + ' (unwritten)'; li.className = 'broken'; }
    ul.appendChild(li); });
  w.appendChild(ul); return w;
}

function renderReader(){
  const m = document.getElementById('main'); m.textContent = '';
  if(!selected || !byId[selected]){ const p = document.createElement('p'); p.className = 'hint';
    p.textContent = 'Select a concept to read it.'; m.appendChild(p); return; }
  const n = byId[selected], r = document.createElement('div'); r.id = 'reader';
  const h = document.createElement('h2'); h.textContent = n.title || n.id; r.appendChild(h);
  if(n.issues.length){ const bd = document.createElement('div'); bd.className = 'badges';
    n.issues.forEach(c => { const s = document.createElement('span'); s.className = 'badge';
      s.textContent = LABELS[c] || c; bd.appendChild(s); }); r.appendChild(bd); }
  const meta = document.createElement('div'); meta.className = 'meta';
  meta.appendChild(kv('id', n.id));
  if(n.type) meta.appendChild(kv('type', n.type));
  if(n.resource) meta.appendChild(kv('resource', n.resource));
  if(n.desc) meta.appendChild(kv('description', n.desc));
  r.appendChild(meta);
  r.appendChild(linksBlock('Links', out[n.id].map(e => e.dst)));
  r.appendChild(linksBlock('Backlinks', inn[n.id].map(e => e.src)));
  if(n.body){ const pre = document.createElement('pre'); pre.className = 'body'; pre.textContent = n.body; r.appendChild(pre); }
  m.appendChild(r);
}

const NS = 'http://www.w3.org/2000/svg';
function renderGraph(){
  const m = document.getElementById('main'); m.textContent = '';
  const leg = document.createElement('div'); leg.id = 'legend';
  types.forEach(t => { const s = document.createElement('span'); s.className = 'leg';
    const i = document.createElement('i'); i.style.background = colorOf[t]; s.appendChild(i);
    s.appendChild(document.createTextNode(t)); leg.appendChild(s); });
  m.appendChild(leg);
  const svg = document.createElementNS(NS, 'svg'); m.appendChild(svg);
  const W = svg.clientWidth || m.clientWidth || 820, H = (window.innerHeight - 150) || 600;
  const R = Math.min(W, H) / 2 - 50, cx = W / 2, cy = H / 2, pos = {};
  nodes.forEach((n, i) => { const a = 2 * Math.PI * i / Math.max(1, nodes.length);
    pos[n.id] = [cx + R * Math.cos(a), cy + R * Math.sin(a)]; });
  edges.forEach(e => { const p = pos[e.src], q = pos[e.dst]; if(!p || !q) return;
    const l = document.createElementNS(NS, 'line');
    l.setAttribute('x1', p[0]); l.setAttribute('y1', p[1]); l.setAttribute('x2', q[0]); l.setAttribute('y2', q[1]);
    l.setAttribute('stroke', e.resolved ? '#3b4252' : '#bf616a'); l.setAttribute('stroke-width', e.resolved ? 1 : 1.5);
    svg.appendChild(l); });
  const nbr = new Set();
  if(selected){ out[selected].forEach(e => nbr.add(e.dst)); inn[selected].forEach(e => nbr.add(e.src)); }
  nodes.forEach(n => { const xy = pos[n.id];
    const c = document.createElementNS(NS, 'circle');
    c.setAttribute('cx', xy[0]); c.setAttribute('cy', xy[1]);
    c.setAttribute('r', n.id === selected ? 9 : (n.reserved ? 5 : 7));
    c.setAttribute('fill', nodeColor(n)); c.style.cursor = 'pointer';
    c.addEventListener('click', () => select(n.id));
    const ttl = document.createElementNS(NS, 'title'); ttl.textContent = (n.title || n.id) + ' [' + (n.type || 'reserved') + ']';
    c.appendChild(ttl); svg.appendChild(c);
    // labels only for the selected node and its neighbours — keeps big bundles legible
    if(n.id === selected || nbr.has(n.id)){
      const t = document.createElementNS(NS, 'text'); t.setAttribute('x', xy[0] + 11); t.setAttribute('y', xy[1] + 4);
      t.setAttribute('class', 'lbl'); t.textContent = n.title || n.id; svg.appendChild(t); }
  });
}

function renderMain(){ view === 'graph' ? renderGraph() : renderReader(); }
function select(id){ selected = id; if(view !== 'graph'){ /* stay/READER */ } renderList(); renderMain(); }

document.getElementById('q').addEventListener('input', renderList);
document.getElementById('view').addEventListener('click', () => {
  view = view === 'graph' ? 'reader' : 'graph';
  document.getElementById('view').textContent = view === 'graph' ? 'Reader view' : 'Graph view';
  renderMain();
});
renderChips(); renderList(); renderMain();
</script>
</body></html>"""
