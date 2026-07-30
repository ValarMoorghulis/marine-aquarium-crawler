#!/usr/bin/env python3
"""完整爬取 - 所有可用源"""
import sys
import json
import hashlib
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
warnings.filterwarnings("ignore")

import httpx
from crawler.parsers.rss import RSSParser
from trust.evaluator import TrustEvaluator
from storage.sqlite_store import SQLiteStore

# 所有已验证可用的 RSS 源
RSS_FEEDS = [
    ("reef_builders", "Reef Builders", "https://reefbuilders.com/feed/", ["news", "coral"], 20, "en"),
    ("aquanerd", "Aquanerd", "https://aquanerd.com/feed", ["coral", "reef", "marine"], 22, "en"),
    ("reef_hobbyist", "Reef Hobbyist Magazine", "https://www.reefhobbyist.com/feed/", ["reef", "coral", "husbandry"], 25, "en"),
    ("saltwater_blog", "Saltwater Aquarium Blog", "https://www.saltwateraquariumblog.com/feed/", ["saltwater", "reef", "guide"], 20, "en"),
]


def main():
    store = SQLiteStore("data/crawler.db")
    evaluator = TrustEvaluator()
    rss_parser = RSSParser()
    client = httpx.Client(timeout=20, follow_redirects=True, verify=False)
    total = 0

    print("=" * 60)
    print("🐠 Marine Aquarium Crawler - Full Run")
    print("=" * 60)

    for source_id, name, feed_url, tags, trust_base, lang in RSS_FEEDS:
        print(f"\n📡 {name}")
        try:
            resp = client.get(feed_url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code != 200:
                print(f"   ❌ HTTP {resp.status_code}")
                continue

            source = {
                "id": source_id, "name": name,
                "language": lang, "category": "media",
                "base_trust_score": trust_base, "tags": tags,
            }
            articles = rss_parser.parse_feed(resp.text, source)
            print(f"   Found {len(articles)} articles")

            saved = 0
            for art in articles:
                trust = evaluator.evaluate(art)
                h = hashlib.sha256(art["content"].encode()).hexdigest()[:16]
                if not store.article_exists(h):
                    store.save_article(art, h)
                    store.save_evaluation(h, trust)
                    saved += 1
                    level = trust["level"]["label"]
                    score = trust["score"]
                    title = art["title"][:55]
                    print(f"   ✅ [{score:3d}] {level} | {title}")

            total += saved
            print(f"   → Saved {saved} new")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print(f"\n{'=' * 60}")
    print(f"📊 Total new articles: {total}")
    print(f"{'=' * 60}")
    store.print_stats()


if __name__ == "__main__":
    main()
