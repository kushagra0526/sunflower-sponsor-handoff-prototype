"""Router vs keyword list on the dev set and the frozen held-out set, routing examples, reply guard → out/report.html

    python demo.py
"""
from __future__ import annotations

import html
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "data"))

from dev import DEV, REPLIES  # noqa: E402
from heldout import HELDOUT  # noqa: E402

from handoff.detect import RANK, detect, keyword  # noqa: E402
from handoff.guard import check_reply  # noqa: E402
from handoff.route import route  # noqa: E402

CRITICAL = {"EMERGENCY", "CRISIS", "URGENT_MED"}


def evaluate(fn, data) -> dict:
    rows = []
    for text, gold, prof in data:
        got = fn(text, prof)["level"]
        rows.append({"text": text, "gold": gold, "got": got, "profile": prof})
    crit = [r for r in rows if r["gold"] in CRITICAL]
    under = [r for r in crit if RANK[r["got"]] < RANK[r["gold"]]]
    calm = [r for r in rows if r["gold"] not in CRITICAL]
    alarms = [r for r in calm if r["got"] in CRITICAL]
    return {"n": len(rows), "exact": sum(r["got"] == r["gold"] for r in rows), "crit": len(crit), "under": under,
            "calm": len(calm), "alarms": alarms, "wrong": [r for r in rows if r["got"] != r["gold"]]}


def line(name, e):
    return (f"  {name:<9} exact {e['exact']}/{e['n']} · critical caught {e['crit'] - len(e['under'])}/{e['crit']} · "
            f"false alarms {len(e['alarms'])}/{e['calm']}")


def main() -> int:
    res = {}
    for set_name, data in (("dev", DEV), ("held-out", HELDOUT)):
        r, k = evaluate(detect, data), evaluate(keyword, data)
        res[set_name] = (r, k)
        print(f"\n== {set_name} ({len(data)} messages)")
        print(line("router", r))
        print(line("keywords", k))
        for w in r["wrong"]:
            tag = "UNDER-ESCALATED" if RANK[w["got"]] < RANK[w["gold"]] else "over-escalated"
            print(f"    router {tag}: gold {w['gold']}, got {w['got']}: “{w['text']}”")

    now = datetime(2026, 10, 9, 21, 14, tzinfo=timezone.utc)
    examples = [("i don't want to be alive anymore", "n"), ("i cut myself again last night", "p"), ("I think I'm overdosing", "p"),
                ("surgery on friday and they're sending me home with oxycodone", "n"),
                ("3 days no alcohol, i'm shaking so bad and seeing bugs on the wall", ""), ("drank again last night, i really want to get on medication this time", ""),
                ("i'd kill for a cheeseburger right now", "")]
    routed = []
    print("\n== routing")
    for text, prof in examples:
        d = detect(text, prof)
        r = route(d["level"], prof, text, now)
        routed.append((text, prof, d, r))
        print(f"  [{d['level']:<12}] {text}\n      notify: {r['notify']} · shared: {r['shared']['basis'] if r['shared'] else 'nothing'}"
              + (" · AUDIT RECORD" if r["audit"] else ""))

    guard = [(lvl, rep, exp, check_reply(lvl, rep)) for lvl, rep, exp in REPLIES]
    ok = sum(sorted(e) == sorted(g) for _, _, e, g in guard)
    print(f"\n== reply guard: {ok}/{len(guard)} replies flagged exactly as expected")
    for lvl, rep, exp, got in guard:
        if got:
            print(f"  {','.join(got):<28} “{rep}”")
    report(res, routed, guard)
    print("\nreport: out/report.html")
    dev_r = res["dev"][0]
    return 0 if (dev_r["exact"] == dev_r["n"] and ok == len(guard)) else 1


