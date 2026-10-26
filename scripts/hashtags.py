#!/usr/bin/env python3
"""Hashtag sets for @page4films captions.

Simon's growth plan asks for 10-15 tags per post in three tiers: broad, mid
and specific. It asks for them in the first comment; he chose the caption
instead (2026-10-12), so the publisher never has to make a comment API call
and the standing "publishing only, never touch comments" rule stands.

Meta's own limit for a caption created through the API is 2200 characters,
30 hashtags and 20 @ tags, verified against the IG User Media reference on
2026-10-12. We stay well inside all three.

Tags are resolved from the post's folder name, so existing queued posts pick
them up without any caption.txt being rewritten.
"""

MAX_TAGS = 5           # Instagram's own cap since the Dec 2025 rollout
MAX_CAPTION = 2200     # Meta API limit, characters

# Instagram announced Dec 2025 that captions on posts and reels are limited to
# FIVE hashtags, rolling out gradually, with its own guidance that "using fewer
# (up to 5) more targeted hashtags, rather than many generic ones" performs
# better. Meta's API reference still documents 30; that looks stale, and we
# follow the platform rather than the doc. This supersedes the growth plan's
# "ten to fifteen per post", which predates the change.
#
# Each set is five: three specific to the post, then one craft anchor and one
# locale anchor.
ANCHOR = ["indiefilmmaker", "atlantafilm"]

TOPIC = [
    (("sound", "silence"), ["productionsound", "locationsound", "soundforfilm"]),
    (("edit", "cut", "passes"), ["filmediting", "postproduction", "filmeditor"]),
    (("camera", "lens", "blocking", "light", "haze", "grade"),
     ["cinematography", "cinematographer", "camerawork"]),
    (("casting", "audition", "actor", "verbs", "rehears"),
     ["casting", "actorslife", "acting"]),
    (("location", "scout"), ["locationscout", "filmlocation", "onset"]),
    (("page", "write", "script", "subtext", "story"),
     ["screenwriting", "screenwriter", "scriptwriting"]),
    (("crew", "feed", "people", "monitor"), ["filmcrew", "setlife", "crewlife"]),
    (("festival",), ["filmfestival", "shortfilm", "indiefilmfestival"]),
    (("schedule", "prep", "producing", "budget", "money"),
     ["filmproduction", "preproduction", "producerlife"]),
    (("short", "first"), ["shortfilm", "shortfilmmaker", "indiefilm"]),
]
DEFAULT_TOPIC = ["indiefilm", "filmmaking", "onset"]

OVERRIDE = {
    "00-legacy-wrap": ["shortfilm", "behindthescenes", "southcarolinafilm",
                       "filmcrew", "indiefilmmaker"],
}


def tags_for(slug):
    """Return the tag list for a post folder name."""
    key = slug.lower()
    if key in OVERRIDE:
        chosen = OVERRIDE[key]
    else:
        chosen = DEFAULT_TOPIC
        for keys, tags in TOPIC:
            if any(k in key for k in keys):
                chosen = tags
                break
    out = []
    for t in chosen + ANCHOR:                 # dedupe, keep order
        if t not in out:
            out.append(t)
    return out[:MAX_TAGS]


# Every post points at the festival calendar (Simon, 2026-10-26). Captions are not clickable,
# so the line names the address and sends people to the bio link.
CALENDAR_LINE = "Free film festival and screenplay contest deadline calendar: festivals.page4films.com (link in bio)"


def append_to(caption, slug):
    """Caption with the calendar line and its tag block appended, trimmed to Meta's limits."""
    if "festivals.page4films.com" not in caption:
        caption = caption + "\n\n" + CALENDAR_LINE
    tags = tags_for(slug)
    existing = caption.count("#")
    while tags:
        block = "\n\n" + " ".join("#" + t for t in tags)
        if (len(caption) + len(block) <= MAX_CAPTION
                and existing + len(tags) <= MAX_TAGS):
            return caption + block, len(tags)
        tags.pop()                             # drop the least specific last
    return caption, 0


if __name__ == "__main__":
    import sys
    for s in sys.argv[1:]:
        t = tags_for(s)
        print(f"{s}  ({len(t)})\n  " + " ".join("#" + x for x in t))
