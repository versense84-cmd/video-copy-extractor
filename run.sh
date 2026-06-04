#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "未找到 .venv，请先按 README 安装依赖。"
  exit 1
fi

source .venv/bin/activate
exec uvicorn app.main:app --host 127.0.0.1 --port 8787
