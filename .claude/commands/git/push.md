# /push - 스마트 푸시

원격 저장소에 안전하게 푸시합니다.

---

## 실행 단계

### 1. 사전 검사

```bash
# 현재 브랜치 확인
git branch --show-current

# 원격 연결 상태 확인
git remote -v

# 로컬/원격 차이 확인
git status
git log origin/$(git branch --show-current)..HEAD --oneline
```

### 2. 안전 검사

**⚠️ 경고 상황:**

| 상황 | 대응 |
|------|------|
| main/master 브랜치 | 확인 요청 |
| force push 필요 | 명시적 확인 |
| 충돌 가능성 | pull 먼저 제안 |
| 커밋되지 않은 변경 | 커밋 먼저 제안 |

### 3. 푸시 실행

```bash
# 일반 푸시
git push origin <branch>

# 새 브랜치인 경우
git push -u origin <branch>
```

### 4. 결과 보고

```
✅ 푸시 완료!

브랜치: feature/login
커밋: 3개
원격: origin (github.com/user/repo)

🔗 https://github.com/user/repo/tree/feature/login
```

---

## 옵션

| 옵션 | 설명 | 예시 |
|------|------|------|
| `--force` | 강제 푸시 (주의!) | `/push --force` |
| `--dry-run` | 실제 푸시 없이 확인 | `/push --dry-run` |

---

## 예시

```bash
/push                      # 현재 브랜치 푸시
/push --dry-run            # 푸시 미리보기
/push origin develop       # 특정 원격/브랜치
```
