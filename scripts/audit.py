#!/usr/bin/env python3
"""Pre-flight every unpublished post. Exit 1 if anything would ship wrong.

Checks the things that have actually bitten this pipeline: a missing Mise
card, a carousel over Instagram's 10-slide cap, media that is not on origin
so the raw URL 404s, a caption over the limits, a stale reel generated before
the Mise card existed, and a post sitting in a queue that is already posted.
"""
import glob
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hashtags
from PIL import Image, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUES = ["queue", "queue-carousels", "queue-reels"]
BACKLOGS = ["backlog-posts", "backlog-carousels", "backlog-reels"]
CARD = (1080, 1350)
REEL = (1080, 1920)
REEL_SECONDS = (17.4, 17.9)      # 15.5s body + 2.2s Mise card
BANNED = ["—", "PHOTOGRAPHER_CREDIT", "TODO", "Augusta, G", "Augusta GA"]

problems, warnings, checked = [], [], 0


def bad(where, msg):
    problems.append(f"{where}: {msg}")


def warn(where, msg):
    warnings.append(f"{where}: {msg}")


def git(*a):
    return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True)


def on_origin(relpath, sha):
    return git("cat-file", "-e", f"{sha}:{relpath}").returncode == 0


def slides(d):
    return sorted(glob.glob(os.path.join(d, "slide_*.png")),
                  key=lambda p: int(p.rsplit("_", 1)[1].split(".")[0]))


def mise_reference(pages):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "gc", os.path.join(ROOT, "scripts", "gen_carousels.py"))
    gc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gc)
    return gc.mise_slide(pages)


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return -1.0


def main():
    global checked
    git("fetch", "-q", "origin", "main")
    sha = git("rev-parse", "origin/main").stdout.strip()
    posted = set(re.sub(r"^\d{4}-\d{2}-\d{2}-", "", n) for n in os.listdir(
        os.path.join(ROOT, "posted")))

    endcard = os.path.join(ROOT, "assets", "mise-endcard.png")
    if not os.path.exists(endcard):
        bad("assets", "mise-endcard.png missing; every card post would be held")
    elif not on_origin("assets/mise-endcard.png", sha):
        bad("assets", "mise-endcard.png is not on origin; card posts would 404")

    seen = {}
    for area in QUEUES + BACKLOGS:
        d0 = os.path.join(ROOT, area)
        if not os.path.isdir(d0):
            continue
        for name in sorted(os.listdir(d0)):
            d = os.path.join(d0, name)
            if not os.path.isdir(d):
                continue
            checked += 1
            where = f"{area}/{name}"

            if name in posted:
                bad(where, "already in posted/; it would publish a second time")
            if name in seen:
                bad(where, f"same folder name also in {seen[name]}")
            seen[name] = area

            if os.path.exists(os.path.join(d, "published.json")):
                info = json.load(open(os.path.join(d, "published.json")))
                bad(where, f"carries published.json (id {info.get('id')}); "
                           "it is already live and must be filed, not published")

            cap_path = os.path.join(d, "caption.txt")
            if not os.path.exists(cap_path):
                bad(where, "no caption.txt; publish.py will skip it silently")
                continue
            caption = open(cap_path).read().strip()
            if not caption:
                bad(where, "caption.txt is empty")

            for b in BANNED:
                if b in caption:
                    bad(where, f"caption contains banned text {b!r}")

            tags = hashtags.tags_for(name)
            if len(tags) != hashtags.MAX_TAGS:
                warn(where, f"{len(tags)} tags, expected {hashtags.MAX_TAGS}")
            final, n = hashtags.append_to(caption, name)
            if n == 0:
                bad(where, "no hashtags would be appended")
            if len(final) > hashtags.MAX_CAPTION:
                bad(where, f"caption+tags is {len(final)} chars, over 2200")
            if final.count("#") > hashtags.MAX_TAGS:
                bad(where, f"{final.count('#')} hashtags, over Instagram's "
                           f"{hashtags.MAX_TAGS}")

            reel = os.path.join(d, "reel.mp4")
            sl = slides(d)
            img = os.path.join(d, "image.png")

            if os.path.exists(reel):
                dur = duration(reel)
                if not (REEL_SECONDS[0] <= dur <= REEL_SECONDS[1]):
                    bad(where, f"reel is {dur:.2f}s; expected ~17.7s with the "
                               "Mise card (15.50s means it predates it)")
                with Image.open(reel) if False else open(os.devnull) as _:
                    pass
                r = subprocess.run(["ffprobe", "-v", "error", "-select_streams",
                                    "v:0", "-show_entries", "stream=width,height",
                                    "-of", "csv=p=0:s=x", reel],
                                   capture_output=True, text=True)
                if r.stdout.strip() != f"{REEL[0]}x{REEL[1]}":
                    bad(where, f"reel is {r.stdout.strip()}, expected 1080x1920")
                if not on_origin(os.path.relpath(reel, ROOT), sha):
                    bad(where, "reel.mp4 is not on origin; the raw URL would 404")

            elif len(sl) >= 2:
                if len(sl) > 10:
                    bad(where, f"{len(sl)} slides, over Instagram's 10")
                for p in sl:
                    if Image.open(p).size != CARD:
                        bad(where, f"{os.path.basename(p)} is "
                                   f"{Image.open(p).size}, expected 1080x1350")
                    if not on_origin(os.path.relpath(p, ROOT), sha):
                        bad(where, f"{os.path.basename(p)} is not on origin; "
                                   "the raw URL would 404")
                ref = mise_reference(len(sl)).convert("RGB")
                last = Image.open(sl[-1]).convert("RGB")
                if last.size == ref.size:
                    box = ImageChops.difference(last, ref).getbbox()
                    if box is not None:
                        bad(where, f"last slide is not the Mise card "
                                   f"(differs in {box})")
                else:
                    bad(where, "last slide is the wrong size for the Mise card")

            elif os.path.exists(img):
                if Image.open(img).size != CARD:
                    bad(where, f"image.png is {Image.open(img).size}, "
                               "expected 1080x1350")
                if not on_origin(os.path.relpath(img, ROOT), sha):
                    bad(where, "image.png is not on origin; the raw URL "
                               "would 404")
            else:
                bad(where, "no reel.mp4, no slides, no image.png")

    print(f"audited {checked} unpublished posts against origin/main@{sha[:7]}\n")
    for w in warnings:
        print(f"  WARN  {w}")
    for p in problems:
        print(f"  FAIL  {p}")
    if not problems:
        print("  all clear" if not warnings else "\n  no blocking problems")
    print(f"\n  {len(problems)} failures, {len(warnings)} warnings")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
