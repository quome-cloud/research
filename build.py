#!/usr/bin/env python3
"""Generate docs/index.html (the GitHub Pages site) from papers.json, CITATIONS.bib
and assets/modules/*.svg.

    python3 build.py

Domain framing (problem statements, partners, who it is for) lives in DOMAINS below.
Paper metadata lives in papers.json. BibTeX comes from CITATIONS.bib by key.
"""
import base64
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
P = json.loads((ROOT / "papers.json").read_text())
GENERATED = P.get("generated", "")

# --------------------------------------------------------------------------- domains
DOMAINS = {
    "healthcare-security": {
        "num": "01",
        "color": "teal",
        "icon": "✚",
        "short": "Healthcare AI security",
        "question": "How do you let an autonomous agent anywhere near patient care?",
        "summary": "A regulatory framework (HAARF), a positive-security prompt firewall (QFIRE) and fourteen enforcement modules. Each module is a standalone paper, a layer in one Rust gateway, and an adversarial dataset with a full data card.",
        "artifacts": [
            ("HAARF", "framework", "https://www.medrxiv.org/content/10.64898/2026.04.09.26350519v1"),
            ("qfire", "gateway", "https://github.com/Task-force-for-AI-agents-in-Healthcare/qfire"),
            ("14 modules", "open source", "#gateway"),
        ],
        "partner": ("Task Force for AI Agents in Healthcare", "https://aihealthagents.org/"),
        "for": "Health systems · device makers · regulators",
    },
    "proof-of-control": {
        "num": "02",
        "color": "amber",
        "icon": "⊚",
        "short": "Proof of control",
        "question": "How do you prove what an AI system did without trusting its operator?",
        "summary": "An open standard of 127 verifiable requirements graded on four tiers, a twelve-paper research roadmap with working software behind the first three, and a practitioner guide for the CISOs who have to deploy it. “Does this agent have proof of control?” becomes a procurable yes or no.",
        "artifacts": [
            ("ov-poc-standard", "open standard", "https://github.com/LFDT-ProofOfControl/ov-poc-standard"),
            ("roadmap", "12 papers", "https://github.com/AAI-Society/poc-research-roadmap"),
            ("guide", "for CISOs", "https://github.com/AAI-Society/poc_guide"),
            ("parallax", "trust calculus", "https://github.com/AAI-Society/parallax"),
            ("transit · occultation · spectrum · ephemeris", "tools", "https://github.com/AAI-Society"),
        ],
        "partner": ("Advanced AI Society", "https://advancedaisociety.org/"),
        "for": "Procurement · auditors · AI governance",
    },
    "world-models": {
        "num": "03",
        "color": "sky",
        "icon": "◎",
        "short": "World models",
        "question": "How do you train agents in simulators that stay exact?",
        "summary": "Verified code world models: an agent authors a world as code in minutes, tests prove it exact with no compounding error, and fine-tuning on trajectories from many verified worlds lifts generalization to held-out domains.",
        "artifacts": [
            ("openworld", "substrate", "https://github.com/quome-cloud/openworld"),
            ("ARC-AGI-3", "atlas", "https://github.com/quome-cloud/openworld/blob/main/papers/arc-3/main.pdf"),
        ],
        "partner": None,
        "for": "Robotics · operations · simulation teams",
    },
    "agentic-systems": {
        "num": "04",
        "color": "rose",
        "icon": "⌘",
        "short": "Agentic evaluation",
        "question": "What does agentic software actually deliver to the people who use it?",
        "summary": "Human-centered benchmarks for agentic systems: hundreds of generated apps, hundreds of raters and a thousand pairwise comparisons show that visual polish and functional reliability come apart, and only task-based evaluation sees it.",
        "artifacts": [
            ("Prompt to Product", "benchmark", "https://arxiv.org/abs/2512.18080"),
        ],
        "partner": None,
        "for": "Product · platform · developer-tools teams",
    },
}
ORDER = ["healthcare-security", "proof-of-control", "world-models", "agentic-systems"]

BLURBS = {
    "quanchor": "sealed goal anchor + goal-drift monitor", "quledger": "tamper-evident audit ledger",
    "qubom": "AIBOM attestation gate", "quwarden": "policy-as-code authorization",
    "qudam": "PHI egress control / DLP", "quantidote": "retrieval-poisoning defense",
    "quorum": "agent identity + k-of-n quorum", "qutriage": "calibrated human oversight",
    "qufair": "equity monitor", "qudrift": "drift & autonomy monitor",
    "qupassport": "regulatory passport gate", "quconsent": "consent + AI disclosure",
    "qubroker": "device-safety broker", "qusiege": "continuous red-team & IR",
}

MERMAID = (ROOT / "assets" / "gateway.mmd").read_text()

# --------------------------------------------------------------------------- data
def parse_bib():
    out, cur, key = {}, [], None
    for line in (ROOT / "CITATIONS.bib").read_text().splitlines():
        m = re.match(r"@\w+\{([^,]+),", line)
        if m:
            if key:
                out[key] = "\n".join(cur).strip()
            key, cur = m.group(1), [line]
        elif key:
            cur.append(line)
    if key:
        out[key] = "\n".join(cur).strip()
    return out

