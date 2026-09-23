# productivity-skill

My [Claude Code](https://claude.com/claude-code) skills in one repo, so a new computer is one clone and one command.

## Install

```bash
git clone https://github.com/PeerawitDeesamer/productivity-skill.git ~/code/productivity-skill
bash ~/code/productivity-skill/install.sh
```

`install.sh` symlinks everything into `~/.claude/` and then runs the posn and skr installers
(TinyTeX, TH Sarabun New, pymupdf, sympy, rclone). No sudo needed.

| Flag | Does |
|---|---|
| `--skills-only` | link only, skip dependencies |
| `--check` | report what is missing, change nothing |

Because they are symlinks, editing a skill in `~/.claude/skills/<name>` edits the repo. Commit and push from `~/code/productivity-skill`.
Anything already in `~/.claude` with the same name is moved to `~/.claude/backup-<date>/`, not deleted.

## What's inside

### Mine

| Skill | What it does |
|---|---|
| [`skr`](skills/skr) | Teacher's PDF sheet → HTML lessons the night before a Thai school test (chem/bio/physics/math) |
| [`posn`](skills/posn) | Mock สอวน. computer camp-1 exams with answer keys, XeLaTeX + TH Sarabun New, uploaded to Drive |
| [`breakdown`](skills/breakdown) | A coach for breaking down competitive-programming / LeetCode problems yourself |
| [`commands/posn-*`](commands) | posn feedback loop: `/posn-score` `/posn-why` `/posn-weakness` `/posn-calibrate` `/posn-feynman` `/posn-variant` |
| [`agents/posn-student`](agents) | Plays a student who doesn't get it, so you have to explain |

skr, posn and breakdown were separate repos before. Their full history was brought in with `git subtree`.

### Not mine (credited)

| Skill | Author |
|---|---|
| [`caveman`](skills/caveman) | [Julius Brussee](https://github.com/JuliusBrussee/caveman) |
| [`grilling`](skills/grilling), [`grill-me`](skills/grill-me) | [Matt Pocock](https://github.com/mattpocock/skills) |

Pinned, unchanged copies under their MIT licenses. See [CREDITS.md](CREDITS.md).

## License

MIT for my own work ([LICENSE](LICENSE)). Third-party skills keep their own license, in their folders.
