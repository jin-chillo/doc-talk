---
description: 대화에서 제안된 작업들을 서브에이전트로 병렬 실행 (수동 배치)
---

# Run Parallel - 제안된 작업 병렬 실행

이 커맨드는 **이전 대화에서 Claude가 제안한 작업 목록**을 서브에이전트로 병렬 실행합니다.

---

## 필수 행동 규칙 (MUST)

> **이 섹션의 지시사항은 반드시 따라야 합니다.**

### 1. 상태 파일 생성 (필수)

작업 시작 전 **반드시** `.claude/parallel-tasks.json` 파일을 생성하세요:

```bash
# Write 도구로 파일 생성
.claude/parallel-tasks.json
```

### 2. 배치 제한 (필수)

- **최대 10개**까지만 동시에 Task 도구 호출
- 10개 초과 시 반드시 배치 분할
- 각 배치 완료 후 **사용자 확인 대기**

### 3. 상태 업데이트 (필수)

- 각 배치 완료 후 상태 파일 업데이트
- Task 실패 시 `status: "failed"` 기록
- 결과 요약을 `result` 필드에 기록

### 4. 작업 완료 후 (필수)

- 모든 배치 완료 시 상태 파일 삭제 (또는 `--keep-state` 시 유지)
- 최종 결과 요약 출력

---

## 사용 시점

Claude와 대화 중 권장 작업이 나왔을 때:

```
Claude: 분석 결과, 다음 작업을 권장합니다:
1. src/auth/login.ts 보안 취약점 수정
2. src/api/users.ts 성능 최적화
3. src/utils/validator.ts 단위 테스트 추가
...
```

```
User: /run-parallel
```

---

## 실행 방식: 수동 배치

### 왜 수동 배치인가?

| 문제 | 해결책 |
|------|--------|
| Auto compacting 에러 시 상태 손실 | 파일 기반 상태 저장으로 복구 가능 |
| 자동 배치 보장 안됨 (프롬프트 기반) | 사용자가 직접 배치 진행 제어 |
| 컨텍스트 폭발 | 배치마다 `/compact` 가능 |

### 실행 흐름

```
Step 1: 작업 목록 추출 → .claude/parallel-tasks.json 생성
           ↓
Step 2: Batch 1 실행 (최대 10개 병렬)
           ↓
       [상태 파일 업데이트]
           ↓
       [사용자: "계속" 입력]
           ↓
Step 3: Batch 2 실행
           ↓
         ... 반복 ...
           ↓
Step N: 전체 결과 종합
```

---

## 상태 파일

`.claude/parallel-tasks.json`:

```json
{
  "created_at": "2025-01-15T10:30:00Z",
  "total_tasks": 23,
  "batch_size": 10,
  "current_batch": 2,
  "tasks": [
    {
      "id": 1,
      "description": "src/auth/login.ts 보안 취약점 수정",
      "type": "security",
      "target": "src/auth/login.ts",
      "status": "completed",
      "batch": 1,
      "result": "XSS 취약점 2건 수정"
    },
    {
      "id": 11,
      "description": "src/utils/date.ts 테스트 추가",
      "type": "test",
      "target": "src/utils/date.ts",
      "status": "pending",
      "batch": 2
    }
  ]
}
```

**상태 파일이 있으면:**
- 세션 종료 후에도 이어서 진행 가능
- Auto compacting 에러 발생해도 복구 가능
- 어디까지 완료했는지 추적 가능

---

## 실행 프로세스

### Step 1: 작업 목록 생성

```markdown
## 실행할 작업 목록

이전 대화에서 23개 작업이 확인되었습니다.

| # | 작업 | 대상 | 유형 | 배치 |
|---|------|------|------|------|
| 1 | 보안 취약점 수정 | src/auth/login.ts | security | 1 |
| 2 | 성능 최적화 | src/api/users.ts | performance | 1 |
| ... | ... | ... | ... | ... |

**배치 계획:**
- Batch 1: Task 1-10
- Batch 2: Task 11-20
- Batch 3: Task 21-23

상태 파일: `.claude/parallel-tasks.json` 생성됨

**Batch 1 실행하시겠습니까?** (Y/n)
```

### Step 2: 배치 실행

```markdown
## Batch 1/3 실행 중... (Task 1-10)

[10개 서브에이전트 병렬 실행]

---

## Batch 1/3 완료

✅ Task 1: 완료 - XSS 취약점 2건 수정
✅ Task 2: 완료 - 쿼리 최적화 30% 개선
❌ Task 5: 실패 - 파일 충돌

**상태 파일 업데이트됨**

### 권장 조치
1. `/compact` 실행 (컨텍스트 정리)
2. `/run-parallel --continue` (다음 배치)

또는: `/run-parallel --continue --compact`
```

