# Integrations — 외부 시스템 연동

> 이 파일은 평소 작업에서 읽지 않는다(progressive disclosure). 연동 작업을 명시 요청할 때만 로드.

## Obsidian / Bucky 연동 상태 (3단계)

| 연동 항목 | 상태 | 비고 |
|---|---|---|
| 귀속 등록 | **active** | `ObsidianVault/03_Projects/tools/JH-MultiAgent.md` 등록 완료 |
| 자동 파일 동기화 | **inactive** | `learnings.md → Obsidian` 동기화 미구현. 명시 요청 전 실행 금지 |
| Bucky 작업 지시 인식 | **active** | Bucky 패킷 수신 시 `project: D:\ai프로젝트\JH-MultiAgent` 명시로 인식 |

**귀속 정보**:

| 항목 | 값 |
|---|---|
| 관리 시스템 | Obsidian Agent Brain System |
| 관리 경로 | `G:\내 드라이브\obsidian-agent-brain-system` |
| 프로젝트 등록 파일 | `ObsidianVault/03_Projects/tools/JH-MultiAgent.md` |
| 오케스트레이터 | Bucky (Discord 봇) |
| 등록일 | 2026-05-30 |

**Bucky 작업 지시 인식 원칙**: Bucky가 Bucky 패킷으로 작업을 지시할 때 `project: D:\ai프로젝트\JH-MultiAgent`로 명시. Claude Code는 해당 패킷을 수신해 운영 규칙에 따라 처리.

## 향후 훅 (미구현 / inactive)

| 연동 대상 | 방향 | 상태 | 도입 시 주의 |
|---|---|---|---|
| JH-브레인시스템 (Obsidian) | learnings.md → Obsidian 메모 동기화 | **inactive** | 단방향(읽기) 우선. 본체 file-as-memory 원칙 깨지 말 것 |
| 버키 에이전트 | 본 시스템 워커풀에 탑재 | **inactive** | 워커풀 구성 변경 = 전면 재감사 대상(orchestrator-rules §2) |

## 연동 금지 원칙 (지금)

- 외부 시스템이 본체 `tasks/`·`_shared/`에 직접 쓰지 않는다.
- 연동을 켜더라도 승인 게이트·검증 게이트는 우회 불가.
- 연동 도입 시 design-basis 새 결정(D*) + system-invariants 새 불변식 추가 후 전면 재감사.
