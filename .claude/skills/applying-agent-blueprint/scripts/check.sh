#!/usr/bin/env bash
# Structural alignment check for a project that adopts AGENT_BLUEPRINT.md.
# Verifies the machine-checkable core invariants. Prints PASS/FAIL per rule
# with evidence, and exits non-zero if any check fails so it can gate a loop.
#
# Usage: scripts/check.sh [repo_root]   (default: current directory)
# Checks structure only, not template wording (see SKILL.md "template sync").

set -uo pipefail

ROOT="${1:-.}"
fail=0

pass() { printf 'PASS  %-12s %s\n' "$1" "$2"; }
flunk() { printf 'FAIL  %-12s %s\n' "$1" "$2"; fail=1; }

# BP-CORE-01: AGENTS.md exists and references the blueprint.
if [ ! -f "$ROOT/AGENTS.md" ]; then
  flunk "BP-CORE-01" "AGENTS.md is missing"
elif grep -q "AGENT_BLUEPRINT.md" "$ROOT/AGENTS.md"; then
  pass "BP-CORE-01" "AGENTS.md references AGENT_BLUEPRINT.md"
else
  flunk "BP-CORE-01" "AGENTS.md does not reference AGENT_BLUEPRINT.md"
fi

# BP-CORE-02: roadmap/index.md exists.
if [ -f "$ROOT/roadmap/index.md" ]; then
  pass "BP-CORE-02" "roadmap/index.md present"
else
  flunk "BP-CORE-02" "roadmap/index.md is missing"
fi

# BP-CORE-03: every numbered work unit opens with YAML frontmatter.
units=0
bad=""
if [ -d "$ROOT/roadmap" ]; then
  while IFS= read -r f; do
    units=$((units + 1))
    [ "$(head -n 1 "$f")" = "---" ] || bad="$bad ${f#"$ROOT"/}"
  done < <(find "$ROOT/roadmap" -maxdepth 1 -type f -name '[0-9]*-*.md' 2>/dev/null)
fi
if [ "$units" -eq 0 ]; then
  pass "BP-CORE-03" "no numbered work units to check"
elif [ -z "$bad" ]; then
  pass "BP-CORE-03" "$units work unit(s) start with YAML frontmatter"
else
  flunk "BP-CORE-03" "missing frontmatter:$bad"
fi

# BP-CORE-09: trailer template present, no hardcoded runtime model value.
if [ -f "$ROOT/AGENTS.md" ] && grep -q "Co-authored-by:" "$ROOT/AGENTS.md"; then
  if grep -qE '^AI-Model:[[:space:]]*\[' "$ROOT/AGENTS.md" || ! grep -qE '^AI-Model:' "$ROOT/AGENTS.md"; then
    pass "BP-CORE-09" "trailer template present, AI-Model left as placeholder"
  else
    flunk "BP-CORE-09" "AI-Model looks hardcoded; store a placeholder, not a runtime value"
  fi
else
  flunk "BP-CORE-09" "no commit trailer template found in AGENTS.md"
fi

echo
if [ "$fail" -eq 0 ]; then
  echo "All structural checks passed."
else
  echo "One or more checks failed."
fi
exit "$fail"
