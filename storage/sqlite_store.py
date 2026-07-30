"""SQLite 本地存储"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime


class SQLiteStore:
    def __init__(self, db_path="data/crawler.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS articles (
                content_hash TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                title TEXT,
                author TEXT,
                url TEXT,
                language TEXT,
                category TEXT,
                data_json TEXT NOT NULL,
                trust_score INTEGER DEFAULT 0,
                trust_level TEXT DEFAULT 'unverified',
                trust_reasons TEXT,
                evaluated_at TEXT,
                archived INTEGER DEFAULT 0,
                crawled_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_source ON articles(source_id);
            CREATE INDEX IF NOT EXISTS idx_trust ON articles(trust_level);
            CREATE INDEX IF NOT EXISTS idx_archived ON articles(archived);

            CREATE TABLE IF NOT EXISTS crawl_log (
                source_id TEXT PRIMARY KEY,
                last_crawl TEXT,
                total_articles INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS crawl_history (
                url TEXT PRIMARY KEY,
                source_id TEXT,
                title TEXT,
                content_hash TEXT,
                status TEXT DEFAULT 'ok',
                crawled_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_history_source ON crawl_history(source_id);
            CREATE INDEX IF NOT EXISTS idx_history_time ON crawl_history(crawled_at);
        """)
        self.conn.commit()

    def url_visited(self, url):
        """检查 URL 是否已爬取过"""
        cur = self.conn.execute("SELECT 1 FROM crawl_history WHERE url=?", (url,))
        return cur.fetchone() is not None

    def mark_visited(self, url, source_id="", title="", content_hash="", status="ok"):
        """标记 URL 为已爬取"""
        self.conn.execute(
            "INSERT OR REPLACE INTO crawl_history (url, source_id, title, content_hash, status, crawled_at) VALUES (?, ?, ?, ?, ?, ?)",
            (url, source_id, title, content_hash, status, datetime.now().isoformat())
        )
        self.conn.commit()

    def get_visited_count(self, source_id=None):
        """获取已爬取的 URL 数量"""
        if source_id:
            cur = self.conn.execute("SELECT COUNT(*) as c FROM crawl_history WHERE source_id=?", (source_id,))
        else:
            cur = self.conn.execute("SELECT COUNT(*) as c FROM crawl_history")
        return cur.fetchone()["c"]

    def article_exists(self, content_hash):
        cur = self.conn.execute("SELECT 1 FROM articles WHERE content_hash=?", (content_hash,))
        return cur.fetchone() is not None

    def save_article(self, article, content_hash):
        self.conn.execute(
            """INSERT OR IGNORE INTO articles
            (content_hash, source_id, title, author, url, language, category, data_json, crawled_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (content_hash, article["source_id"], article["title"], article["author"],
             article["url"], article.get("language", ""), article.get("category", ""),
             json.dumps(article, ensure_ascii=False), article.get("crawled_at", datetime.now().isoformat()))
        )
        self.conn.commit()

    def save_evaluation(self, content_hash, result):
        self.conn.execute(
            """UPDATE articles SET trust_score=?, trust_level=?, trust_reasons=?, evaluated_at=?
            WHERE content_hash=?""",
            (result["score"], result["level"]["level"],
             json.dumps(result["reasons"], ensure_ascii=False),
             datetime.now().isoformat(), content_hash)
        )
        self.conn.commit()

    def get_unevaluated_articles(self, limit=500):
        cur = self.conn.execute(
            "SELECT content_hash, data_json FROM articles WHERE trust_level='unverified' LIMIT ?",
            (limit,)
        )
        return cur.fetchall()

    def get_archivable_articles(self):
        """获取可归档的文章（trust_score >= 20）"""
        cur = self.conn.execute(
            """SELECT content_hash, data_json, trust_score, trust_level
            FROM articles WHERE archived=0 AND trust_score >= 20
            ORDER BY trust_score DESC"""
        )
        return cur.fetchall()

    def mark_archived(self, content_hash):
        self.conn.execute("UPDATE articles SET archived=1 WHERE content_hash=?", (content_hash,))
        self.conn.commit()

    def update_crawl_time(self, source_id):
        self.conn.execute(
            """INSERT OR REPLACE INTO crawl_log (source_id, last_crawl, total_articles)
            VALUES (?, ?, (SELECT COUNT(*) FROM articles WHERE source_id=?))""",
            (source_id, datetime.now().isoformat(), source_id)
        )
        self.conn.commit()

    def get_last_crawl_time(self, source_id):
        cur = self.conn.execute("SELECT last_crawl FROM crawl_log WHERE source_id=?", (source_id,))
        row = cur.fetchone()
        return row["last_crawl"] if row else None

    def print_stats(self):
        cur = self.conn.execute("""
            SELECT source_id, trust_level, COUNT(*) as cnt
            FROM articles GROUP BY source_id, trust_level ORDER BY source_id
        """)
        print("\n📊 Crawler Statistics")
        print("=" * 50)
        for row in cur:
            print(f"  {row['source_id']:20s} | {row['trust_level']:15s} | {row['cnt']}")
        
        # 爬取历史统计
        cur2 = self.conn.execute("""
            SELECT source_id, COUNT(*) as cnt, 
                   MIN(crawled_at) as first, MAX(crawled_at) as last
            FROM crawl_history GROUP BY source_id ORDER BY source_id
        """)
        rows = cur2.fetchall()
        if rows:
            print("\n🔗 Crawl History (URLs visited)")
            print("-" * 50)
            total_visited = 0
            for row in rows:
                print(f"  {row['source_id']:20s} | {row['cnt']:5d} URLs | last: {row['last'][:10]}")
                total_visited += row['cnt']
            print(f"  {'TOTAL':20s} | {total_visited:5d} URLs")
        print("=" * 50)
