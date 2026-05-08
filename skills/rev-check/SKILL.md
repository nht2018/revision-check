---
name: rev-check
description: Use this skill when the user prefixes a request with "$rev-check" or explicitly asks to use rev-check. It reviews planned edits first, opens a local Revision Review approval page, and applies only approved changes. Useful for LaTeX papers, theses, academic prose, bibliography cleanup, and other editing tasks where the user wants click-based approval before modification.
---

# Rev Check

Use this skill only when the user explicitly prefixes the task with `$rev-check` or asks to use `rev-check`.
Without that trigger, follow the normal agent workflow.

Core rule: inspect first, propose concrete edit items, open the approval page, then modify only approved items.

## Workflow

1. Inspect without editing.
   - Read relevant source files, generated artifacts, logs, or rendered output as needed.
   - Do not modify files before approval.
   - Distinguish true source issues from PDF extraction artifacts, generated-file artifacts, and template-driven behavior.

2. Create review items.
   - Group repeated edits by rule. One row should represent one modification class, not one occurrence.
   - Use stable IDs: `G1`, `G2`, ... for grouped rules; `L1`, `L2`, ... for single-location or paragraph-level edits.
   - Each item should include `id`, `locations`, `occurrence_count`, `issue_type`, `priority`, `current_problem`, `proposed_change`, `reason`, and, for prose edits, full `current_text` and `proposed_text`.
   - Use Chinese for visible `issue_type` and `reason` unless the user asks otherwise.
   - Do not show internal IDs or priority as columns in the HTML page; priority is used only for sorting.
   - The `范围` cell should include representative locations and `总数：...`. Do not create a separate `数量` column.
   - For polishing proposals, make `reason` concrete: explain why the replacement improves academic tone, logic, terminology, sentence structure, ambiguity, or consistency.

3. Open the approval page.
   - For more than a few items, write a JSON list of review items and serve it with `scripts/serve_approval.py`.
   - Use the fixed title `Revision Review` unless the user explicitly asks for another title.
   - Prefer `--open-browser --exit-on-confirm`.

Example:

```bash
python3 /path/to/rev-check/scripts/serve_approval.py /tmp/rev-check-items.json \
  --output-json /tmp/rev-check-approval.json \
  --open-browser \
  --exit-on-confirm
```

4. Apply only approved edits.
   - If the approval JSON contains `cancelled: true`, stop and do not modify files.
   - Apply only `approved_items`.
   - Do not apply unapproved items.
   - If `ignored_items` are present, treat them as default suppressions for the current project/workflow. A later explicit user request overrides previous ignores.
   - Preserve unrelated user changes.

5. Verify and report.
   - Run the project’s normal validation command when available, such as `latexmk`, `bash compile.sh`, tests, or lint.
   - Report what was changed, what was skipped, and any remaining validation warnings.

## Review Item Schema

```json
[
  {
    "id": "L1",
    "locations": ["main.tex:79-83"],
    "occurrence_count": 1,
    "issue_type": "段落级润色",
    "priority": "medium",
    "current_problem": "开篇动机表述偏长。",
    "proposed_change": "改为更直接的 classical-to-quantum 动机段落。",
    "current_text": "Original paragraph...",
    "proposed_text": "Revised paragraph...",
    "reason": "解释具体词汇、句式和逻辑衔接为什么更好。"
  }
]
```

## Approval Page Behavior

- Buttons: `全选`, `清空`, `关闭`, `确认修改`.
- `关闭` cancels the run, writes `cancelled: true`, stops the local server, and attempts to close the page.
- `批准` and `总是忽略` are mutually exclusive for the same row, but both may be unchecked.
- The `总是忽略` tooltip explains that ignored items are suppressed by default but can be reconsidered if the user explicitly asks.
- Columns can be resized by dragging table-header boundaries.
- `当前` and `拟修改` highlight only differing token spans.
