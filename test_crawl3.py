#!/usr/bin/env python3
"""综合测试 - RSS + 浏览器 + 直接爬取"""
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
from crawler.parsers.forum import ForumParser
from trust.evaluator import TrustEvaluator
from storage.sqlite_store import SQLiteStore


def crawl_rss(source_id, source_name, feed_url, tags, trust_base, lang="en"):
    """通过 RSS 爬取"""
    print(f"\n📡 RSS: {source_name}")
    print(f"   URL: {feed_url}")

    store = SQLiteStore("data/crawler.db")
    evaluator = TrustEvaluator()
    rss_parser = RSSParser()
    client = httpx.Client(timeout=20, follow_redirects=True, verify=False)

    try:
        resp = client.get(feed_url, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            print(f"   ❌ Status {resp.status_code}")
            return 0

        source = {
            "id": source_id, "name": source_name,
            "language": lang, "category": "media",
            "base_trust_score": trust_base, "tags": tags,
        }
        articles = rss_parser.parse_feed(resp.text, source)
        print(f"   Found {len(articles)} articles")

        saved = 0
        for art in articles[:10]:
            trust = evaluator.evaluate(art)
            h = hashlib.sha256(art["content"].encode()).hexdigest()[:16]
            if not store.article_exists(h):
                store.save_article(art, h)
                store.save_evaluation(h, trust)
                saved += 1
                print(f"   ✅ [{trust['score']:3d}] {trust['level']['label']} | {art['title'][:50]}")

        print(f"   Saved: {saved}")
        return saved
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return 0


def crawl_browser(source_id, source_name, base_url, sections, tags, trust_base, lang="en"):
    """通过浏览器爬取（反爬站点）"""
    print(f"\n🌐 Browser: {source_name}")

    from crawler.browser import BrowserCrawler
    store = SQLiteStore("data/crawler.db")
    evaluator = TrustEvaluator()
    browser = BrowserCrawler()

    try:
        browser.start()
        saved = 0
        for section in sections:
            articles = browser.crawl_forum_section(base_url, section, {
                "id": source_id, "name": source_name,
                "language": lang, "category": "international_forum",
                "base_trust_score": trust_base, "tags": tags,
            }, max_articles=3)

            for art in articles:
                trust = evaluator.evaluate(art)
                h = hashlib.sha256(art["content"].encode()).hexdigest()[:16]
                if not store.article_exists(h):
                    store.save_article(art, h)
                    store.save_evaluation(h, trust)
                    saved += 1
                    print(f"   ✅ [{trust['score']:3d}] {trust['level']['label']} | {art['title'][:50]}")

        print(f"   Saved: {saved}")
        return saved
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return 0
    finally:
        browser.stop()


def crawl_direct(source_id, source_name, base_url, sections, tags, trust_base, lang="en"):
    """直接 HTTP 爬取（无反爬的站点）"""
    print(f"\n🔗 Direct: {source_name}")

    store = SQLiteStore("data/crawler.db")
    evaluator = TrustEvaluator()
    client = httpx.Client(timeout=20, follow_redirects=True, verify=False)
    saved = 0

    for section in sections:
        url = base_url + section
        try:
            time.sleep(3)
            resp = client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code != 200:
                continue

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "lxml")
            links = set()
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if any(p in href.lower() for p in ["/article/", "/articles/", "/news/"]):
                    if not href.startswith("http"):
                        href = base_url + href
                    if len(href) > 30:
                        links.add(href)

            for link in list(links)[:3]:
                time.sleep(3)
                art_resp = client.get(link, headers={"User-Agent": "Mozilla/5.0"})
                if art_resp.status_code != 200:
                    continue

                art_soup = BeautifulSoup(art_resp.text, "lxml")
                title = ""
                for sel in ["h1", ".article-title"]:
                    el = art_soup.select_one(sel)
                    if el:
                        title = el.get_text(strip=True)[:200]
                        break

                content_el = art_soup.select_one("article, main, .content")
                content = content_el.get_text(separator="\n", strip=True) if content_el else ""

                if len(content) < 200:
                    continue

                art = {
                    "title": title, "author": "", "date": "",
                    "content": content[:5000], "url": link,
                    "source_id": source_id, "source_name": source_name,
                    "language": lang, "category": "academic_journal",
                    "tags": tags, "base_trust_score": trust_base,
                    "user_role": "researcher", "stats": {},
                    "crawled_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                }

                trust = evaluator.evaluate(art)
                h = hashlib.sha256(content.encode()).hexdigest()[:16]
                if not store.article_exists(h):
                    store.save_article(art, h)
                    store.save_evaluation(h, trust)
                    saved += 1
                    print(f"   ✅ [{trust['score']:3d}] {trust['level']['label']} | {title[:50]}")
        except Exception as e:
            print(f"   ⚠️  {e}")

    print(f"   Saved: {saved}")
    return saved


if __name__ == "__main__":
    total = 0

    # ===== RSS 源（最稳定）=====
    total += crawl_rss("reef_builders", "Reef Builders",
        "https://reefbuilders.com/feed/",
        ["news", "coral", "equipment"], 20)

    total += crawl_rss("aquanerd", "Aquanerd",
        "https://aquanerd.com/feed",
        ["coral", "reef", "marine"], 22)

    # ===== 浏览器爬取（反爬站点）=====
    total += crawl_browser("reef2reef", "Reef2Reef",
        "https://www.reef2reef.com",
        ["/forums/saltwater-aquarium-fish.56/"],
        ["coral", "fish", "reef"], 25)

    total += crawl_browser("aquarium_advice", "Aquarium Advice",
        "https://www.aquariumadvice.com",
        ["/forums/saltwater-reef-aquaria.11/"],
        ["reef", "beginner"], 22)

    # ===== 直接爬取（无反爬）=====
    total += crawl_direct("noaa_coral", "NOAA Coral Reef",
        "https://www.coralreef.noaa.gov",
        ["/about/crrc-and-rcci"],
        ["conservation", "monitoring"], 38)

    print(f"\n{'='*50}")
    print(f"Total new articles: {total}")

    store = SQLiteStore("data/crawler.db")
    store.print_stats()
