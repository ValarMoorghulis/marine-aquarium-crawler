"""Agent 调度器 - 自主调度爬虫任务"""
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class AgentScheduler:
    """Agent 自主调度器，由 OpenClaw cron 触发"""

    def __init__(self):
        self.state_path = Path("data/agent_state.json")
        self.state = self._load_state()

    def _load_state(self):
        if self.state_path.exists():
            with open(self.state_path) as f:
                return json.load(f)
        return {
            "last_daily_run": None,
            "last_weekly_run": None,
            "last_sync": None,
            "total_articles_crawled": 0,
            "total_articles_synced": 0,
        }

    def _save_state(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, "w") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def should_run_daily(self):
        """是否需要执行每日任务"""
        last = self.state.get("last_daily_run")
        if not last:
            return True
        last_dt = datetime.fromisoformat(last)
        return (datetime.now() - last_dt).total_seconds() > 82800  # 23小时

    def should_run_weekly(self):
        """是否需要执行每周任务"""
        last = self.state.get("last_weekly_run")
        if not last:
            return True
        last_dt = datetime.fromisoformat(last)
        return (datetime.now() - last_dt).total_seconds() > 604800 - 3600  # ~7天

    def mark_daily_run(self):
        self.state["last_daily_run"] = datetime.now().isoformat()
        self._save_state()

    def mark_weekly_run(self):
        self.state["last_weekly_run"] = datetime.now().isoformat()
        self._save_state()

    def get_status(self):
        """返回当前调度状态"""
        return {
            "next_daily": self._time_until(self.state.get("last_daily_run"), 86400),
            "next_weekly": self._time_until(self.state.get("last_weekly_run"), 604800),
            "total_crawled": self.state.get("total_articles_crawled", 0),
            "total_synced": self.state.get("total_articles_synced", 0),
        }

    def _time_until(self, last_iso, interval):
        if not last_iso:
            return "now"
        last_dt = datetime.fromisoformat(last_iso)
        diff = interval - (datetime.now() - last_dt).total_seconds()
        if diff <= 0:
            return "now"
        hours = int(diff // 3600)
        mins = int((diff % 3600) // 60)
        return f"{hours}h{mins}m"
