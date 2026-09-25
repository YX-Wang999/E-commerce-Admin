#!/usr/bin/env bash
# Run Django management commands for scheduled backend tasks.
# Usage:
#   run-scheduled-tasks.sh cancel-timeout
#   run-scheduled-tasks.sh auto-confirm-receipt
#   run-scheduled-tasks.sh process-points-expiry
#   run-scheduled-tasks.sh all

set -euo pipefail

BACKEND_DIR="${BACKEND_DIR:-/var/www/admin/backend}"
LOG_DIR="${LOG_DIR:-/var/log/ecommerce}"
TASK="${1:-}"

if [[ -z "$TASK" ]]; then
  echo "Usage: $0 {cancel-timeout|auto-confirm-receipt|process-points-expiry|all}" >&2
  exit 1
fi

mkdir -p "$LOG_DIR"
cd "$BACKEND_DIR"

if [[ ! -f venv/bin/activate ]]; then
  echo "Virtualenv not found: $BACKEND_DIR/venv" >&2
  exit 1
fi

# shellcheck disable=SC1091
source venv/bin/activate

run_task() {
  local name="$1"
  shift
  local logfile="$LOG_DIR/${name}-$(date +%Y%m%d).log"
  {
    echo "=== $(date -Iseconds) ${name} ==="
    "$@"
    echo "=== done ==="
  } >>"$logfile" 2>&1
}

case "$TASK" in
  cancel-timeout)
    run_task cancel-timeout python manage.py cancel_timeout_orders
    ;;
  auto-confirm-receipt)
    run_task auto-confirm-receipt python manage.py auto_confirm_receipt
    ;;
  process-points-expiry)
    run_task process-points-expiry python manage.py process_points_expiry
    ;;
  all)
    run_task cancel-timeout python manage.py cancel_timeout_orders
    run_task auto-confirm-receipt python manage.py auto_confirm_receipt
    run_task process-points-expiry python manage.py process_points_expiry
    ;;
  *)
    echo "Unknown task: $TASK" >&2
    echo "Usage: $0 {cancel-timeout|auto-confirm-receipt|process-points-expiry|all}" >&2
    exit 1
    ;;
esac
