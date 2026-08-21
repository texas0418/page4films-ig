#!/usr/bin/env python3
"""Publish the oldest queued post to @page4films via the Instagram API
(Instagram Login flavor, graph.instagram.com — no Facebook anything).

Media staging uses GitHub raw URLs over HTTPS. The previous SiteGround
SSH hop (port 18765) was unreachable from some networks and silently
cost four scheduled slots in August 2026; HTTPS works anywhere the Mac
has internet at all.

Flow: make sure the post's files are on origin/main -> build immutable
raw.githubusercontent.com permalinks pinned to a commit SHA -> create
media container -> poll until ready -> publish -> move the post folder
to posted/ and push that bookkeeping commit.

Publishing only. This script must never touch likes, follows, comments,
or DMs. Captions are reviewed by Simon before they reach a queue.

Also refreshes the long-lived token (60-day) once it is older than 7 days.

Handles three queue formats, detected per folder:
  image.png                  -> single photo post
  slide_1.png..slide_N.png   -> carousel
  reel.mp4                   -> reel

Usage: publish.py [--dry-run] [--queue DIR]   (dry run does everything
except media_publish; nothing appears on the feed. --queue defaults to
queue/; cron passes queue-carousels/ on Tuesdays, queue-reels/ on Sats.)
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT, ".env")
API = "https://graph.instagram.com/v23.0"
RAW_BASE = "https://raw.githubusercontent.com"
BRANCH = "main"
DRY_RUN = "--dry-run" in sys.argv
QUEUE = "queue"
if "--queue" in sys.argv:
    QUEUE = sys.argv[sys.argv.index("--queue") + 1].strip("/")


def log(msg):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def git(*args, check=True):
    return subprocess.run(["git", "-C", ROOT, *args], check=check,
                          capture_output=True, text=True)


def repo_slug():
    """owner/name parsed from the origin remote."""
    url = git("remote", "get-url", "origin").stdout.strip()
    slug = url.split("github.com", 1)[1].lstrip(":/")
    return slug[:-4] if slug.endswith(".git") else slug


def read_env():
    env = {}
    if os.path.exists(ENV_PATH):
        for line in open(ENV_PATH):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def write_env(env):
    with open(ENV_PATH, "w") as fh:
        for k, v in env.items():
            fh.write(f"{k}={v}\n")


def api_get(path, **params):
    qs = urllib.parse.urlencode(params)
    with urllib.request.urlopen(f"{API}/{path}?{qs}", timeout=60) as r:
        return json.load(r)


def api_post(path, **params):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"{API}/{path}", data=data)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def refresh_token_if_due(env):
    today = date.today().isoformat()
    if "IG_TOKEN_REFRESHED_AT" not in env:
        env["IG_TOKEN_REFRESHED_AT"] = today
        write_env(env)
        return env
    age = (date.today() - date.fromisoformat(env["IG_TOKEN_REFRESHED_AT"])).days
    if age < 7:
        return env
    try:
        qs = urllib.parse.urlencode({"grant_type": "ig_refresh_token",
                                     "access_token": env["IG_ACCESS_TOKEN"]})
        with urllib.request.urlopen(
                f"https://graph.instagram.com/refresh_access_token?{qs}",
                timeout=60) as r:
            out = json.load(r)
        env["IG_ACCESS_TOKEN"] = out["access_token"]
        env["IG_TOKEN_REFRESHED_AT"] = today
        write_env(env)
        log("token refreshed")
    except Exception as e:  # keep publishing on the old token; it lasts 60 days
        log(f"token refresh failed (continuing): {e}")
    return env


def next_post():
    """Return (name, kind, repo-relative paths, caption) for the oldest folder."""
    q = os.path.join(ROOT, QUEUE)
    if not os.path.isdir(q):
        return None, None, None, None

    def rel(p):
        return os.path.relpath(p, ROOT)

    for name in sorted(os.listdir(q)):
        d = os.path.join(q, name)
        cap = os.path.join(d, "caption.txt")
        if not (os.path.isdir(d) and os.path.exists(cap)):
            continue
        caption = open(cap).read().strip()
        if os.path.exists(os.path.join(d, "reel.mp4")):
            return name, "reel", [rel(os.path.join(d, "reel.mp4"))], caption
        slides = sorted(glob.glob(os.path.join(d, "slide_*.png")),
                        key=lambda p: int(p.rsplit("_", 1)[1].split(".")[0]))
        if len(slides) >= 2:
            return name, "carousel", [rel(p) for p in slides], caption
        if os.path.exists(os.path.join(d, "image.png")):
            return name, "image", [rel(os.path.join(d, "image.png"))], caption
    return None, None, None, None


def sync(message):
    """Commit and push local state. Returns True on a successful push."""
    git("add", "-A", check=False)
    if git("diff", "--cached", "--quiet", check=False).returncode != 0:
        git("-c", "user.name=Simon Shih",
            "-c", "user.email=sspi.investments@gmail.com",
            "commit", "-qm", message, check=False)
    p = git("push", "origin", BRANCH, check=False)
    if p.returncode != 0:
        tail = p.stderr.strip().splitlines()
        log(f"push failed: {tail[-1] if tail else 'unknown error'}")
        return False
    return True


def remote_sha_with(paths):
    """SHA on origin/<BRANCH> whose tree contains every path, or None."""
    git("fetch", "-q", "origin", BRANCH, check=False)
    r = git("rev-parse", f"origin/{BRANCH}", check=False)
    if r.returncode != 0:
        return None
    sha = r.stdout.strip()
    for p in paths:
        if git("cat-file", "-e", f"{sha}:{p}", check=False).returncode != 0:
            return None
    return sha


def url_ready(url, tries=10, pause=3):
    """raw.githubusercontent.com can lag a second or two behind a push."""
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=30) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(pause)
    return False


def main():
    env = read_env()
    if not env.get("IG_ACCESS_TOKEN"):
        log("no IG_ACCESS_TOKEN in .env; aborting")
        sys.exit(1)
    env = refresh_token_if_due(env)
    token = env["IG_ACCESS_TOKEN"]

    name, kind, paths, caption = next_post()
    if not name:
        log(f"{QUEUE} empty; nothing to publish")
        return
    log(f"publishing {name} [{kind}]" + (" (dry run)" if DRY_RUN else ""))

    me = api_get("me", fields="user_id,username", access_token=token)
    ig_id = me["user_id"]
    if me.get("username") != "page4films":
        log(f"token belongs to @{me.get('username')}, not @page4films; aborting")
        sys.exit(1)

    # Instagram fetches the media itself, so it has to be live on GitHub first.
    sha = remote_sha_with(paths)
    if not sha:
        log("media not on origin yet; pushing")
        sync(f"Queue sync before publishing {name}")
        sha = remote_sha_with(paths)
    if not sha:
        log("ERROR: media is not on GitHub and the push failed. "
            "Run 'git push origin main' in the project, then rerun.")
        sys.exit(1)

    slug = repo_slug()
    urls = [f"{RAW_BASE}/{slug}/{sha}/{urllib.parse.quote(p)}" for p in paths]
    if not url_ready(urls[0]):
        log(f"ERROR: {urls[0]} is not fetchable; aborting before Instagram sees it")
        sys.exit(1)
    log(f"media live at {slug}@{sha[:7]} ({len(urls)} file(s))")

    def wait(cid, tries, pause):
        for _ in range(tries):
            status = api_get(cid, fields="status_code", access_token=token)
            if status.get("status_code") == "FINISHED":
                return
            if status.get("status_code") == "ERROR":
                raise RuntimeError(f"container error: {status}")
            time.sleep(pause)
        raise RuntimeError("container never reached FINISHED")

    if kind == "image":
        cid = api_post(f"{ig_id}/media", image_url=urls[0],
                       caption=caption, access_token=token)["id"]
        wait(cid, 30, 4)
    elif kind == "carousel":
        children = []
        for u in urls:
            children.append(api_post(f"{ig_id}/media", image_url=u,
                                     is_carousel_item="true",
                                     access_token=token)["id"])
        for c in children:
            wait(c, 30, 4)
        cid = api_post(f"{ig_id}/media", media_type="CAROUSEL",
                       children=",".join(children), caption=caption,
                       access_token=token)["id"]
        wait(cid, 30, 4)
    else:  # reel
        cid = api_post(f"{ig_id}/media", media_type="REELS",
                       video_url=urls[0], caption=caption,
                       access_token=token)["id"]
        wait(cid, 60, 10)  # video processing takes longer

    if DRY_RUN:
        log(f"dry run: container {cid} ready; skipping media_publish")
        return

    out = api_post(f"{ig_id}/media_publish", creation_id=cid, access_token=token)
    log(f"published media id {out.get('id')}")
    dest = f"{date.today().isoformat()}-{name}"
    shutil.move(os.path.join(ROOT, QUEUE, name), os.path.join(ROOT, "posted", dest))
    log(f"moved to posted/{dest}")
    sync(f"Published {dest}")


if __name__ == "__main__":
    main()