BIB = parse_bib()
sections = {s["id"]: s for s in P["sections"]}

papers = []
for sid in ORDER:
    s = sections[sid]
    for p in s["papers"]:
        q = dict(p)
        q["area"] = sid
        q["area_title"] = s["title"]
        q["affils"] = p.get("author_affils") or p.get("author_affiliations") or {}
        q["bibtex"] = BIB.get(p["key"], "")
        for k in ("author_affils", "author_affiliations", "extra"):
            q.pop(k, None)
        papers.append(q)

areas = []
for sid in ORDER:
    s, d = sections[sid], DOMAINS[sid]
    ps = [p for p in papers if p["area"] == sid]
    areas.append({
        "id": sid, "title": s["title"], **{k: v for k, v in d.items()},
        "papers": len(ps),
        "repos": len({p["code_url"] for p in ps if p.get("code_url")}),
        "datasets": len({p["dataset_url"] for p in ps if p.get("dataset_url")}),
    })

def tile_svg(src: str) -> str:
    """Crop a wide module logo (tile + wordmark) down to the square tile only."""
    src = re.sub(r'viewBox="[^"]*" width="\d+" height="\d+"', 'viewBox="30 40 296 260"', src, count=1)
    src = re.sub(r'\s*<g transform="translate\(372,0\)">.*?</g>\n', "\n", src, count=1, flags=re.S)
    src = src.replace(' filter="url(#glow)"', "")
    src = re.sub(r'\s*<filter id="glow".*?</filter>', "", src, count=1, flags=re.S)
    return src

tiles = {}
for f in sorted((ROOT / "assets" / "modules").glob("*-logo.svg")):
    svg = tile_svg(f.read_text())
    tiles[f.name.replace("-logo.svg", "")] = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()

DATA = {
    "stats": P["stats"], "affiliations": P["affiliations"], "areas": areas,
    "papers": papers, "blurbs": BLURBS, "tiles": tiles, "mermaid": MERMAID,
}

