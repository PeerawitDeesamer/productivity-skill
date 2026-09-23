# breakdown — a problem-solving coach

A [Claude Code](https://claude.com/claude-code) skill that teaches you to break down
competitive-programming problems (สอวน./POSN, Codeforces) and LeetCode-style problems
**yourself**. It's a coach, not a solver: it asks questions, and it only tells you the
answer when you ask for it.

It coaches in Thai and keeps technical terms in English. You write your solutions in C++.

## How it works

Paste a problem and run `/breakdown`. The skill walks you through six stages:

1. Restate the problem and its input/output
2. Work the samples by hand
3. Brute force and its complexity
4. **Use the constraints to find the target complexity.** This stage is never skipped.
5. Find the pattern or technique to optimize
6. Write the C++; the skill reviews it and asks about edge cases

If you answer a stage correctly in one go, it moves on.

When you're stuck, hints come in three rungs, and only when you ask:
**L1** a nudging question → **L2** a pointer to where to look → **L3** the technique name and key insight.

| Type | What happens |
|---|---|
| `hint` | Moves up one rung |
| `เฉลย` / `show me` | Walks through the expert's thinking, stage by stage, then the code |
| `test` | Compiles your code with `g++ -O2`, runs the samples plus generated edge cases, and reports ✅/❌ without fixing anything |

Each problem ends with a one-line pattern takeaway, e.g.
`📌 เห็น "หาคู่ใน sorted array + n ≤ 10^5" → คิดถึง two pointers O(n)`.

There are no logs, no reminders and no review schedule.

## Install

```sh
git clone https://github.com/PeerawitDeesamer/breakdown ~/.claude/skills/breakdown
```

On macOS, `test` automatically works around the missing `<bits/stdc++.h>` in Apple clang.

## License

MIT
