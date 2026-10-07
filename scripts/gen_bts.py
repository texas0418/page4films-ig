#!/usr/bin/env python3
"""Build a behind-the-scenes carousel from unit stills.

The stills are landscape 3:2 and the feed is 4:5, so rather than crop the
photographer's framing away, each frame is letterboxed onto the dossier
card with the usual chrome. Slides are rendered through gen_carousels so
the chrome and the closing Mise card stay identical to every other post.

Output goes to pending-bts/, NOT a publish queue, because publish.py only
reads the directory it is handed. Move the folder into queue/ once Simon
has approved it and the photographer credit is filled in.
"""
import importlib.util
import os

from PIL import Image, ImageCms, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BTS = ("/Users/myfuckingmacbookair/My Documents/Acting/Roles/2026/"
       "Legacy Short Film/BTS")

spec = importlib.util.spec_from_file_location(
    "gen_carousels", os.path.join(ROOT, "scripts", "gen_carousels.py"))
gc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gc)

W, H = gc.W, gc.H
PHOTO_W = 952                      # inside the crop marks, which sit at 64
KICKER = "LEGACY"


def to_srgb(im):
    """Unit stills carry a working profile; convert rather than assume sRGB."""
    icc = im.info.get("icc_profile")
    if icc:
        try:
            import io
            src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            im = ImageCms.profileToProfile(im, src, ImageCms.createProfile("sRGB"),
                                           outputMode="RGB")
        except Exception:
            im = im.convert("RGB")
    return im.convert("RGB")


def photo_slide(path, page, pages, caption):
    img, draw = gc.slide_base()
    gc.chrome(draw, KICKER, page, pages)

    ph = to_srgb(Image.open(path))
    w = PHOTO_W
    h = int(round(ph.size[1] * w / ph.size[0]))
    ph = ph.resize((w, h), Image.LANCZOS)
    x, y = (W - w) // 2, 300
    img.paste(ph, (x, y))
    draw.rectangle((x, y, x + w - 1, y + h - 1), outline=(214, 208, 196), width=2)

    if not caption:
        return img
    cy = y + h + 72
    size = gc.fit(draw, caption, gc.AVENIR, 5, 42)
    fnt = gc.f(gc.AVENIR, size, 5)
    for line in caption:
        gc.center(draw, line, cy, fnt, gc.SOFT)
        cy += int(size * 1.5)
    return img


# (filename, caption lines)
# Captions describe what is in the frame. They do not make claims about the
# film's content: Simon corrected one that did (2026-10-06), and the standing
# rule is that facts about the work come from him, not from inference.
FRAMES = [
    ("260830Legacy_0097.tif", ["The stone house.", "Columbia, South Carolina."]),
    ("260830Legacy_0515.tif", ["Scene 13C, take five.", "August 30."]),
    ("260830Legacy_0021.tif", ["Hair and makeup."]),
    ("260830Legacy_0439.tif", ["Haze going in.", "Light you can see."]),
    ("260830Legacy_0493.tif", ["At the window,", "with the haze still hanging."]),
    ("260930Legacy_1301.tif", []),   # deliberately no caption
]

CAPTION = """
Legacy is shot. Columbia, South Carolina, and it is in post now.

A young father living out of his car takes a job from an aging handyman renovating an empty house, and finds a mentor whose own family is falling apart over what the house is worth.

Written and directed by John Valley.
Produced by David Axe and Simon Shih.
Executive producer Bob Bates.
Stills by Augusta Quirk, @aaaquirk.
"""


def main():
    pages = len(FRAMES) + 2            # cover + frames + Mise
    out = os.path.join(ROOT, "pending-bts", "00-legacy-wrap")
    os.makedirs(out, exist_ok=True)

    slides = [gc.cover(KICKER, ["Shot in", "Columbia."],
                       "Legacy is in post.", pages)]
    for i, (name, cap) in enumerate(FRAMES, start=2):
        slides.append(photo_slide(os.path.join(BTS, name), i, pages, cap))
    slides.append(gc.mise_slide(pages))

    for i, s in enumerate(slides, 1):
        s.save(os.path.join(out, f"slide_{i}.png"))
    cap_path = os.path.join(out, "caption.txt")
    if not os.path.exists(cap_path):
        with open(cap_path, "w") as fh:
            fh.write(CAPTION.strip() + "\n")
    print(f"built {os.path.relpath(out, ROOT)} ({pages} slides)")


if __name__ == "__main__":
    main()