def report(res, routed, guard):
    e = html.escape
    out = HERE / "out"
    out.mkdir(exist_ok=True)

    def card(name, ev, kw):
        def cell(x, good):
            return f"<td class={'g' if good else 'b'}>{x}</td>"
        return (f"<div class=card><h3>{name} · {ev['n']} messages</h3><table><tr><th></th><th>router</th><th>keyword list</th></tr>"
                f"<tr><td>critical messages caught (not under-escalated)</td>{cell(f'{ev['crit'] - len(ev['under'])}/{ev['crit']}', not ev['under'])}"
                f"{cell(f'{kw['crit'] - len(kw['under'])}/{kw['crit']}', not kw['under'])}</tr>"
                f"<tr><td>false alarms on calm messages</td>{cell(f'{len(ev['alarms'])}/{ev['calm']}', len(ev['alarms']) <= 1)}{cell(f'{len(kw['alarms'])}/{kw['calm']}', len(kw['alarms']) <= 1)}</tr>"
                f"<tr><td>exact level</td><td>{ev['exact']}/{ev['n']}</td><td>{kw['exact']}/{kw['n']}</td></tr></table>"
                + ("<p class=sub>Router misses:</p><ul>" + "".join(
                    f"<li><b>{'UNDER' if RANK[w['got']] < RANK[w['gold']] else 'over'}</b> gold {w['gold']} → {w['got']}: “{e(w['text'])}”</li>" for w in ev["wrong"]) + "</ul>"
                   if ev["wrong"] else "<p class=sub>No router misses.</p>") + "</div>")

    rrows = "".join(f"<tr><td><b>{d['level']}</b></td><td>“{e(t)}”</td><td>{ {'n': 'patient, consent', 'p': 'patient, no consent', '': 'app-only'}[p]}</td>"
                    f"<td>{e(r['notify'] or '—')}</td><td>{e(r['shared']['basis']) if r['shared'] else 'nothing'}{' · <b>audit record</b>' if r['audit'] else ''}"
                    f"{' · asks consent' if r['ask_consent'] else ''}</td></tr>" for t, p, d, r in routed)
    grows = "".join(f"<tr><td>{lvl}</td><td>“{e(rep)}”</td><td>{', '.join(got) or '—'}</td><td>{'✓' if sorted(got) == sorted(exp) else '✗'}</td></tr>"
                    for lvl, rep, exp, got in guard)
    (out / "report.html").write_text(f"""<!doctype html><meta charset=utf-8><title>Sponsor handoff</title>
<style>body{{font:14px/1.45 'Segoe UI',system-ui,sans-serif;margin:28px;max-width:1400px;color:#1d1d1f;background:#fafaf8}}h1{{font-size:23px;margin:0}}
h2{{font-size:17px;margin:24px 0 8px}}h3{{margin:0 0 8px;font-size:15px}}.sub{{color:#666}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
.card{{background:#fff;border:1px solid #e5e5e0;border-radius:8px;padding:12px 16px}}table{{border-collapse:collapse;background:#fff}}
td,th{{border-top:1px solid #e5e5e0;padding:5px 10px;text-align:left;vertical-align:top}}.g{{color:#15803d;font-weight:600}}.b{{color:#b91c1c;font-weight:600}}</style>
<h1>AI sponsor → clinic handoff: which messages need a clinician, and what may be shared</h1>
<div class=sub>Invented messages. Labels are mine, not a clinician's. Held-out set committed to git before the router was written, run once.</div>
<h2>Escalation level</h2><div class=grid>{card('Dev set (built on this)', *res['dev'])}{card('Frozen held-out set', *res['held-out'])}</div>
<h2>Routing (42 CFR Part 2 aware)</h2><table><tr><th>level</th><th>message</th><th>user</th><th>notify</th><th>shared</th></tr>{rrows}</table>
<h2>Reply guard on Sam's drafts</h2><table><tr><th>level</th><th>draft reply</th><th>flags</th><th></th></tr>{grows}</table>
<p class=sub>Not a clinical tool. Unofficial prototype by Kushagra Pratap Singh. Not affiliated with Sunflower.</p>""", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
