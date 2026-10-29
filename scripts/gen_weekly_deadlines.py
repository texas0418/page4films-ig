#!/usr/bin/env python3
"""Sunday "Closing This Week" post (Simon, 2026-10-28).

Reads the live Festival Calendar data, picks the festivals, contests and funds
with a deadline in the coming week (Sunday to Saturday), and renders a 2-slide
carousel into queue-weekly/: the deadline card, then the Mise card (every post
ends on a Mise card, standing rule). Also writes bluesky.txt for bsky_post.py.

  gen_weekly_deadlines.py [--start YYYY-MM-DD] [--data path/to/festivals.json]
Default start = the coming Sunday (today if today is Sunday).
"""
import json
import os
import subprocess
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_carousels import (W, H, INK, RED, MUTED, RULE, SOFT, BODONI, AVENIR, f, center, tracked,
                           chrome, slide_base, mise_slide)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAL = "festivals.page4films.com"
MAX_ROWS = 7
TYPE = {"festival": "Festival", "contest": "Screenplay contest", "fund": "Fund or lab"}


def load(path):
    if path:
        return json.load(open(path))["festivals"]
    out = subprocess.run(["ssh", "siteground-page4films", "cat www/festivals.page4films.com/public_html/data/festivals.json"],
                         capture_output=True, timeout=120, check=True).stdout
    return json.loads(out)["festivals"]


def week_items(fests, start):
    end = start + timedelta(days=6)
    rows = []
    for f_ in fests:
        if f_.get("type") == "event" or f_.get("estimated") or f_.get("status_note") == "inactive":
            continue
        tiers = [t for t in (f_.get("deadlines") or []) if t.get("date")]
        fin = f_.get("final_deadline")
        if fin and not any(t["date"] == fin for t in tiers):
            tiers.append({"label": "Final", "date": fin, "fee": None})
        hits = sorted((t for t in tiers if start.isoformat() <= t["date"] <= end.isoformat()), key=lambda t: t["date"])
        if not hits:
            continue
        t = hits[0]
        label = (t.get("label") or "Deadline").replace(" deadline", "").replace(" Deadline", "")
        is_final = t["date"] == fin
        rows.append({"name": f_["name"], "date": t["date"], "label": "Final" if is_final else label, "fee": t.get("fee") or "",
                     "type": TYPE.get(f_.get("type"), "Festival"), "oscar": bool(f_.get("oscar")), "bafta": bool(f_.get("bafta")),
                     "final": is_final, "id": f_["id"]})
    # Most useful first when there are too many: final deadlines, then Oscar/BAFTA, then earliest.
    rows.sort(key=lambda r: (r["date"], r["name"].lower()))
    total = len(rows)
    if total > MAX_ROWS:
        # Spread across the week: each day's list ordered Oscar/BAFTA first, then final deadlines,
        # then take one per day in turn until the card is full.
        days = {}
        for r in rows:
            days.setdefault(r["date"], []).append(r)
        for v in days.values():
            v.sort(key=lambda r: (not (r["oscar"] or r["bafta"]), not r["final"], r["name"].lower()))
        pick, order = [], sorted(days)
        while len(pick) < MAX_ROWS and any(days[d] for d in order):
            for d_ in order:
                if days[d_] and len(pick) < MAX_ROWS:
                    pick.append(days[d_].pop(0))
        rows = sorted(pick, key=lambda r: (r["date"], r["name"].lower()))
    return rows, total


def short(draw, text, fnt, width):
    if draw.textlength(text, font=fnt) <= width:
        return text
    while text and draw.textlength(text + "...", font=fnt) > width:
        text = text[:-1]
    return text.rstrip() + "..."


