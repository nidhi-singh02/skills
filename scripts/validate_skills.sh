#!/bin/sh
# Validate every skill in this repo against the Agent Skills spec.
# https://agentskills.io/specification
fail=0
for d in skills/*/; do
  npx -y skills-ref validate "$d" || fail=1
done
exit $fail
