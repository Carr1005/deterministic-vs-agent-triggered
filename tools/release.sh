#!/usr/bin/env bash
# release.sh — AUTHOR TOOL. Publish the current `main` as a single-commit `release`.
#
# Why two branches:
#   main      ordinary authoring history. Never rewritten, so a collaborator can pull
#             safely and revert points survive.
#   release   rebuilt from scratch as ONE commit every time you share, and set as the
#             repository's default branch so a plain `git clone` gets it. A learner's
#             `git log` then reads as the course rather than as your changelog.
#
# Force-pushing `release` is safe by construction: nobody keeps a long-lived clone of it,
# because README tells learners to take a fresh copy per run. Never force-push `main`.
#
# The commit is built with `git commit-tree` from main's committed tree, NOT by checking
# out an orphan branch and running `git add -A`. That distinction matters: `add -A` would
# sweep in whatever is untracked at the time — interim-docs/trial-2/ is ~930 KB of session
# log sitting there right now — whereas commit-tree cannot see the working directory at all.
set -u
cd "$(dirname "$0")/.."

BRANCH="release"
MSG="SnackBot — an interactive course on who invokes each agent-memory operation"

fail() { echo "FAIL  $1"; exit 1; }

# --- refuse unless we are somewhere sane -----------------------------------------
[ -d .git ] || fail "not a git repository."
cur="$(git branch --show-current)"
[ "$cur" = "main" ] || fail "on branch '$cur'; run this from main (the authoring branch)."
[ -z "$(git status --porcelain)" ] || {
  echo "NOTE  uncommitted or untracked files present:"
  git status --short | sed 's/^/      /'
  echo "      commit-tree ignores them, so the release is built from main's committed"
  echo "      tree regardless. Continuing."
}
git remote get-url origin >/dev/null 2>&1 || fail "no 'origin' remote to publish to."

# --- the share gate, wired in so it stops the release ----------------------------
echo "== share gate"
bash setup/pristine.sh || fail "pristine.sh refused this tree — do not publish it."

# --- build the single commit from main's committed tree ---------------------------
echo
echo "== building $BRANCH"
tree="$(git rev-parse "main^{tree}")" || fail "cannot resolve main's tree."
commit="$(git commit-tree "$tree" -m "$MSG")" || fail "commit-tree failed."
git branch -f "$BRANCH" "$commit" >/dev/null
echo "PASS  $BRANCH = $(git rev-parse --short "$commit") (one commit, no parent)"

# main's tree and the release tree must be byte-identical
if [ -n "$(git diff "main" "$BRANCH")" ]; then
  git diff --stat main "$BRANCH" | sed 's/^/      /'
  fail "$BRANCH does not match main's tree."
fi
echo "PASS  tree matches main exactly"
n="$(git log --oneline "$BRANCH" | wc -l | tr -d ' ')"
[ "$n" = 1 ] || fail "$BRANCH has $n commits, expected 1."
echo "PASS  history is exactly one commit"

# --- publish ----------------------------------------------------------------------
echo
echo "== publishing"
git push -f -q origin "$BRANCH" || fail "push failed."
echo "PASS  pushed $BRANCH"

url="$(git remote get-url origin)"
cat <<EOF

============================================================
RELEASED.

Learners clone this — no branch flag needed, provided '$BRANCH'
is the repository's default branch:

    git clone $url snackbot-my-run

Set it once with:  gh repo edit --default-branch $BRANCH

Working on the course itself? Clone 'main' instead:

    git clone -b main $url
============================================================
EOF
