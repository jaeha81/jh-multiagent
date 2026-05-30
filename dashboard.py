"""JH-MultiAgent 로컬 대시보드 — python dashboard.py"""

import os
import sys
import glob
import subprocess
from pathlib import Path
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.columns import Columns
    from rich.text import Text
    from rich import box
    import rich.markup
except ImportError:
    print("rich 미설치: pip install rich")
    sys.exit(1)

BASE = Path(__file__).parent
TASKS_DIR = BASE / "tasks"
SHARED_DIR = BASE / "_shared"

console = Console()


def read_yaml_field(text: str, field: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(field + ":"):
            return stripped.split(":", 1)[1].strip()
    return ""


def load_tasks():
    tasks = []
    if not TASKS_DIR.exists():
        return tasks
    for task_dir in sorted(TASKS_DIR.iterdir()):
        if not task_dir.is_dir():
            continue
        task_file = task_dir / "task.md"
        if not task_file.exists():
            continue
        content = task_file.read_text(encoding="utf-8")
        status = read_yaml_field(content, "status") or "unknown"
        priority = read_yaml_field(content, "priority") or "-"
        updated = read_yaml_field(content, "updated") or "-"

        # 워커 목록
        workers = []
        workers_dir = task_dir / "workers"
        if workers_dir.exists():
            workers = [w.name for w in workers_dir.iterdir() if w.is_dir()]

        tasks.append({
            "name": task_dir.name,
            "status": status,
            "priority": priority,
            "updated": updated,
            "workers": workers,
        })
    return tasks


STATUS_STYLE = {
    "pending":     "yellow",
    "in-progress": "cyan",
    "done":        "green",
    "failed":      "red",
    "unknown":     "dim",
}

PRIORITY_STYLE = {
    "high":   "bold red",
    "medium": "yellow",
    "low":    "dim",
}


def render_tasks(tasks):
    table = Table(
        title="📋 Tasks",
        box=box.ROUNDED,
        show_lines=True,
        header_style="bold blue",
        expand=True,
    )
    table.add_column("태스크", style="bold", min_width=20)
    table.add_column("상태", justify="center", min_width=12)
    table.add_column("우선순위", justify="center", min_width=10)
    table.add_column("갱신일", justify="center", min_width=12)
    table.add_column("워커", min_width=20)

    for t in tasks:
        st = t["status"]
        pr = t["priority"]
        status_text = Text(st, style=STATUS_STYLE.get(st, "white"))
        priority_text = Text(pr, style=PRIORITY_STYLE.get(pr, "white"))
        workers_str = ", ".join(t["workers"]) if t["workers"] else "없음"
        table.add_row(t["name"], status_text, priority_text, t["updated"], workers_str)

    return table


def run_cmd(cmd: str) -> tuple[bool, str]:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        out = (r.stdout + r.stderr).strip()[:60]
        return r.returncode == 0, out
    except Exception as e:
        return False, str(e)[:60]


def render_system():
    checks = []

    # claude
    ok, out = run_cmd("claude --version")
    checks.append(("claude", "✅" if ok else "❌", out if ok else "미설치 또는 경로 없음"))

    # codex
    ok, out = run_cmd("codex --version")
    checks.append(("codex", "✅" if ok else "⚠️ ", out[:40] if ok else "미설치/미인증"))

    # mcp.json
    mcp_path = BASE / ".mcp.json"
    checks.append((".mcp.json", "✅" if mcp_path.exists() else "❌", str(mcp_path) if mcp_path.exists() else "없음"))

    # tasks 폴더
    checks.append(("tasks/", "✅" if TASKS_DIR.exists() else "❌", str(len(list(TASKS_DIR.iterdir()))) + "개" if TASKS_DIR.exists() else "없음"))

    # Obsidian 브레인시스템 귀속
    obsidian_link = BASE / "_local" / "brain-system-link.md"
    checks.append(("obsidian 귀속", "✅" if obsidian_link.exists() else "⚠️ ", "등록됨" if obsidian_link.exists() else "미등록"))

    table = Table(box=box.SIMPLE, show_header=False, expand=True)
    table.add_column("항목", style="bold", min_width=18)
    table.add_column("상태", justify="center", min_width=4)
    table.add_column("정보")
    for item, icon, info in checks:
        table.add_row(item, icon, info)

    return Panel(table, title="⚙️  시스템 점검", border_style="blue")


def render_quickstart():
    lines = [
        "[bold cyan]멀티에이전트 시작하기[/]",
        "",
        "[dim]1.[/] [yellow]cd D:\\ai프로젝트\\JH-MultiAgent[/]",
        "[dim]2.[/] [yellow]claude[/]   [dim]← CLAUDE.md 자동 로드됨[/]",
        "",
        "[bold]태스크 새로 만들기:[/]",
        "  tasks/ 아래 폴더 생성 → task.md 작성 (_templates/task.md 복사)",
        "",
        "[bold]Obsidian 브레인시스템 귀속 경로:[/]",
        "  [dim]G:\\내 드라이브\\obsidian-agent-brain-system\\ObsidianVault\\03_Projects\\tools\\JH-MultiAgent.md[/]",
    ]
    return Panel("\n".join(lines), title="🚀 빠른 시작", border_style="green")


def main():
    console.clear()
    console.rule("[bold blue]JH-MultiAgent 대시보드[/]", style="blue")
    console.print(f"[dim]경로: {BASE}   |   갱신: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/]\n")

    # 시스템 점검 + 빠른 시작 (2열)
    sys_panel = render_system()
    qs_panel = render_quickstart()
    console.print(Columns([sys_panel, qs_panel], equal=True, expand=True))
    console.print()

    # 태스크 목록
    tasks = load_tasks()
    if tasks:
        console.print(render_tasks(tasks))
    else:
        console.print(Panel("[dim]태스크 없음. tasks/ 폴더에 태스크를 추가하세요.[/]", title="📋 Tasks", border_style="yellow"))

    console.print()
    console.rule("[dim]q: 종료  |  r: 새로고침  |  Enter: 새로고침[/]", style="dim")

    try:
        cmd = console.input("")
        if cmd.lower() != "q":
            main()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]종료[/]")


if __name__ == "__main__":
    main()
