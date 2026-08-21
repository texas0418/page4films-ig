#!/usr/bin/env python3
"""Generate weekly carousel essays into queue-carousels/.

Multi-slide craft essays in the posted dossier style: cover slide with
page counter and KEEP SWIPING hint, numbered point slides, closer slide.
Queue format: one folder per carousel with slide_1.png..slide_N.png +
caption.txt. Filmmaker craft only per Simon's standing rule.
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1080, 1350
MAXW = 880

CREAM = (245, 239, 228)
INK = (26, 26, 26)
RED = (139, 26, 26)
MUTED = (120, 114, 104)
RULE = (205, 198, 185)
SOFT = (74, 70, 63)

BODONI = "/System/Library/Fonts/Supplemental/Bodoni 72.ttc"
AVENIR = "/System/Library/Fonts/Avenir Next.ttc"


def f(path, size, index=0):
    return ImageFont.truetype(path, size, index=index)


def fit(draw, lines, path, index, size):
    while size > 30:
        fnt = f(path, size, index)
        if max(draw.textlength(t, font=fnt) for t in lines) <= MAXW:
            return size
        size -= 4
    return size


def tracked(draw, text, y, fnt, fill, tracking=8, x=None):
    widths = [draw.textlength(ch, font=fnt) + tracking for ch in text]
    total = sum(widths) - tracking
    cx = (W - total) / 2 if x is None else x
    for ch, w in zip(text, widths):
        draw.text((cx, y), ch, font=fnt, fill=fill)
        cx += w


def center(draw, text, y, fnt, fill):
    draw.text(((W - draw.textlength(text, font=fnt)) / 2, y), text, font=fnt, fill=fill)


def crop_marks(draw):
    m, L, w = 64, 34, 3
    for cx, cy, dx, dy in ((m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)):
        draw.line([(cx, cy), (cx + dx * L, cy)], fill=INK, width=w)
        draw.line([(cx, cy), (cx, cy + dy * L)], fill=INK, width=w)


def chrome(draw, kicker, page, pages, last=False):
    crop_marks(draw)
    kf = f(AVENIR, 27, 2)
    tracked(draw, "PAGE 4 FILMS", 96, kf, INK, tracking=10)
    tracked(draw, kicker, 96, kf, RED, tracking=4, x=112)
    numf = f(AVENIR, 27, 5)
    num = f"{page:02d} / {pages:02d}"
    draw.text((W - 112 - draw.textlength(num, font=numf), 96), num, font=numf, fill=MUTED)
    draw.ellipse((W / 2 - 5, 153, W / 2 + 5, 163), fill=RED)
    draw.line([(W / 2 - 82, H - 96), (W / 2 + 82, H - 96)], fill=RULE, width=2)
    tracked(draw, "PAGE4FILMS.COM", H - 74, f(AVENIR, 24, 2), MUTED, tracking=6)
    if not last:
        tracked(draw, "KEEP SWIPING", H - 74, f(AVENIR, 24, 2), RED, tracking=5, x=112)


def slide_base():
    img = Image.new("RGB", (W, H), CREAM)
    return img, ImageDraw.Draw(img)


def cover(kicker, head, sub, pages):
    img, draw = slide_base()
    chrome(draw, kicker, 1, pages)
    hsize = fit(draw, head, BODONI, 2, 116)
    y = (H - int(hsize * 1.06) * len(head) - 180) / 2
    hf = f(BODONI, hsize, 2)
    for line in head:
        center(draw, line, y, hf, INK)
        y += int(hsize * 1.06)
    y += 30
    center(draw, sub, y, f(BODONI, 58, 1), RED)
    draw.line([(W / 2 - 160, y + 110), (W / 2 + 160, y + 110)], fill=RULE, width=2)
    return img


def point(kicker, n, pages, title, support):
    img, draw = slide_base()
    chrome(draw, kicker, n + 1, pages)
    nf = f(BODONI, 200, 2)
    center(draw, str(n), 300, nf, RED)
    tsize = fit(draw, [title], BODONI, 2, 92)
    center(draw, title, 610, f(BODONI, tsize, 2), INK)
    ssize = fit(draw, support, AVENIR, 5, 48)
    y = 610 + int(tsize * 1.06) + 70
    draw.line([(W / 2 - 160, y - 34), (W / 2 + 160, y - 34)], fill=RULE, width=2)
    y += 26
    sf = f(AVENIR, ssize, 5)
    for line in support:
        center(draw, line, y, sf, SOFT)
        y += int(ssize * 1.5)
    return img


def closer(kicker, pages):
    img, draw = slide_base()
    chrome(draw, kicker, pages, pages, last=True)
    center(draw, "Keep this one.", 480, f(BODONI, 110, 2), INK)
    center(draw, "Save it for the shoot day.", 640, f(BODONI, 56, 1), RED)
    draw.line([(W / 2 - 160, 760), (W / 2 + 160, 760)], fill=RULE, width=2)
    tracked(draw, "FOLLOW @PAGE4FILMS", 830, f(AVENIR, 34, 2), INK, tracking=6)
    center(draw, "New cards Monday, Wednesday and Friday.", 910, f(AVENIR, 38, 5), SOFT)
    return img


def carousel(slug, kicker, head, sub, points, caption):
    pages = len(points) + 2
    out = os.path.join(ROOT, "queue-carousels", slug)
    os.makedirs(out, exist_ok=True)
    slides = [cover(kicker, head, sub, pages)]
    for i, (title, support) in enumerate(points, 1):
        slides.append(point(kicker, i, pages, title, support))
    slides.append(closer(kicker, pages))
    for i, s in enumerate(slides, 1):
        s.save(os.path.join(out, f"slide_{i}.png"))
    with open(os.path.join(out, "caption.txt"), "w") as fh:
        fh.write(caption.strip() + "\n")
    print("built", slug, f"({pages} slides)")


carousel("c01-seven-questions", "PREP",
         ["Seven questions", "before you roll."], "Answer them the night before.",
         [("What is this scene about?", ["One sentence, or the edit", "will ask again."]),
          ("Which shot does it live on?", ["Protect that one", "before anything else."]),
          ("Has the blocking been walked?", ["On the actual floor,", "with the actual actors."]),
          ("What does sound need?", ["Quiet the fridge. Kill the AC.", "Ask before you unplug."]),
          ("Where is the light from?", ["Name the real source", "before you fake it."]),
          ("What is the backup plan?", ["Weather, lost location, sick actor.", "One answer for each."]),
          ("When is lunch?", ["Everyone already knows.", "That's the point."])],
         "The night before checklist we actually use. Seven questions, and if one of them has no answer, tomorrow already has a problem."),

carousel("c02-reads-as-cheap", "CRAFT",
         ["What reads", "as cheap."], "It's never the camera.",
         [("Clipped audio", ["The fastest way", "to lose an audience."]),
          ("Mixed color temps", ["Windows fighting lamps,", "nobody winning."]),
          ("Unmotivated light", ["Pretty with no reason", "reads false."]),
          ("Rushed inserts", ["The cutaway you didn't light", "like the rest of the scene."]),
          ("Empty frame corners", ["Undressed rooms", "tell on the schedule."]),
          ("Safe, wide coverage", ["Fear photographs", "as flatness."])],
         "None of these cost money to fix, which is exactly why they read as cheap when they're ignored. The camera was never the problem."),

carousel("c03-table-read", "THE PAGE",
         ["Run the table read", "like it matters."], "The script gets caught here or on set.",
         [("Cast every part", ["Even the one line roles.", "Don't double the leads."]),
          ("Hand off stage directions", ["Someone else reads them.", "You listen. That's your job."]),
          ("Don't perform, don't direct", ["First reads are for hearing,", "not fixing."]),
          ("Mark the stumbles", ["Where readers trip,", "the writing tripped first."]),
          ("Watch the room", ["Boredom is data.", "So is leaning in."]),
          ("Rewrite within two days", ["While the stumbles", "are still warm."])],
         "A table read isn't a performance, it's an instrument reading. Here's how we run one so the script gets caught before the schedule pays for it."),

carousel("c04-crewing-up", "PEOPLE",
         ["Crewing up on", "a small budget."], "Respect is the currency.",
         [("Say the number early", ["Honesty about money", "is where respect starts."]),
          ("Feed people properly", ["Hot food and real breaks.", "No exceptions."]),
          ("Keep short days short", ["Twelve hours", "means twelve hours."]),
          ("Give real credits", ["And send reel footage fast,", "not eventually."]),
          ("Hire attitude over gear", ["Kits can be rented.", "Calm can't."]),
          ("Call them back", ["The next film", "starts with this crew."])],
         "You can't always pay people what they're worth. You can always be straight with them, feed them well and send the footage fast. How we crew small."),

carousel("c05-location-scout", "LOCATIONS",
         ["Scout like a", "department head."], "The location says yes. Verify it.",
         [("Listen for ten minutes", ["Traffic, planes, that fridge.", "Sound scouts too."]),
          ("Visit at your shoot hour", ["The light you see", "is the light you get."]),
          ("Find the power", ["Circuits, panels,", "and what trips when."]),
          ("Count the bathrooms", ["Crew comfort is", "schedule insurance."]),
          ("Solve parking on paper", ["Ten cars need somewhere", "legal to sit for twelve hours."]),
          ("Get permission in writing", ["A handshake evaporates", "on shoot day."]),
          ("Photograph everything", ["Wides, corners, ceilings.", "Prep remembers for you."])],
         "A location says yes in the afternoon and betrays you at call time. Scout like every department is standing next to you."),

carousel("c06-six-passes", "THE EDIT",
         ["Cut it", "six times."], "One job per pass.",
         [("Story pass", ["Does every scene", "earn its place?"]),
          ("Performance pass", ["Best takes only. Ignore", "the schedule's favorites."]),
          ("Rhythm pass", ["Where does it drag?", "Cut sooner."]),
          ("Sound pass", ["Smooth the seams before", "anyone else hears them."]),
          ("Eyes pass", ["Watch strangers watch it.", "Say nothing."]),
          ("Ego pass", ["Kill what's there for you,", "not for the film."])],
         "The cut goes wrong when one viewing tries to do six jobs at once. One pass, one job, six times through. It's slower and it's faster."),

carousel("c07-rehearsal-week", "DIRECTING",
         ["Rehearse for a week.", "Save a month."], "The cheapest production value there is.",
         [("Read it, then talk", ["Biography, backstory,", "what they want and from whom."]),
          ("Walk the real spaces", ["Or tape the floor", "to match them."]),
          ("Find the verbs", ["What each character does", "to the other one."]),
          ("Let them surprise you", ["The blocking actors invent", "usually beats yours."]),
          ("Lock what works", ["Repeatable beats", "brilliant once."]),
          ("Leave room on the day", ["Rehearsal builds the floor,", "not the ceiling."])],
         "A week of rehearsal is the cheapest production value there is. This is what we try to get done before anyone touches a camera."),

carousel("c08-first-short", "POV",
         ["Your first short,", "honestly."], "None of this is about gear.",
         [("Keep it under ten minutes", ["Festivals program", "short shorts first."]),
          ("One location if you can", ["Company moves", "eat half a day."]),
          ("Spend on sound", ["It's the line between", "student film and cinema."]),
          ("Cast patient people", ["First sets run slow.", "Kindness survives them."]),
          ("Finish it", ["An exported file beats", "a perfect timeline."]),
          ("Then make another", ["The second one is where", "you start improving."])],
         "Everything we'd tell someone about to make their first short film. None of it is about the gear."),

print("done")
