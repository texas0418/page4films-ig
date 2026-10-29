#!/bin/zsh
# Sunday "Closing This Week": publish today's pre-generated card to Instagram, then Bluesky.
# Cards are generated ahead (gen_weekly_deadlines.py) and pushed in a session, because cron cannot git push.
ROOT="/Users/myfuckingmacbookair/Documents/GitHub/page4films-ig"
PY="$ROOT/.venv/bin/python"
TODAY=$(date +%Y-%m-%d)
cd "$ROOT" || exit 1
mkdir -p posted/skipped-weekly
# A card for a past week must never post late.
for d in queue-weekly/*-closing-this-week(N); do
  start=${${d:t}[1,10]}
  [[ "$start" < "$TODAY" ]] && mv "$d" posted/skipped-weekly/ && echo "skipped stale $d"
done
F="queue-weekly/${TODAY}-closing-this-week"
if [[ ! -d "$F" ]]; then echo "no weekly card for $TODAY"; exit 0; fi
"$PY" scripts/publish.py --queue queue-weekly ${@}
P=$(ls -d posted/*"${TODAY}-closing-this-week" 2>/dev/null | head -1)
[[ -n "$P" ]] && "$PY" scripts/bsky_post.py "$P"
exit 0
