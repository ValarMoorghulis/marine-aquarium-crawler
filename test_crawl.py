#!/usr/bin/env python3
"""快速测试爬虫核心流程"""
import sys
import json
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import httpx
from bs4 import BeautifulSoup
from crawler.parsers.forum import ForumParser
from trust.evaluator import TrustEvaluator
from storage.sqlite_store import SQLiteStore


def test_crawl():
    store = SQLiteStore("data/crawler.db")
    parser = ForumParser()
    evaluator = TrustEvaluator()
    client = httpx.Client(timeout=30, follow_redirects=True)

    # 测试爬取 CMF 论坛一个板块
    test_url = "https://www.cmfish.com/bbs/forum.php?mod=forumdisplay&fid=16"
    print(f"Testing: {test_url}")

    try:
        resp = client.get(test_url, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        print(f"  Status: {resp.status_code}, Length: {len(resp.text)}")

        links = parser.extract_article_links(resp.text, "https://www.cmfish.com")
        print(f"  Found {len(links)} article links")

        # 只爬前3篇测试
        saved = 0
        for link in links[:3]:
            try:
                import time
                time.sleep(3)
                art_resp = client.get(link, headers={"User-Agent": "Mozilla/5.0"})
                art_resp.raise_for_status()
                article = parser.parse_article(art_resp.text, link, {
                    "id": "cmfish", "name": "CMF海水观赏鱼论坛",
                    "language": "zh", "category": "domestic_forum",
                    "base_trust_score": 25, "tags": ["reef", "breeding"]
                })

                if article and len(article.get("content", "")) > 50:
                    # 信任评估
                    trust = evaluator.evaluate(article)
                    article["trust_score"] = trust["score"]

                    content_hash = hashlib.sha256(article["content"].encode()).hexdigest()[:16]
                    store.save_article(article, content_hash)
                    store.save_evaluation(content_hash, trust)
                    saved += 1

                    title = article["title"][:50]
                    score = trust["score"]
                    level = trust["level"]["label"]
                    print(f"  ✅ [{score:3d}] {level} | {title}")
            except Exception as e:
                print(f"  ⚠️  Failed: {link[:60]}... - {e}")

        print(f"\nTotal saved: {saved} articles")
        store.print_stats()
        return saved

    except Exception as e:
        print(f"Error: {e}")
        return 0


if __name__ == "__main__":
    test_crawl()
