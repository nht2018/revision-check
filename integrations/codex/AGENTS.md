## Rev Check

When a user prompt starts with `$rev-check`, use the `rev-check` approval workflow:

1. Inspect first without editing.
2. Group proposed edits into approval items.
3. Open the local `Revision Review` approval page.
4. Apply only approved items.
5. If the approval JSON contains `cancelled: true`, stop without modifying files.

If the prompt does not start with `$rev-check`, use the normal project workflow.
