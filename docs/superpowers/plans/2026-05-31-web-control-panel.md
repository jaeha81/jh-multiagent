# Web Control Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local mouse-friendly web control panel so a user can start JH-MultiAgent development from natural-language requests.

**Architecture:** Add a Python standard-library HTTP server for the UI and local APIs, plus a PowerShell launcher that starts the server and opens the browser. Keep worker calls and external repo writes behind the existing approval model.

**Tech Stack:** Python 3 stdlib, HTML/CSS/JavaScript, Windows PowerShell.

---

### Task 1: Local Web Server

**Files:**
- Create: `web_control_panel.py`

- [x] Create an HTTP server bound to `127.0.0.1`.
- [x] Serve a browser UI with a left action rail, natural-language request form, status area, and task list.
- [x] Add APIs for status, selfcheck, task draft creation, file upload, and launching Claude/Codex sessions.

### Task 2: Windows Launcher

**Files:**
- Create: `launch-web.ps1`
- Modify: `launch.ps1`

- [x] Start the web server in the background.
- [x] Wait until the server writes its URL marker.
- [x] Open the local URL in the default browser.
- [x] Add the web panel to the existing launcher menu.

### Task 3: Docs And Checks

**Files:**
- Modify: `README.md`
- Modify: `_shared/run-selfcheck.ps1`

- [x] Document the web panel entry point.
- [x] Add selfcheck coverage for the web panel and launcher script.
- [x] Verify Python syntax, selfcheck, server health, task creation, upload, and launcher script parsing.

### Notes

This repo forbids Codex commits unless explicitly requested, so this implementation plan intentionally omits commit steps.
