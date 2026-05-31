"""Local web control panel for JH-MultiAgent.

Run:
    python -X utf8 web_control_panel.py
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import socket
import string
import subprocess
import sys
import time
import uuid
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


BASE = Path(__file__).resolve().parent
TASKS_DIR = BASE / "tasks"
LOCAL_DIR = BASE / "_local"
UPLOADS_DIR = LOCAL_DIR / "uploads"
URL_MARKER = LOCAL_DIR / "web-control-panel-url.txt"


def now_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z가-힣_-]+", "-", text.strip())
    cleaned = re.sub(r"-+", "-", cleaned).strip("-_")
    if not cleaned:
        cleaned = "natural-language-task"
    return cleaned[:48]


def read_yaml_field(text: str, field: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(field + ":"):
            return stripped.split(":", 1)[1].strip()
    return ""


def load_tasks() -> list[dict[str, object]]:
    tasks: list[dict[str, object]] = []
    if not TASKS_DIR.exists():
        return tasks
    for task_dir in sorted(TASKS_DIR.iterdir(), key=lambda p: p.name.lower()):
        if not task_dir.is_dir() or task_dir.name == ".gitkeep":
            continue
        task_file = task_dir / "task.md"
        if not task_file.exists():
            continue
        try:
            content = task_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = task_file.read_text(errors="replace")
        workers_dir = task_dir / "workers"
        workers = []
        if workers_dir.exists():
            workers = [p.name for p in workers_dir.iterdir() if p.is_dir()]
        tasks.append(
            {
                "name": task_dir.name,
                "status": read_yaml_field(content, "status") or "unknown",
                "priority": read_yaml_field(content, "priority") or "-",
                "updated": read_yaml_field(content, "updated") or "-",
                "workers": workers,
            }
        )
    return tasks


def run_command(args: list[str], timeout: int = 30) -> dict[str, object]:
    try:
        result = subprocess.run(
            args,
            cwd=BASE,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return {
            "ok": result.returncode == 0,
            "code": result.returncode,
            "output": (result.stdout + result.stderr).strip(),
        }
    except Exception as exc:
        return {"ok": False, "code": -1, "output": str(exc)}


def command_exists(name: str) -> bool:
    checker = ["powershell", "-NoProfile", "-Command", f"Get-Command {name} -ErrorAction SilentlyContinue"]
    return bool(run_command(checker, timeout=5)["ok"])


def system_status() -> dict[str, object]:
    return {
        "base": str(BASE),
        "tasks": load_tasks(),
        "tools": {
            "python": command_exists("python"),
            "claude": command_exists("claude"),
            "codex": command_exists("codex"),
        },
        "files": {
            "AGENTS.md": (BASE / "AGENTS.md").exists(),
            "CLAUDE.md": (BASE / "CLAUDE.md").exists(),
            ".mcp.json": (BASE / ".mcp.json").exists(),
            "selfcheck": (BASE / "_shared" / "run-selfcheck.ps1").exists(),
        },
    }


def safe_child_path(parent: Path, raw_name: str) -> Path:
    name = Path(raw_name).name
    name = re.sub(r"[^0-9A-Za-z가-힣._ -]+", "_", name).strip(" .")
    if not name:
        name = f"upload-{uuid.uuid4().hex}.bin"
    return parent / name


def list_local_drives() -> list[dict[str, str]]:
    drives: list[dict[str, str]] = []
    if os.name == "nt":
        for letter in string.ascii_uppercase:
            root = Path(f"{letter}:\\")
            if root.exists():
                drives.append({"name": f"{letter}:\\", "path": str(root)})
    else:
        drives.append({"name": "/", "path": "/"})
        home = Path.home()
        if home.exists():
            drives.append({"name": str(home), "path": str(home)})
    return drives


def list_directory(path_value: str) -> dict[str, object]:
    if not path_value:
        path = BASE
    else:
        path = Path(path_value).expanduser()
    path = path.resolve()
    if not path.exists():
        raise ValueError(f"경로가 존재하지 않습니다: {path}")
    if not path.is_dir():
        raise ValueError(f"폴더가 아닙니다: {path}")

    entries = []
    try:
        children = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        children = []
    for child in children:
        if child.is_dir():
            entries.append({"name": child.name, "path": str(child)})

    parent = path.parent if path.parent != path else None
    return {
        "path": str(path),
        "parent": str(parent) if parent else "",
        "entries": entries[:300],
    }


def create_task(payload: dict[str, object]) -> dict[str, object]:
    request = str(payload.get("request", "")).strip()
    if not request:
        raise ValueError("자연어 개발 요청을 입력해야 합니다.")

    target_repo = str(payload.get("targetRepo", "")).strip()
    model = str(payload.get("model", "default")).strip() or "default"
    permission = str(payload.get("permission", "approval-required")).strip() or "approval-required"
    options = payload.get("options", {})
    if not isinstance(options, dict):
        options = {}

    task_name = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{slugify(request)}"
    task_dir = TASKS_DIR / task_name
    task_dir.mkdir(parents=True, exist_ok=False)
    (task_dir / "workers").mkdir(exist_ok=True)
    (task_dir / "sources").mkdir(exist_ok=True)
    (task_dir / "artifacts").mkdir(exist_ok=True)

    planned_workers = [
        {"role": "claude-main", "purpose": "자연어 개발 요청 분석 및 구현 계획 수립"},
    ]
    if options.get("autoReview"):
        planned_workers.append({"role": "codex-critic", "purpose": "산출물 독립 검수"})

    worker_yaml = "\n".join(
        f"- role: {worker['role']}\n  purpose: {worker['purpose']}" for worker in planned_workers
    )
    option_lines = "\n".join(f"- {key}: {value}" for key, value in sorted(options.items()))
    if not option_lines:
        option_lines = "- 선택 옵션 없음"

    task_md = f"""# {task_name}

