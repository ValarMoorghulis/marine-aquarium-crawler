#!/bin/bash
# 海水水族爬虫 - 每日自动执行脚本
set -e

PROJECT_DIR="/home/ubuntu/Git/marine-aquarium-crawler"
VENV="$PROJECT_DIR/.venv/bin/python"
LOG_DIR="$PROJECT_DIR/logs"
TODAY=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/crawl_$TODAY.log"

mkdir -p "$LOG_DIR"

echo "=== Marine Crawler Daily Run: $(date) ===" >> "$LOG_FILE"

# 1. 增量爬取
cd "$PROJECT_DIR"
$VENV main.py --mode incremental >> "$LOG_FILE" 2>&1 || echo "Crawl failed" >> "$LOG_FILE"

# 2. 信任评估
$VENV main.py --mode evaluate >> "$LOG_FILE" 2>&1 || echo "Evaluate failed" >> "$LOG_FILE"

# 3. 同步到 My-vault
$VENV main.py --mode sync >> "$LOG_FILE" 2>&1 || echo "Sync failed" >> "$LOG_FILE"

# 4. 推送爬虫仓库
cd "$PROJECT_DIR"
git add -A && git diff --cached --quiet || git commit -m "auto: daily crawl $(date +%Y-%m-%d)" >> "$LOG_FILE" 2>&1
GIT_SSH_COMMAND="ssh -i /home/ubuntu/.ssh/id_ed25519 -o StrictHostKeyChecking=no" git push >> "$LOG_FILE" 2>&1 || true

echo "=== Done: $(date) ===" >> "$LOG_FILE"
