#!/usr/bin/env python3
"""Generate weekly typographic reels into queue-reels/.

15.5s 1080x1920 h264 videos in the dossier style: kicker + wordmark,
hook headline, two beat lines, end card with the folded-page logo.
Silent by default; if assets/audio/ holds .mp3/.m4a files, one is mixed
in per reel (royalty-free tracks supplied by Simon only). Instagram
trending audio cannot be attached via the API.

Queue format: queue-reels/<slug>/reel.mp4 + caption.txt
"""
import glob
import os
import random
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1080, 1920
FPS = 30
DUR = 15.5

CREAM = (245, 239, 228)
INK = (26, 26, 26)
RED = (139, 26, 26)
MUTED = (120, 114, 104)
SOFT = (74, 70, 63)

BODONI = "/System/Library/Fonts/Supplemental/Bodoni 72.ttc"
AVENIR = "/System/Library/Fonts/Avenir Next.ttc"
FFMPEG = "/usr/local/bin/ffmpeg"


def f(path, size, index=0):
    return ImageFont.truetype(path, size, index=index)


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def layer(draw_fn):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(img))
    return img


def tracked(draw, text, y, fnt, fill, tracking=8):
    widths = [draw.textlength(ch, font=fnt) + tracking for ch in text]
    total = sum(widths) - tracking
    cx = (W - total) / 2
    for ch, w in zip(text, widths):
        draw.text((cx, y), ch, font=fnt, fill=fill)
        cx += w


def center(draw, text, y, fnt, fill):
    draw.text(((W - draw.textlength(text, font=fnt)) / 2, y), text, font=fnt, fill=fill)


def fit_size(lines, path, index, size, maxw=900):
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    while size > 30:
        fnt = f(path, size, index)
        if max(probe.textlength(t, font=fnt) for t in lines) <= maxw:
            return size
        size -= 4
    return size


GRAIN = [Image.effect_noise((W, H), 14).convert("L") for _ in range(6)]


