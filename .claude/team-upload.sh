#!/usr/bin/env bash
# Copy files/folders from llm-local into team repo (AXC_team5) 김지민/llm-local/<same path>, then commit + push.
# Usage: bash .claude/team-upload.sh [--dry-run] <path> [<path> ...]   (paths relative to llm-local)
set -euo pipefail

REPO_URL="https://github.com/starlike2you/AXC_team5.git"
TEAM_DIR="${LOCALAPPDATA:-$HOME}/AXC_team5"
SRC_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST_SUB="김지민/llm-local"
TEAM_ROOT="김지민"
# 임시 예외: 이 경로로 시작하면 김지민/llm-local/ 대신 김지민/ 바로 아래로 올린다.
# (웰니스기획전 프로젝트가 끝나면 사용자 요청으로 지운다)
TOP_LEVEL=("웰니스기획전")

DRY=0
if [ "${1:-}" = "--dry-run" ]; then DRY=1; shift; fi
[ $# -eq 0 ] && { echo "ERROR: no file given"; exit 1; }

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

for p in "$@"; do
  p="${p#./}"
  dest="$DEST_SUB/$p"
  for t in "${TOP_LEVEL[@]}"; do
    if [ "$p" = "$t" ] || [ "${p#"$t"/}" != "$p" ]; then dest="$TEAM_ROOT/$p"; fi
  done
  echo "copy: $p -> $dest"
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

git add "$TEAM_ROOT"
if git diff --cached --quiet; then
  echo "NO CHANGE: team repo already has the same content"
  exit 0
fi
git diff --cached --stat
git commit -q -m "김지민: $* 업로드"
git push -q origin main
echo "PUSHED: $(git log --oneline -1)"
