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
from PIL import Image, ImageDraw
from gen_carousels import (W, H, INK, RED, MUTED, RULE, SOFT, CREAM, BODONI, AVENIR, f, center, tracked,
                           chrome, slide_base, mise_slide)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAL = "festivals.page4films.com"
PER_CARD = 7
MAX_CARDS = 9          # Instagram allows 10 slides; the last one is the Mise card
MAX_ROWS = PER_CARD * MAX_CARDS
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
    rows.sort(key=lambda r: (r["date"], not (r["oscar"] or r["bafta"]), not r["final"], r["name"].lower()))
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
        rows = sorted(pick, key=lambda r: (r["date"], not (r["oscar"] or r["bafta"]), not r["final"], r["name"].lower()))
    return rows, total


def short(draw, text, fnt, width):
    if draw.textlength(text, font=fnt) <= width:
        return text
    while text and draw.textlength(text + "...", font=fnt) > width:
        text = text[:-1]
    return text.rstrip() + "..."


GOLD = (242, 177, 36)
PALE = (250, 220, 200)
SOFTPALE = (240, 200, 190)
LINE = (170, 60, 60)


def card(rows, total, start, page=1, pages=2, shown=None):
    """Marquee design (Simon 10-28: the weekly festival post is ALWAYS this design, so it is easy to find)."""
    end = start + timedelta(days=6)
    img = Image.new("RGB", (W, H), RED)
    draw = ImageDraw.Draw(img)
    span = f"{start:%b} {start.day} to {end:%b} {end.day}, {end.year}".upper() if start.month != end.month else f"{start:%b} {start.day} to {end.day}, {end.year}".upper()
    draw.rounded_rectangle((90, 90, W - 90, 330), radius=18, fill=CREAM)
    for x in range(120, W - 100, 36):
        draw.ellipse((x - 6, 104, x + 6, 116), fill=GOLD)
        draw.ellipse((x - 6, 304, x + 6, 316), fill=GOLD)
    center(draw, "NOW CLOSING" if page == 1 else "NOW CLOSING, CONTINUED", 140, f(AVENIR, 30, 2), RED)
    center(draw, "This Week's Deadlines", 185, f(BODONI, 70, 2), INK)
    center(draw, span, 270, f(AVENIR, 26, 2), MUTED)
    num = f"{page:02d} / {pages:02d}"
    nf = f(AVENIR, 24, 5)
    draw.text((W - 110 - draw.textlength(num, font=nf), 352), num, font=nf, fill=PALE)
    y, x0, x1 = 400, 110, W - 110
    datef, namef, metaf = f(AVENIR, 28, 2), f(BODONI, 40, 2), f(AVENIR, 24, 5)
    for r in rows:
        d = datetime.strptime(r["date"], "%Y-%m-%d")
        draw.text((x0, y + 4), f"{d:%a %b} {d.day}".upper(), font=datef, fill=PALE)
        draw.text((x0 + 250, y), short(draw, r["name"], namef, x1 - x0 - 250), font=namef, fill=CREAM)
        meta = ("Final deadline" if r["final"] else r["label"] + " deadline") + (f"  ·  {r['fee']}" if r["fee"] else "")
        if r["oscar"]:
            meta += "  ·  Oscar qualifying"
        elif r["bafta"]:
            meta += "  ·  BAFTA qualifying"
        if r["type"] != "Festival":
            meta = r["type"] + "  ·  " + meta
        draw.text((x0 + 250, y + 50), short(draw, meta, metaf, x1 - x0 - 250), font=metaf, fill=SOFTPALE)
        y += 100
        draw.line([(x0, y - 14), (x1, y - 14)], fill=LINE, width=1)
    if not rows:
        center(draw, "A quiet week for deadlines.", 620, f(BODONI, 56, 1), CREAM)
        center(draw, "See what opens next on the calendar.", 710, f(AVENIR, 36, 5), PALE)
    shown = len(rows) if shown is None else shown
    more = total - shown
    if page < pages - 1:
        tail = "Keep swiping for more deadlines"
    else:
        tail = (f"+ {more} more at {CAL}" if more > 0 else f"Every deadline: {CAL}")
    center(draw, tail, H - 140, f(AVENIR, 30, 5), CREAM)
    tracked(draw, "PAGE 4 FILMS  ·  " + ("SWIPE FOR MORE" if page < pages else "FREE DEADLINE CALENDAR"), H - 90, f(AVENIR, 22, 2), PALE, tracking=6)
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
    for old in os.listdir(d):
        if old.startswith("slide_") and old.endswith(".png"):
            os.remove(os.path.join(d, old))
    chunks = [rows[i:i + PER_CARD] for i in range(0, len(rows), PER_CARD)] or [[]]
    pages = len(chunks) + 1
    for n, chunk in enumerate(chunks, 1):
        card(chunk, total, start, page=n, pages=pages, shown=len(rows)).save(os.path.join(d, f"slide_{n}.png"))
    mise_slide(pages).save(os.path.join(d, f"slide_{pages}.png"))
    open(os.path.join(d, "caption.txt"), "w").write(caption(rows, total, start) + "\n")
    open(os.path.join(d, "bluesky.txt"), "w").write(bluesky_text(rows, total, start) + "\n")
    json.dump({"rows": rows, "total": total, "start": start.isoformat()}, open(os.path.join(d, "items.json"), "w"), indent=1)
    print(d, f"{len(rows)} shown of {total}")


if __name__ == "__main__":
    main()
