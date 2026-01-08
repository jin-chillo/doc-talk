#!/bin/bash
# 작업 완료 후 커밋 제안 Hook
#
# 사용법:
# .claude/settings.json에 아래 설정 추가
# {
#   "hooks": {
#     "PostToolUse": [{
#       "matcher": "Edit|Write",
#       "hooks": [{"type": "command", "command": ".claude/hooks/post-task.sh"}]
#     }]
#   }
# }

# Git 저장소 확인
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    exit 0
fi

# 변경된 파일 수 확인
CHANGED_FILES=$(git status --porcelain | wc -l | tr -d ' ')

if [ "$CHANGED_FILES" -gt 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📝 변경된 파일: ${CHANGED_FILES}개"
    echo ""
    git status --short | head -10
    if [ "$CHANGED_FILES" -gt 10 ]; then
        echo "   ... 외 $((CHANGED_FILES - 10))개"
    fi
    echo ""
    echo "💡 커밋하려면: /commit"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi
