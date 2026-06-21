# Codebase reconnaissance

Run these when scaffolding or aligning a **mature existing** repo. The output grounds `AGENTS.md` project-specific rules, validation priorities, and key files in observed risk rather than assumptions. Skip for new/empty repos.

| Signal | Command | What it reveals |
|--------|---------|-----------------|
| Churn hotspots | `git log --format=format: --name-only --since="1 year ago" \| sort \| uniq -c \| sort -nr \| head -20` | Files that change most often — candidates for tighter validation or ownership rules |
| Bus factor | `git shortlog -sn --no-merges --since="6 months ago"` | Knowledge concentration — flag where one contributor owns 60%+ of recent changes |
| Bug clusters | `git log -i -E --grep="fix\|bug\|broken" --name-only --format='' \| sort \| uniq -c \| sort -nr \| head -20` | Files with the most bug-related commits — cross-reference with churn for highest-risk code |
| Project momentum | `git log --format='%ad' --date=format:'%Y-%m' \| sort \| uniq -c` | Commit frequency by month — team health, departures, batch-release patterns |
| Firefighting | `git log --oneline --since="1 year ago" \| grep -iE 'revert\|hotfix\|emergency\|rollback'` | Revert/hotfix rate — frequent entries suggest deploy or test-coverage gaps |

Use the results to:
- Prioritize which areas get validation commands or stricter review.
- Identify files that warrant explicit ownership or focused test coverage.
- Calibrate project-specific rules to actual risk, not convention.

Source: [The Git Commands I Run Before Reading Any Code](https://piechowski.io/post/git-commands-before-reading-code/) — Ally Piechowski.
