#!/bin/bash
# Grade the agent's final working tree: run the sealed tests, then let Reward Kit score them.
# Harbor copies the submission in as root with the agent's own file modes, so a file the agent
# left 0600 would be unreadable to the grader. Started as root ([verifier] user), this grants
# read on that copy and hands /logs/verifier to the grader; everything that runs submitted code
# runs as the grader, uid 10001. Started as the grader, it runs both steps directly.
set -o pipefail
mkdir -p /logs/verifier
# Fail closed: if grading crashes before score.py writes reward.json, Harbor reads this 0.
echo 0 > /logs/verifier/reward.txt
grader=()
if [ "$(id -u)" -eq 0 ]; then
  artifact=$(python -c 'import json; print(json.load(open("/tests/graded/config.json"))["artifact"])')
  if [ -d "$artifact" ]; then chmod -R a+rX -- "$artifact"; fi
  chown -R 10001:10001 /logs/verifier
  grader=(setpriv --reuid=10001 --regid=10001 --clear-groups env HOME=/home/grader USER=grader)
fi
cd / && "${grader[@]}" python /tests/run_graded.py
exec "${grader[@]}" python /tests/score.py /logs/verifier/reward.json
