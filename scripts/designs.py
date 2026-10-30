"""Rotating card designs for regular @page4films posts (Simon, 2026-10-29).

Four designs, picked by the post number so the rotation is deterministic:
  0 A   Call Sheet, cream paper: production paperwork, ink border and header bar, typewriter labels
  1 A-  Call Sheet reversed, ink page
  2 B   Ticket Stubs, dark page: the headline sits on a cream admit-one stub
  3 B-  Ticket Stubs reversed, cream page with an ink stub
The weekly Closing This Week post is always design C (Marquee) and lives in gen_weekly_deadlines.py.
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
# Projector scheme (Simon picked 10-30): butter paper, navy ink, red accent. No dark pages.
PAPER = (251, 243, 221)
NAVY = (31, 42, 68)
RED = (192, 57, 43)
MUTED = (120, 120, 110)
RULE = (214, 205, 184)
SOFT = (70, 76, 92)
BODONI = "/System/Library/Fonts/Supplemental/Bodoni 72.ttc"
AVENIR = "/System/Library/Fonts/Avenir Next.ttc"
COURIER = "/System/Library/Fonts/Courier.ttc"
NAMES = ["A navy", "A red", "B navy", "B red"]


def f(path, size, index=0):
    return ImageFont.truetype(path, size, index=index)


def pick(num):
    return int(num) % 4


def palette(design):
    """Every page is butter paper. Designs 0 and 2 use navy for the frame or stub, 1 and 3 use red."""
    frame = NAVY if design in (0, 2) else RED
    return dict(bg=PAPER, ink=NAVY, accent=RED if design in (0, 2) else NAVY, body=SOFT, muted=MUTED, rule=RULE,
                frame=frame, panel=frame, panel_ink=PAPER)


def tracked(draw, text, y, fnt, fill, tracking=8, x=None):
    widths = [draw.textlength(ch, font=fnt) + tracking for ch in text]
    total = sum(widths) - tracking
    cx = (W - total) / 2 if x is None else x
    for ch, w in zip(text, widths):
        draw.text((cx, y), ch, font=fnt, fill=fill)
        cx += w


def center(draw, text, y, fnt, fill):
    draw.text(((W - draw.textlength(text, font=fnt)) / 2, y), text, font=fnt, fill=fill)


def page(design):
    p = palette(design)
    img = Image.new("RGB", (W, H), p["bg"])
    return img, ImageDraw.Draw(img), p


def stub(draw, box, fill, bg, perforation_x=None, accent=RED, radius=14):
    """An admit-one stub: rounded panel, half-moon notches on the long sides, optional perforation."""
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=radius, fill=fill)
    cy = (y0 + y1) / 2
    for cx in (x0, x1):
        draw.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), fill=bg)
    if perforation_x:
        for py in range(int(y0 + 14), int(y1 - 14), 14):
            draw.line([(perforation_x, py), (perforation_x, py + 7)], fill=accent, width=2)


def frame(draw, design, kicker, num, last=False, swipe=False):
    """Header and footer for the design. Returns (content_top, content_bottom) in pixels."""
    p = palette(design)
    if design in (0, 1):
        draw.rectangle((60, 60, W - 60, H - 60), outline=p["frame"], width=4)
        draw.rectangle((60, 60, W - 60, 200), fill=p["frame"])
        tracked(draw, "PAGE 4 FILMS", 88, f(AVENIR, 26, 2), p["bg"], tracking=10)
        center(draw, kicker.upper(), 128, f(COURIER, 40, 1), p["bg"])
        row = f(COURIER, 26, 1)
        draw.line([(60, 262), (W - 60, 262)], fill=p["frame"], width=2)
        draw.text((92, 222), f"CARD {num}", font=row, fill=p["accent"])
        right = "PAGE4FILMS.COM"
        draw.text((W - 92 - draw.textlength(right, font=row), 222), right, font=row, fill=p["muted"])
        foot = "KEEP SWIPING" if swipe and not last else "FOLLOW @PAGE4FILMS"
        draw.line([(60, H - 150), (W - 60, H - 150)], fill=p["frame"], width=2)
        center(draw, foot, H - 118, f(COURIER, 26, 1), p["accent"] if swipe and not last else p["muted"])
        return 300, H - 170
    tracked(draw, "PAGE 4 FILMS", 92, f(AVENIR, 26, 2), p["ink"], tracking=10)
    tracked(draw, kicker.upper(), 136, f(AVENIR, 24, 2), p["accent"], tracking=6)
    nf = f(AVENIR, 24, 5)
    draw.text((W - 90 - draw.textlength(num, font=nf), 92), num, font=nf, fill=p["muted"])
    foot = "ADMIT ONE  ·  KEEP SWIPING" if swipe and not last else "ADMIT ONE  ·  PAGE4FILMS.COM"
    tracked(draw, foot, H - 84, f(AVENIR, 22, 2), p["frame"], tracking=5)
    return 220, H - 130


def fit(draw, lines, path, index, size, maxw):
    if not lines:
        return size
    while size > 30:
        fnt = f(path, size, index)
        if max(draw.textlength(t, font=fnt) for t in lines) <= maxw:
            return size
        size -= 4
    return size


def headline_block(draw, design, p, head, sub, body, top, bottom):
    """Headline (+ optional italic sub) and body lines, laid out for the design."""
    if design in (0, 1):
        maxw = 820
        hsize = fit(draw, head, BODONI, 2, 112, maxw)
        bsize = fit(draw, body, AVENIR, 5, 50, maxw)
        ssize = fit(draw, [sub], BODONI, 1, 60, maxw) if sub else 0
        hh = int(hsize * 1.06) * len(head)
        sh = int(ssize * 1.25) if sub else 0
        bh = int(bsize * 1.55) * len(body)
        block = hh + (26 + sh if sub else 0) + 40 + 70 + bh
        y = top + max(0, (bottom - top - block) / 2)
        hf = f(BODONI, hsize, 2)
        for line in head:
            center(draw, line, y, hf, p["ink"]); y += int(hsize * 1.06)
        if sub:
            y += 26; center(draw, sub, y, f(BODONI, ssize, 1), p["accent"]); y += sh
        y += 40
        draw.line([(120, y), (W - 120, y)], fill=p["rule"], width=2)
        y += 70
        bf = f(AVENIR, bsize, 5)
        for line in body:
            center(draw, line, y, bf, p["body"]); y += int(bsize * 1.55)
        return
    # ticket stub: headline centered on the stub, "ADMIT ONE" along the top edge, body under it on the page
    maxw = 760
    hsize = fit(draw, head, BODONI, 2, 104, maxw)
    ssize = fit(draw, [sub], BODONI, 1, 56, maxw) if sub else 0
    sh = int(ssize * 1.25) if sub else 0
    inner = int(hsize * 1.06) * len(head) + (20 + sh if sub else 0)
    stub_h = inner + 190
    bsize = fit(draw, body, AVENIR, 5, 48, 860)
    bh = int(bsize * 1.55) * len(body)
    block = stub_h + 70 + bh
    y0 = top + max(0, (bottom - top - block) / 2)
    box = (90, y0, W - 90, y0 + stub_h)
    stub(draw, box, p["panel"], p["bg"], accent=p["panel_ink"])
    for px in range(110, W - 110, 16):
        draw.line([(px, y0 + 64), (px + 8, y0 + 64)], fill=p["bg"], width=2)
    tracked(draw, "ADMIT ONE", y0 + 28, f(AVENIR, 22, 2), p["panel_ink"], tracking=8)
    y = y0 + 100
    hf = f(BODONI, hsize, 2)
    for line in head:
        center(draw, line, y, hf, p["panel_ink"]); y += int(hsize * 1.06)
    if sub:
        y += 20; center(draw, sub, y, f(BODONI, ssize, 1), p["panel_ink"])
    y = y0 + stub_h + 70
    bf = f(AVENIR, bsize, 5)
    for line in body:
        center(draw, line, y, bf, p["body"]); y += int(bsize * 1.55)
