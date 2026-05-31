# audit-kianu 통합 방식 A/B 판정

## Meta

```yaml
status: done
created: 2026-05-30
updated: 2026-05-31
completed: 2026-05-31
priority: high
```

## Goal

JH-MultiAgent가 자기 자신을 워커로 사용해 JH-keanu 프로젝트를 read-only로 감사하고, 통합 방식 A(입력 유지) / B(3개 패턴 이식) 중 하나를 근거 기반으로 판정한다.

## Constraints

- 판정은 사람이 최종 승인한다. 시스템은 근거 리포트까지만 산출한다.
- 자기확증을 막기 위해 claude-main 분석 후 codex-critic이 독립 검증한다.
- JH-keanu 코드는 수정하지 않는다. 이번 작업은 read-only 감사다.

## Acceptance Criteria

- [x] 판정 기준 5개 항목 점수화: 완성도 / 멀티벤더 지지도 / 미해결 async 블로킹 이슈 / 유지보수비 / 이식 회귀위험
- [x] A 또는 B와 근거를 worker 결과로 산출
- [x] codex-critic이 claude-main 분석을 독립적으로 검증
- [x] 사람 최종 승인용 결론 라인 작성
- [x] selfcheck와 dashboard 실행으로 JH-MultiAgent 사용 가능 상태 확인

## Worker Plan

```yaml
workers_approved:
  - worker: claude-main
    approved_at: 2026-05-31
    purpose: JH-keanu 아키텍처/완성도 분석, 3개 패턴 이식 타당성 리포트 작성
    approved_by: user
    write_scope: none
  - worker: codex-critic
    approved_at: 2026-05-31
    purpose: claude-main 분석 독립 검증, 경로/근거/결론 타당성 확인
    approved_by: user
    write_scope: none

planned_workers:
  - role: claude-main
    purpose: JH-keanu 아키텍처/완성도 분석, 3개 패턴 이식 타당성 검토
  - role: codex-critic
    purpose: claude-main 결과 독립 검증
```

## Context Snapshot

```yaml
target_repo_requested: D:\ai프로젝트\JH-kianu
target_repo_verified: D:\ai프로젝트\jh-keanu\jh-keanu
write_scope: none
```

확인 결과 요청 경로 `D:\ai프로젝트\JH-kianu`는 존재하지 않고, 실제 분석 가능한 repo는 `D:\ai프로젝트\jh-keanu\jh-keanu`였다. worker 결과와 Codex 검증은 실제 존재 경로를 기준으로 수행했다.

## Final Decision

**판정: A(입력 유지) 권고.**

근거: JH-keanu 쪽 3개 패턴은 현재 JH-MultiAgent에 이식할 만큼 완성도와 운영 적합성이 높지 않다. claude-main은 총점 12/25로 A를 권고했고, codex-critic도 핵심 근거가 코드/문서 검색 결과와 대체로 일치한다고 확인했다. 특히 JH-keanu는 AgentManager 실행 계약, IntentGate의 실제 LLM 주입 여부, tmux/동적 orchestration 모델이 JH-MultiAgent의 파일 기반 승인 게이트 모델과 충돌한다.

## Remaining Human Action

사용자는 이 결론을 기준으로 Claude에게 다음을 지시하면 된다:

```text
JH-MultiAgent에는 JH-keanu의 3개 패턴을 이식하지 말고 현재 입력/파일 기반 운영 구조를 유지해라.
단, JH-keanu에서 참고할 수 있는 아이디어는 별도 후보로 분리해 문서화만 하고, 승인 게이트/worker 파일 기록/append-only log 원칙은 유지해라.
```
