---
description: 프로젝트 상태 빠른 점검
---

프로젝트의 전반적인 상태를 빠르게 점검해줘.

**체크 항목:**

1. **Claude 설정**
   - `.claude/` 디렉토리 존재
   - `CLAUDE.md` 파일 존재
   - 커스텀 명령어 존재

2. **테스트**
   - 테스트 파일 존재
   - 테스트 프레임워크 설정

3. **코드 품질**
   - Linter 설정 (ESLint, Pylint 등)
   - Formatter 설정 (Prettier, Black 등)

4. **Git**
   - `.gitignore` 존재
   - Uncommitted changes

5. **의존성**
   - 의존성 파일 존재 (package.json, requirements.txt 등)
   - Lock 파일 존재

6. **문서화**
   - README.md 존재

**출력 형식:**

```markdown
# 프로젝트 건강도 체크

## 점수: [점수]/100

## 체크 결과
| 항목 | 상태 |
|------|------|
| Claude 설정 | ✅/❌ |
| 테스트 | ✅/❌ |
| 코드 품질 | ✅/❌ |
| Git | ✅/❌ |
| 의존성 | ✅/❌ |
| 문서화 | ✅/❌ |

## 개선 제안
1. [제안 사항]
```
