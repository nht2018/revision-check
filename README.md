中文 | [English](README_EN.md)

# revision-check

`revision-check` 是一个面向 AI coding agents 的“先审查、再批准、后修改”工作流。

当你希望 agent 修改论文、LaTeX、代码或文档，但不希望它直接写文件时，在请求前加上：

```text
$revision-check 关于修改的prompt
```

agent 会先检查文件、整理计划修改项，并打开一个本地审批页面 `Revision Review`。你可以用鼠标勾选要批准的修改、选择“总是忽略”、调整列宽、查看原文和拟修改之间的差异。只有你批准的项目才会被写入文件。


## 安装

你需要一个支持自定义技能、规则或项目指令的主流 coding agent，例如 [Codex](https://chatgpt.com/codex/)、[Claude Code](https://code.claude.com/docs/en/quickstart)、[Cursor CLI](https://cursor.com/) 等。

```text
Install the skill from https://github.com/nht2018/revision-check.git as revision-check.
```
agent 通常会根据自身机制拉取并启用这个 skill。

## 用法

加载 revision-check skill 后，使用方式是：

```text
$revision-check 关于修改的prompt
```
然后浏览器中会自动弹出审批页面，你可以进行审批。

![Revision Review demo](assets/demo.jpg)


## 设计原则

- 审批优先于修改。
- 用户最新指令优先于历史忽略偏好。
- 尽量做最小、可解释、可验证的修改。
- 对论文和 LaTeX，优先保留技术结论、证明结构、实验结果和模板文件。
