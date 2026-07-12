# Skill: migrate (Modernize mode — stretch goal)
Bring an existing codebase up to date by editing IN PLACE, never a rewrite.
1. Inventory framework/version/deps; report what's outdated.
2. Plan ordered, in-place, individually-verifiable changes.
3. Apply one change per commit on a branch.
4. Verify after each: app still starts, endpoints return the same shape.
5. Quarantine anything ambiguous; never silently change behavior.
6. Open ONE PR with a checklist body.
Hard rules: preserve behavior, no rewrites, every change revertible, prove it works.
