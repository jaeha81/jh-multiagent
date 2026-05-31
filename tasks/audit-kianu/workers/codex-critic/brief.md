# Brief - codex-critic / audit-kianu

```yaml
target_repo: D:\ai프로젝트\jh-keanu\jh-keanu
write_scope: none
mode: read-only
```

## Objective

claude-main의 `tasks/audit-kianu/workers/claude-main/result.md`를 독립 검증한다. 검증 대상은 JH-keanu 코드/문서 근거, A/B 결론 타당성, JH-MultiAgent 운영 규칙 충족 여부다.

## Inputs

- `tasks/audit-kianu/task.md`
- `tasks/audit-kianu/workers/claude-main/result.md`
- `D:\ai프로젝트\jh-keanu\jh-keanu`

## Checks

1. claude-main이 주장한 핵심 근거가 실제 repo에서 확인되는지 검증한다.
2. target_repo 경로가 실제 존재하는지 확인한다.
3. JH-MultiAgent 작업 완료 조건이 충족되는지 확인한다.
4. 최종 A/B 판정에 치명적 반례가 있는지 확인한다.

## Do NOT

- JH-keanu 파일 수정 금지
- 커밋/푸시 금지
- JH-MultiAgent의 다른 task 수정 금지