## 메타

```yaml
status: pending
created: {now_date()}
updated: {now_date()}
priority: medium
```

## Goal

{request}

## Constraints

- 사용자는 자연어 개발 요청으로 작업을 시작한다.
- worker 호출 전 사용자 승인을 받아야 한다.
- 외부 repo 직접 쓰기는 target_repo, write_scope, task 승인, log [APPROVAL]이 모두 있을 때만 허용한다.
- commit/push는 사용자가 명시하지 않는 한 수행하지 않는다.

## Acceptance Criteria

- [ ] 요청이 task/context/log 파일에 보존된다.
- [ ] 필요한 worker가 최소 범위로 선정된다.
- [ ] 실행 전 승인 게이트가 유지된다.
- [ ] 검증 결과가 log.md에 기록된다.

## Worker Plan

```yaml
workers_approved: []
planned_workers:
{worker_yaml}
```

## Context Snapshot

- target_repo: {target_repo or "N/A"}
- model: {model}
- permission: {permission}
- selected_options:
{option_lines}

## Notes

웹 컨트롤 패널에서 생성된 작업 초안입니다. Claude orchestrator에서 이 task를 이어서 진행하세요.
"""
    context_md = f"""# Context — {task_name}

## 현재 상태

사용자가 웹 컨트롤 패널에서 자연어 개발 요청을 입력했습니다.

## 핵심 정보

- 요청: {request}
- target_repo: {target_repo or "N/A"}
- model: {model}
- permission: {permission}
- options:
{option_lines}

## 미해결 이슈

- worker 호출 전 사용자의 승인 필요.
- 외부 repo 쓰기 범위가 필요하면 target_repo와 write_scope를 확정해야 함.
"""
    log_md = f"""# Log — {task_name}

[{now_stamp()}] [DECISION] 웹 컨트롤 패널에서 task 초안 생성. target_repo={target_repo or "N/A"}, model={model}, permission={permission}
"""

    (task_dir / "task.md").write_text(task_md, encoding="utf-8")
    (task_dir / "context.md").write_text(context_md, encoding="utf-8")
    (task_dir / "log.md").write_text(log_md, encoding="utf-8")

    start_prompt = f"""JH-MultiAgent 작업을 시작하세요.

task_path: {task_dir}
target_repo: {target_repo or "N/A"}
permission: {permission}
model: {model}

사용자 요청:
{request}

