#!/usr/bin/env python3
"""Render events.json into events.html and the homepage event cards/banner.
Usage: python3 tools/render_events.py [YYYY-MM-DD]   (date defaults to today, US/Eastern)"""
import datetime, json, re, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
TODAY = datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.date.today()
KINDS = {"meeting": ("General Meeting", "Meeting", "badge-meeting"), "debate": ("Debate", "Debate", "badge-debate"),
         "speaker": ("Speaker", "Speaker", "badge-speaker"), "fireside": ("Speaker", "Fireside Chat", "badge-fireside"),
         "career": ("Career Development", "Career", "badge-career")}
DWS = "Daniel Webster Debate Series"
events = json.load(open(ROOT / "tools" / "events.json", encoding="utf-8"))
for e in events: e["d"] = datetime.date.fromisoformat(e["date"])
# Policy: do not publish events more than one month out unless the owner approved ("approved": true).
CUTOFF = TODAY + datetime.timedelta(days=31)
events = [e for e in events if e["d"] <= CUTOFF or e.get("approved")]

def t12(s):
    h, m = map(int, s.split(":")); return h % 12 or 12, m, "am" if h < 12 else "pm"
def fmt(a, b):
    if not a: return None
    ha, ma, pa = t12(a); sa = f"{ha}:{ma:02d}"
    if not b: return f"{sa} {pa}"
    hb, mb, pb = t12(b); sb = f"{hb}:{mb:02d}"
    return f"{sa} &ndash; {sb} {pb}" if pa == pb else f"{sa} {pa} &ndash; {sb} {pb}"

def row(e):
    d = e["d"]; tl, bt, bc = KINDS[e["kind"]]; time = fmt(e.get("start"), e.get("end"))
    meta = f'<span class="event-type-badge {bc}">{bt}</span>'
    if time: meta += f'\n          <div class="event-row-time">{time}</div>'
    if e.get("loc"): meta += f'\n          <div class="event-row-location">{e["loc"]}</div>'
    return f'''      <div class="event-row" data-date="{e["date"]}">
        <div class="event-row-date">
          <div class="event-row-month">{d.strftime("%b")}</div>
          <div class="event-row-day">{d.day}</div>
          <div class="event-row-weekday">{d.strftime("%a")}</div>
        </div>
        <div class="event-row-body">
          <div class="event-row-type">{tl}</div>
          <div class="event-row-title">{e["title"]}</div>
          <div class="event-row-speaker">{e["sub"]}</div>
        </div>
        <div class="event-row-meta">
          {meta}
        </div>
      </div>
'''
def card(e):
    d = e["d"]; tl = KINDS[e["kind"]][0]
    strong, _, rest = e["sub"].partition(" &middot; ")
    when = " &middot; ".join(x for x in (fmt(e.get("start"), e.get("end")), e.get("loc")) if x)
    td = f'\n            <div class="event-time">{when}</div>' if when else ""
    return f'''        <div class="event-card">
          <div class="event-head">
            <div class="event-date"><div class="event-month">{d.strftime("%b")}</div><div class="event-day">{d.day}</div></div>
            <div class="event-meta"><div class="event-type">{tl}</div><div class="event-name">{e["title"]}</div></div>
          </div>
          <div class="event-body">
            <div class="event-speaker"><strong>{strong}</strong>{rest}</div>{td}
          </div>
        </div>
'''
up = sorted([e for e in events if e["d"] >= TODAY], key=lambda e: (e["d"], e.get("start") or ""))
past = sorted([e for e in events if e["d"] < TODAY], key=lambda e: (e["d"], e.get("start") or ""), reverse=True)

p = ROOT / "events.html"; s = p.read_text(encoding="utf-8")
def swap(s, id_, rows):
    pat = re.compile(r'(<div class="events-list" id="%s">\n).*?(?=^    </div>\n)' % id_, re.S | re.M)
    s, n = pat.subn(lambda m: m.group(1) + rows, s, count=1)
    if n != 1: sys.exit(f"{id_} block not found")
    return s
s = swap(s, "upcoming-list", "".join(row(e) for e in up))
s = swap(s, "past-list", "".join(row(e) for e in past))
p.write_text(s, encoding="utf-8")

p = ROOT / "index.html"; s = p.read_text(encoding="utf-8")
grid = '      <div class="events-grid">\n' + "".join(card(e) for e in up[:3]) + '      </div>\n'
s, n = re.subn(r'      <div class="events-grid">\n.*?\n      </div>\n(?=      <div style="text-align:center; margin-top: 24px;">)', lambda m: grid, s, count=1, flags=re.S)
if n != 1: sys.exit("homepage grid not found")
if up:
    e = up[0]; label = f'{DWS}: {e["sub"].split(" &middot; ")[0]}' if e["kind"] == "debate" else e["title"]
    when = f'{e["d"].strftime("%b")}. {e["d"].day}, {e["d"].year}'
    banner = f'    <p><strong>Next event:</strong> {label} &middot; {when}</p>'
else:
    banner = '    <p><strong>Next event:</strong> Check back soon for upcoming events</p>'
s, n = re.subn(r'    <p><strong>Next event:</strong>.*?</p>', lambda m: banner, s, count=1)
if n != 1: sys.exit("banner not found")
p.write_text(s, encoding="utf-8")
print("upcoming", len(up), "past", len(past))