### Step 3: 자동 복구 시스템 (Auto Recovery)

> **핵심 기능**: 세션 종료, 에러, Auto-compacting 발생 시 **자동으로 상태를 감지하고 복구**합니다.

#### 자동 복구 트리거

| 상황 | 자동 감지 | 복구 동작 |
|------|----------|----------|
| 세션 재시작 | `.claude/parallel-tasks.json` 존재 | 자동 복구 제안 |
| Auto-compacting 에러 | 백업 파일 확인 | 자동 롤백 |
| Task 실패 | status: "failed" 감지 | 재시도 제안 |
| 네트워크 타임아웃 | 3회 재시도 후 실패 | 부분 저장 |

#### 자동 복구 프로세스

```
세션 시작 또는 /run-parallel 실행
        ↓
┌─────────────────────────────────┐
│ 상태 파일 자동 감지              │
│ .claude/parallel-tasks.json     │
└─────────────────────────────────┘
        ↓ 파일 존재
┌─────────────────────────────────┐
│ 상태 무결성 검증                 │
│ - JSON 파싱 가능?               │
│ - 필수 필드 존재?               │
│ - 마지막 수정 시간 확인          │
└─────────────────────────────────┘
        ↓ 검증 통과
┌─────────────────────────────────┐
│ 자동 복구 제안 (5초 타임아웃)    │
│                                 │
│ "이전 작업 상태 발견:           │
│  - 완료: 15/23개               │
│  - 실패: 2개                   │
│  - 대기: 6개                   │
│                                 │
│  자동 복구하시겠습니까?          │
│  [Y: 이어서] [n: 새로 시작]     │
│  [r: 실패만 재시도]             │
│                                 │
│  (5초 후 자동으로 이어서 진행)"   │
└─────────────────────────────────┘
        ↓ Y 또는 타임아웃
   자동 복구 시작
        ↓
   남은 배치부터 실행
```

#### 무결성 검증 실패 시 자동 복구

```
JSON 파싱 실패 또는 손상 감지
        ↓
┌─────────────────────────────────┐
│ 백업 파일 탐색                   │
│ .claude/parallel-tasks.json.bak │
│ .claude/parallel-tasks.json.1   │
│ .claude/parallel-tasks.json.2   │
└─────────────────────────────────┘
        ↓ 백업 발견
   최신 유효 백업으로 자동 복원
        ↓
   복구 완료 알림
```

#### 실패 작업 자동 재시도 정책

```json
{
  "retry_policy": {
    "max_retries": 3,
    "backoff": "exponential",
    "backoff_base": 2,
    "retry_on": [
      "network_timeout",
      "rate_limit",
      "temporary_failure"
    ],
    "no_retry_on": [
      "file_not_found",
      "permission_denied",
      "invalid_input"
    ]
  }
}
```

**재시도 동작:**
```
Task 실패 감지
    ↓
[에러 유형 분류]
    ├─ 일시적 에러 (재시도 가능)
    │   → 1초 대기 → 재시도 1
    │   → 2초 대기 → 재시도 2
    │   → 4초 대기 → 재시도 3
    │   → 3회 실패 시 "failed" 기록
    │
    └─ 영구적 에러 (재시도 불가)
        → 즉시 "failed" 기록
        → 에러 원인 상세 기록
```

#### 자동 백업 시스템

매 배치 완료 시 자동 백업:

```bash
# 자동 생성되는 백업 파일
.claude/parallel-tasks.json       # 현재 상태
.claude/parallel-tasks.json.bak   # 이전 배치 상태
.claude/parallel-tasks.json.1     # 1단계 이전
.claude/parallel-tasks.json.2     # 2단계 이전 (최대 3개 유지)
```

#### 복구 명령어

```bash
# 자동 복구 (권장)
/run-parallel --resume

# 특정 백업에서 복구
/run-parallel --restore .claude/parallel-tasks.json.bak

# 실패한 작업만 재시도
/run-parallel --retry-failed

# 특정 작업 재시도
/run-parallel --retry 5,12,18

# 강제 새로 시작 (기존 상태 무시)
/run-parallel --force-new
```

#### 복구 상태 리포트