# --------------------------------------------------------------------------- page
CSS = r"""
:root{
  --bg:#fbfbfd; --bg-2:#ffffff; --bg-3:#f1f2f7; --fg:#0c1024; --fg-2:#3b4262; --fg-3:#6a7190; --line:#e3e6ef; --line-2:#cfd3e1;
  --accent:#5b3df5; --accent-2:#0ea5e9;
  --teal:#0b8f7c; --teal-bg:#e3f6f2; --amber:#b45309; --amber-bg:#fdf1dc; --sky:#0b7fc2; --sky-bg:#e4f3fd; --rose:#c42a63; --rose-bg:#fde7ef;
  --display:'Inter Tight',ui-sans-serif,system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;
  --body:'Inter',ui-sans-serif,system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;
  --mono:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace;
  --radius:20px; --radius-s:12px;
  --shadow:0 1px 2px rgba(12,16,36,.05),0 20px 50px -28px rgba(12,16,36,.28);
  --glow:radial-gradient(60% 50% at 70% 30%,rgba(91,61,245,.14),transparent 70%),radial-gradient(40% 40% at 20% 80%,rgba(14,165,233,.12),transparent 70%);
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#090c1a; --bg-2:#10152a; --bg-3:#161c35; --fg:#eef0fa; --fg-2:#c2c8e0; --fg-3:#8a92b5; --line:#232b4d; --line-2:#334071;
  --accent:#a78bfa; --accent-2:#38bdf8;
  --teal:#34d3bd; --teal-bg:#0d2f2a; --amber:#fbbf24; --amber-bg:#3a2707; --sky:#4cc3ff; --sky-bg:#0b2a41; --rose:#fb7aa6; --rose-bg:#3b1024;
  --shadow:0 1px 2px rgba(0,0,0,.5),0 24px 60px -30px rgba(0,0,0,.8);
  --glow:radial-gradient(60% 50% at 70% 30%,rgba(167,139,250,.16),transparent 70%),radial-gradient(40% 40% at 20% 80%,rgba(56,189,248,.12),transparent 70%);
  color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#090c1a; --bg-2:#10152a; --bg-3:#161c35; --fg:#eef0fa; --fg-2:#c2c8e0; --fg-3:#8a92b5; --line:#232b4d; --line-2:#334071;
  --accent:#a78bfa; --accent-2:#38bdf8;
  --teal:#34d3bd; --teal-bg:#0d2f2a; --amber:#fbbf24; --amber-bg:#3a2707; --sky:#4cc3ff; --sky-bg:#0b2a41; --rose:#fb7aa6; --rose-bg:#3b1024;
  --shadow:0 1px 2px rgba(0,0,0,.5),0 24px 60px -30px rgba(0,0,0,.8);
  --glow:radial-gradient(60% 50% at 70% 30%,rgba(167,139,250,.16),transparent 70%),radial-gradient(40% 40% at 20% 80%,rgba(56,189,248,.12),transparent 70%);
  color-scheme:dark}
*{box-sizing:border-box}
html,body{overflow-x:clip}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--body);font-size:16.5px;line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
a:focus-visible,button:focus-visible{outline:3px solid var(--accent);outline-offset:3px;border-radius:6px}
h1,h2,h3,h4{font-family:var(--display);letter-spacing:-.025em;line-height:1.08;margin:0;text-wrap:balance}
p{margin:0}
code{font-family:var(--mono);font-size:.9em}
.wrap{max-width:1200px;margin:0 auto;padding-inline:clamp(16px,4vw,40px)}
.eyebrow{font-family:var(--display);font-size:12.5px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--fg-3)}
.eyebrow.c-teal{color:var(--teal)} .eyebrow.c-amber{color:var(--amber)} .eyebrow.c-sky{color:var(--sky)} .eyebrow.c-rose{color:var(--rose)}
.lead{font-size:clamp(17px,1.5vw,20px);color:var(--fg-2);max-width:60ch;line-height:1.55}
.btn{display:inline-flex;align-items:center;gap:8px;font-family:var(--display);font-weight:600;font-size:15px;padding:12px 20px;border-radius:999px;border:1px solid var(--line-2);background:var(--bg-2);color:var(--fg);transition:transform .15s,box-shadow .15s,background .15s;cursor:pointer}
.btn:hover{transform:translateY(-1px);box-shadow:var(--shadow)}
.btn.primary{background:var(--fg);color:var(--bg);border-color:var(--fg)}
.btn.primary:hover{background:var(--accent);border-color:var(--accent);color:#fff}
/* nav */
.nav{position:sticky;top:0;z-index:20;backdrop-filter:saturate(1.4) blur(14px);background:color-mix(in srgb,var(--bg) 84%,transparent);border-bottom:1px solid var(--line)}
.nav .wrap{display:flex;align-items:center;gap:28px;height:64px}
.brand{display:flex;align-items:center;gap:10px;font-family:var(--display);font-weight:700;font-size:17.5px;letter-spacing:-.01em}
.brand i{width:26px;height:26px;border-radius:8px;background:linear-gradient(135deg,var(--accent),var(--accent-2));display:inline-block}
.brand span{color:var(--fg-3);font-weight:500}
.nav ul{display:flex;gap:24px;list-style:none;margin:0 0 0 auto;padding:0;font-family:var(--display);font-size:14px;font-weight:600;color:var(--fg-2)}
.nav li a:hover{color:var(--fg)}
.nav .btn{padding:8px 14px;font-size:13.5px}
@media (max-width:820px){.nav ul{display:none}}
/* hero */
.hero{position:relative;padding-block:clamp(64px,10vw,140px) clamp(48px,7vw,96px);overflow:hidden}
.hero::before{content:"";position:absolute;inset:0;background:var(--glow);pointer-events:none}
.hero::after{content:"";position:absolute;inset:0;background-image:linear-gradient(var(--line) 1px,transparent 1px),linear-gradient(90deg,var(--line) 1px,transparent 1px);background-size:48px 48px;opacity:.35;mask-image:radial-gradient(70% 70% at 50% 40%,#000 20%,transparent 80%);-webkit-mask-image:radial-gradient(70% 70% at 50% 40%,#000 20%,transparent 80%);pointer-events:none}
.hero .wrap{position:relative;display:grid;grid-template-columns:minmax(0,7fr) minmax(0,5fr);gap:clamp(32px,6vw,88px);align-items:center}
.hero h1{font-size:clamp(42px,6.4vw,84px);font-weight:700;max-width:15ch;letter-spacing:-.035em}
.hero h1 em{font-style:normal;background:linear-gradient(90deg,var(--accent),var(--accent-2));-webkit-background-clip:text;background-clip:text;color:transparent}
.hero .lead{margin-top:24px}
.cta{display:flex;flex-wrap:wrap;gap:12px;margin-top:32px}
.hero-aside{display:flex;flex-direction:column;gap:14px}
.evidence{background:var(--bg-2);border:1px solid var(--line);border-radius:var(--radius);padding:22px 24px;box-shadow:var(--shadow)}
.evidence .eyebrow{margin-bottom:12px}
.evidence ol{list-style:none;margin:0;padding:0;display:grid;gap:10px}
.evidence li{display:grid;grid-template-columns:34px 1fr;gap:12px;align-items:start;font-family:var(--display);font-size:14.5px;color:var(--fg-2)}
.evidence li b{display:block;color:var(--fg);font-weight:600}
.evidence li i{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;font-style:normal;font-weight:700;font-size:13px;background:var(--bg-3);color:var(--fg)}
.mosaic{display:grid;grid-template-columns:repeat(7,1fr);gap:8px;padding:4px}
.mosaic img{width:100%;aspect-ratio:296/260;border-radius:22%;box-shadow:var(--shadow);transition:transform .25s}
.mosaic img:hover{transform:scale(1.08)}
@media (max-width:900px){.hero .wrap{grid-template-columns:1fr}}
/* stats */
.stats{border-block:1px solid var(--line);background:var(--bg-2)}
.stats .wrap{display:grid;grid-template-columns:repeat(5,1fr)}
.stat{padding:26px 10px;border-left:1px solid var(--line)} .stat:first-child{border-left:0}
.stat b{display:block;font-family:var(--display);font-size:clamp(28px,3vw,40px);font-weight:700;letter-spacing:-.03em;font-variant-numeric:tabular-nums}
.stat span{font-family:var(--display);font-size:13px;color:var(--fg-3);font-weight:500}
@media (max-width:760px){.stats .wrap{grid-template-columns:1fr 1fr 1fr} .stat{border-left:0;border-top:1px solid var(--line)} .stat:nth-child(-n+3){border-top:0}}
@media (max-width:480px){.stats .wrap{grid-template-columns:1fr 1fr} .stat:nth-child(3){border-top:1px solid var(--line)}}
/* sections */
section.block{padding-block:clamp(64px,8vw,112px)}
.sec-head{display:flex;align-items:end;justify-content:space-between;gap:28px;margin-bottom:40px;flex-wrap:wrap}
.sec-head h2{font-size:clamp(30px,4vw,50px);font-weight:700;margin-top:12px;max-width:20ch}
.sec-head .lead{max-width:42ch}
/* domains */
.domains{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.domain{position:relative;display:flex;flex-direction:column;gap:16px;padding:32px;border-radius:var(--radius);background:var(--bg-2);border:1px solid var(--line);overflow:hidden;transition:transform .2s,box-shadow .2s,border-color .2s}
.domain:hover{transform:translateY(-3px);box-shadow:var(--shadow);border-color:var(--line-2)}
.domain::before{content:"";position:absolute;inset:0 0 auto 0;height:4px;background:var(--dc)}
.domain.teal{--dc:var(--teal);--dbg:var(--teal-bg)} .domain.amber{--dc:var(--amber);--dbg:var(--amber-bg)} .domain.sky{--dc:var(--sky);--dbg:var(--sky-bg)} .domain.rose{--dc:var(--rose);--dbg:var(--rose-bg)}
.domain .head{display:flex;align-items:center;gap:14px}
.domain .glyph{width:48px;height:48px;border-radius:14px;display:grid;place-items:center;font-size:24px;font-family:var(--display);font-weight:700;background:var(--dbg);color:var(--dc)}
.domain .num{font-family:var(--mono);font-size:12.5px;color:var(--fg-3);letter-spacing:.08em}
.domain .name{font-family:var(--display);font-weight:700;font-size:15px;color:var(--fg-2)}
.domain h3{font-size:clamp(23px,2.3vw,30px);font-weight:700;letter-spacing:-.03em}
.domain p.sum{color:var(--fg-2);font-size:15.5px;line-height:1.55}
.artifacts{display:flex;flex-wrap:wrap;gap:8px}
.artifacts a{display:inline-flex;align-items:center;gap:8px;font-family:var(--display);font-size:13px;font-weight:600;padding:7px 12px;border-radius:999px;background:var(--bg-3);border:1px solid transparent;color:var(--fg)}
.artifacts a:hover{border-color:var(--line-2)} .artifacts a span{color:var(--fg-3);font-weight:500}
.domain .foot{margin-top:auto;padding-top:16px;border-top:1px solid var(--line);display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap;font-family:var(--display);font-size:13px;color:var(--fg-3)}
.domain .foot b{color:var(--fg);font-weight:600} .domain .foot .counts{font-variant-numeric:tabular-nums}
.domain .foot .go{color:var(--dc);font-weight:700}
.domain .for{font-family:var(--display);font-size:13px;color:var(--fg-3)} .domain .for b{color:var(--fg-2);font-weight:600}
@media (max-width:860px){.domains{grid-template-columns:1fr}}
/* featured program */
.two{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:40px;align-items:start}
.two>*{min-width:0}
.gateway{background:var(--bg-2);border:1px solid var(--line);border-radius:var(--radius);padding:18px;overflow-x:auto;box-shadow:var(--shadow)}
.gateway svg{max-width:100%;height:auto}
.modlist{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:22px}
.modlist a{display:flex;gap:10px;align-items:center;padding:10px;border-radius:12px;border:1px solid var(--line);background:var(--bg-2);font-family:var(--display);font-size:13px;transition:border-color .15s,transform .15s}
.modlist a:hover{border-color:var(--line-2);transform:translateY(-1px)}
.modlist a img{width:34px;height:30px;border-radius:9px} .modlist a b{display:block;font-weight:600} .modlist a span{color:var(--fg-3);font-size:12px}
@media (max-width:960px){.two{grid-template-columns:1fr}}
@media (max-width:420px){.modlist{grid-template-columns:1fr}}
/* partner */
.partner-band{background:var(--fg);color:var(--bg);border-radius:calc(var(--radius) + 8px);padding:clamp(32px,5vw,64px);position:relative;overflow:hidden}
.partner-band::before{content:"";position:absolute;inset:0;background:radial-gradient(50% 60% at 85% 20%,rgba(167,139,250,.35),transparent 70%),radial-gradient(40% 50% at 10% 90%,rgba(56,189,248,.3),transparent 70%);pointer-events:none}
.partner-band>*{position:relative}
.partner-band .eyebrow{color:color-mix(in srgb,var(--bg) 70%,transparent)}
.partner-band h2{font-size:clamp(30px,4vw,50px);font-weight:700;margin-top:12px;max-width:18ch}
.partner-band .lead{color:color-mix(in srgb,var(--bg) 82%,transparent);margin-top:18px}
.steps{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:40px}
.step{padding:22px;border-radius:16px;background:color-mix(in srgb,var(--bg) 10%,transparent);border:1px solid color-mix(in srgb,var(--bg) 18%,transparent)}
.step i{display:inline-grid;place-items:center;width:30px;height:30px;border-radius:9px;background:var(--bg);color:var(--fg);font-style:normal;font-family:var(--display);font-weight:700;font-size:13px;margin-bottom:14px}
.step b{display:block;font-family:var(--display);font-size:17px;font-weight:700;margin-bottom:6px;letter-spacing:-.01em}
.step p{font-size:14.5px;line-height:1.5;color:color-mix(in srgb,var(--bg) 78%,transparent)}
.partner-band .cta{margin-top:36px}
.partner-band .btn{background:var(--bg);color:var(--fg);border-color:var(--bg)}
.partner-band .btn.ghost{background:transparent;color:var(--bg);border-color:color-mix(in srgb,var(--bg) 40%,transparent)}
@media (max-width:960px){.steps{grid-template-columns:1fr 1fr}} @media (max-width:520px){.steps{grid-template-columns:1fr}}
.promises{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:24px}
.promise{padding:26px;border-radius:var(--radius);background:var(--bg-2);border:1px solid var(--line)}
.promise b{display:block;font-family:var(--display);font-size:18px;font-weight:700;margin-bottom:8px;letter-spacing:-.01em}
.promise p{color:var(--fg-2);font-size:15px;line-height:1.55}
@media (max-width:860px){.promises{grid-template-columns:1fr}}
/* publications */
.filters{display:flex;flex-wrap:wrap;gap:8px}
.chip{font-family:var(--display);font-size:13.5px;font-weight:600;padding:9px 14px;border-radius:999px;border:1px solid var(--line-2);background:var(--bg-2);color:var(--fg-2);cursor:pointer}
.chip[aria-pressed="true"]{background:var(--fg);color:var(--bg);border-color:var(--fg)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:18px}
.card{display:flex;flex-direction:column;gap:12px;padding:24px;border-radius:var(--radius);background:var(--bg-2);border:1px solid var(--line);min-width:0;transition:transform .2s,box-shadow .2s}
.card:hover{transform:translateY(-2px);box-shadow:var(--shadow)}
.card .top{display:flex;align-items:center;gap:12px}
.card .tag{display:inline-flex;align-items:center;gap:8px;font-family:var(--display);font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase}
.card .tag::before{content:"";width:8px;height:8px;border-radius:50%;background:currentColor}
.tag.sky{color:var(--sky)} .tag.teal{color:var(--teal)} .tag.amber{color:var(--amber)} .tag.rose{color:var(--rose)}
.card h3{font-size:18.5px;line-height:1.28;font-weight:600;letter-spacing:-.015em}
.card .impact{color:var(--fg-2);font-size:15px;line-height:1.5}
.card .headline{font-family:var(--mono);font-size:12.5px;color:var(--fg);background:var(--bg-3);padding:8px 10px;border-radius:10px;border-left:3px solid var(--accent)}
.authors{font-family:var(--display);font-size:13px;color:var(--fg-3);line-height:1.5} .authors sup{font-size:9px;margin-left:1px}
.card .meta{font-family:var(--display);font-size:12.5px;color:var(--fg-3)}
.card .links{display:flex;flex-wrap:wrap;gap:8px;margin-top:auto;padding-top:6px}
.pill{font-family:var(--display);font-size:13px;font-weight:600;padding:7px 12px;border-radius:999px;background:var(--bg-3);color:var(--fg);border:1px solid transparent;cursor:pointer}
.pill:hover{border-color:var(--line-2)} .pill.hf{background:#ffe9a8;color:#3a2a00}
.modtile{width:40px;height:36px;border-radius:12px;flex:none}
.grid>*,.domains>*,.partners>*{min-width:0;overflow-wrap:anywhere}
/* collaborators */
.partners{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px}
.partner{padding:28px;border-radius:var(--radius);background:var(--bg-2);border:1px solid var(--line);display:flex;flex-direction:column;gap:10px;transition:transform .2s,box-shadow .2s}
.partner:hover{transform:translateY(-2px);box-shadow:var(--shadow)}
.partner-name{font-family:var(--display);font-weight:700;font-size:21px;letter-spacing:-.015em}
.partner p{color:var(--fg-2);font-size:15px} .partner .link{font-family:var(--display);font-weight:700;color:var(--accent);margin-top:auto}
.insts{display:flex;flex-wrap:wrap;gap:8px;margin-top:26px}
.insts span{font-family:var(--display);font-size:13px;font-weight:500;padding:8px 12px;border-radius:10px;background:var(--bg-2);border:1px solid var(--line);color:var(--fg-2)} .insts sup{color:var(--fg-3)}
/* cite modal */
dialog{border:0;border-radius:var(--radius);padding:0;max-width:min(760px,92vw);background:var(--bg-2);color:var(--fg);box-shadow:var(--shadow)}
dialog::backdrop{background:rgba(5,8,25,.55);backdrop-filter:blur(4px)}
.modal{padding:26px} .modal h3{font-size:18px;margin-bottom:12px}
.modal pre{font-family:var(--mono);font-size:12.5px;line-height:1.55;background:var(--bg-3);padding:16px;border-radius:12px;overflow:auto;max-height:50vh;white-space:pre-wrap}
.modal .row{display:flex;gap:10px;justify-content:flex-end;margin-top:14px}
footer{border-top:1px solid var(--line);padding-block:40px;font-family:var(--display);font-size:13.5px;color:var(--fg-3)}
footer .wrap{display:flex;flex-wrap:wrap;gap:16px;justify-content:space-between}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""

JS = r"""
(function(){
  const D = JSON.parse(document.getElementById('data').textContent);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const affIdx = Object.fromEntries(Object.keys(D.affiliations).map((k,i)=>[k,i+1]));
  const areaOf = Object.fromEntries(D.areas.map(a=>[a.id,a]));
  const plural = (n,w) => `${n} ${w}${n===1?'':'s'}`;
  // hero mosaic
  document.getElementById('mosaic').innerHTML = Object.entries(D.tiles).map(([k,v])=>`<img src="${v}" alt="${k}" title="${k} — ${esc(D.blurbs[k]||'')}">`).join('');
  // domains
  document.getElementById('domain-cards').innerHTML = D.areas.map(a => {
    const arts = a.artifacts.map(([n,k,u])=>`<a href="${u}" ${u.startsWith('#')?'':'target="_blank" rel="noopener"'}>${esc(n)}<span>${esc(k)}</span></a>`).join('');
    const counts = [plural(a.papers,'paper'), a.repos?plural(a.repos,'repo'):null, a.datasets?plural(a.datasets,'dataset'):null].filter(Boolean).join(' · ');
    const partner = a.partner ? `<div class="for">With <b><a href="${a.partner[1]}" target="_blank" rel="noopener">${esc(a.partner[0])}</a></b></div>` : '';
    return `<article class="domain ${a.color}" id="domain-${a.id}">
      <div class="head"><div class="glyph">${a.icon}</div><div><div class="num">DOMAIN ${a.num}</div><div class="name">${esc(a.title)}</div></div></div>
      <h3>${esc(a.question)}</h3>
      <p class="sum">${esc(a.summary)}</p>
      <div class="artifacts">${arts}</div>
      <div class="for">For <b>${esc(a.for)}</b></div>${partner}
      <div class="foot"><span class="counts">${counts}</span><a class="go" href="#publications" data-area="${a.id}">Publications →</a></div>
    </article>`; }).join('');
  // filters + grid
  const filters = document.getElementById('filters'), grid = document.getElementById('paper-grid');
  const all = [{id:'all',title:'All'}].concat(D.areas);
  let current = 'all';
  function authors(p){ return p.authors.map(a => { const s=(p.affils[a]||[]).map(k=>affIdx[k]).filter(Boolean).join(','); return esc(a)+(s?`<sup>${s}</sup>`:''); }).join(', '); }
  function card(p){
    const a = areaOf[p.area]; const tile = p.module && D.tiles[p.module] ? `<img class="modtile" src="${D.tiles[p.module]}" alt="">` : '';
    const head = p.headline ? `<div class="headline">${esc(p.headline)}</div>` : '';
    const links = [`<a class="pill" href="${p.paper_url}" target="_blank" rel="noopener">Paper</a>`,
      p.code_url ? `<a class="pill" href="${p.code_url}" target="_blank" rel="noopener">Code · ${esc(p.code_label)}</a>` : '',
      p.dataset_url ? `<a class="pill hf" href="${p.dataset_url}" target="_blank" rel="noopener">🤗 ${esc(p.dataset_label)}</a>` : '',
      `<button class="pill" data-cite="${esc(p.key)}">Cite</button>`].join('');
    return `<article class="card" data-area="${p.area}"><div class="top">${tile}<span class="tag ${a.color}">${esc(a.short)}${p.module?` · ${esc(p.module)}`:''}</span></div>
      <h3>${esc(p.title)}</h3><p class="impact">${esc(p.module ? p.tagline : p.impact)}</p>${head}
      <div class="authors">${authors(p)}</div><div class="meta">${esc(p.venue)}, ${p.year}${p.haarf?` · HAARF ${esc(p.haarf)}`:''}</div><div class="links">${links}</div></article>`;
  }
  function render(){
    filters.innerHTML = all.map(a=>`<button class="chip" aria-pressed="${a.id===current}" data-f="${a.id}">${esc(a.title)} (${a.id==='all'?D.papers.length:a.papers})</button>`).join('');
    grid.innerHTML = D.papers.filter(p=>current==='all'||p.area===current).map(card).join('');
  }
  render();
  filters.addEventListener('click', e => { const b=e.target.closest('[data-f]'); if(!b) return; current=b.dataset.f; render(); });
  document.addEventListener('click', e => { const el=e.target.closest('a[data-area]'); if(!el) return; current = el.dataset.area; render(); });
  // cite modal
  const dlg = document.getElementById('cite'), pre = document.getElementById('cite-pre'), ttl = document.getElementById('cite-title');
  grid.addEventListener('click', e => { const b=e.target.closest('[data-cite]'); if(!b) return; const p=D.papers.find(x=>x.key===b.dataset.cite); ttl.textContent=p.title; pre.textContent=p.bibtex; dlg.showModal(); });
  document.getElementById('cite-close').onclick = () => dlg.close();
  document.getElementById('cite-copy').onclick = async function(){ try { await navigator.clipboard.writeText(pre.textContent); this.textContent='Copied'; setTimeout(()=>this.textContent='Copy BibTeX',1500); } catch(_){ const r=document.createRange(); r.selectNodeContents(pre); const s=getSelection(); s.removeAllRanges(); s.addRange(r); } };
  // module list
  document.getElementById('modlist').innerHTML = D.papers.filter(p=>p.module).map(p=>`<a href="${p.code_url}" target="_blank" rel="noopener"><img src="${D.tiles[p.module]}" alt=""><div><b>${p.module}</b><span>${esc(D.blurbs[p.module]||'')} · HAARF ${esc(p.haarf)}</span></div></a>`).join('');
  // institutions
  document.getElementById('insts').innerHTML = Object.entries(D.affiliations).map(([k,v],i)=>`<span><sup>${i+1}</sup> ${v.url?`<a href="${v.url}" target="_blank" rel="noopener">${esc(v.name)}</a>`:esc(v.name)}</span>`).join('');
  // gateway diagram
  const dark = matchMedia('(prefers-color-scheme: dark)').matches && document.documentElement.dataset.theme!=='light' || document.documentElement.dataset.theme==='dark';
  if (window.mermaid) {
    mermaid.initialize({startOnLoad:false, theme: dark?'dark':'base', fontFamily:'Inter, sans-serif',
      themeVariables: dark?{}:{primaryColor:'#f1f2f7',primaryBorderColor:'#5b3df5',primaryTextColor:'#0c1024',lineColor:'#6a7190',clusterBkg:'#ffffff',clusterBorder:'#e3e6ef',edgeLabelBackground:'#fbfbfd'}});
    (document.fonts ? document.fonts.ready : Promise.resolve()).then(() => mermaid.render('gw', D.mermaid)).then(r => { document.getElementById('gateway-diagram').innerHTML = r.svg; }).catch(()=>{});
  }
})();
"""

def page():
    st = P["stats"]
    data_json = json.dumps(DATA).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><title>Quome Research</title>
<meta name="description" content="Quome Research partners with health systems, standards bodies and regulated enterprises on verifiable AI. Four problem domains, every paper with its code and data.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap">
<style>{CSS}</style></head><body>

<nav class="nav"><div class="wrap">
  <a class="brand" href="#top"><i></i>Quome <span>Research</span></a>
  <ul><li><a href="#domains">Domains</a></li><li><a href="#program">Programs</a></li><li><a href="#publications">Publications</a></li><li><a href="#collaborators">Collaborators</a></li><li><a href="https://github.com/quome-cloud/research" target="_blank" rel="noopener">GitHub ↗</a></li><li><a class="btn primary" href="#partner">Partner with us</a></li></ul>
</div></nav>

<header class="hero" id="top"><div class="wrap">
  <div>
    <div class="eyebrow">Quome Research · Enterprise research partnerships</div>
    <h1>Research partnerships for AI that <em>has to be right.</em></h1>
    <p class="lead">We work with health systems, standards bodies and regulated enterprises on one question: how do you know an autonomous system did what it was supposed to? Every answer ships as a paper, a repository and a dataset that anyone can run.</p>
    <div class="cta"><a class="btn primary" href="#domains">Explore the domains</a><a class="btn" href="#partner">Partner with us</a></div>
  </div>
  <div class="hero-aside">
    <div class="evidence"><div class="eyebrow">What every result ships with</div>
      <ol>
        <li><i>§</i><div><b>The paper</b>Preprint on arXiv or medRxiv, with per-author affiliations.</div></li>
        <li><i>&lt;/&gt;</i><div><b>The code</b>Apache 2.0, reproducible on local hardware with no paid model keys.</div></li>
        <li><i>⊞</i><div><b>The data</b>Synthetic adversarial datasets on Hugging Face with full data cards.</div></li>
      </ol>
    </div>
    <div class="mosaic" id="mosaic" aria-label="The fourteen healthcare-security modules"></div>
  </div>
</div></header>

<div class="stats"><div class="wrap">
  <div class="stat"><b>{st['papers']}</b><span>papers, every one with code</span></div>
  <div class="stat"><b>{st['repos']}</b><span>open-source repositories</span></div>
  <div class="stat"><b>{st['datasets']}</b><span>datasets on Hugging Face</span></div>
  <div class="stat"><b>{st['authors']}</b><span>co-authors</span></div>
  <div class="stat"><b>{st['institutions']}</b><span>partner institutions</span></div>
</div></div>

<section class="block" id="domains"><div class="wrap">
  <div class="sec-head"><div><div class="eyebrow">Problem domains</div><h2>Four problems. One standard of evidence.</h2></div><p class="lead">Each domain starts from a question a partner has to answer in production, and ends with results that reproduce from a public repository.</p></div>
  <div class="domains" id="domain-cards"></div>
</div></section>

<section class="block" id="program" style="background:var(--bg-3)"><div class="wrap">
  <div class="sec-head"><div><div class="eyebrow c-teal">Featured program · Healthcare AI security</div><h2>One gateway. Fourteen enforcement modules.</h2></div></div>
  <div class="two">
    <div>
      <p class="lead">QUOKKAGUARD is a single Rust gateway, <code>qfire</code>, that sits in front of any OpenAI-compatible model and decides <b>allow</b>, <b>block</b> or <b>escalate</b> for every request and response. Each module is a standalone paper, a layer in the gateway and an adversarial dataset. Together they implement the controls of HAARF, the regulatory framework written with the Task Force for AI Agents in Healthcare.</p>
      <div class="modlist" id="modlist"></div>
    </div>
    <div class="gateway"><div id="gateway-diagram" aria-label="Gateway architecture"></div></div>
  </div>
</div></section>

<section class="block" id="partner"><div class="wrap">
  <div class="partner-band">
    <div class="eyebrow">Enterprise research partnerships</div>
    <h2>Bring us the problem. We publish the evidence.</h2>
    <p class="lead">Partners define the question with their clinicians, security engineers and compliance teams. We build the testbed, red-team it, and publish the result together, in the open.</p>
    <div class="steps">
      <div class="step"><i>1</i><b>Scope the question</b><p>A concrete failure mode in your deployment becomes a research question with a measurable outcome.</p></div>
      <div class="step"><i>2</i><b>Build the testbed</b><p>Open-source harness on local models and synthetic data. No PHI or proprietary data leaves your network.</p></div>
      <div class="step"><i>3</i><b>Red-team it</b><p>An adversarial dataset with a full data card, so the defense is measured against attacks, not assumptions.</p></div>
      <div class="step"><i>4</i><b>Publish together</b><p>Preprint, repository and dataset go public on the same day, with your team as co-authors.</p></div>
    </div>
    <div class="cta"><a class="btn" href="mailto:jim@quome.com?subject=Research%20partnership">Start a conversation</a><a class="btn ghost" href="#collaborators">See who we work with</a></div>
  </div>
  <div class="promises">
    <div class="promise"><b>Open by default</b><p>Code is Apache 2.0 and datasets are on Hugging Face. Partners can audit every number, and so can their regulators.</p></div>
    <div class="promise"><b>Standards, not just papers</b><p>Findings feed HAARF and the Proof-of-Control Standard through open working groups, so a result becomes a control others can adopt.</p></div>
    <div class="promise"><b>Reproducible on your hardware</b><p>Every experiment reruns on local 7B to 120B models with no paid API keys, so a partner can verify it before relying on it.</p></div>
  </div>
</div></section>

<section class="block" id="publications" style="background:var(--bg-3)"><div class="wrap">
  <div class="sec-head"><div><div class="eyebrow">Publications</div><h2>Papers, with the code and data behind them.</h2></div><div class="filters" id="filters" role="group" aria-label="Filter by domain"></div></div>
  <div class="grid" id="paper-grid"></div>
</div></section>

<section class="block" id="collaborators"><div class="wrap">
  <div class="sec-head"><div><div class="eyebrow">Collaborators</div><h2>Built in the open, with the people who have to live with the results.</h2></div></div>
  <div class="partners"><a class="partner" href="https://aihealthagents.org/" target="_blank" rel="noopener"><div class="partner-name">Task Force for AI Agents in Healthcare</div><p>Clinicians, security engineers and regulators defining how autonomous agents are verified before they touch patient care. Home of HAARF.</p><span class="link">Visit →</span></a><a class="partner" href="https://advancedaisociety.org/" target="_blank" rel="noopener"><div class="partner-name">Advanced AI Society</div><p>Steward of the Proof-of-Control Initiative: open standards for verifying what AI agents actually did, in a form anyone can check.</p><span class="link">Visit →</span></a></div>
  <div class="insts" id="insts"></div>
</div></section>

<footer><div class="wrap"><div>© 2026 Quome, Inc. · Apache License 2.0 · Generated {GENERATED}</div><div><a href="mailto:jim@quome.com">jim@quome.com</a> · <a href="https://quome.com" target="_blank" rel="noopener">quome.com</a> · <a href="https://github.com/quome-cloud/research/blob/main/CITATIONS.bib" target="_blank" rel="noopener">CITATIONS.bib</a></div></div></footer>

<dialog id="cite"><div class="modal"><h3 id="cite-title"></h3><pre id="cite-pre"></pre><div class="row"><button class="btn" id="cite-copy">Copy BibTeX</button><button class="btn" id="cite-close">Close</button></div></div></dialog>

<script id="data" type="application/json">{data_json}</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.1/mermaid.min.js"></script>
<script>{JS}</script>
</body></html>
"""

if __name__ == "__main__":
    out = page()
    (ROOT / "docs" / "index.html").write_text(out)
    (ROOT / ".preview" / "index.html").write_text(out)
    print(f"wrote docs/index.html ({len(out):,} bytes), {len(papers)} papers, {len(tiles)} tiles")
