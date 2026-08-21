#!/usr/bin/env python3
"""Keep the publish queues topped up to a two-week buffer.

Runs Sunday via cron. Moves the oldest folders from backlog-* into the
matching queue until each queue holds two weeks of content:
  queue/           6 posts   (Mon/Wed/Fri)
  queue-carousels/ 2 posts   (Tue)
  queue-reels/     2 posts   (Sat)

Warns (log + best-effort macOS notification) when a backlog can't cover
the NEXT top-up, so new content gets generated before the well runs dry.
Never generates or publishes anything itself.
"""
import os
import shutil
import subprocess
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = [("queue", "backlog-posts", 6),
           ("queue-carousels", "backlog-carousels", 2),
           ("queue-reels", "backlog-reels", 2)]


def log(msg):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] replenish: {msg}", flush=True)


def folders(path):
    p = os.path.join(ROOT, path)
    if not os.path.isdir(p):
        return []
    return sorted(d for d in os.listdir(p)
                  if os.path.isdir(os.path.join(p, d)) and not d.startswith("."))


def notify(text):
    try:
        subprocess.run(["osascript", "-e",
                        f'display notification "{text}" with title "page4films-ig"'],
                       check=False, capture_output=True, timeout=10)
    except Exception:
        pass


low = []
for queue, backlog, target in TARGETS:
    have = folders(queue)
    need = target - len(have)
    pool = folders(backlog)
    for name in pool[:max(0, need)]:
        shutil.move(os.path.join(ROOT, backlog, name),
                    os.path.join(ROOT, queue, name))
        log(f"{backlog}/{name} -> {queue}/")
    remaining = len(folders(backlog))
    log(f"{queue}: {len(folders(queue))}/{target} queued, {remaining} in {backlog}")
    if remaining < target:
        low.append(f"{backlog} down to {remaining}")

if low:
    msg = "; ".join(low) + " — time to generate a new batch"
    log("LOW BACKLOG: " + msg)
    notify(msg)
