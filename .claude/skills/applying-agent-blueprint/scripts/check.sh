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

# BP-ADOPT-02: the references/ companion directory landed with the blueprint.
missing=""
for r in commit-attribution.md user-profile.md work-unit-example.md sources.md; do
  [ -f "$ROOT/references/$r" ] || missing="$missing $r"
done
if [ -z "$missing" ]; then
  pass "BP-ADOPT-02" "references/ has all 4 companion files"
else
  flunk "BP-ADOPT-02" "references/ is missing:$missing"
fi

# BP-VERSION: AGENTS.md carries the same version string as the blueprint.
bp_ver=$(sed -n 's/^version:[[:space:]]*"\{0,1\}\([^"]*\)"\{0,1\}$/\1/p' "$ROOT/AGENT_BLUEPRINT.md" 2>/dev/null | head -n 1)
if [ -z "$bp_ver" ]; then
  flunk "BP-VERSION" "no version in AGENT_BLUEPRINT.md frontmatter"
elif [ -f "$ROOT/AGENTS.md" ] && grep -qF "$bp_ver" "$ROOT/AGENTS.md"; then
  pass "BP-VERSION" "AGENTS.md matches blueprint version $bp_ver"
else
  flunk "BP-VERSION" "AGENTS.md does not carry blueprint version $bp_ver"
fi

# BP-WRITE-04: the project declares its persuasive-text exemptions, or "none".
if [ -f "$ROOT/AGENTS.md" ] && grep -q "BP-WRITE-04" "$ROOT/AGENTS.md"; then
  pass "BP-WRITE-04" "AGENTS.md declares its exemptions"
else
  flunk "BP-WRITE-04" "AGENTS.md does not declare BP-WRITE-04 exemptions (state 'none' if there are none)"
fi

# BP-INSTR-10: hedged modals in project policy. Advisory, not a gate.
# Deliberately does not set fail: a noisy gate gets disabled, which is the
# failure mode BP-VERIFY cites ([21]). Promote to flunk once a project is clean.
if [ -f "$ROOT/AGENTS.md" ]; then
  hedges=$(grep -nEc '\b(should|may|might|could)\b' "$ROOT/AGENTS.md" || true)
  if [ "${hedges:-0}" -eq 0 ]; then
    pass "BP-INSTR-10" "AGENTS.md has no hedged modals"
  else
    printf 'WARN  %-12s %s\n' "BP-INSTR-10" "$hedges line(s) in AGENTS.md use should/may/might/could:"
    grep -nE '\b(should|may|might|could)\b' "$ROOT/AGENTS.md" | sed 's/^/               /'
  fi
fi

echo
if [ "$fail" -eq 0 ]; then
  echo "All structural checks passed."
else
  echo "One or more checks failed."
fi
exit "$fail"
