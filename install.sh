#!/usr/bin/env bash
# install.sh — link every skill, command and agent in this repo into ~/.claude,
# then let posn and skr install what they need (TinyTeX, TH Sarabun New, pymupdf...).
#
#   git clone https://github.com/PeerawitDeesamer/claude-skills.git ~/code/claude-skills
#   bash ~/code/claude-skills/install.sh                # link + install dependencies
#   bash ~/code/claude-skills/install.sh --skills-only  # link only
#   bash ~/code/claude-skills/install.sh --check        # report only, change nothing
#
# Links, not copies: edit a skill in the repo and Claude Code sees it at once,
# and `git commit` picks up the change. Anything already at a target that is not
# our link is moved to ~/.claude/backup-<date>/, never deleted.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
CLAUDE="$HOME/.claude"
BACKUP="$CLAUDE/backup-$(date +%Y%m%d-%H%M%S)"
CHECK=0
DEPS=1
for a in "$@"; do
  case "$a" in
    --check) CHECK=1 ;;
    --skills-only) DEPS=0 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown option: $a" >&2; exit 2 ;;
  esac
done

ok()   { printf '  \033[32mOK\033[0m   %s\n' "$*"; }
miss() { printf '  \033[33mMISS\033[0m %s\n' "$*"; }
FAILS=0

# link <source> <target>
link() {
  local src="$1" dst="$2" name
  name="${dst#"$CLAUDE"/}"
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    ok "$name"; return
  fi
  if [ "$CHECK" = 1 ]; then
    miss "$name is not linked to the repo"; FAILS=$((FAILS + 1)); return
  fi
  if [ -e "$dst" ] || [ -L "$dst" ]; then
    # outside skills/: a backup left there would load as a second copy of the skill
    mkdir -p "$(dirname "$BACKUP/$name")"
    mv "$dst" "$BACKUP/$name"
    printf '  moved old %s to %s\n' "$name" "${BACKUP/#$HOME/~}/$name"
  fi
  ln -s "$src" "$dst" && ok "$name → repo"
}

echo "claude-skills — $REPO"
[ "$CHECK" = 1 ] || mkdir -p "$CLAUDE/skills" "$CLAUDE/commands" "$CLAUDE/agents"

echo; echo "skills"
for d in "$REPO"/skills/*/; do
  d="${d%/}"; link "$d" "$CLAUDE/skills/$(basename "$d")"
done
echo; echo "commands"
for f in "$REPO"/commands/*.md; do link "$f" "$CLAUDE/commands/$(basename "$f")"; done
echo; echo "agents"
for f in "$REPO"/agents/*.md; do link "$f" "$CLAUDE/agents/$(basename "$f")"; done

if [ "$DEPS" = 1 ]; then
  flag=(); [ "$CHECK" = 1 ] && flag=(--check)
  echo; echo "==> posn dependencies"
  bash "$CLAUDE/skills/posn/install.sh" ${flag[@]+"${flag[@]}"} || FAILS=$((FAILS + 1))
  echo; echo "==> skr dependencies"
  bash "$CLAUDE/skills/skr/install.sh" ${flag[@]+"${flag[@]}"} || FAILS=$((FAILS + 1))
fi

echo
if [ "$FAILS" = 0 ]; then echo "done. Restart Claude Code to pick up new skills."
else echo "$FAILS problem(s) above."; exit 1; fi
