#!/usr/bin/env python3
"""Generate Page 4 Films IG post images (1080x1350) + captions into queue/.

Visual system mirrors the account's posted dossier style
(Graphics/Instagram/_posted): cream paper, dark ink, deep red accent,
Didone serif headlines, letterspaced sans kickers, corner crop marks.
Palette sampled from the actual posted slides, not invented.

Editorial note (Simon, 2026-08-02): filmmaker craft/taste posts only —
no project announcements until there is actual news; BTS when filming.
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1080, 1350

CREAM = (245, 239, 228)
INK = (26, 26, 26)
RED = (139, 26, 26)
MUTED = (120, 114, 104)
RULE = (205, 198, 185)
# dark-card variants
D_CREAM = (240, 236, 228)
D_MUTED = (172, 168, 160)
D_RULE = (70, 68, 64)

BODONI = "/System/Library/Fonts/Supplemental/Bodoni 72.ttc"      # 0 Book, 1 Book Italic, 2 Bold
BASKERVILLE = "/System/Library/Fonts/Supplemental/Baskerville.ttc"  # 2 Italic
AVENIR = "/System/Library/Fonts/Avenir Next.ttc"                 # 2 Demi, 5 Medium, 7 Regular


def f(path, size, index=0):
    return ImageFont.truetype(path, size, index=index)


def tracked(draw, text, y, fnt, fill, tracking=8, x=None):
    """Letterspaced text; centered when x is None. Returns text width."""
    widths = [draw.textlength(ch, font=fnt) + tracking for ch in text]
    total = sum(widths) - tracking
    cx = (W - total) / 2 if x is None else x
    for ch, w in zip(text, widths):
        draw.text((cx, y), ch, font=fnt, fill=fill)
        cx += w
    return total


def center(draw, text, y, fnt, fill):
    tw = draw.textlength(text, font=fnt)
    draw.text(((W - tw) / 2, y), text, font=fnt, fill=fill)


def crop_marks(draw, ink):
    m, L, w = 64, 34, 3
    for cx, cy, dx, dy in ((m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)):
        draw.line([(cx, cy), (cx + dx * L, cy)], fill=ink, width=w)
        draw.line([(cx, cy), (cx, cy + dy * L)], fill=ink, width=w)


def chrome(draw, kicker, num, dark=False):
    """Header + footer shared by every card."""
    ink = D_CREAM if dark else INK
    muted = D_MUTED if dark else MUTED
    accent = RED if not dark else (196, 74, 74)
    crop_marks(draw, ink)
    kf = f(AVENIR, 27, 2)
    tracked(draw, "PAGE 4 FILMS", 96, kf, ink, tracking=10)
    tracked(draw, kicker, 96, kf, accent, tracking=4, x=112)
    numf = f(AVENIR, 27, 5)
    nw = draw.textlength(num, font=numf)
    draw.text((W - 112 - nw, 96), num, font=numf, fill=muted)
    d = 5
    draw.ellipse((W / 2 - d, 158 - d, W / 2 + d, 158 + d), fill=accent)
    rule = D_RULE if dark else RULE
    draw.line([(W / 2 - 82, H - 96), (W / 2 + 82, H - 96)], fill=rule, width=2)
    tracked(draw, "PAGE4FILMS.COM", H - 74, f(AVENIR, 24, 2), muted, tracking=6)


def headline(draw, lines, y, size, fill=INK, leading=1.06):
    fnt = f(BODONI, size, 2)
    for line in lines:
        center(draw, line, y, fnt, fill)
        y += int(size * leading)
    return y


def sub_italic(draw, text, y, size=52, fill=RED):
    center(draw, text, y, f(BODONI, size, 1), fill)
    return y + int(size * 1.2)


def divider(draw, y, dark=False):
    draw.line([(W / 2 - 160, y), (W / 2 + 160, y)], fill=D_RULE if dark else RULE, width=2)
    return y + 2


def body(draw, lines, y, size=52, fill=None, dark=False, leading=1.55):
    fill = fill or (D_MUTED if dark else (74, 70, 63))
    fnt = f(AVENIR, size, 5)
    for line in lines:
        center(draw, line, y, fnt, fill)
        y += int(size * leading)
    return y


def card(name, caption, build, dark=False):
    img = Image.new("RGB", (W, H), INK if dark else CREAM)
    draw = ImageDraw.Draw(img)
    build(img, draw)
    out = os.path.join(ROOT, "queue", name)
    os.makedirs(out, exist_ok=True)
    img.save(os.path.join(out, "image.png"))
    with open(os.path.join(out, "caption.txt"), "w") as fh:
        fh.write(caption.strip() + "\n")
    print("built", name)


# ---- 01 taste: watch it twice ----
def p1(img, draw):
    chrome(draw, "TASTE", "NO. 001")
    y = headline(draw, ["Watch it twice."], 430, 126)
    y = sub_italic(draw, "Once for the story.", y + 34, 62)
    y = sub_italic(draw, "Once for the seams.", y - 10, 62)
    divider(draw, y + 40)
    body(draw, ["The second viewing is", "the real film school."], y + 88, 54)


# ---- 02 craft: sound ----
def p2(img, draw):
    chrome(draw, "CRAFT", "NO. 002")
    y = headline(draw, ["Sound is half", "the picture."], 400, 118)
    divider(draw, y + 44)
    body(draw, ["Audiences forgive a soft shot.", "They never forgive bad audio."], y + 94, 54)


# ---- 03 casting ----
def p3(img, draw):
    chrome(draw, "CASTING", "NO. 003")
    y = headline(draw, ["Cast the person,", "not the reel."], 390, 110)
    divider(draw, y + 42)
    body(draw, ["The reel shows range.", "The room shows truth."], y + 92, 54)


# ---- 04 locations ----
def p4(img, draw):
    chrome(draw, "LOCATIONS", "NO. 004")
    y = headline(draw, ["The location is", "a character."], 390, 112)
    divider(draw, y + 42)
    body(draw, ["On a small film, write toward", "the rooms you can actually get."], y + 92, 52)


# ---- 05 audience note, dark card ----
def p5(img, draw):
    chrome(draw, "AUDIENCE", "NO. 005", dark=True)
    y = headline(draw, ["Small and warm", "beats big", "and cold."], 400, 116, fill=D_CREAM)
    divider(draw, y + 44, dark=True)
    body(draw, ["The audience we want", "shows up for the work."], y + 92, 54, dark=True)


# ---- 06 on set: rehearsal ----
def p6(img, draw):
    chrome(draw, "ON SET", "NO. 006")
    y = headline(draw, ["Shoot the", "rehearsal."], 400, 122)
    divider(draw, y + 44)
    body(draw, ["Some of the best takes happen", "before anyone says action."], y + 94, 52)


# ---- 07 the edit ----
def p7(img, draw):
    chrome(draw, "THE EDIT", "NO. 007")
    y = headline(draw, ["The edit is", "the last rewrite."], 390, 110)
    divider(draw, y + 42)
    body(draw, ["The script gets three drafts.", "The cut gets thirty."], y + 92, 54)


# ---- 08 blocking, dark card ----
def p8(img, draw):
    chrome(draw, "BLOCKING", "NO. 008", dark=True)
    y = headline(draw, ["Blocking is", "the shot list."], 410, 116, fill=D_CREAM)
    divider(draw, y + 44, dark=True)
    body(draw, ["Move the actors before", "you move the camera."], y + 92, 54, dark=True)


card("01-watch-it-twice", """
Any film that works deserves two viewings. The first is for the story, the second is for the seams. The second watch is the real film school.
""", p1)

card("02-sound", """
The cheapest upgrade on any small film is sound. Audiences will forgive a soft shot but they won't sit through bad audio. Budget for it like it's the camera.
""", p2)

card("03-casting", """
A reel shows you what an actor did with someone else's material. The room shows you what they'll do with yours. Trust the room.
""", p3)

card("04-locations", """
On a microbudget the location list is the real first draft. Write toward the rooms you can actually get and the film gets better, not smaller.
""", p4)

card("05-audience-note", """
We'd rather reach two hundred people who genuinely care about independent film than ten thousand who scroll past. Small and warm beats big and cold.
""", p5, dark=True)

card("06-shoot-the-rehearsal", """
Some of the best takes happen before anyone says action. Roll the rehearsal. You can always cut it, but you can't go back and catch it.
""", p6)

card("07-the-edit", """
Nobody ever sees the script. They see the cut. Treat the edit like the last rewrite of the film, because that's exactly what it is.
""", p7)

card("08-blocking", """
Get the blocking right and the shot list writes itself. Get it wrong and no amount of coverage will save the scene.
""", p8, dark=True)

print("done")
