---
name: code-summary
description: >-
  Turns git commits into a Chinese Markdown technical feature document (API,
  protocol, flow diagrams, risks, usage examples, commit table). Supports start
  commit through HEAD, explicit SHA list, or default window. Use for 代码总结,
  技术文档, feature doc from commits, or /code-summary with SHAs.
---

# Code Summary (Git → Markdown)

## When to apply

Use this skill when the user wants a **code / change summary** from git, especially with any of:

- A **start commit** (inclusive range through latest / specified end)
- **Specific commits** (one or more SHAs)
- Output as **Markdown file** with a **short English filename** (see below)

Default language for the summary body: **Simplified Chinese** unless the user asks otherwise.

**Output mode (default vs optional):**

- **Default — `feature-doc`**: read like **end-user / 联调 oriented technical doc** (same section order as a good `*_snap.md`: 概述 → 实现细节 → 触发方式 → 执行步骤框图 → 风险 → 示例 → 提交表 → 平台).
- **Optional — `commit-changelog`**: only if the user explicitly asks for **变更说明 / PR 说明 / 纯提交总结** — then use the shorter “范围说明 / 变更概览 / 关键文件 …” checklist (legacy style).

---

## Inputs (resolve in this order)

1. **Explicit commit list**  
   If the user gives one or more SHAs (e.g. `abc1234`, `def5678` or `abc1234..def5678` as a list):  
   **Only** summarize those commits, in **chronological order** (oldest first).  
   Collect history with **one** shell command (see **Claude Code / Bash** below)—do **not** spawn **parallel** `Bash` tool calls per SHA (that often triggers `Invalid tool parameters` / `parallel tool call Bash errored`).

2. **Start commit**  
   If the user gives a **start commit** (and no conflicting explicit list):  
   Summarize **from that commit through**:
   - **HEAD**, or
   - an **end commit** if the user also names one (inclusive range).  
   Use: `git log --reverse --oneline <start>^..<end>` and `git diff <start>^..<end>` (or `<start>..<end>` if the user said “between” clearly—confirm if ambiguous).  
   Prefer **`^..`** so the start commit itself is included when the user says “从某 commit 开始”.

3. **Neither**  
   If nothing is specified: ask once, or use a small default (e.g. last **10** commits or **7 days**) and state it in the doc.

---

## What to collect (run in repo root)

- `cd` to the **git repository root** first (Claude Code cwd may not be the repo).
- `git status -sb` and current branch name (context only).
- For **ranges**: `git log --reverse --oneline <range>`, then `git diff --stat <range>`, then targeted `git diff <range> -- <paths>` for hot files.
- For **listed SHAs**: prefer **one** `Bash` invocation (loop below), not N parallel calls.
- Optionally: `git diff-tree --no-commit-id --name-only -r <sha>` per commit for file lists.

Read **actual file contents** when the diff alone is unclear (renames, generated code, large moves).

---

## Default Markdown structure (`feature-doc`)

Produce **one** `.md` file. Section **order and depth** should match a strong feature write-up (reference style: `jpeg_snap.md`):

### Title

`# <功能名> 技术文档` — 功能名用中文，具体、可搜索（例如「JPEG 快照功能」）。

### 1. `## 概述`

2–5 句：做什么、谁会用、和主流程（如远程桌面/主码流）的关系。**可在一句话里带分支名 + 时间范围**（代替单独大段「范围说明」）。

### 2. `## 实现细节`

#### `### 1. 核心接口`

对每个**对外**入口（C/C++ API、全局函数等）列出：

- **签名**（从源码复制）
- **位置**：`路径:行号`（打开文件核对）
- **功能**、**参数**、**返回值**

#### `### 2. 协议 / 命令 / 配置`（若本次变更涉及）

例如 UDS 命令码、JSON 字段、默认值；写清 **头文件/常量定义位置**。

#### `### 3. 主要实现文件`

| 文件 | 说明 |

### 3. `## 触发方式`

分小节（如「UDS」「直接调用 SDK」），给出**可复制**的 JSON / 命令行 / 伪代码示例。默认值、可选字段写清楚。

### 4. `## 函数执行步骤`

用 **ASCII 框图**（`┌──…──┐`）按**调用链**分层，例如：UDS 回调 → `board_sdk_*` → 平台实现 → MPI 调用。

- 每一步标注 **仓库内真实路径**（函数名必须与源码一致）。
- **禁止臆造**代码中不存在的函数、宏、模块名、芯片 API 名；若未在已读文件中看到，写「以仓库 `path/to/file` 实现为准」或省略该层。

