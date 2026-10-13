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

MAX_TAGS = 30          # Meta's hard limit
MAX_CAPTION = 2200     # Meta's hard limit, characters

BASE = ["indiefilm", "filmmaking", "indiefilmmaker", "independentfilm",
        "filmmakerlife", "filmcommunity"]
LOCALE = ["atlantafilm", "georgiafilm"]

# first keyword found in the slug wins
TOPIC = [
    (("sound", "silence"), ["productionsound", "locationsound", "filmsound"]),
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
    (("short", "first"), ["shortfilm", "shortfilmmaker"]),
]
DEFAULT_TOPIC = ["filmproduction", "onset", "setlife"]

# posts that need their own set rather than a keyword match
OVERRIDE = {
    "00-legacy-wrap": ["shortfilm", "behindthescenes", "onset", "filmcrew",
                       "southcarolinafilm", "columbiasc", "setlife",
                       "filmproduction"],
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
    for t in BASE + LOCALE + chosen:          # dedupe, keep order
        if t not in out:
            out.append(t)
    return out[:MAX_TAGS]


def append_to(caption, slug):
    """Caption with its tag block appended, trimmed to Meta's limits."""
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
