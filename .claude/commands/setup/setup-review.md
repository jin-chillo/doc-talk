---
description: code-review-plugin 설치 및 설정 가이드
---

`code-review-plugin`을 현재 프로젝트에 설치해줘.

**설치 프로세스:**

1. **프로젝트 언어 감지**
   - TypeScript/JavaScript → `typescript` preset
   - Python → `python` preset
   - Go → `go` preset

2. **설치 명령어 실행**
   ```bash
   ./code-review-plugin/setup.sh [preset] [현재 프로젝트 경로]
   ```

3. **설치 확인**
   - `.claude/agents/` 에 에이전트 파일 복사됨
   - `.claude/review-config.json` 설정 파일 생성됨

**설치 후 사용법:**

```bash
# PR 전체 리뷰 (3개 에이전트 병렬)
claude "pr-reviewer로 리뷰해줘"

# 개별 에이전트
claude "code-reviewer로 코드 검토해줘"
claude "security-reviewer로 보안 검사해줘"
claude "test-analyzer로 테스트 분석해줘"
```
