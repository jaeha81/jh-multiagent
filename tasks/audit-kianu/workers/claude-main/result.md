# Result — claude-main / audit-kianu

```yaml
worker: claude-main
task: audit-kianu
status: complete
completed_at: 2026-05-31 00:10
```

## Summary

JH-키아누 read-only 감사 완료. 통합 방식 A(독립 유지) 권고. 핵심 근거: LLM 실행 경로 스텁·계약 불일치, 3패턴 모두 이식 가치 낮음 또는 비용 초과, 두 시스템의 운영 모델 철학 충돌.

## Output

---

# JH-키아누 read-only 감사 리포트

근거 파일: `backend/main.py`, `backend/agents/manager.py`, `backend/orchestrator/engine.py` (1034 LOC), `backend/orchestrator/ralph_loop.py`, `backend/brain/connector.py`, `backend/hooks/engine.py`, `backend/tools/registry.py`, `backend/sessions/manager.py`, `CLAUDE.md`, `tests/`, `frontend/app/`.

## 1. 시스템 완성도 평가

| 항목 | 점수/5 | 근거 |
|---|---|---|
| 완성도 | 2 / 5 | 골격(FastAPI 6단계 lifespan, 5역할 spec, Ralph Loop, IntentGate, HookEngine, ToolRegistry)은 정렬돼 있으나 핵심 LLM 실행 경로가 **스텁**. `AgentManager.execute_agent()`는 LLM을 호출하지 않고 `{"content":"…Claude Code 세션에서 실행하세요"}`만 반환. `OrchestratorEngine._execute_agent()`는 `result["response"]["content"]`를 접근 — **런타임 KeyError 확정**. 실제 호출 시 모든 라우팅 핸들러가 except 분기로 빠짐. |
| 멀티벤더 지원 | 1 / 5 | CLAUDE.md "Claude 전용 멀티에이전트". `TIER_TO_MODEL`은 Claude 3개 티어 하드코딩. Gemini/Codex 어댑터·라우터 부재. 멀티벤더 도입 시 manager 전면 재설계 필요. |
| async 블로킹 이슈 | 4 / 5 (실제 블로킹 위험은 **낮음**) | 코드베이스 전수 확인 결과 `anthropic.Anthropic()` / `client.messages.create` 사용처 **0건**. `claude_client.send_message`는 인자로 받으나 어디서도 주입되지 않음 (`classify_async(..., None)`, engine.py:227-230), 키워드 fallback만 동작. `requirements.txt`에 `anthropic==0.42.0` 선언만. "동기 클라이언트가 FastAPI 이벤트루프를 블로킹"하는 이슈는 현재 코드 기준 **재현 불가 — 호출이 없어서**. BrainConnector는 gspread 동기 호출을 `run_in_executor`로 감싸 처리(connector.py:40,193) — 좋은 패턴. 향후 실제 SDK 연동 시 위험으로 재평가 필요. |
| 유지보수비 | 2 / 5 | `orchestrator/engine.py` 1034 LOC 단일 파일 과대. 모듈 전역 가변 상태 `_ralph_loop_registry`/`_wave_manager`(engine.py:28-30) — 멀티 인스턴스/테스트 격리 어려움. AgentManager↔OrchestratorEngine 반환 스키마 계약 불일치. 테스트 2개(unit/integration) — 커버리지 낮음. main.py lifespan docstring은 "6단계"이나 실제 9단계로 표류. |
| 이식 회귀위험 | 3 / 5 | JH-MultiAgent(파일·태스크 기반 정적 오케스트레이션)과 키아누(FastAPI+WebSocket+Supabase+tmux+Ralph Loop 동적 런타임) — 운영 모델이 본질적으로 다름. 글자캡처는 tmux 의존성 유입. 키아누 CLAUDE.md의 "승인 오버라이드" 원칙이 JH-MultiAgent의 `workers_approved` 게이트와 철학 충돌. |

**총점: 12 / 25 (48%)** — 골격은 갖췄으나 핵심 실행 경로 미완.

## 2. 핵심 미해결 이슈

1. **AgentManager↔Orchestrator 계약 깨짐** — `execute_agent()` 반환에 `response` 키 없음 → `_execute_agent()`에서 즉시 KeyError. 실 LLM 연동 전 수정 필수. 키아누 자체 운영을 막는 1순위 결함.
2. **claude_client 미주입** — IntentGate.classify_async는 무조건 키워드 fallback. 의도 분류 정확도 = 키워드 매칭 수준에 고정.
3. **async 블로킹은 아직 "잠재 위험"** — 현재 Anthropic SDK import 0건, 블로킹 이슈 미발생. 향후 실제 SDK 연동 시점에 재평가 권장.
4. **모듈 전역 상태** — `_ralph_loop_registry`, `_wave_manager` (engine.py:28-30) 멀티 세션/재시작·테스트 시 누수 위험. `app.state`로 이전 권장.
5. **승인 게이트 철학 충돌** — 키아누 CLAUDE.md는 "승인 없이 코드 수정 금지 규칙 오버라이드". JH-MultiAgent 핵심 규칙과 정면 충돌.

## 3. 3패턴 이식 타당성

### ① 교차검증 패턴
키아누에 **존재하지 않음**. QA 에이전트는 Claude 단일 벤더 자가검증. JH-MultiAgent의 codex-critic은 이미 별도 모델(Codex)로 교차검증 구현 — **이식할 것 없음. 역방향(JH→키아누)이 자연스러움**.

### ② Gemini 연동 패턴 (BrainConnector)
`brain/connector.py`는 Obsidian vault 파일 I/O + Google Sheets gspread 래퍼. **LLM을 호출하지 않음**. JH-MultiAgent의 `mcp__gemini-cli__ask-gemini`(MCP 기반 단일 진입점)가 이미 더 깔끔. **이식 가치 낮음**.

### ③ 글자캡처 패턴 (`/api/tmux/pane/{role}/output`)
tmux pane 후행 N라인 캡처. 운영 가치는 있으나 **(a) tmux 런타임 의존성**, **(b) JH-MultiAgent의 파일-기반 result.md 모델과 충돌**, **(c) Windows 기본 환경에 tmux 미존재**. **이식 비용 > 가치**. 동등 기능은 `tasks/<task>/log.md` tee로 달성 가능.

## 4. A vs B 판정 근거

**B(3패턴 이식)에 부정적인 신호:**
- 키아누 LLM 실행 경로 자체가 미완(스텁+계약 불일치) — 미검증 패턴을 가져오는 셈
- 3패턴 모두 JH-MultiAgent에 이미 동등·우월한 대체물이 있거나(①②), 비용이 가치 초과(③)
- 승인 게이트 철학 충돌 — 이식 시 JH-MultiAgent 핵심 불변식 훼손 위험
- FastAPI+Supabase+tmux 런타임 의존성 부채 유입

**A(독립 유지)에 긍정적인 신호:**
- 두 시스템의 운영 모델이 본질적으로 다름(런타임 오케스트레이션 vs 파일 기반 태스크) → 독립 유지가 명확
- 키아누에서 검증된 패턴이 나오면 그때 선별 이식하는 편이 회귀위험 최소
- JH-MultiAgent는 이미 codex-critic·gemini worker로 멀티벤더+교차검증 안정 제공

## 5. 권고안

**판정: A (독립 유지) 권고.** 조건부 후속 사항:

1. **키아누 측 결함 회신** (read-only 감사 산출물 — 수정은 키아누 팀):
   - `AgentManager.execute_agent` ↔ `OrchestratorEngine._execute_agent` 반환 스키마 통일 (`response.content`/`usage` 키 합의)
   - `claude_client` 의존성 주입 경로 정의 또는 `classify_async`에서 None 시 분기 명시
   - 모듈 전역 상태(`_ralph_loop_registry`, `_wave_manager`)를 `app.state`로 이전
2. **async 블로킹 이슈** — 향후 Anthropic SDK 실 호출 추가 시 그 시점에 재평가 (현재 미발생)
3. **향후 단일 패턴 검토 시** — 글자캡처보다 **IntentGate LLM 분류기 + 키워드 fallback 이중 구조** 참고가 더 가치 있으나, 현재 JH-MultiAgent 라우팅이 결정적이라 도입 필요성 낮음
4. **인터페이스** — 두 시스템 간 연결이 필요하다면 "파일 핸드오프"(`tasks/<task>/sources/keanu-export/`)로 좁게 유지

## Verification Checklist

- [x] output이 brief의 output_format과 일치 (6섹션 순서, 5항목 점수표, 3패턴 개별 평가)
- [x] 참조한 파일 경로가 실제 존재 (backend/* 트리 직접 확인, 라인 참조)
- [x] task.md의 constraints 충족 (read-only, 키아누 코드 수정·커밋·푸시 없음, write_scope=none)
- [x] Do NOT 항목 위반 없음 (파일 직접 쓰기 없음, JH-MultiAgent 편향 회피, 파일 inline 없이 경로·라인 참조)

## Issues / Caveats

- **async 블로킹 이슈 재정의 필요**: task.md의 가정("동기 클라이언트가 이벤트루프 블로킹")은 현재 코드 기준 재현 불가. 향후 SDK 연동 시 위험으로 재분류 권장.
- codex-critic 교차검증 미수행 (이번 단계 미승인). 이 리포트의 낙관 편향 가능성은 codex-critic 호출 후 재검토 권장.
