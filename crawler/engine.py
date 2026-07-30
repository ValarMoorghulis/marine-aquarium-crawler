"""爬虫引擎 - 调度采集任务"""
import json
import time
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta

import httpx
from fake_useragent import UserAgent

from crawler.parsers.forum import ForumParser
from crawler.parsers.blog import BlogParser
from crawler.parsers.academic import AcademicParser
from crawler.content_classifier import get_classifier

logger = logging.getLogger(__name__)


class CrawlerEngine:
    def __init__(self, store, source_id=None):
        self.store = store
        self.config = self._load_config()
        self.ua = UserAgent()
        self.client = httpx.Client(
            timeout=30,
            follow_redirects=True,
            headers={"Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7"}
        )
        self.parsers = {
            "forum": ForumParser(),
            "blog": BlogParser(),
            "academic": AcademicParser(),
            "institution": AcademicParser(),
            "knowledge_base": AcademicParser(),
        }
        self.source_filter = source_id

    def _load_config(self):
        config_path = Path(__file__).parent.parent / "config" / "sources.json"
        with open(config_path) as f:
            return json.load(f)

    def crawl_all(self):
        """全量爬取所有源"""
        sources = self._get_filtered_sources()
        logger.info(f"Starting full crawl of {len(sources)} sources")
        for source in sources:
            self._crawl_source(source, full=True)
        logger.info("Full crawl complete")

    def crawl_incremental(self):
        """增量爬取 - 只爬取更新的内容"""
        sources = self._get_filtered_sources()
        logger.info(f"Starting incremental crawl of {len(sources)} sources")
        for source in sources:
            last_crawl = self.store.get_last_crawl_time(source["id"])
            if last_crawl and datetime.fromisoformat(last_crawl) > datetime.now() - timedelta(hours=20):
                logger.debug(f"Skipping {source['id']}: crawled recently")
                continue
            self._crawl_source(source, full=False)
        logger.info("Incremental crawl complete")

    def _get_filtered_sources(self):
        sources = self.config["sources"]
        if self.source_filter:
            sources = [s for s in sources if s["id"] == self.source_filter]
        priority_order = {"high": 0, "medium": 1, "low": 2}
        return sorted(sources, key=lambda s: priority_order.get(s.get("priority", "low"), 2))

    def _crawl_source(self, source, full=False):
        """爬取单个源"""
        logger.info(f"Crawling: {source['name']} ({source['url']})")
        try:
            parser = self.parsers.get(source["type"], ForumParser())
            articles = []
            for section in source["crawl_config"]["sections"]:
                url = source["url"] + section
                articles.extend(self._fetch_section(url, source, parser))

            saved = 0
            skipped = 0
            classifier = get_classifier()
            for article in articles:
                # 内容分类过滤：丢弃闲聊/水帖
                keep, classify_result = classifier.should_keep(article)
                if not keep:
                    skipped += 1
                    logger.debug(
                        f"  Skipped [{classify_result['content_type']}]: "
                        f"{article.get('title', '')[:60]}"
                    )
                    continue
                content_hash = hashlib.sha256(article["content"].encode()).hexdigest()[:16]
                if not self.store.article_exists(content_hash):
                    # 将分类结果写入 article 元数据
                    article["content_type"] = classify_result["content_type"]
                    article["classification_confidence"] = classify_result["confidence"]
                    self.store.save_article(article, content_hash)
                    saved += 1

            self.store.update_crawl_time(source["id"])
            logger.info(
                f"  {source['id']}: found {len(articles)}, "
                f"kept {saved}, skipped {skipped} (noise/discussion)"
            )
        except Exception as e:
            logger.error(f"  Failed to crawl {source['id']}: {e}")

    def _fetch_section(self, url, source, parser):
        """获取一个板块的文章列表"""
        articles = []
        try:
            delay = source["crawl_config"].get("delay_seconds", 3)
            time.sleep(delay + (hash(url) % 2))  # 礼貌延迟 + 随机偏移

            headers = {"User-Agent": self.ua.random}
            resp = self.client.get(url, headers=headers)
            resp.raise_for_status()

            links = parser.extract_article_links(resp.text, url)
            max_pages = source["crawl_config"].get("max_pages_per_section", 5)

            for link in links[:max_pages * 10]:  # 限制每板块最多抓取文章数
                try:
                    time.sleep(delay)
                    article_resp = self.client.get(link, headers=headers)
                    article_resp.raise_for_status()
                    article = parser.parse_article(article_resp.text, link, source)
                    if article and len(article.get("content", "")) > 100:
                        articles.append(article)
                except Exception as e:
                    logger.debug(f"  Failed to fetch article {link}: {e}")
        except Exception as e:
            logger.error(f"  Failed to fetch section {url}: {e}")
        return articles
