"""浏览器爬虫 - 使用 Playwright 绕过反爬保护"""
import re
import time
import logging
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BrowserCrawler:
    """使用 Playwright 无头浏览器爬取有反爬保护的站点"""

    def __init__(self):
        self.playwright = None
        self.browser = None

    def start(self):
        from playwright.sync_api import sync_playwright
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )

    def stop(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def fetch_page(self, url, wait_ms=3000):
        """用浏览器获取页面内容"""
        context = self.browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
        )
        # 注入反检测脚本
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = {runtime: {}};
        """)

        page = context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(wait_ms)
            html = page.content()
            return html
        except Exception as e:
            logger.error(f"Browser fetch failed for {url}: {e}")
            return None
        finally:
            page.close()
            context.close()

    def crawl_forum_section(self, base_url, section_path, source, max_articles=5):
        """爬取论坛板块"""
        url = base_url + section_path
        html = self.fetch_page(url, wait_ms=5000)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        links = set()

        # XenForo
        for a in soup.select("a[data-tp-primary], .structItem-title a"):
            href = a.get("href", "")
            if href and "/threads/" in href:
                if not href.startswith("http"):
                    href = base_url + "/" + href.lstrip("/")
                links.add(href)

        # Discuz
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if re.search(r"thread-\d+-1-1\.html|tid=\d+", href):
                if not href.startswith("http"):
                    href = base_url + "/" + href.lstrip("/")
                if "redirect" not in href:
                    links.add(href)

        articles = []
        for link in list(links)[:max_articles]:
            time.sleep(3)
            art_html = self.fetch_page(link, wait_ms=3000)
            if art_html:
                article = self._parse_article(art_html, link, source)
                if article and len(article.get("content", "")) > 100:
                    articles.append(article)

        return articles

    def _parse_article(self, html, url, source):
        soup = BeautifulSoup(html, "lxml")

        title = ""
        for sel in ["h1.p-title-value", "h1.title", "h1"]:
            el = soup.select_one(sel)
            if el:
                title = el.get_text(strip=True)
                break

        author = ""
        for sel in [".message-userDetails .username", ".author a", ".postauthor a"]:
            el = soup.select_one(sel)
            if el:
                author = el.get_text(strip=True)
                break

        content = ""
        for sel in [".message-body .bbWrapper", ".message-content", ".postcontent", ".t_f"]:
            el = soup.select_one(sel)
            if el:
                for tag in el(["script", "style", "iframe"]):
                    tag.decompose()
                content = el.get_text(separator="\n", strip=True)
                break

        return {
            "title": title,
            "author": author,
            "date": "",
            "content": content,
            "url": url,
            "source_id": source["id"],
            "source_name": source["name"],
            "language": source.get("language", "en"),
            "category": source.get("category", ""),
            "tags": source.get("tags", []),
            "base_trust_score": source.get("base_trust_score", 25),
            "user_role": "",
            "stats": {},
            "crawled_at": datetime.now().isoformat(),
        }
