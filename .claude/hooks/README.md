# Claude Code Hooks

Claude Code 작업 완료 후 자동으로 실행되는 Hook 설정입니다.

---

## 설치 방법

`.claude/settings.json`에 Hook 설정을 추가합니다:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "echo '파일 변경 감지'"
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/session-end.sh"
          }
        ]
      }
    ]
  }
}
```

---

## 제공되는 Hook

### 1. 작업 완료 후 커밋 제안 (post-task.sh)

작업 완료 후 변경사항이 있으면 커밋을 제안합니다.

### 2. 세션 종료 시 요약 (session-end.sh)

세션 종료 시 작업 요약을 출력합니다.

### 3. 병렬 작업 상태 관리 (parallel-state-manager.sh)

`/run-parallel` 커맨드의 상태 파일을 관리합니다.

**기능:**
- 상태 파일 백업/복구
- 진행 상황 추적
- 배치 완료 감지
- 손상된 상태 복구

**설정 예시:**
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {"type": "command", "command": ".claude/hooks/parallel-state-manager.sh backup"}
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {"type": "command", "command": ".claude/hooks/parallel-state-manager.sh progress"}
        ]
      }
    ]
  }
}
```

**명령어:**
```bash
./parallel-state-manager.sh status     # 상태 확인
./parallel-state-manager.sh progress   # 진행 상황
./parallel-state-manager.sh backup     # 백업
./parallel-state-manager.sh recover    # 복구
./parallel-state-manager.sh cleanup    # 정리
```

---

## Hook 종류

| Hook | 트리거 시점 |
|------|------------|
| `PreToolUse` | 도구 실행 전 |
| `PostToolUse` | 도구 실행 후 |
| `SessionEnd` | 세션 종료 시 |
| `PermissionRequest` | 권한 요청 시 |

---

## 주의사항

- Hook은 동기적으로 실행됩니다
- 실행 시간이 긴 Hook은 사용자 경험에 영향을 줍니다
- 민감한 정보를 Hook에서 출력하지 마세요
