## Revision Check

If the user's request begins with `$revision-check`, do not edit files immediately.
Use the Revision Review workflow:

1. Inspect relevant files and identify concrete proposed edits.
2. Group repeated edits by rule.
3. Write review items as JSON.
4. Start `skills/revision-check/scripts/serve_approval.py` to open the local approval page.
5. Wait for the approval JSON.
6. Apply only approved items.

If the approval result contains `cancelled: true`, stop without modifying files.
If the request does not begin with `$revision-check`, follow the normal Claude Code workflow.
