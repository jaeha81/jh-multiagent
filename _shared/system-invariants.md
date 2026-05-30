# System Invariants — 시스템 수정 후 자가 점검

> **로드 정책**: 평소 미로드. 시스템 파일 수정·검증 작업일 때만 (`orchestrator-rules.md` §2).
> 목적: 시스템 변경 후 **전면 멀티에이전트 재감사 대신** 이 점검만 돌려 모순 재발을 잡는다.
> 통과해야 커밋. 깨지면 고치거나, 의도된 변경이면 `design-basis.md` 결정(D*)·이 표를 함께 갱신.

## 불변식 목록

| ID | 불변식 | 깨지면 |
|---|---|---|
| INV1 | `write_scope` 값 집합이 CLAUDE.md(정의처)·routing.md·_templates/worker-brief.md·task-folder.md·매뉴얼에서 동일 (`none`/`tasks-only`/패턴) | D1 위반 — 어디든 한 곳만 다르면 시스템 자체 모순 |
| INV2 | codex-critic 선행조건에 "claude-main result.md 존재 필수" 같은 **전용 강제** 표현 없음 (일반화 표현이어야) | D2 위반 |
| INV3 | log 태그 = 정확히 `DECISION\|WORKER_CALL\|VERIFICATION\|ERROR\|APPROVAL\|COMPLETE` 6종 (_templates/log.md, 매뉴얼) | 파서·일관성 깨짐 |
| INV4 | context.md 한도 1500자, brief 한도 1200자 수치가 CLAUDE.md·매뉴얼·_templates 헤더에서 동일 | 한도 불일치 |
| INV5 | 외부 매뉴얼 메인 섹션 개수 == manual-repo `CLAUDE.md`의 메인 섹션 목록 개수 | 매뉴얼↔manual-repo 빌드 스펙 불일치 (현재 R3 미해소 시 의도적 FAIL) |
| INV6 | 매뉴얼 `workers_approved` 예시 스키마가 approval-policy.md와 일치 (`worker:`/date-only/`purpose:`/`approved_by:`, `HH:MM` 없음) | B1/B6 재발 |
| INV7 | 권위 우선순위 문구가 매뉴얼 §3과 design-basis.md §2에서 동일 (CLAUDE.md > routing/approval/orchestrator-rules > 매뉴얼) | Clash 해소 규칙 붕괴 |
| INV8 | 인터랙티브 전용 + worktree/백그라운드 세션 금지 규칙이 orchestrator-rules.md와 매뉴얼에 모두 존재 | D5 위반 |
| INV9 | gemini 브리지·기본모델이 routing.md·design-basis.md D4에서 일치 (`gemini-cli` 브리지 / 기본 `gemini-2.5-pro`) | 정본이 잘못된 브리지·모델을 기본 호출 (D4 위반) |
| INV10 | 구(舊) 호출형 `mcp__gemini-pro__`·`mcp__gemini__gemini_`가 routing.md·task-folder.md·CLAUDE.md에 호출 명령/예시로 등장하지 않음 (gemini-cli 브리지로 통일) | 마이그레이션 누락 — 잔존 호출 참조가 즉시 실패 (D4 위반) |

## 자가 점검 스크립트 (JH 적응판)

`~/JH-MultiAgent`에서 실행. 외부 매뉴얼 미구성(D6)이므로 매뉴얼 결합 검사(INV5/INV6, INV7~9의 매뉴얼 절반)는 **SKIP** 처리한다.

```bash
ROOT="${ROOT:-$HOME/JH-MultiAgent}"
cd "$ROOT" || exit 1
P=0; F=0
chk(){ if [ -z "$2" ]; then echo "  PASS $1"; P=$((P+1)); else echo "  FAIL $1"; echo "$2" | sed 's/^/    /'; F=$((F+1)); fi; }

echo "INV1 tasks-only 값집합 분포 (CLAUDE/routing/worker-brief/task-folder 모두 존재)"
miss=""; for f in CLAUDE.md _shared/routing.md _templates/worker-brief.md _templates/task-folder.md; do
  grep -q 'tasks-only' "$f" || miss="$miss $f"; done
chk INV1 "$miss"

echo "INV3 log 태그 6종 정의 라인"
chk INV3 "$(grep -q 'DECISION | WORKER_CALL | VERIFICATION | ERROR | APPROVAL | COMPLETE' _templates/log.md || echo 'log.md 태그라인 없음')"

echo "INV4 컨텍스트 한도 1500/1200 수치 일치"
chk INV4 "$(grep -q '1500자' CLAUDE.md && grep -q '1200자' CLAUDE.md && grep -q '1500자' _templates/context.md && grep -q '1200자' _templates/worker-brief.md || echo '한도 수치 누락')"

echo "INV9 gemini 브리지·기본모델 일치 (routing=gemini-cli/2.5-pro, design-basis D4 동일)"
g1="$(grep -c 'gemini-cli' _shared/routing.md)"; g2="$(grep -c 'gemini-2.5-pro' _shared/routing.md)"; g3="$(grep -c 'gemini-cli' _shared/design-basis.md)"
chk INV9 "$([ "$g1" -ge 1 ] && [ "$g2" -ge 1 ] && [ "$g3" -ge 1 ] || echo "routing gemini-cli=$g1 2.5-pro=$g2 / design-basis gemini-cli=$g3")"

echo "INV10 구 호출형 잔존 0 (routing/task-folder/CLAUDE)"
leak="$(grep -rn 'mcp__gemini-pro__\|mcp__gemini__gemini_' CLAUDE.md _shared/routing.md _templates/task-folder.md)"
chk INV10 "$leak"

echo "INV8 인터랙티브/worktree 금지 (orchestrator-rules에 존재)"
chk INV8 "$(grep -qi 'worktree\|백그라운드\|background' _shared/orchestrator-rules.md || echo 'orchestrator-rules 금지규칙 없음')"

echo "--- SKIP (외부 매뉴얼 미구성, D6): INV5 INV6 INV7매뉴얼 INV9매뉴얼 ---"
echo ""; echo "결과: PASS=$P FAIL=$F"; [ "$F" -eq 0 ] && echo "ALL PASS" || echo "FAIL 있음 — 커밋 금지"
```

## 전면 재감사가 필요한 경우 (이 점검으로 부족)

- 새 외부 개념·레퍼런스를 시스템에 도입할 때 (개념↔규칙 매핑 자체가 바뀜)
- worker pool 구성·역할이 바뀔 때
- 위 불변식으로 표현 불가한 구조 변경
→ 그때만 `tasks/<new>/`로 새 점검 작업 + 필요 시 codex-critic/gemini. 그 외 일반 수정은 이 스크립트로 충분.
