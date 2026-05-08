[中文](README.md) | English

# revision-check

`revision-check` is a review-before-edit workflow for AI coding agents.

When you want an agent to edit a paper, LaTeX project, codebase, or document, but you do not want it to write files immediately, prefix the request with:

```text
$rev-check
```

The agent first inspects the files, prepares concrete proposed edits, and opens a local `Revision Review` approval page. You can approve selected items, mark items as always ignored, resize columns, and compare the original and proposed text with highlighted differences. Only approved items are applied.

![Revision Review demo](assets/demo.jpg)

## Features

- Explicit `$rev-check` trigger: without the prefix, the agent uses its normal workflow.
- Local approval UI: no cloud service is required; approval results are written to a local JSON file.
- Approved edits only: unchecked items, cancelled runs, and ignored items are not applied.
- Grouped proposals: repeated edits of the same type appear as one row.
- Difference highlighting: changed token spans are highlighted in `当前` and `拟修改`.
- Resizable columns: drag table-header boundaries to adjust the review workspace.
- Close button: cancel the approval run and stop the local server without editing files.
- Multi-agent support: includes a Codex skill plus rule templates for Claude Code and Cursor.

## Install for Codex

```bash
git clone https://github.com/nht2018/revision-check.git
cd revision-check
bash install.sh
```

Then use:

```text
$rev-check Polish the introduction in main.tex. Inspect first, open the approval page, and apply only what I approve.
```

## Claude Code and Cursor

`$rev-check` is not a global system command. Claude Code, Cursor, and similar agents must load the corresponding rule file before the prefix can control their behavior.

Claude Code:

```text
integrations/claude-code/CLAUDE.md
```

Cursor:

```text
integrations/cursor/rev-check.mdc
```

After installing the rule, use:

```text
$rev-check Revise this paper introduction, but show me the approval page before editing.
```

## Run the Approval Page Manually

```bash
python3 skills/rev-check/scripts/serve_approval.py examples/review_items.json \
  --output-json /tmp/rev-check-approval.json \
  --open-browser \
  --exit-on-confirm
```

Then inspect:

```bash
cat /tmp/rev-check-approval.json
```

If the user clicks `关闭`, the result is:

```json
{
  "cancelled": true,
  "approved_ids": [],
  "approved_items": [],
  "ignored_ids": [],
  "ignored_items": []
}
```

## Review Item Schema

```json
[
  {
    "id": "L1",
    "locations": ["main.tex:79-83"],
    "occurrence_count": 1,
    "issue_type": "段落级润色",
    "priority": "medium",
    "current_problem": "The opening motivation is too long.",
    "proposed_change": "Rewrite it as a clearer motivation paragraph.",
    "current_text": "Original paragraph...",
    "proposed_text": "Revised paragraph...",
    "reason": "Explain why the proposed wording, syntax, or logical transition is better."
  }
]
```

Important fields:

- `id`: stable ID, such as `L1` or `G1`.
- `locations`: representative locations, such as `main.tex:79-83`.
- `occurrence_count`: total affected occurrences shown under `范围`.
- `issue_type`: visible issue type.
- `priority`: sorting key: `high`, `medium`, `low`, or `optional`.
- `current_text`: original text shown in `当前`.
- `proposed_text`: proposed text shown in `拟修改`.
- `reason`: detailed explanation. For polishing, explain why the new word, phrase, sentence structure, or transition is preferable.

## Repository Layout

```text
revision-check/
├── README.md
├── README_EN.md
├── install.sh
├── assets/
│   └── demo.jpg
├── examples/
│   └── review_items.json
├── integrations/
│   ├── claude-code/
│   ├── codex/
│   └── cursor/
└── skills/
    └── rev-check/
        ├── SKILL.md
        ├── agents/
        └── scripts/
```

## Principles

- Review before editing.
- The newest explicit user instruction overrides earlier ignore preferences.
- Keep edits minimal, explainable, and verifiable.
- For papers and LaTeX projects, preserve technical claims, proof structure, experimental results, and template files unless explicitly approved.
