[中文](README.md) | English

# revision-check

`revision-check` is a "review first, approve next, edit last" workflow for AI coding agents.

When you want an agent to edit a paper, LaTeX project, codebase, or document, but you do not want it to write files directly, prefix the request with:

```text
$revision-check your editing prompt
```

The agent first inspects the files, prepares planned edit items, and opens a local `Revision Review` approval page. You can approve changes with the mouse, mark items as "always ignore", resize columns, and compare the original text with the proposed revision. Only approved items are written to files.

## Installation

Usually, you only need to enter this in your agent:

```text
Install the skill from https://github.com/nht2018/revision-check.git as revision-check.
```

Mainstream coding agents that support custom skills, rules, or project instructions can usually fetch and enable this skill through their own mechanisms, such as Codex, Claude Code, and Cursor CLI.

## Usage

After loading the `revision-check` skill, use:

```text
$revision-check your editing prompt
```

Then the approval page will open automatically in the browser, where you can review and approve the proposed changes.

![Revision Review demo](assets/demo.jpg)

## Design Principles

- Approval comes before editing.
- The user's latest instruction overrides previous ignore preferences.
- Edits should be minimal, explainable, and verifiable.
- For papers and LaTeX projects, preserve technical claims, proof structures, experimental results, and template files by default.
