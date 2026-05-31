# Brief — claude-main / audit-kianu

<!-- HARD LIMIT: 240단어 영문. 파일 내용 inline 금지. 경로만 전달. -->

## Execution Context

```yaml
target_repo: D:\ai프로젝트\jh-keanu\jh-keanu
write_scope: none   # read-only 감사. 키아누 코드 수정 금지.
```

## Objective

JH-키아누 repo를 read-only로 감사하여 통합 방식 A(독립 유지) vs B(3패턴 이식) 판정을 위한 근거 리포트를 작성한다.

## Input

```
task:       tasks/audit-kianu/task.md
context:    tasks/audit-kianu/context.md
main_entry: D:\ai프로젝트\jh-keanu\jh-keanu\backend\main.py
agents_mgr: D:\ai프로젝트\jh-keanu\jh-keanu\backend\agents\manager.py
orchestr:   D:\ai프로젝트\jh-keanu\jh-keanu\backend\orchestrator\engine.py
ralph_loop: D:\ai프로젝트\jh-keanu\jh-keanu\backend\orchestrator\ralph_loop.py
brain_conn: D:\ai프로젝트\jh-keanu\jh-keanu\backend\brain\connector.py
claude_md:  D:\ai프로젝트\jh-keanu\jh-keanu\CLAUDE.md
hooks/:     D:\ai프로젝트\jh-keanu\jh-keanu\backend\hooks\
tools/:     D:\ai프로젝트\jh-keanu\jh-keanu\backend\tools\
sessions/:  D:\ai프로젝트\jh-keanu\jh-keanu\backend\sessions\
frontend/:  D:\ai프로젝트\jh-keanu\jh-keanu\frontend\app\
```

## Constraints

- 판정 기준 5개 항목을 점수표로 정량화: 완성도 / 멀티벤더 지원 / async 블로킹 이슈 / 유지보수비 / 이식 회귀위험
- 3패턴 각각의 이식 타당성 평가: ① 교차검증 패턴 ② gemini 연동 패턴 ③ 글자캡처 패턴
- 키아누의 ClaudeClient.send_message() 동기 클라이언트가 FastAPI 이벤트루프를 블로킹하는 이슈 반드시 반영
- 사람이 최종 결정. 리포트는 근거 제공까지만.

## Output Format

- 텍스트로 반환 (파일 직접 쓰기 금지). Orchestrator가 result.md에 저장.
- 형식: Markdown. 섹션 구성:
  1. 시스템 완성도 평가 (점수표)
  2. 핵심 미해결 이슈
  3. 3패턴 이식 타당성 분석
  4. A vs B 판정 근거
  5. 권고안
- 응답 끝에 Verification Checklist 4항목 포함

## Do NOT

- 키아누 코드 수정/커밋/푸시 금지
- 어느 파일도 직접 쓰지 말 것
- JH-MultiAgent 시스템에 유리한 방향으로 편향하지 말 것
