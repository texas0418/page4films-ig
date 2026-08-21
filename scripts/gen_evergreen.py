#!/usr/bin/env python3
"""Generate evergreen filmmaker cards NO. 009-036 into queue/.

Same dossier visual system as gen_batch.py, data-driven. Filmmaker
craft/taste/POV only per Simon's standing rule. Auto-fits headline and
body sizes so nothing crowds the margins.
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
D_CREAM = (240, 236, 228)
D_MUTED = (172, 168, 160)
D_RULE = (70, 68, 64)

BODONI = "/System/Library/Fonts/Supplemental/Bodoni 72.ttc"
AVENIR = "/System/Library/Fonts/Avenir Next.ttc"


def f(path, size, index=0):
    return ImageFont.truetype(path, size, index=index)


def fit(draw, lines, path, index, size):
    """Shrink size until every line fits MAXW."""
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


def crop_marks(draw, ink):
    m, L, w = 64, 34, 3
    for cx, cy, dx, dy in ((m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)):
        draw.line([(cx, cy), (cx + dx * L, cy)], fill=ink, width=w)
        draw.line([(cx, cy), (cx, cy + dy * L)], fill=ink, width=w)


def chrome(draw, kicker, num, dark):
    ink = D_CREAM if dark else INK
    muted = D_MUTED if dark else MUTED
    accent = (196, 74, 74) if dark else RED
    crop_marks(draw, ink)
    kf = f(AVENIR, 27, 2)
    tracked(draw, "PAGE 4 FILMS", 96, kf, ink, tracking=10)
    tracked(draw, kicker, 96, kf, accent, tracking=4, x=112)
    numf = f(AVENIR, 27, 5)
    draw.text((W - 112 - draw.textlength(num, font=numf), 96), num, font=numf, fill=muted)
    draw.ellipse((W / 2 - 5, 153, W / 2 + 5, 163), fill=accent)
    draw.line([(W / 2 - 82, H - 96), (W / 2 + 82, H - 96)], fill=D_RULE if dark else RULE, width=2)
    tracked(draw, "PAGE4FILMS.COM", H - 74, f(AVENIR, 24, 2), muted, tracking=6)


def build(slug, num, kicker, head, bodyl, sub=None, dark=False, caption=""):
    img = Image.new("RGB", (W, H), INK if dark else CREAM)
    draw = ImageDraw.Draw(img)
    chrome(draw, kicker, f"NO. {num:03d}", dark)

    hsize = fit(draw, head, BODONI, 2, 118)
    bsize = fit(draw, bodyl, AVENIR, 5, 54)
    hh = int(hsize * 1.06) * len(head)
    sh = int(64 * 1.2) if sub else 0
    bh = int(bsize * 1.55) * len(bodyl)
    block = hh + (34 + sh if sub else 0) + 44 + 2 + 92 + bh
    y = max(240, (H - block) / 2 - 20)

    hf = f(BODONI, hsize, 2)
    for line in head:
        center(draw, line, y, hf, D_CREAM if dark else INK)
        y += int(hsize * 1.06)
    if sub:
        y += 34
        center(draw, sub, y, f(BODONI, 62, 1), (196, 74, 74) if dark else RED)
        y += sh
    y += 44
    draw.line([(W / 2 - 160, y), (W / 2 + 160, y)], fill=D_RULE if dark else RULE, width=2)
    y += 92
    bf = f(AVENIR, bsize, 5)
    bfill = D_MUTED if dark else (74, 70, 63)
    for line in bodyl:
        center(draw, line, y, bf, bfill)
        y += int(bsize * 1.55)

    out = os.path.join(ROOT, "queue", f"{num:02d}-{slug}")
    os.makedirs(out, exist_ok=True)
    img.save(os.path.join(out, "image.png"))
    with open(os.path.join(out, "caption.txt"), "w") as fh:
        fh.write(caption.strip() + "\n")
    print("built", f"{num:02d}-{slug}")


POSTS = [
    dict(slug="feed-the-crew", kicker="ON SET", head=["Feed the crew", "well."],
         body=["Nobody does their best", "work hungry."],
         caption="Feed the crew well and half your problems never happen. Nobody does their best work hungry. It's the best money on the budget."),
    dict(slug="write-it-badly", kicker="THE PAGE", head=["Write it", "badly first."],
         body=["You can't rewrite", "a blank page."],
         caption="First drafts aren't supposed to be good, they're supposed to exist. Write it badly, then make it better. You can't rewrite a blank page."),
    dict(slug="enter-late", kicker="THE PAGE", head=["Enter late.", "Leave early."],
         body=["The audience", "will keep up."],
         caption="Start the scene as late as you possibly can and get out before it's finished. The audience will keep up. They always do."),
    dict(slug="light-the-room", kicker="CRAFT", head=["Light the room,", "not the face."],
         body=["If the light has a reason,", "the eye believes it."],
         caption="Make the light make sense. If it could come from the window, the lamp or the hallway, the eye believes it. Pretty but unmotivated always reads false."),
    dict(slug="record-the-silence", kicker="SOUND", head=["Record the", "silence."],
         body=["Thirty seconds of room tone", "saves the whole edit."],
         caption="Before you wrap a location, get thirty seconds of everyone standing still. Room tone feels like nothing on the day and saves you in the edit."),
    dict(slug="study-the-failures", kicker="TASTE", head=["Study the", "failures."],
         body=["Bad films teach faster", "than great ones."],
         caption="Great films hide their choices. Bad ones show you exactly where things went wrong, which makes them better teachers. Study the failures."),
    dict(slug="finished-beats-perfect", kicker="POV", dark=True,
         head=["Finished", "beats perfect."],
         body=["A flawed film exists.", "A perfect one doesn't."],
         caption="A flawed film that exists beats a perfect film that doesn't. Finish things. Finished is a skill and you get better at it by doing it."),
    dict(slug="extra-take", kicker="ON SET", head=["Take the", "extra take."],
         body=["It costs two minutes.", "A reshoot costs a day."],
         caption="When you think you have it, take one more. The extra take costs two minutes. The reshoot costs a day you don't have."),
    dict(slug="direct-with-verbs", kicker="DIRECTING", head=["Direct with", "verbs."],
         body=["Nobody can act sadder.", "Anybody can do something."],
         caption="Actors can't play an adjective. Give them a verb instead, something to do to the other person, and watch the scene wake up."),
    dict(slug="call-cut-late", kicker="ON SET", head=["Call cut late."],
         body=["The seconds after the scene", "are often the scene."],
         caption="Don't call cut the second the lines end. Let the take breathe. What people do when they think the scene is over is often the most honest thing you shoot."),
    dict(slug="watch-on-mute", kicker="TASTE", head=["Watch it", "on mute."],
         body=["If the story survives silence,", "the directing works."],
         caption="Watch a film you love with the sound off. If the story still tracks, that's directing. That test never flatters, which is why it's useful."),
    dict(slug="subtext", kicker="THE PAGE", head=["People rarely say", "what they mean."],
         body=["Dialogue is the surface.", "Subtext is the scene."],
         caption="People almost never say what they mean. Write the conversation on the surface and let the real scene run underneath it."),
    dict(slug="scout-the-hour", kicker="PREP", head=["Scout at the hour", "you'll shoot."],
         body=["The light is part", "of the location."],
         caption="Scout the location at the hour you plan to shoot it. The charming morning room can be a cave by four. The light is part of the location."),
    dict(slug="wardrobe", kicker="WARDROBE", head=["Clothes are", "backstory."],
         body=["What a character wears is", "a decision they already made."],
         caption="Wardrobe is backstory you don't have to write. What someone wears is a decision they made before the scene started. Treat it like dialogue."),
    dict(slug="set-dressing", kicker="DESIGN", head=["Rooms tell on", "their people."],
         body=["Set dressing is character work,", "not decoration."],
         caption="Rooms tell on the people who live in them. The dishes, the walls, what's taped to the fridge. Set dressing is character work, not decoration."),
    dict(slug="grade-faces-first", kicker="THE GRADE", head=["Grade faces", "first."],
         body=["The audience knows skin", "better than anything."],
         caption="In the grade, get skin right first. The audience knows faces better than anything else on screen. Once people look human you can push the rest."),
    dict(slug="temp-track", kicker="THE SCORE", head=["Beware the", "temp track."],
         body=["Familiarity always beats", "the new score."],
         caption="Careful with the temp score. You'll hear it a hundred times in the edit, fall in love, and no composer can compete with familiarity."),
    dict(slug="invisible-cut", kicker="THE EDIT", head=["The best cut", "is invisible."],
         body=["If they see the seam,", "they left the story."],
         caption="If the audience notices a cut, they left the story for a second. The best editing is invisible. Flashy is easy, invisible is hard."),
    dict(slug="steal-the-why", kicker="TASTE", head=["Steal the why,", "not the shot."],
         body=["Homage copies.", "Understanding adapts."],
         caption="When a shot stops you, don't copy it. Ask why it worked, then solve your own scene with the same thinking. Steal the why, not the shot."),
    dict(slug="watch-older-films", kicker="TASTE", head=["Watch older", "films."],
         body=["Your problem was solved", "decades ago."],
         caption="Watch older films. Whatever problem you're wrestling with, somebody solved it decades ago with less gear and fewer takes."),
    dict(slug="specific-travels", kicker="POV", dark=True,
         head=["Specific travels.", "General doesn't."],
         body=["The local story is", "the universal one."],
         caption="The more specific a story is, the wider it travels. General is forgettable everywhere. Specific is understood everywhere."),
    dict(slug="learn-every-name", kicker="PEOPLE", head=["Learn every", "name."],
         body=["People work harder for", "someone who knows them."],
         caption="Learn every name on your set by day one, including the PAs. People do their best work for someone who knows who they are."),
    dict(slug="everyone-goes-home", kicker="SAFETY", dark=True,
         head=["No shot is", "worth it."],
         body=["Everyone goes home safe.", "Every day."],
         caption="No shot is worth someone getting hurt. Everyone goes home safe, every day. That's the one rule with no exceptions."),
    dict(slug="festivals-are-rooms", kicker="FESTIVALS", head=["Festivals are rooms,", "not trophies."],
         body=["Go for the people,", "not the laurels."],
         caption="Festivals aren't trophies, they're rooms full of people who love the same thing you do. Go for the conversations. The laurels are a bonus."),
    dict(slug="money-on-screen", kicker="BUDGET", head=["Put the money", "on the screen."],
         body=["Every dollar should show up", "in the frame or the mix."],
         caption="Put the money on the screen. If a dollar doesn't show up in the frame or the mix, ask it what it's doing on the budget."),
    dict(slug="stay-for-credits", kicker="TASTE", head=["Stay for the", "credits."],
         body=["That crawl is", "your next crew."],
         caption="Stay for the credits. Every name on that crawl is someone who might shoot, cut or score your next film. That's the hiring pool."),
    dict(slug="leave-the-monitor", kicker="DIRECTING", head=["Get out from", "behind the monitor."],
         body=["The performance happens", "in the room."],
         caption="Get out from behind the monitor. Watch the actors, not the screen. The performance happens in the room, and the room can tell if you've left it."),
    dict(slug="every-rule", kicker="POV", dark=True,
         head=["Every rule has", "an exception."],
         body=["Including", "this one."],
         caption="Every rule in filmmaking has an exception, including this one. Learn the rules so you know exactly what you're paying when you break them."),
]

for i, p in enumerate(POSTS, start=9):
    build(p["slug"], i, p["kicker"], p["head"], p["body"],
          sub=p.get("sub"), dark=p.get("dark", False), caption=p["caption"])
print("done")
