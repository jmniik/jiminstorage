#!/usr/bin/env bash
# Copy files/folders from llm-local into the team repo (AXC_team5) at a folder the user names, then commit + push.
# Usage: bash .claude/team-upload.sh [--dry-run] --to <team-repo folder> <path> [<path> ...]
#   <path>   : relative to llm-local
#   --to     : folder inside the team repo, e.g. "김지민/archive" or "조정민/26.11.18" or "." (repo root)
#   Each file/folder goes to <to>/<its own name>.
set -euo pipefail

REPO_URL="https://github.com/starlike2you/AXC_team5.git"
TEAM_DIR="${LOCALAPPDATA:-$HOME}/AXC_team5"
SRC_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

DRY=0; TO=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1; shift ;;
    --to) TO="${2:-}"; shift 2 || true ;;
    *) break ;;
  esac
done
[ -z "$TO" ] && { echo "ERROR: no destination (--to) given"; exit 1; }
[ $# -eq 0 ] && { echo "ERROR: no file given"; exit 1; }

# destination check: inside the repo, no '..', not .git
TO="${TO#./}"; TO="${TO%/}"; [ -z "$TO" ] && TO="."
case "/$TO/" in
  */../*|/.git/*|*/.git/*) echo "ERROR: bad destination: $TO"; exit 1 ;;
esac
case "$TO" in /*|[A-Za-z]:*) echo "ERROR: destination must be a path inside the team repo: $TO"; exit 1 ;; esac

# check sources first
for p in "$@"; do
  [ -e "$SRC_ROOT/$p" ] || { echo "ERROR: not found in llm-local: $p"; exit 1; }
done

# get / update team repo clone
if [ ! -d "$TEAM_DIR/.git" ]; then
  git clone -q "$REPO_URL" "$TEAM_DIR"
fi
cd "$TEAM_DIR"
git config user.name  "$(git -C "$SRC_ROOT" config user.name)"
git config user.email "$(git -C "$SRC_ROOT" config user.email)"
git pull -q --rebase origin main

[ -d "$TO" ] || echo "NEW FOLDER: $TO (will be created)"

dests=()
for p in "$@"; do
  p="${p#./}"; p="${p%/}"
  name="$(basename "$p")"
  if [ "$TO" = "." ]; then dest="$name"; else dest="$TO/$name"; fi
  dests+=("$dest")
  if [ -e "$dest" ]; then
    if [ -f "$dest" ] && cmp -s "$SRC_ROOT/$p" "$dest"; then
      echo "same: $p -> $dest"
    else
      echo "OVERWRITE: $p -> $dest (already exists in team repo)"
    fi
  else
    echo "copy: $p -> $dest"
  fi
  if [ $DRY -eq 0 ]; then
    mkdir -p "$(dirname "$dest")"
    if [ -d "$SRC_ROOT/$p" ]; then
      mkdir -p "$dest"
      cp -r "$SRC_ROOT/$p/." "$dest/"
    else
      cp "$SRC_ROOT/$p" "$dest"
    fi
  fi
done

if [ $DRY -eq 1 ]; then echo "DRY RUN: nothing copied or pushed"; exit 0; fi

git add -- "${dests[@]}"
if git diff --cached --quiet; then
  echo "NO CHANGE: team repo already has the same content"
  exit 0
fi
git diff --cached --stat
git commit -q -m "김지민: $* → $TO 업로드"
git push -q origin main
echo "PUSHED: $(git log --oneline -1)"
