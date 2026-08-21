#!/bin/bash
# Push this repo to GitHub one commit at a time.
#
# A single 9MB push dies with "RPC failed; HTTP 408" on a slow link
# (offshore ~265 KB/s). History is deliberately split into small,
# deadline-ordered commits so each push is 0.1-2MB and finishes well
# inside GitHub's timeout.
#
# Safe to re-run: commits already on the remote are skipped, so if the
# connection drops halfway, just run it again to pick up where it left off.

set -u
cd "$(dirname "$0")/.." || exit 1

# HTTP/2 multiplexing is what actually breaks on flaky links; 1.1 is steadier.
git config --local http.version HTTP/1.1
git config --local http.postBuffer 524288000
# Don't abort unless throughput is under 1KB/s for a full minute.
git config --local http.lowSpeedLimit 1000
git config --local http.lowSpeedTime 60

remote_sha=$(git ls-remote origin refs/heads/main 2>/dev/null | cut -f1)

pushed=0
skipped=0
for sha in $(git rev-list --reverse HEAD); do
  subject=$(git log -1 --format=%s "$sha")

  if [ -n "$remote_sha" ] && git merge-base --is-ancestor "$sha" "$remote_sha" 2>/dev/null; then
    echo "  already on GitHub: $subject"
    skipped=$((skipped + 1))
    continue
  fi

  ok=0
  for attempt in 1 2 3 4 5; do
    printf "  pushing (try %d): %s ... " "$attempt" "$subject"
    if git push -q origin "$sha:refs/heads/main" 2>/dev/null; then
      echo "ok"
      ok=1
      pushed=$((pushed + 1))
      break
    fi
    echo "failed"
    sleep $((attempt * 5))
  done

  if [ "$ok" -ne 1 ]; then
    echo
    echo "Stopped at: $subject"
    echo "Everything before this point is safely on GitHub."
    echo "Re-run this script when the connection is better; it resumes here."
    exit 1
  fi
  remote_sha=$sha
done

git branch --set-upstream-to=origin/main main >/dev/null 2>&1
git fetch -q origin main 2>/dev/null

echo
echo "Done. $pushed pushed, $skipped already there."
echo "Repo: https://github.com/texas0418/page4films-ig"
