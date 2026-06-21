# User profile template

Git-ignored interaction preferences (`[BP-WF-PROFILE]`). Add `.agent-profile.md` to `.gitignore`, then create the file below. Ask the sample questions only to fill gaps; the live conversation always outranks this file.

## .agent-profile.md

```markdown
# User Profile

Personal calibration for agent interactions in this project. The live conversation always outranks this file.

## Response calibration

- Lead with the conclusion, support after; match length to the task (proportionate over exhaustive).
- [Explanation preference: brief | standard | thorough; explain unknowns vs ask first]
- [Communication style: code-focused | narrative | casual | formal; high-level first vs drill-down]

## Calibration facts

- Experience: [beginner | intermediate | advanced per domain]
- Languages/frameworks: [list]
- Team context: [solo | collaborative; target audience if relevant]
- [Values / constraints worth remembering across sessions]
```

## Sample questions (ask only to fill gaps)

- "What's your experience level with [project's primary domain]?"
- "Which languages/frameworks are you comfortable with?"
- "Brief confirmations or detailed explanations?"
- "Should I explain things you may not know, or ask first?"
- "Any communication preferences (formal/casual, code vs prose, high-level first)?"
- "Solo work or a team project?"

## Calibration

- Explain more for beginners; assume familiarity for experts.
- Match explanation depth and communication style to stated preference.
- Consider team context for commit/message conventions.
