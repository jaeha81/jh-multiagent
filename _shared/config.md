# Config — 운영 토글

> Orchestrator는 새 작업 시작 시 이 파일을 읽고 분기한다. (가벼운 상시 로드 — 1줄 단위)

```yaml
gemini_enabled: true
# true  : routing.md 의 gemini 분기 정상 동작 (mcp__gemini-cli__ask-gemini)
# false : gemini 분기를 건너뛴다. 멀티모달/제3자 검토가 필요한 작업이면
#         호출하지 않고 사용자에게 대체안(코드 검토는 codex-critic, 문서는 claude-main)을 묻는다.
```

## 토글 규칙

- `gemini_enabled: false` 인데 작업이 이미지·스크린샷·50p+ 문서·"제3자 시각 검토"를 요구하면:
  1. gemini 워커를 planned_workers 에 넣지 않는다
  2. log.md 에 `[DECISION] gemini disabled — 대체 경로 질의` 기록
  3. 사용자 승인 후 대체 워커로 진행
- 토글 변경은 시스템 수정이 아니므로 system-invariants 자가점검 불필요(운영 파라미터).
