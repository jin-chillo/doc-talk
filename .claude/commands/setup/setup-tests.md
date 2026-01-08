# /setup-tests - 테스트 환경 설정

프로젝트에 테스트 환경을 자동으로 설정합니다.

---

## 실행 단계

### 1. 프로젝트 분석

```bash
# 패키지 매니저 확인
ls package.json pyproject.toml go.mod pubspec.yaml

# 기존 테스트 설정 확인
ls jest.config.* vitest.config.* pytest.ini setup.cfg
```

### 2. 테스트 프레임워크 감지/선택

**자동 감지:**

| 파일 | 프레임워크 |
|------|-----------|
| `package.json` + React/Next | Jest 또는 Vitest |
| `vite.config.*` | Vitest |
| `pyproject.toml` / `requirements.txt` | pytest |
| `go.mod` | go test |
| `pubspec.yaml` | flutter_test |

**사용자 선택 (감지 실패 시):**

```
? 테스트 프레임워크를 선택하세요:
  ❯ Jest
    Vitest
    pytest
    go test
    flutter_test
```

### 3. 커버리지 목표 설정

```
? 커버리지 목표를 설정하세요:
  ❯ 80% (권장)
    70%
    90%
    커스텀
```

### 4. 설정 파일 생성

**Jest:**
```javascript
// jest.config.js
module.exports = {
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};
```

**Vitest:**
```typescript
// vite.config.ts (test 섹션)
test: {
  coverage: {
    thresholds: {
      global: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
    },
  },
}
```

**pytest:**
```toml
# pyproject.toml
[tool.coverage.report]
fail_under = 80
```

**Go:**
```makefile
# Makefile
test-coverage:
	@COVERAGE=$$(go tool cover -func=coverage.out | grep total | awk '{print $$3}' | sed 's/%//'); \
	if [ $$(echo "$$COVERAGE < 80" | bc -l) -eq 1 ]; then \
		echo "Coverage $$COVERAGE% is below 80%"; exit 1; \
	fi
```

### 5. 테스트 에이전트 설치

```bash
# 필요한 에이전트만 복사
cp templates/agents/test/* .claude/agents/
```

### 6. package.json / pyproject.toml 스크립트 추가

**JavaScript/TypeScript:**
```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage"
  }
}
```

**Python:**
```toml
[tool.poetry.scripts]
test = "pytest"
```

---

## 생성되는 파일

| 파일 | 설명 |
|------|------|
| `jest.config.js` / `vitest.config.ts` | 테스트 설정 |
| `src/test/setup.ts` | 테스트 셋업 |
| `.claude/agents/test-*.md` | 테스트 에이전트 |

---

## 설치 후 사용법

```bash
# 테스트 실행
claude "test-runner로 테스트 실행해줘"

# 테스트 생성
claude "unit-test-generator로 src/services/user.ts 테스트 만들어줘"

# 전체 파이프라인
claude "test-suite로 전체 테스트 파이프라인 실행해줘"
```
