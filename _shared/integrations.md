# Integrations — 외부 시스템 연동

> 이 파일은 평소 작업에서 읽지 않는다(progressive disclosure). 연동 작업을 명시 요청할 때만 로드.

## 귀속 관리 시스템 (활성)

| 항목 | 값 |
|---|---|
| 관리 시스템 | Obsidian Agent Brain System |
| 관리 경로 | `G:\내 드라이브\obsidian-agent-brain-system` |
| 프로젝트 등록 파일 | `ObsidianVault/03_Projects/tools/JH-MultiAgent.md` |
| 오케스트레이터 | Bucky (Discord 봇) |
| 등록일 | 2026-05-30 |

**원칙**: 이 시스템의 작업 지시·상태·기록은 Obsidian Agent Brain System이 관리한다.
Bucky가 Bucky 패킷으로 작업을 지시할 때 `project: D:\ai프로젝트\JH-MultiAgent`로 명시.

## 향후 훅 (미구현)

| 연동 대상 | 방향 | 상태 | 도입 시 주의 |
|---|---|---|---|
| JH-브레인시스템 (Obsidian) | learnings.md → Obsidian 메모 동기화 | 미구현 | 단방향(읽기) 우선. 본체 file-as-memory 원칙 깨지 말 것 |
| 버키 에이전트 | 본 시스템 워커풀에 탑재 | 미구현 | 워커풀 구성 변경 = 전면 재감사 대상(orchestrator-rules §2) |

## 연동 금지 원칙 (지금)

- 외부 시스템이 본체 `tasks/`·`_shared/`에 직접 쓰지 않는다.
- 연동을 켜더라도 승인 게이트·검증 게이트는 우회 불가.
- 연동 도입 시 design-basis 새 결정(D*) + system-invariants 새 불변식 추가 후 전면 재감사.