진행 규칙:
- 먼저 task.md, context.md, log.md를 읽고 현재 상태를 확인하세요.
- 필요한 경우 target_repo에서 구현하세요.
- 외부 repo 쓰기는 사용자가 승인한 범위 안에서만 수행하세요.
- commit/push는 사용자가 명시적으로 요청한 경우에만 수행하세요.
- 진행 상태와 검증 결과를 사용자에게 명확히 보고하세요.
"""
    prompt_path = task_dir / "artifacts" / "claude-start-prompt.txt"
    prompt_path.write_text(start_prompt, encoding="utf-8")

    return {"task": task_name, "path": str(task_dir), "promptPath": str(prompt_path), "targetRepo": target_repo}


def parse_multipart(body: bytes, content_type: str) -> list[tuple[str, bytes]]:
    match = re.search(r"boundary=(.+)", content_type)
    if not match:
        raise ValueError("multipart boundary가 없습니다.")
    boundary = match.group(1).strip().strip('"').encode()
    files: list[tuple[str, bytes]] = []
    for part in body.split(b"--" + boundary):
        if not part or part in (b"--\r\n", b"--"):
            continue
        header_blob, sep, data = part.partition(b"\r\n\r\n")
        if not sep:
            continue
        headers = header_blob.decode("utf-8", errors="replace")
        filename_match = re.search(r'filename="([^"]*)"', headers)
        if not filename_match:
            continue
        filename = filename_match.group(1)
        data = data.rstrip(b"\r\n")
        files.append((filename, data))
    return files


def ps_single_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def launch_interactive(command_name: str, payload: dict[str, object] | None = None) -> dict[str, object]:
    payload = payload or {}
    if command_name not in {"claude", "codex"}:
        raise ValueError("허용되지 않은 명령입니다.")
    title = "JH Claude Orchestrator" if command_name == "claude" else "JH Codex Review"
    cwd = BASE
    target_repo = str(payload.get("targetRepo", "") or "").strip()
    if target_repo and Path(target_repo).exists():
        cwd = Path(target_repo)

    if command_name == "claude" and payload.get("promptPath"):
        prompt_path = str(payload["promptPath"])
        ps = (
            "Set-Location -LiteralPath "
            + ps_single_quote(str(cwd))
            + f"; Write-Host '{title}' -ForegroundColor Cyan"
            + f"; Write-Host '요청 프롬프트를 Claude에 전달합니다.' -ForegroundColor Yellow"
            + "; $prompt = [System.IO.File]::ReadAllText("
            + ps_single_quote(prompt_path)
            + ", [System.Text.Encoding]::UTF8)"
            + "; claude $prompt"
        )
    else:
        ps = (
            "Set-Location -LiteralPath "
            + ps_single_quote(str(cwd))
            + f"; Write-Host '{title}' -ForegroundColor Cyan; {command_name}"
        )
    subprocess.Popen(
        ["cmd", "/c", "start", title, "powershell", "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", ps],
        cwd=BASE,
        shell=False,
    )
    return {"ok": True, "message": f"{title} 창을 열었습니다.", "cwd": str(cwd)}


HTML_PAGE = r"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>JH-MultiAgent Control Panel</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f7fb;
      --panel: #ffffff;
      --ink: #172033;
      --muted: #69758a;
      --line: #dce3ef;
      --accent: #0d7a68;
      --accent-dark: #075c4f;
      --danger: #b42318;
      --warn: #9a5b00;
      --ok: #087443;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", "Malgun Gothic", Arial, sans-serif;
      background: var(--bg);
      color: var(--ink);
      letter-spacing: 0;
    }
    .app {
      min-height: 100vh;
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr) 340px;
    }
    aside, main, .right {
      padding: 18px;
    }
    aside {
      background: #101828;
      color: #f8fafc;
      border-right: 1px solid #0b1220;
    }
    .brand {
      font-size: 18px;
      font-weight: 700;
      margin-bottom: 18px;
    }
    .section-title {
      margin: 18px 0 8px;
      font-size: 12px;
      color: #aab7cf;
      text-transform: uppercase;
      font-weight: 700;
    }
    button, select, input, textarea {
      font: inherit;
    }
    .rail-button, .primary, .secondary {
      width: 100%;
      min-height: 42px;
      border-radius: 8px;
      border: 1px solid transparent;
      cursor: pointer;
      text-align: left;
    }
    .rail-button {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 9px 10px;
      margin-bottom: 8px;
      color: #f8fafc;
      background: #1d2939;
    }
    .rail-button:hover { background: #26364f; }
    .toggle {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 10px;
      margin-bottom: 8px;
      border: 1px solid #2f405d;
      border-radius: 8px;
      background: #162238;
      cursor: pointer;
    }
    .toggle input { width: 18px; height: 18px; }
    main {
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }
    h1 {
      margin: 0 0 8px;
      font-size: 24px;
    }
    .muted { color: var(--muted); }
    label {
      display: block;
      font-size: 13px;
      font-weight: 700;
      margin-bottom: 6px;
    }
    textarea {
      width: 100%;
      min-height: 170px;
      resize: vertical;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    input[type="text"], select {
      width: 100%;
      min-height: 40px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px 10px;
      background: #fff;
    }
    .grid2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    .actions {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 10px;
      margin-top: 12px;
    }
    .path-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 92px;
      gap: 8px;
    }
    .primary {
      text-align: center;
      color: white;
      background: var(--accent);
      border-color: var(--accent-dark);
      font-weight: 700;
    }
    .primary:hover { background: var(--accent-dark); }
    .secondary {
      text-align: center;
      color: var(--ink);
      background: #eef3f8;
      border-color: var(--line);
    }
    .status-line {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      padding: 9px 0;
      border-bottom: 1px solid var(--line);
    }
    .status-line:last-child { border-bottom: 0; }
    .pill {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 2px 8px;
      border-radius: 999px;
      font-weight: 700;
      font-size: 12px;
    }
    .ok { color: var(--ok); background: #e8f7ef; }
    .bad { color: var(--danger); background: #ffebe8; }
    .warn { color: var(--warn); background: #fff5db; }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      max-height: 260px;
      overflow: auto;
      padding: 12px;
      border-radius: 8px;
      background: #111827;
      color: #f9fafb;
    }
    .task {
      padding: 10px 0;
      border-bottom: 1px solid var(--line);
    }
    .task:last-child { border-bottom: 0; }
    .task strong { display: block; }
    .modal-backdrop {
      position: fixed;
      inset: 0;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 18px;
      background: rgba(15, 23, 42, 0.48);
      z-index: 20;
    }
    .modal-backdrop.open { display: flex; }
    .modal {
      width: min(760px, 96vw);
      max-height: 86vh;
      display: flex;
      flex-direction: column;
      gap: 12px;
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      box-shadow: 0 18px 70px rgba(15, 23, 42, 0.24);
    }
    .modal-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
    }
    .folder-list {
      min-height: 260px;
      max-height: 420px;
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    .folder-item {
      width: 100%;
      display: block;
      text-align: left;
      padding: 10px 12px;
      border: 0;
      border-bottom: 1px solid var(--line);
      background: #fff;
      cursor: pointer;
    }
    .folder-item:hover { background: #f0f5fa; }
    .folder-item:last-child { border-bottom: 0; }
    .modal-actions {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 10px;
    }
    @media (max-width: 1100px) {
      .app { grid-template-columns: 230px minmax(0, 1fr); }
      .right { grid-column: 1 / -1; }
    }
    @media (max-width: 760px) {
      .app { grid-template-columns: 1fr; }
      aside { border-right: 0; }
      .grid2, .actions { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <div class="brand">JH-MultiAgent</div>
      <button class="rail-button" id="openFolder">📁 폴더 진입</button>
      <button class="rail-button" id="insertLink">🔗 링크 전송</button>
      <button class="rail-button" id="uploadButton">📎 파일 업로드</button>
      <input id="fileInput" type="file" multiple hidden>

      <div class="section-title">실행 옵션</div>
      <label class="toggle"><span>기본 권한</span><input id="basicPermission" type="checkbox" checked></label>
      <label class="toggle"><span>자동 검토</span><input id="autoReview" type="checkbox" checked></label>
      <label class="toggle"><span>골모드 작동</span><input id="goalMode" type="checkbox"></label>
      <label class="toggle"><span>케이브맨 실행</span><input id="caveman" type="checkbox"></label>

      <div class="section-title">모델</div>
      <select id="model">
        <option value="default">기본 모델</option>
        <option value="lightweight">가벼운 모델</option>
        <option value="high-reasoning">고추론 모델</option>
      </select>

      <div class="section-title">세션</div>
      <button class="rail-button" id="startClaude">▶ Claude Orchestrator</button>
      <button class="rail-button" id="startCodex">◎ Codex Review</button>
    </aside>

    <main>
      <section class="panel">
        <h1>자연어 개발 요청</h1>
        <p class="muted">요청을 입력한 뒤 Enter를 누르면 task를 만들고 Claude orchestrator 개발 세션을 엽니다. 줄바꿈은 Shift+Enter입니다.</p>
        <label for="request">요청</label>
        <textarea id="request" placeholder="예: D:\ai프로젝트\sniper-buying-dashboard에서 관리자 화면에 에이전트 실행 로그 탭 추가해줘."></textarea>
        <div class="grid2">
          <div>
            <label for="targetRepo">target_repo</label>
            <div class="path-row">
              <input id="targetRepo" type="text" placeholder="예: D:\ai프로젝트\sniper-buying-dashboard">
              <button class="secondary" id="browseRepo" type="button">찾기</button>
            </div>
          </div>
          <div>
            <label for="permission">권한 모드</label>
            <select id="permission">
              <option value="approval-required">승인 후 worker 호출</option>
              <option value="read-only-review">읽기 전용 검토</option>
              <option value="tasks-only">task 내부 산출물만</option>
            </select>
          </div>
        </div>
        <div class="actions">
          <button class="primary" id="createTask">진행: 개발 착수</button>
          <button class="secondary" id="runSelfcheck">자가검증</button>
          <button class="secondary" id="refresh">상태 새로고침</button>
        </div>
      </section>
      <section class="panel">
        <h2>결과</h2>
        <pre id="output">대기 중</pre>
      </section>
    </main>

    <section class="right">
      <div class="panel">
        <h2>시스템 상태</h2>
        <div id="status"></div>
      </div>
      <div class="panel" style="margin-top:14px">
        <h2>Tasks</h2>
        <div id="tasks"></div>
      </div>
    </section>
  </div>

  <div class="modal-backdrop" id="folderModal" aria-hidden="true">
    <div class="modal" role="dialog" aria-modal="true" aria-labelledby="folderTitle">
      <div class="modal-head">
        <div>
          <h2 id="folderTitle">작업 폴더 선택</h2>
          <p class="muted" id="folderPath">드라이브 선택</p>
        </div>
        <button class="secondary" id="closeFolder" type="button" style="width:88px">닫기</button>
      </div>
      <div class="folder-list" id="folderList"></div>
      <div class="modal-actions">
        <button class="secondary" id="folderUp" type="button">상위 폴더</button>
        <button class="primary" id="chooseFolder" type="button">이 폴더 지정</button>
        <button class="secondary" id="folderRefresh" type="button">새로고침</button>
      </div>
    </div>
  </div>

  <script>
    const $ = (id) => document.getElementById(id);
    const out = $("output");
    let currentFolder = "";

    function selectedOptions() {
      return {
        basicPermission: $("basicPermission").checked,
        autoReview: $("autoReview").checked,
        goalMode: $("goalMode").checked,
        caveman: $("caveman").checked
      };
    }

    async function api(path, options = {}) {
      const response = await fetch(path, options);
      const text = await response.text();
      let data;
      try { data = JSON.parse(text); } catch { data = { ok: false, output: text }; }
      if (!response.ok) throw new Error(data.error || data.output || response.statusText);
      return data;
    }

    function write(data) {
      out.textContent = typeof data === "string" ? data : JSON.stringify(data, null, 2);
    }

    async function refreshStatus() {
      const data = await api("/api/status");
      const tool = (name, ok) => `<div class="status-line"><span>${name}</span><span class="pill ${ok ? "ok" : "bad"}">${ok ? "OK" : "NG"}</span></div>`;
      $("status").innerHTML = [
        `<div class="status-line"><span>경로</span><span>${data.base}</span></div>`,
        tool("python", data.tools.python),
        tool("claude", data.tools.claude),
        tool("codex", data.tools.codex),
        tool(".mcp.json", data.files[".mcp.json"]),
        tool("selfcheck", data.files.selfcheck)
      ].join("");
      $("tasks").innerHTML = data.tasks.length
        ? data.tasks.map(t => `<div class="task"><strong>${t.name}</strong><span class="muted">${t.status} · ${t.priority} · ${t.updated}</span></div>`).join("")
        : `<p class="muted">아직 task가 없습니다.</p>`;
    }

    async function openFolderPicker(startPath = "") {
      $("folderModal").classList.add("open");
      $("folderModal").setAttribute("aria-hidden", "false");
      if (startPath) {
        await loadFolder(startPath);
      } else {
        await loadDrives();
      }
    }

    function closeFolderPicker() {
      $("folderModal").classList.remove("open");
      $("folderModal").setAttribute("aria-hidden", "true");
    }

    function renderFolderItems(items) {
      $("folderList").innerHTML = items.length
        ? items.map(item => `<button class="folder-item" data-path="${item.path.replaceAll('"', '&quot;')}">📁 ${item.name}</button>`).join("")
        : `<div class="folder-item muted">표시할 하위 폴더가 없습니다.</div>`;
      for (const button of $("folderList").querySelectorAll("button[data-path]")) {
        button.onclick = () => loadFolder(button.dataset.path);
      }
    }

    async function loadDrives() {
      currentFolder = "";
      $("folderPath").textContent = "드라이브 선택";
      const data = await api("/api/drives");
      renderFolderItems(data.drives);
    }

    async function loadFolder(path) {
      const data = await api(`/api/list-dir?path=${encodeURIComponent(path)}`);
      currentFolder = data.path;
      $("folderPath").textContent = data.path;
      renderFolderItems(data.entries);
      $("folderUp").disabled = !data.parent;
      $("folderUp").dataset.parent = data.parent || "";
    }

    $("refresh").onclick = async () => {
      try { await refreshStatus(); write("상태를 새로고침했습니다."); } catch (e) { write("오류: " + e.message); }
    };
    $("runSelfcheck").onclick = async () => {
      write("자가검증 실행 중...");
      try { write(await api("/api/selfcheck", { method: "POST" })); await refreshStatus(); } catch (e) { write("오류: " + e.message); }
    };
    async function startDevelopment() {
      write("개발 착수 준비 중...");
      try {
        const payload = {
          request: $("request").value,
          targetRepo: $("targetRepo").value,
          model: $("model").value,
          permission: $("permission").value,
          options: selectedOptions()
        };
        const created = await api("/api/create-task", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
        await refreshStatus();
        const launched = await api("/api/start-session", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ command: "claude", promptPath: created.promptPath, targetRepo: created.targetRepo }) });
        write({
          ok: true,
          status: "Claude 개발 세션 시작됨",
          task: created.task,
          taskPath: created.path,
          promptPath: created.promptPath,
          cliWorkingDirectory: launched.cwd,
          message: "새 PowerShell 창의 Claude가 이 요청 프롬프트를 받은 상태입니다."
        });
      } catch (e) { write("오류: " + e.message); }
    }
    $("createTask").onclick = startDevelopment;
    $("request").addEventListener("keydown", async (event) => {
      if (event.key === "Enter" && !event.shiftKey && !event.ctrlKey && !event.altKey && !event.isComposing) {
        event.preventDefault();
        await startDevelopment();
      }
    });
    $("openFolder").onclick = async () => {
      try { write(await api("/api/open-folder", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ path: $("targetRepo").value }) })); } catch (e) { write("오류: " + e.message); }
    };
    $("browseRepo").onclick = async () => {
      try { await openFolderPicker($("targetRepo").value.trim()); } catch (e) { write("오류: " + e.message); await openFolderPicker(""); }
    };
    $("closeFolder").onclick = closeFolderPicker;
    $("folderModal").addEventListener("click", (event) => {
      if (event.target === $("folderModal")) closeFolderPicker();
    });
    $("folderRefresh").onclick = async () => {
      try { currentFolder ? await loadFolder(currentFolder) : await loadDrives(); } catch (e) { write("오류: " + e.message); }
    };
    $("folderUp").onclick = async () => {
      const parent = $("folderUp").dataset.parent;
      if (parent) await loadFolder(parent);
    };
    $("chooseFolder").onclick = () => {
      if (!currentFolder) {
        write("드라이브 안의 작업 폴더를 선택하세요.");
        return;
      }
      $("targetRepo").value = currentFolder;
      closeFolderPicker();
      write(`작업 폴더 지정: ${currentFolder}`);
    };
    $("insertLink").onclick = () => {
      const link = prompt("전송할 링크를 입력하세요.");
      if (link) $("request").value += `\n\n참고 링크: ${link}`;
    };
    $("uploadButton").onclick = () => $("fileInput").click();
    $("fileInput").onchange = async () => {
      const form = new FormData();
      for (const file of $("fileInput").files) form.append("files", file);
      write("파일 업로드 중...");
      try { write(await api("/api/upload", { method: "POST", body: form })); } catch (e) { write("오류: " + e.message); }
    };
    $("startClaude").onclick = async () => {
      try { write(await api("/api/start-session", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ command: "claude" }) })); } catch (e) { write("오류: " + e.message); }
    };
    $("startCodex").onclick = async () => {
      try { write(await api("/api/start-session", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ command: "codex" }) })); } catch (e) { write("오류: " + e.message); }
    };

    refreshStatus().catch(e => write("초기 상태 확인 실패: " + e.message));
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "JHMultiAgentWeb/1.0"

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stderr.write("[%s] %s\n" % (now_stamp(), fmt % args))

    def send_json(self, data: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        return self.rfile.read(length) if length else b""

    def read_json(self) -> dict[str, object]:
        body = self.read_body()
        if not body:
            return {}
        return json.loads(body.decode("utf-8"))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            body = HTML_PAGE.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/api/status":
            self.send_json(system_status())
            return
        if parsed.path == "/api/drives":
            self.send_json({"drives": list_local_drives()})
            return
        if parsed.path == "/api/list-dir":
            query = parse_qs(parsed.query)
            self.send_json(list_directory(query.get("path", [""])[0]))
            return
        if parsed.path == "/health":
            self.send_json({"ok": True, "base": str(BASE)})
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/selfcheck":
                result = run_command(["powershell", "-ExecutionPolicy", "Bypass", "-File", "_shared\\run-selfcheck.ps1"], timeout=60)
                self.send_json(result, HTTPStatus.OK if result["ok"] else HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            if parsed.path == "/api/create-task":
                self.send_json({"ok": True, **create_task(self.read_json())})
                return
            if parsed.path == "/api/open-folder":
                payload = self.read_json()
                folder = Path(str(payload.get("path") or BASE)).expanduser()
                if not folder.exists():
                    raise ValueError(f"폴더가 존재하지 않습니다: {folder}")
                subprocess.Popen(["explorer.exe", str(folder)], cwd=BASE)
                self.send_json({"ok": True, "path": str(folder)})
                return
            if parsed.path == "/api/start-session":
                payload = self.read_json()
                self.send_json(launch_interactive(str(payload.get("command", "")), payload))
                return
            if parsed.path == "/api/upload":
                UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
                files = parse_multipart(self.read_body(), self.headers.get("Content-Type", ""))
                saved = []
                for filename, data in files:
                    dest = safe_child_path(UPLOADS_DIR, filename)
                    if dest.exists():
                        dest = dest.with_name(f"{dest.stem}-{uuid.uuid4().hex[:8]}{dest.suffix}")
                    dest.write_bytes(data)
                    saved.append(str(dest))
                self.send_json({"ok": True, "saved": saved})
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)


def find_available_port(host: str, start_port: int) -> int:
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind((host, port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"사용 가능한 포트를 찾지 못했습니다: {start_port}-{start_port + 49}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--once", action="store_true", help="print resolved URL and exit")
    args = parser.parse_args()

    port = find_available_port(args.host, args.port)
    url = f"http://{args.host}:{port}/"
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    URL_MARKER.write_text(url, encoding="utf-8")

    if args.once:
        print(url)
        return 0

    httpd = ThreadingHTTPServer((args.host, port), Handler)
    print(f"JH-MultiAgent web control panel: {url}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web control panel.", flush=True)
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
