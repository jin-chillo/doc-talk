#!/bin/bash
# 세션 종료 시 요약 Hook
#
# 사용법:
# .claude/settings.json에 아래 설정 추가
# {
#   "hooks": {
#     "SessionEnd": [{
#       "hooks": [{"type": "command", "command": ".claude/hooks/session-end.sh"}]
#     }]
#   }
# }

echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║             📊 세션 요약                          ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

# Git 상태 확인
if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    # 커밋되지 않은 변경사항
    UNSTAGED=$(git diff --stat | tail -1)
    STAGED=$(git diff --cached --stat | tail -1)
    UNTRACKED=$(git status --porcelain | grep "^??" | wc -l | tr -d ' ')

    if [ -n "$UNSTAGED" ] || [ -n "$STAGED" ] || [ "$UNTRACKED" -gt 0 ]; then
        echo "📁 커밋되지 않은 변경사항:"
        if [ -n "$STAGED" ]; then
            echo "   Staged: $STAGED"
        fi
        if [ -n "$UNSTAGED" ]; then
            echo "   Unstaged: $UNSTAGED"
        fi
        if [ "$UNTRACKED" -gt 0 ]; then
            echo "   Untracked: ${UNTRACKED}개 파일"
        fi
        echo ""
        echo "💡 커밋하려면 다음 세션에서: /commit"
    else
        echo "✅ 모든 변경사항이 커밋되었습니다."
    fi

    # 오늘 커밋 수
    TODAY_COMMITS=$(git log --since="00:00" --oneline 2>/dev/null | wc -l | tr -d ' ')
    if [ "$TODAY_COMMITS" -gt 0 ]; then
        echo ""
        echo "📈 오늘 커밋: ${TODAY_COMMITS}개"
    fi
else
    echo "⚠️  Git 저장소가 아닙니다."
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "👋 다음에 또 만나요!"
echo ""
