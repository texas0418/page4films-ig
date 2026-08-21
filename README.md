# page4films-ig

Content pipeline for the @page4films Instagram account (Page 4 Films, Simon's
film production company). Modeled on the paint-the-town-ig pipeline.

## Layout

- `queue/` — one folder per pending post: `image.png` (1080x1350) + `caption.txt`.
  Simon reviews everything here before it publishes.
- `posted/` — published posts get moved here by the publisher.
- `assets/` — real brand assets copied from
  `~/My Documents/Business/Page 4 Films/Graphics/` (logos, IG profile images).
- `scripts/gen_batch.py` — generates post cards + captions into `queue/`.
- `scripts/publish.py` — (planned) cron publisher via the Instagram Graph API
  content-publishing endpoints. Publishing only; likes, follows, comments and
  DMs are never automated.

## Visual system

Mirrors the account's existing posted style (see
`Graphics/Instagram/_posted/` in the business folder), not an invented one:

- Cream paper `#F5EFE4`, ink `#1A1A1A`, deep red accent `#8B1A1A`
  (sampled from the actual posted slides; website palette also uses gold
  `#C8A96E` but the IG dossier style uses red).
- Bodoni 72 (stand-in for Playfair Display) for headlines, Bodoni 72 Book
  Italic for red sublines, Baskerville for serif body, Avenir Next
  (stand-in for DM Sans) for kickers and body text. All system fonts.
- Dossier chrome: corner crop marks, red pillar kicker top left,
  letterspaced PAGE 4 FILMS wordmark with red dot, NO. counter top right,
  PAGE4FILMS.COM footer.

## Editorial rules

- Current editorial rule (Simon, 2026-08-02): filmmaker craft/taste/POV
  posts ONLY. No project announcements or slate content until there is
  actual news; BTS posts happen when a project is filming. Check the live
  @page4films grid before drafting — don't repeat posted content.
- Cadence: 3 posts per week.
- Captions must read 100% human: proper capitalization and punctuation,
  contractions, one idea per caption, no bullets, no em dashes, no
  marketing adjectives, no assistant-speak, no hashtags in the caption.
- Facts about Page 4 Films come only from Simon and his files, never from
  web or IG search (same-name brands have caused mislabeling).

## Usage

```
.venv/bin/python scripts/gen_batch.py
```

Regenerates the batch into `queue/`. Review images and captions there;
edit the script and rerun to revise.

## Status (2026-08-02): LIVE

- [x] Batch of 8 filmmaker cards approved and queued
- [x] Meta setup: Instagram API with Instagram Login — NO Facebook Page
      (Simon wants zero Facebook presence; nothing may ever post to FB).
      Reuses the "Simon Builds Publisher-IG" Meta app; @page4films added
      as Instagram Tester and connected; long-lived token in gitignored
      `.env` (60 days; publish.py auto-refreshes weekly)
- [x] `scripts/publish.py` — builds a raw.githubusercontent.com permalink
      for the post's media (pinned to a commit SHA, so it can't rot),
      creates the container on graph.instagram.com, publishes, then moves
      the post to `posted/` and pushes that bookkeeping commit.

### Media staging: GitHub raw over HTTPS (changed 2026-08-21)

Instagram fetches media by URL, so the files have to be publicly
readable somewhere. That used to be a temp file scp'd to simonbuilds.app
over SSH on port 18765 — and that port is blocked on some networks
Simon works from, which silently cost four scheduled slots (Aug 11, 12,
14, 17). Nothing was lost, because a failed post stays at the head of
the queue, but the schedule slipped ~4 days.

Now the repo itself is the media host. **This repo must stay public** or
Instagram gets a 404 and the publisher aborts before creating a
container. Publishing needs the media to already be on `origin/main`:
`publish.py` pushes if it isn't, but the reliable path is that queue
content is pushed when it's generated. Everything runs over HTTPS/443.

Safety: the publisher HEAD-checks the raw URL and aborts if it isn't
fetchable, so a bad URL never reaches Instagram. `.env` (the token)
and `assets/audio/` are gitignored — the audio is large and
re-downloadable from Pixabay, and is only needed locally when
generating reels.
- [x] Cron (logs to `logs/publish.log`):
      Mon/Wed/Fri 11:00 cards from `queue/`,
      Tue 11:00 carousels from `queue-carousels/`,
      Sat 11:00 reels from `queue-reels/`,
      Sun 10:30 `replenish.py`.
- [x] Two-week buffer policy (Simon, 2026-08-03): queues hold exactly
      two weeks (6 cards, 2 carousels, 2 reels). Surplus lives in
      `backlog-posts/`, `backlog-carousels/`, `backlog-reels/`;
      `replenish.py` tops queues up every Sunday and warns (log +
      macOS notification) when a backlog can't cover the next top-up.
      BTS/news posts slot in by dropping a folder into `queue/` with a
      low sort name (e.g. `00-bts-...`) — it publishes next.
- [x] `scripts/gen_carousels.py` — multi-slide craft essays
      (cover / numbered points / closer, max 10 slides).
- [x] `scripts/gen_reels.py` — 15.5s typographic reels, 1080x1920.
      Silent by default; drop royalty-free .mp3/.m4a into `assets/audio/`
      and regenerate to score them. IG trending audio is app-only, the
      API can't attach it.
- Token note: Instagram invalidates tokens on password/session changes
  (error code 190). Fix = regenerate in the Meta app dashboard, paste
  into `.env`, delete the IG_TOKEN_REFRESHED_AT line.
