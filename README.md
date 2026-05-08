# revision-check

`revision-check` 是一个面向 AI coding agents 的“先审查、再批准、后修改”工作流。

当你希望 agent 修改论文、LaTeX、代码或文档，但不希望它直接写文件时，在请求前加上：

```text
$rev-check
```

agent 会先检查文件、整理计划修改项，并打开一个本地审批页面 `Revision Review`。你可以用鼠标勾选要批准的修改、选择“总是忽略”、调整列宽、查看原文和拟修改之间的差异。只有你批准的项目才会被写入文件。

![Revision Review demo](assets/demo.jpg)

## 核心特性

- `$rev-check` 显式触发：不加前缀时，agent 使用自己的正常工作流。
- 本地审批界面：不依赖云服务，审批结果写入本地 JSON。
- 只改批准项：未勾选、关闭审批、或“总是忽略”的项目不会被修改。
- 分组提案：同一类重复修改显示为一行，例如多处 `$n$ qubit` 统一改为 `$n$-qubit`。
- 差异高亮：`当前` 和 `拟修改` 中不同的 token 会被高亮。
- 可调列宽：可以拖拽表头边界调整浏览宽度。
- 关闭按钮：停止审批并关闭页面，不会修改文件。
- 跨 agent 可用：提供 Codex skill，以及 Claude Code / Cursor 的规则模板。

## 安装到 Codex

克隆仓库后运行：

```bash
git clone https://github.com/nht2018/revision-check.git
cd revision-check
bash install.sh
```

之后在 Codex 中使用：

```text
$rev-check 润色 main.tex 的 introduction。先检查，打开审批页，我确认后再修改。
```

## Claude Code / Cursor 用法

`$rev-check` 不是系统级魔法命令。Claude Code、Cursor 等 agent 需要先加载本仓库提供的规则文件，才会按这个 workflow 工作。

Claude Code 可参考：

```text
integrations/claude-code/CLAUDE.md
```

Cursor 可参考：

```text
integrations/cursor/rev-check.mdc
```

把相应内容放到项目规则或用户规则中后，使用方式同样是：

```text
$rev-check 修改这篇论文的 Introduction，但先给我审批界面。
```

## 手动启动审批页面

如果你已经有 review items JSON，可以直接运行：

```bash
python3 skills/rev-check/scripts/serve_approval.py examples/review_items.json \
  --output-json /tmp/rev-check-approval.json \
  --open-browser \
  --exit-on-confirm
```

确认后读取：

```bash
cat /tmp/rev-check-approval.json
```

如果点击“关闭”，结果会是：

```json
{
  "cancelled": true,
  "approved_ids": [],
  "approved_items": [],
  "ignored_ids": [],
  "ignored_items": []
}
```

## Review Item 格式

```json
[
  {
    "id": "L1",
    "locations": ["main.tex:79-83"],
    "occurrence_count": 1,
    "issue_type": "段落级润色",
    "priority": "medium",
    "current_problem": "开篇动机表述偏长。",
    "proposed_change": "改为更直接的动机段落。",
    "current_text": "Original paragraph...",
    "proposed_text": "Revised paragraph...",
    "reason": "解释具体词汇、句式和逻辑衔接为什么更好。"
  }
]
```

字段说明：

- `id`：稳定 ID，例如 `L1` 或 `G1`。
- `locations`：代表性位置；范围可写作 `main.tex:79-83`。
- `occurrence_count`：这一行实际影响的修改总数，会显示在“范围”列里的 `总数：...`。
- `issue_type`：问题类型，建议用中文。
- `priority`：排序用，可取 `high`、`medium`、`low`、`optional`。
- `current_text`：原文，会显示在 `当前` 列。
- `proposed_text`：拟修改文本，会显示在 `拟修改` 列。
- `reason`：详细理由，尤其是润色类修改，应说明为什么改词、改句式或改逻辑连接。

## 仓库结构

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

## 设计原则

- 审批优先于修改。
- 用户最新指令优先于历史忽略偏好。
- 尽量做最小、可解释、可验证的修改。
- 对论文和 LaTeX，优先保留技术结论、证明结构、实验结果和模板文件。

## English README

See [README_EN.md](README_EN.md).
