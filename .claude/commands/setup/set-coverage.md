# /set-coverage - 테스트 커버리지 목표 설정

테스트 커버리지 목표를 설정하고 설정 파일을 업데이트합니다.

---

## 사용법

```bash
/set-coverage 80          # 80% 목표 설정
/set-coverage             # 대화형 설정
```

---

## 실행 단계

### 1. 현재 설정 확인

```bash
# 테스트 프레임워크 감지
ls jest.config.* vitest.config.* pyproject.toml go.mod
```

### 2. 현재 커버리지 분석

```bash
# 현재 커버리지 측정
npm run test:coverage     # JS/TS
pytest --cov              # Python
go test -cover ./...      # Go
```

### 3. 목표 설정

```
📊 현재 커버리지: 65%

? 커버리지 목표를 선택하세요:
  ❯ 70% (현실적)
    80% (권장)
    90% (엄격)
    커스텀

? 세부 목표를 설정할까요? (Y/n)
  - Lines: 80%
  - Functions: 80%
  - Branches: 75%
  - Statements: 80%
```

### 4. 설정 파일 업데이트

**Jest (jest.config.js):**

```javascript
module.exports = {
  // ... 기존 설정
  coverageThreshold: {
    global: {
      branches: 75,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};
```

**Vitest (vite.config.ts):**

```typescript
export default defineConfig({
  test: {
    coverage: {
      thresholds: {
        global: {
          branches: 75,
          functions: 80,
          lines: 80,
          statements: 80,
        },
      },
    },
  },
});
```

**pytest (pyproject.toml):**

```toml
[tool.coverage.report]
fail_under = 80
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
]
```

**Go (Makefile):**

```makefile
COVERAGE_THRESHOLD=80

check-coverage:
	@COVERAGE=$$(go tool cover -func=coverage.out | grep total | awk '{print $$3}' | sed 's/%//'); \
	if [ $$(echo "$$COVERAGE < $(COVERAGE_THRESHOLD)" | bc -l) -eq 1 ]; then \
		echo "❌ Coverage $$COVERAGE% is below $(COVERAGE_THRESHOLD)%"; \
		exit 1; \
	else \
		echo "✅ Coverage $$COVERAGE% meets threshold"; \
	fi
```

### 5. CI 설정 업데이트 (선택)

```
? CI 파이프라인에 커버리지 체크를 추가할까요? (Y/n)
```

**GitHub Actions:**

```yaml
# .github/workflows/test.yml
- name: Check coverage threshold
  run: npm run test:coverage
  # 커버리지 미달 시 CI 실패
```

---

## 커버리지 가이드라인

| 프로젝트 유형 | 권장 목표 | 설명 |
|--------------|----------|------|
| 신규 프로젝트 | 80% | 처음부터 높은 기준 유지 |
| 레거시 마이그레이션 | 50% → 점진적 | 현실적 시작점 |
| 핵심 비즈니스 로직 | 90%+ | 중요 코드는 높은 커버리지 |
| 유틸리티 | 70% | 상대적으로 낮아도 됨 |

---

## 결과 보고

```
✅ 커버리지 목표가 설정되었습니다!

파일: jest.config.js
목표:
  - Lines: 80%
  - Functions: 80%
  - Branches: 75%
  - Statements: 80%

현재 커버리지: 65%
필요한 추가 커버리지: 15%

💡 낮은 커버리지 파일:
  - src/services/payment.ts (45%)
  - src/utils/validation.ts (52%)
  - src/api/handlers.ts (58%)

이 파일들의 테스트를 생성할까요? (Y/n)
```
