#!/bin/bash
# parallel-state-manager.sh
# /run-parallel 커맨드의 상태 파일을 관리하는 Hook
#
# 사용법:
#   이 스크립트는 Claude Code Hook으로 등록하여 사용합니다.
#   Task 도구 호출 전후에 자동으로 상태를 관리합니다.

STATE_FILE=".claude/parallel-tasks.json"
BACKUP_DIR=".claude/parallel-backups"
MAX_BACKUPS=3
RETRY_MAX=3
RETRY_BACKOFF_BASE=2

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 상태 파일 존재 확인
check_state_file() {
    if [ -f "$STATE_FILE" ]; then
        echo -e "${GREEN}[parallel-state]${NC} 상태 파일 존재: $STATE_FILE"
        return 0
    else
        echo -e "${YELLOW}[parallel-state]${NC} 상태 파일 없음"
        return 1
    fi
}

# 상태 파일 백업
backup_state() {
    if [ -f "$STATE_FILE" ]; then
        mkdir -p "$BACKUP_DIR"
        local timestamp=$(date +%Y%m%d_%H%M%S)
        cp "$STATE_FILE" "$BACKUP_DIR/parallel-tasks_$timestamp.json"
        echo -e "${GREEN}[parallel-state]${NC} 백업 생성: parallel-tasks_$timestamp.json"
    fi
}

# 상태 파일 검증
validate_state() {
    if [ -f "$STATE_FILE" ]; then
        # JSON 유효성 검사
        if command -v jq &> /dev/null; then
            if jq empty "$STATE_FILE" 2>/dev/null; then
                echo -e "${GREEN}[parallel-state]${NC} 상태 파일 유효"
                return 0
            else
                echo -e "${RED}[parallel-state]${NC} 상태 파일 손상됨"
                return 1
            fi
        else
            # jq 없으면 기본 검사만
            if grep -q "tasks" "$STATE_FILE"; then
                return 0
            fi
        fi
    fi
    return 1
}

# 진행 상황 출력
show_progress() {
    if [ -f "$STATE_FILE" ] && command -v jq &> /dev/null; then
        local total=$(jq '.total_tasks // 0' "$STATE_FILE")
        local completed=$(jq '[.tasks[] | select(.status == "completed")] | length' "$STATE_FILE")
        local failed=$(jq '[.tasks[] | select(.status == "failed")] | length' "$STATE_FILE")
        local current_batch=$(jq '.current_batch // 1' "$STATE_FILE")

        echo -e "${GREEN}[parallel-state]${NC} 진행 상황: $completed/$total 완료, $failed 실패 (Batch $current_batch)"
    fi
}

# 배치 완료 체크
check_batch_complete() {
    if [ -f "$STATE_FILE" ] && command -v jq &> /dev/null; then
        local current_batch=$(jq '.current_batch // 1' "$STATE_FILE")
        local pending_in_batch=$(jq --arg batch "$current_batch" \
            '[.tasks[] | select(.batch == ($batch | tonumber) and .status == "pending")] | length' \
            "$STATE_FILE")

        if [ "$pending_in_batch" -eq 0 ]; then
            echo -e "${GREEN}[parallel-state]${NC} Batch $current_batch 완료"
            return 0
        fi
    fi
    return 1
}

# 다음 배치로 이동
advance_batch() {
    if [ -f "$STATE_FILE" ] && command -v jq &> /dev/null; then
        local current_batch=$(jq '.current_batch // 1' "$STATE_FILE")
        local next_batch=$((current_batch + 1))

        # 다음 배치에 작업이 있는지 확인
        local has_next=$(jq --arg batch "$next_batch" \
            '[.tasks[] | select(.batch == ($batch | tonumber))] | length' \
            "$STATE_FILE")

        if [ "$has_next" -gt 0 ]; then
            jq ".current_batch = $next_batch" "$STATE_FILE" > "$STATE_FILE.tmp" && \
                mv "$STATE_FILE.tmp" "$STATE_FILE"
            echo -e "${GREEN}[parallel-state]${NC} Batch $next_batch로 이동"
            return 0
        else
            echo -e "${GREEN}[parallel-state]${NC} 모든 배치 완료"
            return 1
        fi
    fi
    return 1
}

# 상태 파일 정리
cleanup_state() {
    if [ -f "$STATE_FILE" ]; then
        # 최종 백업
        backup_state

        # 완료 여부 확인
        if command -v jq &> /dev/null; then
            local pending=$(jq '[.tasks[] | select(.status == "pending")] | length' "$STATE_FILE")
            if [ "$pending" -eq 0 ]; then
                rm -f "$STATE_FILE"
                echo -e "${GREEN}[parallel-state]${NC} 상태 파일 정리 완료"
            else
                echo -e "${YELLOW}[parallel-state]${NC} 미완료 작업 있음, 상태 파일 유지"
            fi
        fi
    fi
}

