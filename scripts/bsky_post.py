#!/usr/bin/env python3
"""Post the newest queue-weekly card to Bluesky as @page4films.bsky.social.

Posting only: no likes, follows or replies. The app password lives in
~/.config/page4films-bluesky/env (BSKY_HANDLE, BSKY_APP_PASSWORD), written by Simon.
  bsky_post.py [--dry] [folder]      default folder = newest in queue-weekly/ or posted/ for today
Writes bluesky.json (the post's uri) into the folder so it never posts twice.
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://bsky.social/xrpc/"
LINK = "festivals.page4films.com"


def env():
    vals = {}
    for line in open(os.path.expanduser("~/.config/page4films-bluesky/env")):
        if "=" in line:
            k, v = line.rstrip("\n").split("=", 1)
            vals[k] = v
    return vals


def call(method, path, token=None, body=None, raw=None, ctype="application/json"):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header("Content-Type", ctype)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    return json.load(urllib.request.urlopen(req, timeout=60))


def pick_folder():
    for q in ("queue-weekly", "posted"):
        d = os.path.join(ROOT, q)
        if not os.path.isdir(d):
            continue
        names = sorted(n for n in os.listdir(d) if n.endswith("closing-this-week"))
        if names:
            return os.path.join(d, names[-1])
    sys.exit("no weekly card found")


def main():
    dry = "--dry" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    folder = args[0] if args else pick_folder()
    if os.path.exists(os.path.join(folder, "bluesky.json")):
        print("already on Bluesky:", folder); return
    text = open(os.path.join(folder, "bluesky.txt")).read().strip()
    items = json.load(open(os.path.join(folder, "items.json")))
    alt = "Closing This Week card from the Page 4 Films Festival Calendar: " + "; ".join(
        f"{r['date']} {r['name']} ({r['label'].lower()} deadline)" for r in items["rows"])[:950]
    b = text.encode("utf-8"); i = b.find(LINK.encode())
    facets = [{"index": {"byteStart": i, "byteEnd": i + len(LINK.encode())},
               "features": [{"$type": "app.bsky.richtext.facet#link", "uri": "https://" + LINK}]}] if i >= 0 else []
    print(text, "\n", f"({len(text)} chars, link facet at byte {i})")
    if dry:
        return
    e = env()
    s = call("POST", "com.atproto.server.createSession", body={"identifier": e["BSKY_HANDLE"], "password": e["BSKY_APP_PASSWORD"]})
    img = open(os.path.join(folder, "slide_1.png"), "rb").read()
    blob = call("POST", "com.atproto.repo.uploadBlob", token=s["accessJwt"], raw=img, ctype="image/png")["blob"]
    record = {"$type": "app.bsky.feed.post", "text": text, "facets": facets,
              "createdAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"), "langs": ["en"],
              "embed": {"$type": "app.bsky.embed.images",
                        "images": [{"alt": alt, "image": blob, "aspectRatio": {"width": 1080, "height": 1350}}]}}
    r = call("POST", "com.atproto.repo.createRecord", token=s["accessJwt"],
             body={"repo": s["did"], "collection": "app.bsky.feed.post", "record": record})
    json.dump({"uri": r["uri"], "cid": r["cid"], "at": record["createdAt"]}, open(os.path.join(folder, "bluesky.json"), "w"))
    print("posted", r["uri"])


if __name__ == "__main__":
    main()