```markdown
## 자동 복구 완료

### 복구 정보
- 원본 상태 파일: .claude/parallel-tasks.json
- 복구 소스: .claude/parallel-tasks.json.bak
- 복구 시간: 2025-01-15 10:35:22

### 작업 현황
| 상태 | 개수 | 비율 |
|------|------|------|
| ✅ 완료 | 15 | 65% |
| ❌ 실패 | 2 | 9% |
| ⏳ 대기 | 6 | 26% |

### 실패 작업 상세
| # | 작업 | 에러 | 재시도 가능 |
|---|------|------|-----------|
| 5 | src/auth 보안 수정 | 파일 잠금 | ✅ |
| 12 | API 테스트 추가 | 타임아웃 | ✅ |

### 권장 조치
1. 실패 작업 재시도: `/run-parallel --retry-failed`
2. 남은 작업 계속: `/run-parallel --continue`
```

---

## 명령어 옵션

```bash
# 기본 실행
/run-parallel

# 다음 배치 진행
/run-parallel --continue

# 다음 배치 + 자동 compact
/run-parallel --continue --compact

# 이전 세션 이어서
/run-parallel --resume

# 상태 확인
/run-parallel --status

# 특정 배치만
/run-parallel --batch 2

# 실패한 작업 재시도
/run-parallel --retry-failed
/run-parallel --retry 5,12

# 특정 번호만
/run-parallel 1,3,5
/run-parallel 1-5

# 특정 유형만
/run-parallel --type security

# 배치 크기 (기본 10, 최대 10)
/run-parallel --batch-size 5

# 작업 초기화
/run-parallel --reset
```

---

## 에이전트 선택 기준

| 작업 키워드 | 에이전트 | 모델 |
|-------------|----------|------|
| 보안, 취약점, XSS, injection | security-reviewer | Opus |
| 성능, 최적화, 속도 | code-reviewer | Sonnet |
| 테스트, 커버리지 | unit-test-generator | Sonnet |
| 리팩토링, 정리 | code-reviewer | Sonnet |
| 빌드, 실행, 확인 | test-runner | Haiku |

---

## 사용 예시

### 예시 1: 기본 흐름

```
User: 이 PR 리뷰해줘

Claude: 4개 개선 작업을 권장합니다:
1. SQL injection 수정
2. N+1 쿼리 최적화
3. 테스트 추가
4. 타입 정의 추가

User: /run-parallel

Claude:
4개 작업 (1개 배치)
상태 파일: .claude/parallel-tasks.json

Batch 1/1 실행 중...
[4개 서브에이전트 병렬 실행]

완료! 성공: 4/4
```

### 예시 2: 대규모 + 복구

```
User: 프로젝트 전체 분석해줘

Claude: 25개 개선 항목 발견...

User: /run-parallel

Claude:
25개 작업, 3개 배치
Batch 1 실행하시겠습니까?

User: Y

[Batch 1 완료]
/compact 후 "계속" 권장

User: /compact
User: /run-parallel --continue

[Batch 2 실행 중... 에러 발생]

--- 새 세션 ---

User: /run-parallel --resume

Claude:
이전 상태: Batch 1,2 완료 (20개)
남은 작업: Batch 3 (5개)

진행하시겠습니까?
```

---

## 주의사항

1. **상태 파일 필수**: `.claude/parallel-tasks.json` 삭제 시 진행 손실
2. **수동 진행**: 각 배치 후 "계속" 입력 필요
3. **compact 권장**: 대규모 작업 시 배치마다 `/compact`
4. **파일 충돌 방지**: 같은 파일 수정 작업은 자동으로 다른 배치에 배치

---

## 관련 커맨드

- `/interview` - 대화형 문답으로 요구사항 수집
- `/parallel-review` - 3개 리뷰어 병렬 실행 (고정 구성)
- `/compact` - 컨텍스트 수동 압축

---

## Hook 설정 (선택사항)

상태 관리를 더 확실하게 하려면 Hook을 설정할 수 있습니다.

### 1. Hook 스크립트 복사

```bash
cp templates/hooks/parallel-state-manager.sh .claude/hooks/
chmod +x .claude/hooks/parallel-state-manager.sh
```

### 2. settings.json 설정

`.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/parallel-state-manager.sh backup"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/parallel-state-manager.sh progress"
          }
        ]
      }
    ]
  }
}
```

### 3. Hook 명령어

```bash
# 상태 확인
.claude/hooks/parallel-state-manager.sh status

# 진행 상황
.claude/hooks/parallel-state-manager.sh progress

# 백업
.claude/hooks/parallel-state-manager.sh backup

# 복구
.claude/hooks/parallel-state-manager.sh recover

# 정리
.claude/hooks/parallel-state-manager.sh cleanup
```

---

## 참고

- [Claude Agent SDK Best Practices](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [Multi-Agent Orchestration](https://dev.to/bredmond1019/multi-agent-orchestration-running-10-claude-instances-in-parallel-part-3-29da)
- [Auto-Compact 가이드](https://claudelog.com/faqs/what-is-claude-code-auto-compact/)
