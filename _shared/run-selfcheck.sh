#!/usr/bin/env bash
# system-invariants.md 의 자가점검 스크립트를 추출 실행
ROOT="${ROOT:-$HOME/JH-MultiAgent}"
SI="$ROOT/_shared/system-invariants.md"
awk '/^```bash$/{f=1;next} /^```$/{if(f){exit}} f' "$SI" > /tmp/jh_selfcheck.sh
ROOT="$ROOT" bash /tmp/jh_selfcheck.sh
