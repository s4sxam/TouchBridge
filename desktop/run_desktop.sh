#!/usr/bin/env bash
set -e

echo "========================================================"
echo "       TouchBridge Universal - Linux/Mac Host Launcher  "
echo "========================================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

python3 -m touchbridge.main "$@"
