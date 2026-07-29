"""学术论文/机构网站解析器"""
from datetime import datetime
from bs4 import BeautifulSoup
import trafilatura


class AcademicParser:
    def extract_article_links(self, html, base_url):
        """从学术网站提取文章链接"""
        soup = BeautifulSoup(html, "lxml")
        links = set()

        # Generic article link patterns
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if any(p in href.lower() for p in ["/article/", "/papers/", "/research/", "/news/"]):
                if not href.startswith("http"):
                    href = base_url.rstrip("/") + "/" + href.lstrip("/")
                if len(href) > 20:
                    links.add(href)

        return list(links)[:30]

    def parse_article(self, html, url, source):
        """解析学术文章"""
        soup = BeautifulSoup(html, "lxml")

        # 标题
        title = ""
        for sel in ["h1", ".article-title", ".paper-title", "title"]:
            el = soup.select_one(sel)
            if el:
                title = el.get_text(strip=True)
                break

        # 作者
        author = ""
        for sel in [".author-list", ".authors", "meta[name='author']"]:
            el = soup.select_one(sel)
            if el:
                author = el.get("content", "") if el.name == "meta" else el.get_text(strip=True)
                break

        # 正文
        content = trafilatura.extract(html)
        if not content:
            content_el = soup.select_one("article, .article-body, main, .content")
            if content_el:
                content = content_el.get_text(separator="\n", strip=True)

        return {
            "title": title,
            "author": author,
            "date": "",
            "content": content or "",
            "url": url,
            "source_id": source["id"],
            "source_name": source["name"],
            "language": source.get("language", "en"),
            "category": source.get("category", ""),
            "tags": source.get("tags", []),
            "base_trust_score": source.get("base_trust_score", 35),
            "user_role": "researcher",
            "stats": {},
            "crawled_at": datetime.now().isoformat(),
        }