# 손상된 상태 복구
recover_state() {
    if [ -d "$BACKUP_DIR" ]; then
        local latest_backup=$(ls -t "$BACKUP_DIR"/*.json 2>/dev/null | head -1)
        if [ -n "$latest_backup" ]; then
            cp "$latest_backup" "$STATE_FILE"
            echo -e "${GREEN}[parallel-state]${NC} 상태 복구 완료: $latest_backup"
            return 0
        fi
    fi
    echo -e "${RED}[parallel-state]${NC} 복구할 백업 없음"
    return 1
}

# ============================================
# 자동 복구 시스템 (Auto Recovery System)
# ============================================

# 롤링 백업 관리 (최대 MAX_BACKUPS개 유지)
rotate_backups() {
    if [ -f "$STATE_FILE" ]; then
        mkdir -p "$BACKUP_DIR"

        # 기존 백업 파일 순환
        if [ -f "${STATE_FILE}.2" ]; then
            rm -f "${STATE_FILE}.2"
        fi
        if [ -f "${STATE_FILE}.1" ]; then
            mv "${STATE_FILE}.1" "${STATE_FILE}.2"
        fi
        if [ -f "${STATE_FILE}.bak" ]; then
            mv "${STATE_FILE}.bak" "${STATE_FILE}.1"
        fi

        # 현재 상태를 .bak으로 백업
        cp "$STATE_FILE" "${STATE_FILE}.bak"
        echo -e "${GREEN}[parallel-state]${NC} 롤링 백업 완료"
    fi
}

# 자동 복구 감지 및 제안
auto_detect_recovery() {
    if [ -f "$STATE_FILE" ]; then
        # 상태 파일 검증
        if ! validate_state > /dev/null 2>&1; then
            echo -e "${YELLOW}[parallel-state]${NC} 손상된 상태 파일 감지"
            auto_recover_from_backup
            return $?
        fi

        # 미완료 작업 확인
        if command -v jq &> /dev/null; then
            local pending=$(jq '[.tasks[] | select(.status == "pending" or .status == "running")] | length' "$STATE_FILE" 2>/dev/null || echo "0")
            local failed=$(jq '[.tasks[] | select(.status == "failed")] | length' "$STATE_FILE" 2>/dev/null || echo "0")
            local completed=$(jq '[.tasks[] | select(.status == "completed")] | length' "$STATE_FILE" 2>/dev/null || echo "0")
            local total=$(jq '.total_tasks // 0' "$STATE_FILE" 2>/dev/null || echo "0")

            if [ "$pending" -gt 0 ] || [ "$failed" -gt 0 ]; then
                echo ""
                echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
                echo -e "${BLUE}║     이전 작업 상태 발견 (Auto Recovery)     ║${NC}"
                echo -e "${BLUE}╠════════════════════════════════════════════╣${NC}"
                echo -e "${BLUE}║${NC} ✅ 완료: ${completed}/${total}개                          ${BLUE}║${NC}"
                echo -e "${BLUE}║${NC} ❌ 실패: ${failed}개                              ${BLUE}║${NC}"
                echo -e "${BLUE}║${NC} ⏳ 대기: ${pending}개                              ${BLUE}║${NC}"
                echo -e "${BLUE}╠════════════════════════════════════════════╣${NC}"
                echo -e "${BLUE}║${NC} [Y] 이어서 진행  [n] 새로 시작            ${BLUE}║${NC}"
                echo -e "${BLUE}║${NC} [r] 실패만 재시도  [s] 상태만 확인        ${BLUE}║${NC}"
                echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
                echo ""
                return 0
            fi
        fi
    fi
    return 1
}

# 백업에서 자동 복구
auto_recover_from_backup() {
    echo -e "${YELLOW}[parallel-state]${NC} 백업에서 자동 복구 시도..."

    # 우선순위: .bak > .1 > .2 > BACKUP_DIR
    local backup_files=("${STATE_FILE}.bak" "${STATE_FILE}.1" "${STATE_FILE}.2")

    for backup in "${backup_files[@]}"; do
        if [ -f "$backup" ]; then
            # 백업 파일 검증
            if command -v jq &> /dev/null && jq empty "$backup" 2>/dev/null; then
                cp "$backup" "$STATE_FILE"
                echo -e "${GREEN}[parallel-state]${NC} 자동 복구 성공: $backup"
                return 0
            fi
        fi
    done

    # BACKUP_DIR에서 복구 시도
    if [ -d "$BACKUP_DIR" ]; then
        local latest_backup=$(ls -t "$BACKUP_DIR"/*.json 2>/dev/null | head -1)
        if [ -n "$latest_backup" ] && jq empty "$latest_backup" 2>/dev/null; then
            cp "$latest_backup" "$STATE_FILE"
            echo -e "${GREEN}[parallel-state]${NC} 자동 복구 성공: $latest_backup"
            return 0
        fi
    fi

    echo -e "${RED}[parallel-state]${NC} 자동 복구 실패: 유효한 백업 없음"
    return 1
}

# 에러 유형별 재시도 가능 여부 판단
is_retryable_error() {
    local error_type="$1"

    # 재시도 가능한 에러
    local retryable=("network_timeout" "rate_limit" "temporary_failure" "connection_reset" "server_error")

    for err in "${retryable[@]}"; do
        if [ "$error_type" = "$err" ]; then
            return 0
        fi
    done

    return 1
}

# 실패 작업 자동 재시도
auto_retry_failed() {
    if [ ! -f "$STATE_FILE" ] || ! command -v jq &> /dev/null; then
        return 1
    fi

    local failed_tasks=$(jq -r '.tasks[] | select(.status == "failed") | .id' "$STATE_FILE")
    local retry_count=0

    for task_id in $failed_tasks; do
        local error_type=$(jq -r --arg id "$task_id" '.tasks[] | select(.id == ($id | tonumber)) | .error_type // "unknown"' "$STATE_FILE")
        local retries=$(jq -r --arg id "$task_id" '.tasks[] | select(.id == ($id | tonumber)) | .retry_count // 0' "$STATE_FILE")

        if is_retryable_error "$error_type" && [ "$retries" -lt "$RETRY_MAX" ]; then
            # 재시도 횟수 증가
            local new_retries=$((retries + 1))
            local backoff=$((RETRY_BACKOFF_BASE ** retries))

            echo -e "${YELLOW}[parallel-state]${NC} Task $task_id 재시도 ($new_retries/$RETRY_MAX), ${backoff}초 대기..."

            # 상태 업데이트
            jq --arg id "$task_id" --argjson retries "$new_retries" \
                '(.tasks[] | select(.id == ($id | tonumber))) |= . + {status: "pending", retry_count: $retries}' \
                "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"

            retry_count=$((retry_count + 1))
        fi
    done

    if [ "$retry_count" -gt 0 ]; then
        echo -e "${GREEN}[parallel-state]${NC} $retry_count개 작업 재시도 대기열에 추가됨"
        return 0
    fi

    echo -e "${YELLOW}[parallel-state]${NC} 재시도 가능한 작업 없음"
    return 1
}

# 세션 시작 시 자동 감지 (Hook에서 호출)
session_start_check() {
    if [ -f "$STATE_FILE" ]; then
        auto_detect_recovery
        return $?
    fi
    return 1
}

# 상태 요약 출력
show_summary() {
    if [ ! -f "$STATE_FILE" ] || ! command -v jq &> /dev/null; then
        echo -e "${YELLOW}[parallel-state]${NC} 상태 파일 없음"
        return 1
    fi

    local total=$(jq '.total_tasks // 0' "$STATE_FILE")
    local completed=$(jq '[.tasks[] | select(.status == "completed")] | length' "$STATE_FILE")
    local failed=$(jq '[.tasks[] | select(.status == "failed")] | length' "$STATE_FILE")
    local pending=$(jq '[.tasks[] | select(.status == "pending")] | length' "$STATE_FILE")
    local running=$(jq '[.tasks[] | select(.status == "running")] | length' "$STATE_FILE")
    local current_batch=$(jq '.current_batch // 1' "$STATE_FILE")
    local created=$(jq -r '.created_at // "unknown"' "$STATE_FILE")

    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo -e "${BLUE}        병렬 작업 상태 요약                 ${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo -e " 생성 시간: $created"
    echo -e " 현재 배치: $current_batch"
    echo -e "${BLUE}───────────────────────────────────────────${NC}"
    echo -e " ✅ 완료:    $completed / $total"
    echo -e " ❌ 실패:    $failed"
    echo -e " ⏳ 대기:    $pending"
    echo -e " 🔄 실행중:  $running"
    echo -e "${BLUE}───────────────────────────────────────────${NC}"

    local progress=$((completed * 100 / total))
    echo -e " 진행률: ${progress}%"
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo ""
}

# 메인 로직
case "${1:-status}" in
    "init")
        # 초기화: .claude 디렉토리 확인
        mkdir -p .claude
        echo -e "${GREEN}[parallel-state]${NC} 초기화 완료"
        ;;
    "check")
        check_state_file
        ;;
    "validate")
        validate_state
        ;;
    "backup")
        backup_state
        ;;
    "progress")
        show_progress
        ;;
    "batch-complete")
        check_batch_complete
        ;;
    "next-batch")
        advance_batch
        ;;
    "cleanup")
        cleanup_state
        ;;
    "recover")
        recover_state
        ;;
    # ===== 자동 복구 명령어 =====
    "rotate")
        rotate_backups
        ;;
    "auto-detect")
        auto_detect_recovery
        ;;
    "auto-recover")
        auto_recover_from_backup
        ;;
    "auto-retry")
        auto_retry_failed
        ;;
    "session-check")
        session_start_check
        ;;
    "summary")
        show_summary
        ;;
    "status"|*)
        check_state_file && show_summary
        ;;
esac
