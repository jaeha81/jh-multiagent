#!/usr/bin/env bash
# JH-MultiAgent — 로컬 연결 셋업 (재하님 PC에서 실행)
# 이 스크립트는 인증(login)을 대신하지 않는다. login 단계는 본인이 직접 수행.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "ROOT=$ROOT"

echo "[1/4] 사전 점검"
command -v claude >/dev/null || { echo "  ✗ Claude Code(claude) 미설치"; exit 1; }
command -v codex  >/dev/null || { echo "  ✗ Codex CLI(codex) 미설치"; exit 1; }
command -v node   >/dev/null || { echo "  ✗ Node.js 미설치"; exit 1; }
echo "  ✓ claude / codex / node 확인"

echo "[2/4] codex 인증 — 본인이 직접 (구독 OAuth). 아래 주석 해제 후 1회 실행:"
echo "       # codex login"

echo "[3/4] MCP 등록"
echo "  codex 워커 등록:"
echo "    claude mcp add codex -- codex mcp-server   # 버전 따라 'codex mcp' 일 수 있음 → codex --help"
echo "  gemini 워커 등록(공개 브리지):"
echo "    npm i -g @google/gemini-cli && gemini      # Google 로그인=무료 티어 (본인 직접)"
echo "    # gemini-cli 는 .mcp.json 에 프로젝트 등록됨 — 이 폴더에서 claude 실행 시 자동 활성"

echo "[4/4] 검증"
echo "  cd \"$ROOT\" && claude     # 세션에서 /mcp 입력 → codex, gemini-cli 활성 확인"
echo "  ROOT=\"$ROOT\" bash _shared/run-selfcheck.sh   # 불변식 자가점검"
echo ""
echo "※ 위 명령들은 표시만 함(안전). 실제 등록은 주석/명령을 직접 실행하세요."
