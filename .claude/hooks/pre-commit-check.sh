#!/bin/bash
# 커밋 전 검사 Hook
#
# 사용법:
# .claude/settings.json에 아래 설정 추가
# {
#   "hooks": {
#     "PreToolUse": [{
#       "matcher": "Bash.*git commit",
#       "hooks": [{"type": "command", "command": ".claude/hooks/pre-commit-check.sh"}]
#     }]
#   }
# }

echo "🔍 커밋 전 검사 중..."

ERRORS=0

# 1. 민감한 파일 검사
SENSITIVE_FILES=$(git diff --cached --name-only | grep -E '\.env$|\.env\.local$|credentials|secret|password' || true)
if [ -n "$SENSITIVE_FILES" ]; then
    echo "⚠️  민감한 파일이 포함되어 있습니다:"
    echo "$SENSITIVE_FILES"
    ERRORS=$((ERRORS + 1))
fi

# 2. 큰 파일 검사 (1MB 이상)
LARGE_FILES=$(git diff --cached --name-only | while read file; do
    if [ -f "$file" ]; then
        SIZE=$(wc -c < "$file" 2>/dev/null || echo 0)
        if [ "$SIZE" -gt 1048576 ]; then
            echo "$file ($(numfmt --to=iec $SIZE 2>/dev/null || echo "${SIZE}B"))"
        fi
    fi
done)
if [ -n "$LARGE_FILES" ]; then
    echo "⚠️  큰 파일이 포함되어 있습니다:"
    echo "$LARGE_FILES"
    ERRORS=$((ERRORS + 1))
fi

# 3. TODO/FIXME 검사
TODOS=$(git diff --cached | grep -E '^\+.*TODO|^\+.*FIXME' | head -5 || true)
if [ -n "$TODOS" ]; then
    echo "📝 새로운 TODO/FIXME가 추가되었습니다:"
    echo "$TODOS"
fi

# 4. console.log/print 검사 (JS/TS/Python)
DEBUG_LOGS=$(git diff --cached | grep -E '^\+.*(console\.log|print\(|debugger)' | head -5 || true)
if [ -n "$DEBUG_LOGS" ]; then
    echo "⚠️  디버그 코드가 포함되어 있습니다:"
    echo "$DEBUG_LOGS"
fi

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo "❌ 커밋 전 검사 실패 (${ERRORS}개 문제)"
    echo "계속하려면 --no-verify 옵션을 사용하세요"
    exit 1
fi

echo "✅ 커밋 전 검사 통과"