### 5. `## 潜在风险`

编号列表；每条包含 **风险** + **缓解措施**（可含并发、权限、阻塞、分辨率切换、资源争用等——按 diff 实际能支撑的内容写，不要空泛堆砌）。

### 6. `## 使用示例`

- Shell / 测试命令（路径、socket 名与项目一致）
- 可选 C/C++ 片段（需与头文件、类型一致）

### 7. `## 相关提交记录`

| 提交（短 SHA） | 说明 |

说明列：**一句人话**，优先结合 diff；可按时间从上到下。

### 8. `## 平台支持`（如适用）

写清哪些 SoC / `board_sdk_api_*` 已实现，其他平台是 stub 还是未实现。

---

### Code citations

When quoting code, use workspace line format only:

```12:18:path/from/repo/root.cpp
// excerpt
```

No HTML entities inside fences.

---

### Legacy structure (`commit-changelog` only)

If the user explicitly wants **纯变更说明**，再用旧模板：**范围说明 → 变更概览 → 按模块分组 → 关键文件 → 行为与兼容性 → 未决与后续**。

---

## Output file naming

- **格式**: 纯英文小写（或数字），**仅** `[a-z0-9_-]`，**最多 32 个字符**，扩展名 **`.md`**。  
- **含义**: 压缩功能主题，例如 `uds-auto-chn-alloc.md`、`mpi-so-dlopen.md`、`jpeg-grap-vi-feed.md`。  
- **长度**: 不含 `.md` 的 stem ≤ **32**。若过长，缩写关键词（`feat`→`f`, `refactor`→`ref`, `video-server`→`vsrv`）并保持可读。  
- **位置**: 默认写在用户指定目录；未指定则 **repo 根目录** 或用户说的 `docs/`；不要擅自创建用户未提及的大型目录结构。

---

## Quality bar (align with user expectations)

- **完整句**、结构清晰；面向「要看懂怎么用、怎么排错」的读者，而不仅是「提交了哪些文件」。
- **只写与变更相关的内容**；不扩写无关重构。
- 若某 commit 消息为空或含糊，以 **diff + 当前文件内容** 为准。
- **准确性优先于篇幅**：宁可少写一个子流程，也不要编造 RK_MPI / 驱动层不存在的调用名；所有命令码、路径、默认文件名以 **grep/读文件** 核实。

---

## Quick examples (for the agent)

**Range:**  
User: “从 `a1b2c3d` 总结到现在”  
→ Summarize `a1b2c3d^..HEAD` (include `a1b2c3d`), filename e.g. `summary-a1b2c3d-to-head.md` only if ≤32 chars; else shorter theme name.

**Explicit SHAs:**  
User: “总结 `e1e1e1`、`f2f2f2` 两个 commit”  
→ Default: full **`feature-doc`** (概述…提交表…); filename e.g. `jpeg-snap-uds-api.md` (theme, ≤32 chars).

**Conflict:**  
User gives both start commit and explicit list → **prefer explicit list**; mention the ignored range briefly under **概述** or **相关提交记录** 表头说明。

---

## Claude Code / Bash (avoid tool errors)

Claude Code’s `Bash` tool often **fails or cancels** when the model issues **several parallel** `git show` calls. Follow this:

1. **Single `Bash` call** for multiple SHAs — loop and print separators:

```bash
cd "/absolute/path/to/repo" || exit 1
for c in \
  9a717be50f2ed23814ea731fce8d2ddca4305251 \
  33b564894c7831b3d9de36824af41dd34ba4bbcd \
  88a7c63497b67f62a10167ebf44583d334ad80d8 \
  330f60af9b7bfb1958242bdece86e044c0a3a7ca
do
  echo "======== COMMIT $c ========"
  git show --no-patch --stat --format=fuller "$c" && git show "$c"
done
```

2. **Sort chronologically** before writing the doc (oldest first). In **one** shell, e.g.:

```bash
for c in SHA1 SHA2 SHA3 SHA4; do git show -s --format="%ct %H" "$c"; done | sort -n
```

Use the resulting commit order as section order in the Markdown.

3. **Do not** pass empty command, or malformed quoting; keep the command as a **single string** with newlines only inside the script if the tool allows, or use `;` between statements.

4. If `/code-summary` passes args as one line of space-separated SHAs, **split on whitespace** and substitute into the `for c in ...` list.

---

## Cursor

The same skill lives under `~/.cursor/skills/code-summary/` for Cursor agents.
