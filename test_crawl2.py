#!/usr/bin/env python3
"""快速测试 - 爬取可访问的源"""
import sys
import json
import hashlib
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import httpx
from bs4 import BeautifulSoup
from trust.evaluator import TrustEvaluator
from storage.sqlite_store import SQLiteStore


def test_wordpress(source_id, source_name, base_url, sections, tags, trust_base):
    """测试 WordPress 博客爬取"""
    store = SQLiteStore("data/crawler.db")
    evaluator = TrustEvaluator()
    client = httpx.Client(timeout=20, follow_redirects=True, verify=False)
    saved = 0

    for section in sections:
        url = base_url + section
        print(f"\nFetching: {url}")
        try:
            time.sleep(2)
            resp = client.get(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
            if resp.status_code != 200:
                print(f"  Status: {resp.status_code}, skip")
                continue

            soup = BeautifulSoup(resp.text, "lxml")
            links = set()
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if len(href) > 20 and not href.endswith(("/tag/", "/category/", "#")):
                    if not href.startswith("http"):
                        href = base_url + "/" + href.lstrip("/")
                    if base_url in href and href.count("/") >= 4:
                        links.add(href)

            links = list(links)[:5]
            print(f"  Found {len(links)} articles to fetch")

            for link in links:
                try:
                    time.sleep(2)
                    art_resp = client.get(link, headers={"User-Agent": "Mozilla/5.0"})
                    if art_resp.status_code != 200:
                        continue

                    art_soup = BeautifulSoup(art_resp.text, "lxml")
                    title = ""
                    for sel in ["h1.entry-title", "h1.post-title", "h1"]:
                        el = art_soup.select_one(sel)
                        if el:
                            title = el.get_text(strip=True)
                            break

                    content_el = art_soup.select_one("article, .post-content, .entry-content, main")
                    content = content_el.get_text(separator="\n", strip=True) if content_el else ""

                    if len(content) < 100:
                        continue

                    article = {
                        "title": title,
                        "author": "",
                        "date": "",
                        "content": content,
                        "url": link,
                        "source_id": source_id,
                        "source_name": source_name,
                        "language": "en",
                        "category": "media",
                        "tags": tags,
                        "base_trust_score": trust_base,
                        "user_role": "",
                        "stats": {},
                        "crawled_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    }

                    trust = evaluator.evaluate(article)
                    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

                    if not store.article_exists(content_hash):
                        store.save_article(article, content_hash)
                        store.save_evaluation(content_hash, trust)
                        saved += 1
                        print(f"  ✅ [{trust['score']:3d}] {trust['level']['label']} | {title[:50]}")

                except Exception as e:
                    print(f"  ⚠️  {e}")

        except Exception as e:
            print(f"  Error: {e}")

    return saved


def test_academic(source_id, source_name, base_url, sections, tags, trust_base):
    """测试学术站点爬取"""
    store = SQLiteStore("data/crawler.db")
    evaluator = TrustEvaluator()
    client = httpx.Client(timeout=20, follow_redirects=True, verify=False)
    saved = 0

    for section in sections:
        url = base_url + section
        print(f"\nFetching: {url}")
        try:
            time.sleep(3)
            resp = client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code != 200:
                print(f"  Status: {resp.status_code}")
                continue

            soup = BeautifulSoup(resp.text, "lxml")
            links = set()
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if any(p in href.lower() for p in ["/article/", "/articles/"]):
                    if not href.startswith("http"):
                        href = base_url + href
                    if len(href) > 30:
                        links.add(href)

            links = list(links)[:5]
            print(f"  Found {len(links)} articles")

            for link in links:
                try:
                    time.sleep(3)
                    art_resp = client.get(link, headers={"User-Agent": "Mozilla/5.0"})
                    if art_resp.status_code != 200:
                        continue

                    art_soup = BeautifulSoup(art_resp.text, "lxml")
                    title = ""
                    for sel in ["h1", ".article-title", "title"]:
                        el = art_soup.select_one(sel)
                        if el:
                            title = el.get_text(strip=True)[:200]
                            break

                    content_el = art_soup.select_one("article, main, .content, .article-body")
                    content = content_el.get_text(separator="\n", strip=True) if content_el else ""

                    if len(content) < 200:
                        continue

                    article = {
                        "title": title,
                        "author": "",
                        "date": "",
                        "content": content[:5000],
                        "url": link,
                        "source_id": source_id,
                        "source_name": source_name,
                        "language": "en",
                        "category": "academic_journal",
                        "tags": tags,
                        "base_trust_score": trust_base,
                        "user_role": "researcher",
                        "stats": {},
                        "crawled_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    }

                    trust = evaluator.evaluate(article)
                    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

                    if not store.article_exists(content_hash):
                        store.save_article(article, content_hash)
                        store.save_evaluation(content_hash, trust)
                        saved += 1
                        print(f"  ✅ [{trust['score']:3d}] {trust['level']['label']} | {title[:50]}")

                except Exception as e:
                    print(f"  ⚠️  {e}")

        except Exception as e:
            print(f"  Error: {e}")

    return saved


if __name__ == "__main__":
    total = 0

    # Reef Builders
    total += test_wordpress(
        "reef_builders", "Reef Builders", "https://reefbuilders.com",
        ["/tag/coral/", "/tag/reef-aquarium/"],
        ["news", "coral"], 20
    )

    # NOAA
    total += test_academic(
        "noaa_coral", "NOAA Coral Reef Conservation", "https://www.coralreef.noaa.gov",
        ["/about/crrc-and-rcci"],
        ["conservation", "monitoring"], 38
    )

    print(f"\n{'='*50}")
    print(f"Total articles saved: {total}")

    store = SQLiteStore("data/crawler.db")
    store.print_stats()