def build_reel(slug, kicker, hook, beats, caption):
    out = os.path.join(ROOT, "queue-reels", slug)
    os.makedirs(out, exist_ok=True)

    def chrome_fn(d):
        kf = f(AVENIR, 30, 2)
        tracked(d, "PAGE 4 FILMS", 170, kf, INK, tracking=12)
        tracked(d, kicker, 240, f(AVENIR, 27, 2), RED, tracking=6)
        d.ellipse((W / 2 - 5, 300, W / 2 + 5, 310), fill=RED)

    hsize = fit_size(hook, BODONI, 2, 120)
    hy = 640

    def hook_fn(d):
        y = hy
        hf = f(BODONI, hsize, 2)
        for line in hook:
            center(d, line, y, hf, INK)
            y += int(hsize * 1.08)

    def rule_fn(d):
        y = hy + int(hsize * 1.08) * len(hook) + 50
        d.line([(W / 2 - 160, y), (W / 2 + 160, y)], fill=(205, 198, 185), width=3)

    bsize = fit_size(beats, BODONI, 1, 66)
    by = hy + int(hsize * 1.08) * len(hook) + 140

    beat_layers = []
    for i, beat in enumerate(beats):
        def beat_fn(d, beat=beat, i=i):
            center(d, beat, by + i * 110, f(BODONI, bsize, 1), RED if i == len(beats) - 1 else SOFT)
        beat_layers.append(layer(beat_fn))

    def end_fn(d):
        s, cx, cy = 240, W / 2, 760
        x0, y0 = cx - s / 2, cy - s / 2
        fold = 70
        d.rectangle((x0, y0, x0 + s, y0 + s), outline=INK, width=5)
        d.polygon([(x0 + s - fold, y0), (x0 + s, y0 + fold), (x0 + s, y0), ], fill=CREAM)
        d.line([(x0 + s - fold, y0), (x0 + s, y0 + fold)], fill=RED, width=5)
        d.line([(x0 + s - fold, y0), (x0 + s - fold, y0 + fold), (x0 + s, y0 + fold)], fill=INK, width=5)
        d.text((cx - d.textlength("4", font=f(BODONI, 150, 1)) / 2, cy - 60), "4",
               font=f(BODONI, 150, 1), fill=RED)
        tracked(d, "PAGE 4 FILMS", cy + 200, f(AVENIR, 34, 2), INK, tracking=12)
        tracked(d, "@PAGE4FILMS", cy + 270, f(AVENIR, 28, 5), MUTED, tracking=8)

    chrome_l, hook_l, rule_l, end_l = layer(chrome_fn), layer(hook_fn), layer(rule_fn), layer(end_fn)

    # (layer, t_in, fade_dur, drift)
    timeline = [(chrome_l, 0.2, 0.8, 0), (hook_l, 0.9, 1.0, 36), (rule_l, 1.7, 0.8, 0)]
    for i, bl in enumerate(beat_layers):
        timeline.append((bl, 3.6 + i * 3.2, 0.9, 26))
    END_T = 11.8

    n_frames = int(DUR * FPS)
    cmd = [FFMPEG, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-"]
    audio = sorted(glob.glob(os.path.join(ROOT, "assets", "audio", "*.m*")))
    if audio:
        cmd += ["-i", random.choice(audio), "-shortest", "-c:a", "aac", "-b:a", "128k",
                "-af", "volume=0.85,afade=t=in:st=0:d=0.8,afade=t=out:st=13.2:d=2.3"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
            "-movflags", "+faststart", os.path.join(out, "reel.mp4")]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for n in range(n_frames):
        t = n / FPS
        frame = Image.new("RGBA", (W, H), CREAM + (255,))
        if t < END_T:
            fade_out = 1.0 if t < END_T - 0.6 else ease((END_T - t) / 0.6)
            for lyr, t_in, dur, drift in timeline:
                a = ease((t - t_in) / dur) * fade_out
                if a <= 0:
                    continue
                dy = int((1 - ease((t - t_in) / dur)) * drift)
                tmp = lyr if a >= 1 and dy == 0 else None
                if tmp is None:
                    tmp = lyr.copy()
                    if a < 1:
                        tmp.putalpha(tmp.getchannel("A").point(lambda p: int(p * a)))
                frame.alpha_composite(tmp, (0, dy))
        else:
            a = ease((t - END_T) / 0.8)
            tmp = end_l.copy()
            if a < 1:
                tmp.putalpha(tmp.getchannel("A").point(lambda p: int(p * a)))
            frame.alpha_composite(tmp)
            ch = chrome_l.copy()
            frame.alpha_composite(ch)
        g = GRAIN[n % len(GRAIN)]
        frame = Image.composite(Image.new("RGBA", (W, H), (20, 18, 16, 255)), frame,
                                g.point(lambda p: int(max(0, p - 245) * 2.2)))
        proc.stdin.write(frame.convert("RGB").tobytes())

    proc.stdin.close()
    proc.wait()
    with open(os.path.join(out, "caption.txt"), "w") as fh:
        fh.write(caption.strip() + "\n")
    print("built", slug, f"({'scored' if audio else 'silent'})")


REELS = [
    dict(slug="r01-blocking-is-free", kicker="CRAFT",
         hook=["The cheapest", "special effect", "is blocking."],
         beats=["Depth beats dolly moves.", "Move people, not the camera."],
         caption="Blocking is free and it photographs like money. Move the people before you move the camera."),
    dict(slug="r02-first-cut-too-long", kicker="THE EDIT",
         hook=["Your first cut", "is too long."],
         beats=["So was everyone's.", "Cut until it hurts, then once more."],
         caption="Every first cut is too long, including yours, including ours. Keep cutting."),
    dict(slug="r03-tuesday-movie", kicker="THE PAGE",
         hook=["Write the film", "you can shoot", "on a Tuesday."],
         beats=["Two people. One room. Real stakes.", "Scope kills more films than talent."],
         caption="Scope kills more small films than talent ever has. Write something you could shoot on a Tuesday."),
    dict(slug="r04-silence-is-a-sound", kicker="SOUND",
         hook=["Silence is", "a sound."],
         beats=["The pause before the answer", "is the answer."],
         caption="The quietest moment in the scene is usually the loudest. Mix for it."),
    dict(slug="r05-light-the-faces", kicker="CRAFT",
         hook=["The audience", "watches faces."],
         beats=["Light them like they matter.", "Everything else is set dressing."],
         caption="Faces carry the film. Spend your light there first."),
    dict(slug="r06-reveal-the-person", kicker="THE PAGE",
         hook=["Don't explain", "the person.", "Reveal them."],
         beats=["What they do when no one watches.", "That's character."],
         caption="Exposition tells. Behavior reveals. Watch what a character does when nobody's looking."),
    dict(slug="r07-promise-you-can-keep", kicker="POV",
         hook=["A short film", "is a promise", "you can keep."],
         beats=["Small, finished, honest.", "Keep it."],
         caption="You don't need permission to make a short film. You need a weekend and a promise you can keep."),
    dict(slug="r08-shoot-this-weekend", kicker="POV",
         hook=["Shoot something", "this weekend."],
         beats=["Phone counts. Friends count.", "Momentum is the whole game."],
         caption="Nothing teaches faster than footage. Shoot something this weekend, even on a phone."),
]

for r in REELS:
    build_reel(r["slug"], r["kicker"], r["hook"], r["beats"], r["caption"])
print("done")
