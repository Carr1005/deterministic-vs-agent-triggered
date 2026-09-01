#!/usr/bin/env bash
# init.sh — FALLBACK, for copies that arrived without git.
#
# You normally never need this. A cloned copy already has a git repo, and the course
# needs nothing more: the tutor reads `git log` for commits named `round-N tutor|spec|
# build|demo`, and finding none means "the course has not started" (course/PROTOCOL.md).
# So there is no baseline commit to create and no setup step here.
#
# This script exists for the channels where git does not travel — an unzipped download
# or a plain folder copy — because the course records every phase as a commit and needs
# somewhere to put them. Idempotent.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v git >/dev/null 2>&1; then
  echo "FAIL  git not found. The course records each phase as a commit,"
  echo "      so git is required. Install it, then re-run: bash setup/init.sh"
  exit 1
fi

if [ -d .git ] && git rev-parse --quiet --verify HEAD >/dev/null; then
  echo "This copy already has a git repo with history — nothing to do."
  echo "The course starts at Round 1 because no round-N commit exists yet:"
  git log --oneline -3
  exit 0
fi

if [ ! -d .git ]; then
  git init >/dev/null
  git symbolic-ref HEAD refs/heads/main      # same as `git init -b main`, works pre-2.28
fi

# Local-only fallback, so a commit never fails on a machine with no global identity.
git config user.email >/dev/null 2>&1 || git config user.email "learner@snackbot.course"
git config user.name  >/dev/null 2>&1 || git config user.name  "SnackBot Learner"

git add -A
git commit -q -m "course baseline"
echo "Git repo created; the course's starting state is committed."
echo
git log --oneline
echo
echo "Next: open your coding agent in this folder and say:"
echo "    Read COURSE.md and start the course."
