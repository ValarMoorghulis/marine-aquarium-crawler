"""Git 同步模块 - 将归档文章同步到 My-vault"""
import json
import subprocess
from pathlib import Path
from datetime import datetime

VAULT_PATH = Path.home() / "Git" / "My-vault" / "02_收获" / "海水水族"
VAULT_PATH.mkdir(parents=True, exist_ok=True)

# 主题分类映射
TOPIC_MAP = {
    "coral": "珊瑚养殖",
    "reef": "珊瑚养殖",
    "sp": "珊瑚养殖",
    "lps": "珊瑚养殖",
    "fish": "海水鱼",
    "breeding": "海水鱼",
    "disease": "鱼病治疗",
    "quarantine": "鱼病治疗",
    "water-quality": "水质管理",
    "water-chemistry": "水质管理",
    "equipment": "设备评测",
    "lighting": "设备评测",
    "research": "学术研究",
    "academic": "学术研究",
    "aquascape": "造景设计",
}


class GitSyncer:
    def __init__(self, store):
        self.store = store

    def sync_to_vault(self):
        """同步高信任度文章到 My-vault"""
        articles = self.store.get_archivable_articles()
        print(f"Syncing {len(articles)} articles to My-vault...")

        for article_data in articles:
            article = json.loads(article_data["data_json"])
            self._write_article(article, article_data)
            self.store.mark_archived(article_data["content_hash"])

        self._update_index()
        self._git_commit()

    def _write_article(self, article, meta):
        """将文章写入 Markdown 文件"""
        topic = self._classify_topic(article)
        topic_dir = VAULT_PATH / topic
        topic_dir.mkdir(exist_ok=True)

        # 文件名
        source = article.get("source_id", "unknown")
        date = article.get("crawled_at", datetime.now().isoformat())[:10]
        title = self._safe_filename(article.get("title", "untitled"))
        filename = f"{source}_{date}_{title}.md"
        filepath = topic_dir / filename

        # 保持原文格式
        lang = article.get("language", "en")
        content = article.get("content", "")

        md_content = f"""# {article.get('title', 'Untitled')}

> **来源**: [{article.get('source_name', '')}]({article.get('url', '')})
> **作者**: {article.get('author', 'Unknown')}
> **日期**: {article.get('date', 'N/A')}
> **信任度**: {meta.get('trust_score', 0)}/100 ({meta.get('trust_level', 'unknown')})
> **采集时间**: {meta.get('crawled_at', '')}

---

{content}

---

*采集自 {article.get('source_name', '')} | 信任评估: {meta.get('trust_level', 'unknown')}*
"""

        filepath.write_text(md_content, encoding="utf-8")
        print(f"  ✅ {topic}/{filename}")

    def _classify_topic(self, article):
        """根据标签分类主题"""
        tags = article.get("tags", [])
        for tag in tags:
            tag_lower = tag.lower().replace(" ", "-")
            for key, topic in TOPIC_MAP.items():
                if key in tag_lower:
                    return topic
        return "其他"

    def _safe_filename(self, title, max_len=60):
        """生成安全文件名"""
        import re
        safe = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', title)
        safe = re.sub(r'\s+', '_', safe.strip())
        return safe[:max_len]

    def _update_index(self):
        """更新索引 README"""
        index_content = "# 🐠 海水水族知识库\n\n"
        index_content += f"> 自动采集更新 | 最后同步: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

        for topic_dir in sorted(VAULT_PATH.iterdir()):
            if topic_dir.is_dir() and not topic_dir.name.startswith("."):
                articles = list(topic_dir.glob("*.md"))
                if articles:
                    index_content += f"## {topic_dir.name}\n\n"
                    for a in sorted(articles, reverse=True):
                        index_content += f"- [{a.stem}]({topic_dir.name}/{a.name})\n"
                    index_content += "\n"

        (VAULT_PATH / "README.md").write_text(index_content, encoding="utf-8")

    def _git_commit(self):
        """Git commit + push"""
        try:
            vault_dir = VAULT_PATH.parent.parent  # My-vault
            subprocess.run(["git", "add", "02_收获/海水水族/"], cwd=vault_dir, check=True)
            result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                cwd=vault_dir
            )
            if result.returncode != 0:
                subprocess.run(
                    ["git", "commit", "-m", f"📚 海水水族知识自动同步 {datetime.now().strftime('%Y-%m-%d')}"],
                    cwd=vault_dir, check=True
                )
                subprocess.run(["git", "push"], cwd=vault_dir, check=True)
                print("  📤 Git push complete")
            else:
                print("  ℹ️  No changes to commit")
        except Exception as e:
            print(f"  ❌ Git sync failed: {e}")
