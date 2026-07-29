"""博客/文章解析器"""
from datetime import datetime
from bs4 import BeautifulSoup
import trafilatura


class BlogParser:
    def extract_article_links(self, html, base_url):
        """从博客列表页提取文章链接"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        links = set()

        # WordPress patterns
        for a in soup.select("article a, .post-title a, h2 a, h3 a"):
            href = a.get("href", "")
            if href and len(href) > 10:
                if not href.startswith("http"):
                    href = base_url.rstrip("/") + "/" + href.lstrip("/")
                links.add(href)

        return list(links)

    def parse_article(self, html, url, source):
        """解析博客文章"""
        soup = BeautifulSoup(html, "lxml")

        # 标题
        title = ""
        for sel in ["h1.entry-title", "h1.post-title", "h1", "title"]:
            el = soup.select_one(sel)
            if el:
                title = el.get_text(strip=True)
                break

        # 正文提取 - 优先 trafilatura
        content = trafilatura.extract(html)
        if not content:
            content_el = soup.select_one("article, .post-content, .entry-content, main")
            if content_el:
                content = content_el.get_text(separator="\n", strip=True)

        return {
            "title": title,
            "author": "",
            "date": "",
            "content": content or "",
            "url": url,
            "source_id": source["id"],
            "source_name": source["name"],
            "language": source.get("language", "en"),
            "category": source.get("category", ""),
            "tags": source.get("tags", []),
            "base_trust_score": source.get("base_trust_score", 10),
            "user_role": "",
            "stats": {},
            "crawled_at": datetime.now().isoformat(),
        }