def card(rows, total, start):
    end = start + timedelta(days=6)
    img, draw = slide_base()
    chrome(draw, "THIS WEEK", 1, 2)
    center(draw, "Closing This Week", 205, f(BODONI, 92, 2), INK)
    span = f"{start:%b} {start.day} to {end:%b} {end.day}, {end.year}" if start.month != end.month else f"{start:%B} {start.day} to {end.day}, {end.year}"
    center(draw, span, 318, f(BODONI, 46, 1), RED)
    draw.line([(W / 2 - 160, 392), (W / 2 + 160, 392)], fill=RULE, width=2)
    y, x0, x1 = 430, 112, W - 112
    datef, namef, metaf = f(AVENIR, 30, 2), f(BODONI, 38, 2), f(AVENIR, 26, 5)
    step = 92 if len(rows) > 6 else 104
    for r in rows:
        d = datetime.strptime(r["date"], "%Y-%m-%d")
        draw.text((x0, y + 6), f"{d:%a} {d:%b} {d.day}".upper(), font=datef, fill=RED)
        draw.text((x0 + 210, y), short(draw, r["name"], namef, x1 - x0 - 210), font=namef, fill=INK)
        meta = r["type"] + "  ·  " + r["label"] + (" deadline" if r["label"] != "Final" else " deadline") + (f"  ·  {r['fee']}" if r["fee"] else "")
        if r["oscar"]:
            meta += "  ·  Oscar qualifying"
        draw.text((x0 + 210, y + 50), short(draw, meta, metaf, x1 - x0 - 210), font=metaf, fill=SOFT)
        y += step
    if not rows:
        center(draw, "A quiet week for deadlines.", 600, f(BODONI, 56, 1), INK)
        center(draw, "See what opens next on the calendar.", 690, f(AVENIR, 38, 5), SOFT)
    more = total - len(rows)
    tail = (f"+ {more} more closing this week" if more > 0 else "Every deadline, checked against each festival's own site")
    center(draw, tail, H - 230, f(AVENIR, 30, 5), MUTED)
    tracked(draw, CAL.upper(), H - 170, f(AVENIR, 32, 2), INK, tracking=5)
    return img


def caption(rows, total, start):
    end = start + timedelta(days=6)
    lines = [f"Closing this week, {start:%b} {start.day} to {end:%b} {end.day}:", ""]
    for r in rows:
        d = datetime.strptime(r["date"], "%Y-%m-%d")
        lines.append(f"{d:%a %b} {d.day}: {r['name']} ({r['label'].lower()} deadline{', ' + r['fee'] if r['fee'] else ''})")
    if total > len(rows):
        lines.append(f"Plus {total - len(rows)} more on the calendar.")
    lines += ["", "Confirm dates and fees on each festival's own site before you pay."]
    return "\n".join(lines)


def bluesky_text(rows, total, start):
    end = start + timedelta(days=6)
    head = f"Film festival and screenplay contest deadlines closing this week ({start:%b} {start.day} to {end:%b} {end.day}):"
    body, n = [], 0
    for r in rows:
        d = datetime.strptime(r["date"], "%Y-%m-%d")
        line = f"{d:%a} {r['name']}"
        if len(head) + sum(len(b) + 1 for b in body) + len(line) + 60 > 290:
            break
        body.append(line); n += 1
    more = total - n
    tail = (f"+{more} more. " if more > 0 else "") + f"Free calendar: {CAL}"
    return "\n".join([head] + body + [tail])


def main():
    data = sys.argv[sys.argv.index("--data") + 1] if "--data" in sys.argv else None
    if "--start" in sys.argv:
        start = date.fromisoformat(sys.argv[sys.argv.index("--start") + 1])
    else:
        t = date.today()
        start = t + timedelta(days=(6 - t.weekday()) % 7)  # weekday(): Mon=0 .. Sun=6
    rows, total = week_items(load(data), start)
    slug = f"{start.isoformat()}-closing-this-week"
    d = os.path.join(ROOT, "queue-weekly", slug)
    if os.path.exists(os.path.join(ROOT, "posted")) and any(n.endswith(slug) for n in os.listdir(os.path.join(ROOT, "posted"))):
        print("already posted", slug); return
    os.makedirs(d, exist_ok=True)
    card(rows, total, start).save(os.path.join(d, "slide_1.png"))
    mise_slide(2).save(os.path.join(d, "slide_2.png"))
    open(os.path.join(d, "caption.txt"), "w").write(caption(rows, total, start) + "\n")
    open(os.path.join(d, "bluesky.txt"), "w").write(bluesky_text(rows, total, start) + "\n")
    json.dump({"rows": rows, "total": total, "start": start.isoformat()}, open(os.path.join(d, "items.json"), "w"), indent=1)
    print(d, f"{len(rows)} shown of {total}")


if __name__ == "__main__":
    main()
