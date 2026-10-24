#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PORT="${1:-8081}"
echo "เปิด http://localhost:${PORT}"
python3 admin/server.py "$PORT"
