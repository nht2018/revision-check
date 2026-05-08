#!/usr/bin/env python3
"""Create a local HTML approval checklist for revision items."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def location_sort_key(location: str) -> tuple[str, int, int, str]:
    match = re.match(r"([^:]+):(\d+)(?::(\d+))?", location)
    if not match:
        return (location, 10**9, 10**9, location)
    path, line, column = match.groups()
    return (path, int(line), int(column or 0), location)


def collect_locations(item: dict[str, Any]) -> list[str]:
    locations: list[str] = []
    raw_locations = item.get("locations", [])
    if isinstance(raw_locations, list):
        locations.extend(str(location) for location in raw_locations if str(location).strip())

    raw_occurrences = item.get("occurrences", [])
    if isinstance(raw_occurrences, list):
        for occurrence in raw_occurrences:
            if isinstance(occurrence, dict):
                location = occurrence.get("location", "")
                if str(location).strip():
                    locations.append(str(location))
            elif str(occurrence).strip():
                locations.append(str(occurrence))

    if not locations and str(item.get("location", "")).strip():
        locations.append(str(item["location"]))
    return locations


def summarize_locations(locations: list[str], limit: int = 4) -> str:
    if not locations:
        return ""
    shown = locations[:limit]
    summary = "; ".join(shown)
    remaining = len(locations) - len(shown)
    if remaining > 0:
        summary += f"; +{remaining} more"
    return summary


def priority_value(value: Any) -> int:
    if isinstance(value, int):
        return value
    text = str(value).strip().lower()
    mapping = {
        "critical": 0,
        "must": 0,
        "high": 1,
        "medium": 2,
        "normal": 2,
        "low": 3,
        "optional": 4,
    }
    return mapping.get(text, 2)


def priority_label(value: Any) -> str:
    rank = priority_value(value)
    labels = {
        0: "高",
        1: "高",
        2: "中",
        3: "低",
        4: "可选",
    }
    return labels.get(rank, "中")


def issue_type_label(value: Any) -> str:
    text = str(value).strip()
    mapping = {
        "Academic style": "学术表达",
        "Clear typo": "明显笔误",
        "Grammar": "语法",
        "Heading consistency": "标题一致性",
        "Sentence flow": "句子流畅度",
        "Spacing": "空格",
        "Style": "风格",
        "Style consistency": "风格一致性",
        "Typo": "拼写/笔误",
    }
    return mapping.get(text, text)


def load_items(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("items", data.get("review_items", []))
    if not isinstance(data, list):
        raise SystemExit("Input JSON must be a list of review items or an object with an items list.")

    items: list[dict[str, Any]] = []
    for index, raw in enumerate(data, start=1):
        if not isinstance(raw, dict):
            raise SystemExit(f"Item {index} is not an object.")
        item = dict(raw)
        locations = collect_locations(item)
        item.setdefault("id", f"G{index}" if len(locations) > 1 else f"L{index}")
        item.setdefault("location", summarize_locations(locations))
        item.setdefault("locations", locations)
        item.setdefault("occurrence_count", len(locations) if locations else 1)
        item.setdefault("issue_type", item.get("type", ""))
        item["issue_type"] = issue_type_label(item.get("issue_type", ""))
        item.setdefault("current_problem", item.get("problem", item.get("pattern", "")))
        item.setdefault("proposed_change", item.get("proposal", item.get("replacement", "")))
        item.setdefault(
            "current_text",
            item.get("current", item.get("original_text", item.get("original", item.get("current_problem", "")))),
        )
        item.setdefault(
            "proposed_text",
            item.get("proposed", item.get("replacement_text", item.get("replacement", item.get("proposed_change", "")))),
        )
        item.setdefault("reason", item.get("risk", ""))
        item.setdefault("priority", item.get("severity", "normal"))
        item["priority_rank"] = priority_value(item.get("priority"))
        item["priority_label"] = priority_label(item.get("priority"))
        item.setdefault("first_order", index)
        if locations:
            item.setdefault("first_location", min(locations, key=location_sort_key))
        else:
            item.setdefault("first_location", item.get("location", ""))
        items.append(item)
    return items


def html_document(
    items: list[dict[str, Any]],
    title: str,
    submit_url: str | None = None,
    auto_close: bool = False,
) -> str:
    payload = json.dumps(items, ensure_ascii=False, indent=2).replace("<", "\\u003c")
    title_json = json.dumps(title, ensure_ascii=False)
    submit_url_json = json.dumps(submit_url or "", ensure_ascii=False)
    auto_close_json = json.dumps(auto_close)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: light;
      --border: #ded6ca;
      --text: #2f2a24;
      --muted: #6f665c;
      --bg: #f7f3ea;
      --panel: #fffdf7;
      --header: #eee7dd;
      --approved: #fff1e7;
      --accent: #c96442;
      --accent-dark: #a94f32;
      --accent-soft: #ead2c6;
      --diff-bg: #fde7dc;
      --diff-text: #7f351f;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background: var(--bg);
    }}
    main {{
      width: min(1760px, calc(100vw - 32px));
      max-width: none;
      margin: 0 auto;
      padding: 24px 0 32px;
    }}
    header {{
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 18px;
    }}
    h1 {{
      margin: 0 0 6px;
      font-size: 24px;
      font-weight: 650;
      letter-spacing: 0;
    }}
    p {{
      margin: 0;
      color: var(--muted);
      line-height: 1.5;
    }}
    .actions {{
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 8px;
    }}
    .toolbar {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 10px;
    }}
    label {{
      color: var(--muted);
      font-size: 14px;
    }}
    select {{
      margin-left: 6px;
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--panel);
      color: var(--text);
      padding: 7px 10px;
      font: inherit;
    }}
    button {{
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--panel);
      color: var(--text);
      padding: 8px 12px;
      font: inherit;
      cursor: pointer;
    }}
    button.primary {{
      border-color: var(--accent);
      background: var(--accent);
      color: #fff;
    }}
    button:hover {{ border-color: var(--accent); }}
    button.primary:hover {{ background: var(--accent-dark); }}
    .panel {{
      background: transparent;
      border: 0;
      border-radius: 0;
      overflow: visible;
    }}
    .table-wrap {{
      overflow: auto;
      max-width: 100%;
      max-height: calc(100vh - 168px);
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
    }}
    table {{
      width: max-content;
      min-width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
    }}
    th, td {{
      border-bottom: 1px solid var(--border);
      padding: 10px 12px;
      text-align: left;
      vertical-align: top;
      font-size: 14px;
      line-height: 1.42;
    }}
    th {{
      background: var(--header);
      font-size: 13px;
      color: #4a4037;
      font-weight: 650;
      position: sticky;
      top: 0;
      user-select: none;
      z-index: 4;
    }}
    .resize-handle {{
      position: absolute;
      top: 0;
      right: -4px;
      width: 8px;
      height: 100%;
      cursor: col-resize;
      z-index: 2;
    }}
    .resize-handle::after {{
      content: "";
      position: absolute;
      top: 9px;
      bottom: 9px;
      left: 3px;
      border-left: 1px solid transparent;
    }}
    th:hover .resize-handle::after,
    body.resizing .resize-handle::after {{
      border-color: var(--accent);
    }}
    tr:last-child td {{ border-bottom: 0; }}
    tr.approved {{ background: var(--approved); }}
    tr.ignored {{ opacity: 0.72; }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 12px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }}
    .review-text {{
      display: block;
      max-height: 420px;
      overflow: auto;
    }}
    .diff-changed {{
      background: var(--diff-bg);
      color: var(--diff-text);
      border-radius: 3px;
      padding: 0 1px;
    }}
    .location {{ width: 190px; }}
    .location-meta {{
      display: block;
      margin-top: 4px;
      color: var(--muted);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 12px;
    }}
    .type {{ width: 120px; }}
    .approve {{ width: 84px; text-align: center; }}
    .ignore {{ width: 116px; text-align: center; }}
    .choice input {{
      width: 20px;
      height: 20px;
      accent-color: var(--accent);
      cursor: pointer;
    }}
    .info {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 16px;
      height: 16px;
      margin-left: 4px;
      border: 1px solid var(--muted);
      border-radius: 50%;
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
      line-height: 1;
      cursor: help;
      vertical-align: middle;
    }}
    .floating-tooltip {{
      position: fixed;
      width: 320px;
      max-width: min(320px, calc(100vw - 24px));
      padding: 9px 10px;
      border-radius: 6px;
      background: #2f2a24;
      color: #fff;
      box-shadow: 0 8px 28px rgba(47, 42, 36, 0.18);
      font-size: 12px;
      font-weight: 400;
      line-height: 1.45;
      text-align: left;
      white-space: normal;
      pointer-events: none;
      z-index: 1000;
    }}
    button:focus-visible,
    select:focus-visible,
    .choice input:focus-visible {{
      outline: 2px solid var(--accent-soft);
      outline-offset: 2px;
    }}
    .status {{
      margin-top: 14px;
      min-height: 20px;
      color: var(--muted);
      font-size: 13px;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <div>
      <h1 id="page-title"></h1>
      <p id="intro"></p>
    </div>
    <div class="actions">
      <button type="button" id="select-all">全选</button>
      <button type="button" id="clear-all">清空</button>
      <button type="button" id="close-page">关闭</button>
      <button type="button" id="confirm" class="primary">确认修改</button>
    </div>
  </header>
  <div class="toolbar">
    <label for="sort-mode">
      排序
      <select id="sort-mode">
        <option value="priority">按优先度排序</option>
        <option value="type">按问题类型排序</option>
        <option value="position">按首次出现位置排序</option>
      </select>
    </label>
  </div>
  <section class="panel">
    <div class="table-wrap">
    <table id="approval-table">
      <colgroup>
        <col style="width: 170px">
        <col style="width: 120px">
        <col style="width: 360px">
        <col style="width: 480px">
        <col style="width: 320px">
        <col style="width: 84px">
        <col style="width: 116px">
      </colgroup>
      <thead>
        <tr>
          <th class="location">范围</th>
          <th class="type">问题类型</th>
          <th>当前</th>
          <th>拟修改</th>
          <th>理由</th>
          <th class="approve">批准</th>
          <th class="ignore">总是忽略 <span class="info" tabindex="0" data-tooltip="表示不批准，并且希望以后默认不要把这个当做修改提案；如果之后明确要求修改这类内容，将以新的要求为准。">i</span></th>
        </tr>
      </thead>
      <tbody id="rows"></tbody>
    </table>
    </div>
  </section>
  <div id="status" class="status"></div>
</main>
<div id="floating-tooltip" class="floating-tooltip" hidden></div>
<script>
const items = {payload};
const title = {title_json};
const submitUrl = {submit_url_json};
const autoClose = {auto_close_json};
const table = document.getElementById("approval-table");
const columns = [...table.querySelectorAll("col")];
const rows = document.getElementById("rows");
const status = document.getElementById("status");
const floatingTooltip = document.getElementById("floating-tooltip");
document.getElementById("page-title").textContent = title;
document.getElementById("intro").textContent = submitUrl
  ? "勾选要批准的修改，然后点击确认修改。可拖拽表头边界调整列宽。"
  : "勾选要批准的修改，然后点击确认修改。可拖拽表头边界调整列宽。";

function textCell(value, asCode = false) {{
  const td = document.createElement("td");
  const node = asCode ? document.createElement("code") : document.createElement("span");
  node.textContent = value || "";
  td.appendChild(node);
  return td;
}}

function locationCell(item) {{
  const td = document.createElement("td");
  const code = document.createElement("code");
  code.textContent = item.location || "";
  td.appendChild(code);
  const meta = document.createElement("span");
  meta.className = "location-meta";
  meta.textContent = `总数：${{item.occurrence_count || 1}}`;
  td.appendChild(meta);
  return td;
}}

function splitTokens(value) {{
  return String(value || "").match(/\\\\[A-Za-z]+|\\s+|[A-Za-z0-9_:$^{{}}]+|./gu) || [];
}}

function prefixSuffixMask(leftTokens, rightTokens) {{
  let start = 0;
  while (
    start < leftTokens.length &&
    start < rightTokens.length &&
    leftTokens[start] === rightTokens[start]
  ) {{
    start += 1;
  }}
  let leftEnd = leftTokens.length - 1;
  let rightEnd = rightTokens.length - 1;
  while (
    leftEnd >= start &&
    rightEnd >= start &&
    leftTokens[leftEnd] === rightTokens[rightEnd]
  ) {{
    leftEnd -= 1;
    rightEnd -= 1;
  }}
  return [
    leftTokens.map((_, index) => index >= start && index <= leftEnd),
    rightTokens.map((_, index) => index >= start && index <= rightEnd)
  ];
}}

function diffMasks(leftTokens, rightTokens) {{
  if (leftTokens.join("") === rightTokens.join("")) {{
    return [
      Array(leftTokens.length).fill(false),
      Array(rightTokens.length).fill(false)
    ];
  }}
  if (leftTokens.length * rightTokens.length > 250000) {{
    return prefixSuffixMask(leftTokens, rightTokens);
  }}

  const dp = Array.from(
    {{length: leftTokens.length + 1}},
    () => new Uint16Array(rightTokens.length + 1)
  );
  for (let i = leftTokens.length - 1; i >= 0; i -= 1) {{
    for (let j = rightTokens.length - 1; j >= 0; j -= 1) {{
      dp[i][j] = leftTokens[i] === rightTokens[j]
        ? dp[i + 1][j + 1] + 1
        : Math.max(dp[i + 1][j], dp[i][j + 1]);
    }}
  }}

  const leftChanged = Array(leftTokens.length).fill(true);
  const rightChanged = Array(rightTokens.length).fill(true);
  let i = 0;
  let j = 0;
  while (i < leftTokens.length && j < rightTokens.length) {{
    if (leftTokens[i] === rightTokens[j]) {{
      leftChanged[i] = false;
      rightChanged[j] = false;
      i += 1;
      j += 1;
    }} else if (dp[i + 1][j] >= dp[i][j + 1]) {{
      i += 1;
    }} else {{
      j += 1;
    }}
  }}
  return [leftChanged, rightChanged];
}}

function appendDiffFragments(container, tokens, changed) {{
  let index = 0;
  while (index < tokens.length) {{
    const isChanged = changed[index];
    let text = "";
    while (index < tokens.length && changed[index] === isChanged) {{
      text += tokens[index];
      index += 1;
    }}
    if (isChanged) {{
      const span = document.createElement("span");
      span.className = "diff-changed";
      span.textContent = text;
      container.appendChild(span);
    }} else {{
      container.appendChild(document.createTextNode(text));
    }}
  }}
}}

function diffCell(value, other, side) {{
  const td = document.createElement("td");
  const code = document.createElement("code");
  code.className = "review-text";
  const leftTokens = splitTokens(value);
  const rightTokens = splitTokens(other);
  const [leftChanged, rightChanged] = diffMasks(leftTokens, rightTokens);
  appendDiffFragments(
    code,
    side === "left" ? leftTokens : rightTokens,
    side === "left" ? leftChanged : rightChanged
  );
  td.appendChild(code);
  return td;
}}

function columnWidth(index) {{
  return parseFloat(columns[index].style.width) || 120;
}}

function minimumColumnWidth(index) {{
  if (index === 2 || index === 3) {{
    return 220;
  }}
  if (index === 4) {{
    return 150;
  }}
  return 56;
}}

function setTableWidth() {{
  const width = columns.reduce((sum, column) => sum + (parseFloat(column.style.width) || 120), 0);
  table.style.width = `${{width}}px`;
}}

function setupColumnResizing() {{
  table.querySelectorAll("thead th").forEach((header, index) => {{
    if (!columns[index]) {{
      return;
    }}
    const handle = document.createElement("span");
    handle.className = "resize-handle";
    handle.addEventListener("mousedown", event => {{
      event.preventDefault();
      const startX = event.clientX;
      const startWidth = columnWidth(index);
      document.body.classList.add("resizing");

      function onMouseMove(moveEvent) {{
        const nextWidth = Math.max(minimumColumnWidth(index), startWidth + moveEvent.clientX - startX);
        columns[index].style.width = `${{nextWidth}}px`;
        setTableWidth();
      }}

      function onMouseUp() {{
        document.body.classList.remove("resizing");
        document.removeEventListener("mousemove", onMouseMove);
        document.removeEventListener("mouseup", onMouseUp);
      }}

      document.addEventListener("mousemove", onMouseMove);
      document.addEventListener("mouseup", onMouseUp);
    }});
    header.appendChild(handle);
  }});
  setTableWidth();
}}

function positionTooltip(trigger) {{
  const rect = trigger.getBoundingClientRect();
  floatingTooltip.hidden = false;
  const tipRect = floatingTooltip.getBoundingClientRect();
  let left = rect.right - tipRect.width;
  let top = rect.top - tipRect.height - 8;
  left = Math.max(12, Math.min(left, window.innerWidth - tipRect.width - 12));
  if (top < 12) {{
    top = Math.min(rect.bottom + 8, window.innerHeight - tipRect.height - 12);
  }}
  floatingTooltip.style.left = `${{left}}px`;
  floatingTooltip.style.top = `${{top}}px`;
}}

function showTooltip(trigger) {{
  const text = trigger.dataset.tooltip || "";
  if (!text) {{
    return;
  }}
  floatingTooltip.textContent = text;
  positionTooltip(trigger);
}}

function hideTooltip() {{
  floatingTooltip.hidden = true;
}}

function setupTooltips() {{
  document.querySelectorAll("[data-tooltip]").forEach(trigger => {{
    trigger.addEventListener("mouseenter", () => showTooltip(trigger));
    trigger.addEventListener("focus", () => showTooltip(trigger));
    trigger.addEventListener("mouseleave", hideTooltip);
    trigger.addEventListener("blur", hideTooltip);
  }});
  window.addEventListener("scroll", hideTooltip, true);
  window.addEventListener("resize", hideTooltip);
}}

function approvedIds() {{
  return [...document.querySelectorAll("input[data-role='approve']:checked")].map(input => input.dataset.id);
}}

function ignoredIds() {{
  return [...document.querySelectorAll("input[data-role='ignore']:checked")].map(input => input.dataset.id);
}}

function approvedItems() {{
  const approved = new Set(approvedIds());
  return items.filter(item => approved.has(String(item.id)));
}}

function ignoredItems() {{
  const ignored = new Set(ignoredIds());
  return items.filter(item => ignored.has(String(item.id)));
}}

function approvalPayload() {{
  return {{
    approved_ids: approvedIds(),
    approved_items: approvedItems(),
    ignored_ids: ignoredIds(),
    ignored_items: ignoredItems()
  }};
}}

function itemPriority(item) {{
  return Number.isFinite(Number(item.priority_rank)) ? Number(item.priority_rank) : 2;
}}

function itemOrder(item) {{
  return Number.isFinite(Number(item.first_order)) ? Number(item.first_order) : 0;
}}

function itemFirstLocation(item) {{
  return String(item.first_location || item.location || "");
}}

function itemType(item) {{
  return String(item.issue_type || "");
}}

function sortedItems() {{
  const mode = document.getElementById("sort-mode").value;
  return [...items].sort((a, b) => {{
    if (mode === "priority") {{
      return itemPriority(a) - itemPriority(b)
        || itemFirstLocation(a).localeCompare(itemFirstLocation(b), undefined, {{numeric: true}})
        || itemOrder(a) - itemOrder(b);
    }}
    if (mode === "type") {{
      return itemType(a).localeCompare(itemType(b), "zh-Hans-CN", {{numeric: true}})
        || itemPriority(a) - itemPriority(b)
        || itemFirstLocation(a).localeCompare(itemFirstLocation(b), undefined, {{numeric: true}})
        || itemOrder(a) - itemOrder(b);
    }}
    return itemFirstLocation(a).localeCompare(itemFirstLocation(b), undefined, {{numeric: true}})
      || itemPriority(a) - itemPriority(b)
      || itemOrder(a) - itemOrder(b);
  }});
}}

function refresh() {{
  const ids = approvedIds();
  const ignored = ignoredIds();
  document.querySelectorAll("tbody tr").forEach(row => {{
    row.classList.toggle("approved", row.querySelector("input[data-role='approve']").checked);
    row.classList.toggle("ignored", row.querySelector("input[data-role='ignore']").checked);
  }});
  status.textContent = `已批准 ${{ids.length}} 项；总是忽略 ${{ignored.length}} 项；未选择 ${{items.length - ids.length - ignored.length}} 项`;
}}

function renderRows() {{
  const checked = new Set(approvedIds());
  const ignored = new Set(ignoredIds());
  rows.innerHTML = "";
  sortedItems().forEach(item => {{
  const tr = document.createElement("tr");
  tr.appendChild(locationCell(item));
  tr.appendChild(textCell(item.issue_type));
  tr.appendChild(diffCell(item.current_text || item.current_problem, item.proposed_text || item.proposed_change, "left"));
  tr.appendChild(diffCell(item.current_text || item.current_problem, item.proposed_text || item.proposed_change, "right"));
  tr.appendChild(textCell(item.reason));
  const approve = document.createElement("td");
  approve.className = "approve choice";
  const approveBox = document.createElement("input");
  approveBox.type = "checkbox";
  approveBox.dataset.id = item.id;
  approveBox.dataset.role = "approve";
  approveBox.checked = checked.has(String(item.id));
  approveBox.addEventListener("change", () => {{
    if (approveBox.checked) {{
      tr.querySelector("input[data-role='ignore']").checked = false;
    }}
    refresh();
  }});
  approve.appendChild(approveBox);
  tr.appendChild(approve);
  const ignore = document.createElement("td");
  ignore.className = "ignore choice";
  const ignoreBox = document.createElement("input");
  ignoreBox.type = "checkbox";
  ignoreBox.dataset.id = item.id;
  ignoreBox.dataset.role = "ignore";
  ignoreBox.checked = ignored.has(String(item.id));
  ignoreBox.addEventListener("change", () => {{
    if (ignoreBox.checked) {{
      tr.querySelector("input[data-role='approve']").checked = false;
    }}
    refresh();
  }});
  ignore.appendChild(ignoreBox);
  tr.appendChild(ignore);
  rows.appendChild(tr);
  }});
  refresh();
}}

document.getElementById("sort-mode").addEventListener("change", renderRows);

document.getElementById("select-all").addEventListener("click", () => {{
  document.querySelectorAll("input[data-role='approve']").forEach(input => input.checked = true);
  document.querySelectorAll("input[data-role='ignore']").forEach(input => input.checked = false);
  refresh();
}});

document.getElementById("clear-all").addEventListener("click", () => {{
  document.querySelectorAll("input[data-id]").forEach(input => input.checked = false);
  refresh();
}});

document.getElementById("close-page").addEventListener("click", async () => {{
  if (!submitUrl) {{
    status.textContent = "已关闭审批。";
    setTimeout(() => window.close(), 200);
    return;
  }}
  try {{
    await fetch("/cancel", {{
      method: "POST",
      headers: {{"Content-Type": "application/json"}},
      body: JSON.stringify({{cancelled: true}})
    }});
    status.textContent = "已关闭审批，本次不会修改文件。";
  }} catch (error) {{
    status.textContent = "关闭请求失败；可以直接关闭此窗口。";
  }}
  setTimeout(() => {{
    window.close();
  }}, 300);
}});

function downloadApproval() {{
  const blob = new Blob([JSON.stringify(approvalPayload(), null, 2)], {{type: "application/json"}});
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "rev-check-approval.json";
  link.click();
  URL.revokeObjectURL(url);
}}

document.getElementById("confirm").addEventListener("click", async () => {{
  const payload = approvalPayload();
  if (!submitUrl) {{
    downloadApproval();
    status.textContent = "已下载批准 JSON。";
    return;
  }}
  const response = await fetch(submitUrl, {{
    method: "POST",
    headers: {{"Content-Type": "application/json"}},
    body: JSON.stringify(payload)
  }});
  if (!response.ok) {{
    status.textContent = "确认失败，请回到 agent 重新打开审批页。";
    return;
  }}
  status.textContent = `已确认批准 ${{payload.approved_ids.length}} 项，总是忽略 ${{payload.ignored_ids.length}} 项。Agent 将继续处理。`;
  if (autoClose) {{
    setTimeout(() => {{
      window.close();
    }}, 600);
  }}
}});

setupColumnResizing();
setupTooltips();
renderRows();
</script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a local HTML approval checklist.")
    parser.add_argument("items_json", type=Path, help="JSON file containing review items.")
    parser.add_argument("--output", type=Path, default=Path("revision-review.html"))
    parser.add_argument("--title", default="Revision Review")
    parser.add_argument("--submit-url", default=None, help="Optional URL that receives approval JSON.")
    parser.add_argument("--auto-close", action="store_true", help="Try to close the browser window after confirmation.")
    args = parser.parse_args()

    items = load_items(args.items_json)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html_document(items, args.title, args.submit_url, args.auto_close), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
