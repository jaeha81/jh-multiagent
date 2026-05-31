# audit-kianu — 통합 방식 A/B 판정

## 메타

```yaml
status: reviewing
created: 2026-05-30
updated: 2026-05-30
priority: high
```

## Goal

본 멀티에이전트 시스템이 **자기 자신의 워커풀로** JH-키아누를 감사하여,
통합 방식 A(독립 유지) / B(3개 패턴만 키아누에 이식) 중 하나를 근거 기반으로 판정한다.

## Constraints

- 판정은 사람이 최종 승인. 시스템은 근거 리포트까지만 산출.
- 시스템이 자기에게 유리하게 판정하는 편향을 막기 위해 codex-critic(타벤더 적대적)·gemini(외부 시각) 교차 필수.
- 키아누 코드를 수정하지 않는다(read-only 감사).

## Acceptance Criteria

- [x] 판정 기준표 점수화: 완성도 / 멀티벤더 지원 / 미해결 async 블로킹 이슈 / 유지보수비 / 이식 회귀위험
- [x] A 또는 B + 근거를 workers 결과로 산출 (A 권고, 총점 12/25)
- [ ] codex-critic 가 claude-main 분석의 낙관 편향을 적대적으로 검증 (미승인)
- [ ] 사람 최종 승인 라인

## Worker Plan

```yaml
workers_approved:
  - worker: claude-main
    approved_at: 2026-05-31
    purpose: JH-키아누 아키텍처·완성도 분석, 3패턴 이식 타당성 리포트 작성
    approved_by: user
    write_scope: none
  # codex-critic / gemini — 이번 단계 미승인. claude-main 결과 수신 후 재요청.
planned_workers:
  - role: claude-main
    purpose: JH-키아누 아키텍처·완성도 분석, 3패턴(교차검증/gemini/글자캡) 이식 타당성
  - role: codex-critic
    purpose: claude-main 분석 적대적 검증 — 이식 회귀위험·async 이슈 실현성
  - role: gemini
    purpose: 55개 repo 외부 시각 스캔(대용량) — config gemini_enabled=true 필요
```

## Context Snapshot

target_repo: D:\ai프로젝트\JH-kianu
판정 입력: JH-키아누 repo + 본 시스템 design-basis.md(개념→규칙 매핑).
알려진 입력 1건: 키아누의 ClaudeClient.send_message() 동기 클라이언트가 FastAPI 이벤트루프를 블로킹하는 미해결 이슈 → 완성도·async 항목에 반영.

## Notes

이 작업은 Phase 2. Phase 1(독립 가동·실작업 2~3건 검증) 완료 후 실행 권장.
