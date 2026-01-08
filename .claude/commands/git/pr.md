# /pr - Pull Request 생성

GitHub/GitLab PR을 자동으로 생성합니다.

---

## 실행 단계

### 1. 사전 검사

```bash
# 현재 브랜치
git branch --show-current

# 푸시되지 않은 커밋 확인
git log origin/$(git branch --show-current)..HEAD --oneline 2>/dev/null || echo "새 브랜치"

# 원격 확인
git remote -v
```

### 2. PR 정보 수집

**자동 분석:**
- 브랜치명에서 이슈 번호 추출 (`feature/123-login` → #123)
- 커밋 메시지들 분석
- 변경 파일 목록

**PR 템플릿 생성:**

```markdown
## Summary
<!-- 변경사항 요약 (커밋 분석 기반) -->

## Changes
<!-- 주요 변경 파일 목록 -->

## Test Plan
<!-- 테스트 방법 -->

## Related Issues
<!-- 관련 이슈 링크 -->
```

### 3. 사용자 확인

```
📋 PR 정보:

제목: feat: 소셜 로그인 기능 추가
브랜치: feature/login → main
커밋: 5개
변경: +234 -12 (8 files)

이대로 PR을 생성할까요? (Y/n/edit)
```

### 4. PR 생성

```bash
# GitHub CLI 사용
gh pr create \
  --title "<title>" \
  --body "<body>" \
  --base main \
  --head <current-branch>
```

### 5. 결과 보고

```
✅ PR 생성 완료!

#42: feat: 소셜 로그인 기능 추가
🔗 https://github.com/user/repo/pull/42

리뷰어: @teammate
라벨: enhancement
```

---

## 옵션

| 옵션 | 설명 | 예시 |
|------|------|------|
| `--base` | 베이스 브랜치 지정 | `/pr --base develop` |
| `--draft` | 드래프트 PR | `/pr --draft` |
| `--reviewer` | 리뷰어 지정 | `/pr --reviewer @user` |
| `--label` | 라벨 추가 | `/pr --label bug` |

---

## 예시

```bash
/pr                        # 대화형 PR 생성
/pr --draft                # 드래프트로 생성
/pr --base develop         # develop에 PR
/pr "로그인 기능 추가"      # 제목 직접 지정
```

---

## 요구사항

- GitHub CLI (`gh`) 설치 필요
- `gh auth login` 인증 완료
