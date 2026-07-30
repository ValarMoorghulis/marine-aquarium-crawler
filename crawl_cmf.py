#!/usr/bin/env python3
"""CMF 爬虫 - 通过 OpenClaw web_fetch API 访问"""
import sys
import json
import hashlib
import re
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import subprocess
import tempfile
from bs4 import BeautifulSoup
from trust.evaluator import TrustEvaluator
from storage.sqlite_store import SQLiteStore

# CMF 论坛板块（使用实际有帖子的子版块）
CMF_SECTIONS = {
    "海水鱼饲养-主版": "https://www.cmfish.com/bbs/forum.php?mod=forumdisplay&fid=22",
    "海水鱼-子版1": "https://www.cmfish.com/bbs/forum.php?mod=forumdisplay&fid=544",
    "海水鱼-子版2": "https://www.cmfish.com/bbs/forum.php?mod=forumdisplay&fid=545",
    "海水鱼-子版3": "https://www.cmfish.com/bbs/forum.php?mod=forumdisplay&fid=546",
    "海水鱼-子版4": "https://www.cmfish.com/bbs/forum.php?mod=forumdisplay&fid=547",
}


def get_thread_urls_from_page(html):
    """从 Discuz 论坛页面提取帖子 URL"""
    urls = set()
    tids = set()

    # 提取所有 tid
    for m in re.finditer(r'[?&;]tid=(\d+)', html):
        tid = m.group(1)
        # 排除 redirect 链接（ goto=lastpost）
        context = html[max(0, m.start()-50):m.end()+50]
        if 'redirect' not in context and 'goto=' not in context:
            tids.add(tid)

    for tid in tids:
        urls.add(f"https://www.cmfish.com/bbs/forum.php?mod=viewthread&tid={tid}")

    return list(urls)


def extract_thread_content(html, url):
    """从 Discuz 帖子页面提取内容"""
    soup = BeautifulSoup(html, "lxml")

    # 标题
    title = ""
    title_el = soup.select_one("h1.ts, .thread-title, #thread_subject")
    if title_el:
        title = title_el.get_text(strip=True)
    if not title:
        for sel in ["h1", "title"]:
            el = soup.select_one(sel)
            if el:
                title = el.get_text(strip=True).split("-")[0].strip()
                break

    # 作者
    author = ""
    author_el = soup.select_one(".authi a, .postauthor a, .xw1")
    if author_el:
        author = author_el.get_text(strip=True)

    # 正文 - 取主楼
    content = ""
    for sel in [".t_f", "#postmessage_", ".postcontent", ".message-content"]:
        el = soup.select_one(sel)
        if el:
            # 清理
            for tag in el(["script", "style", "iframe"]):
                tag.decompose()
            for br in el.find_all("br"):
                br.replace_with("\n")
            content = el.get_text(separator="\n", strip=True)
            break

    # 统计
    stats = {"likes": 0, "replies": 0}
    replies_el = soup.select_one(".ts .xg1")
    if replies_el:
        m = re.search(r"(\d+)", replies_el.get_text())
        if m:
            stats["replies"] = int(m.group(1))

    support_el = soup.select_one("[id^='recommend_add_']")
    if support_el:
        m = re.search(r"(\d+)", support_el.get_text())
        if m:
            stats["likes"] = int(m.group(1))

    # 用户等级
    user_role = ""
    rank_el = soup.select_one(".rankline, .postlevel")
    if rank_el:
        user_role = rank_el.get_text(strip=True)

    if len(content) < 50:
        return None

    return {
        "title": title,
        "author": author,
        "date": "",
        "content": content,
        "url": url,
        "source_id": "cmfish",
        "source_name": "CMF海水观赏鱼论坛",
        "language": "zh",
        "category": "domestic_forum",
        "tags": ["reef", "fish", "coral", "breeding"],
        "base_trust_score": 25,
        "user_role": user_role,
        "stats": stats,
        "crawled_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def curl_get(url):
    """用 curl 获取页面（绕过 TLS 指纹检测）"""
    result = subprocess.run(
        ["curl", "-sL", "--max-time", "20",
         "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
         "-H", "Accept: text/html,application/xhtml+xml",
         "-H", "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8",
         url],
        capture_output=True, timeout=25
    )
    if result.returncode != 0:
        return None
    # CMF 用 GBK 编码
    try:
        return result.stdout.decode("gbk")
    except Exception:
        return result.stdout.decode("utf-8", errors="replace")


def crawl_cmf_via_curl(max_threads_per_section=5):
    """通过 curl 爬取 CMF（绕过 TLS 指纹检测）"""
    store = SQLiteStore("data/crawler.db")
    evaluator = TrustEvaluator()

    total = 0
    for section_name, section_url in CMF_SECTIONS.items():
        print(f"\n📂 {section_name}: {section_url}")
        try:
            time.sleep(3)
            html = curl_get(section_url)
            if not html:
                print(f"   ❌ Failed to fetch")
                continue

            thread_urls = get_thread_urls_from_page(html)
            print(f"   Found {len(thread_urls)} threads")

            for turl in thread_urls[:max_threads_per_section]:
                try:
                    time.sleep(4)
                    thtml = curl_get(turl)
                    if not thtml:
                        continue

                    article = extract_thread_content(thtml, turl)
                    if not article:
                        continue

                    trust = evaluator.evaluate(article)
                    h = hashlib.sha256(article["content"].encode()).hexdigest()[:16]

                    if not store.article_exists(h):
                        store.save_article(article, h)
                        store.save_evaluation(h, trust)
                        total += 1
                        score = trust["score"]
                        level = trust["level"]["label"]
                        print(f"   ✅ [{score:3d}] {level} | {article['title'][:45]}")

                except Exception as e:
                    print(f"   ⚠️  {turl[:50]}... - {e}")

        except Exception as e:
            print(f"   ❌ Section error: {e}")

    return total


if __name__ == "__main__":
    print("=" * 60)
    print("🐠 CMF Forum Crawler")
    print("=" * 60)
    total = crawl_cmf_via_curl(max_threads_per_section=3)
    print(f"\n{'=' * 60}")
    print(f"Total new articles from CMF: {total}")
    print(f"{'=' * 60}")
    store = SQLiteStore("data/crawler.db")
    store.print_stats()
