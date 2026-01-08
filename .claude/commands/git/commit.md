# /commit - 스마트 커밋

변경사항을 분석하여 컨벤셔널 커밋 메시지를 자동 생성합니다.

---

## 실행 단계

### 1. 변경사항 확인

```bash
git status
git diff --staged
git diff
```

### 2. 변경 분석

- 어떤 파일이 변경되었는지
- 변경의 성격 (feat, fix, refactor, docs, test, chore 등)
- 주요 변경 내용 요약

### 3. 커밋 메시지 생성

**컨벤셔널 커밋 형식:**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**타입 분류:**
| 타입 | 설명 |
|------|------|
| feat | 새로운 기능 |
| fix | 버그 수정 |
| refactor | 리팩토링 |
| docs | 문서 변경 |
| test | 테스트 추가/수정 |
| chore | 빌드, 설정 변경 |
| style | 코드 스타일 변경 |
| perf | 성능 개선 |

### 4. 사용자 확인

생성된 커밋 메시지를 보여주고 확인 요청:

```
📝 커밋 메시지:

feat(auth): 소셜 로그인 기능 추가

- Google OAuth 연동
- 카카오 로그인 연동
- 세션 관리 로직 추가

이 메시지로 커밋할까요? (Y/n/edit)
```

### 5. 커밋 실행

```bash
git add -A  # 또는 선택적 add
git commit -m "<generated message>"
```

---

## 옵션

| 옵션 | 설명 | 예시 |
|------|------|------|
| `--all` | 모든 변경사항 포함 | `/commit --all` |
| `--staged` | staged만 커밋 | `/commit --staged` |
| `--amend` | 마지막 커밋 수정 | `/commit --amend` |

---

## 예시

```bash
/commit                    # 대화형 커밋
/commit --all              # 전체 변경사항 커밋
/commit "feat: 로그인"     # 메시지 직접 지정
```
