"""RSS 解析器 - 最稳定的爬取方式"""
import re
from datetime import datetime
from bs4 import BeautifulSoup


class RSSParser:
    """解析 RSS/Atom feed，提取文章"""

    def parse_feed(self, xml_text, source):
        """解析 RSS/Atom XML，返回文章列表"""
        soup = BeautifulSoup(xml_text, "lxml-xml")
        articles = []

        # RSS 2.0
        for item in soup.find_all("item"):
            article = self._parse_rss_item(item, source)
            if article:
                articles.append(article)

        # Atom
        for entry in soup.find_all("entry"):
            article = self._parse_atom_entry(entry, source)
            if article:
                articles.append(article)

        return articles

    def _parse_rss_item(self, item, source):
        title = self._get_text(item, "title")
        link = self._get_text(item, "link")
        description = self._get_text(item, "description")
        content = self._get_text(item, "content\\:encoded") or description
        pub_date = self._get_text(item, "pubDate")
        author = self._get_text(item, "dc\\:creator") or self._get_text(item, "author")

        if not link or len(content or "") < 50:
            return None

        # 清理 HTML
        content_clean = self._clean_html(content)

        return {
            "title": title or "Untitled",
            "author": author or "",
            "date": pub_date or "",
            "content": content_clean,
            "url": link,
            "source_id": source["id"],
            "source_name": source["name"],
            "language": source.get("language", "en"),
            "category": source.get("category", ""),
            "tags": source.get("tags", []),
            "base_trust_score": source.get("base_trust_score", 20),
            "user_role": "",
            "stats": {},
            "crawled_at": datetime.now().isoformat(),
        }

    def _parse_atom_entry(self, entry, source):
        title = self._get_text(entry, "title")
        link_el = entry.find("link")
        link = link_el["href"] if link_el and link_el.get("href") else ""
        content_el = entry.find("content") or entry.find("summary")
        content = content_el.get_text() if content_el else ""
        pub_date = self._get_text(entry, "published") or self._get_text(entry, "updated")
        author_el = entry.find("author")
        author = ""
        if author_el:
            name_el = author_el.find("name")
            author = name_el.get_text() if name_el else ""

        if not link or len(content) < 50:
            return None

        return {
            "title": title or "Untitled",
            "author": author,
            "date": pub_date or "",
            "content": self._clean_html(content),
            "url": link,
            "source_id": source["id"],
            "source_name": source["name"],
            "language": source.get("language", "en"),
            "category": source.get("category", ""),
            "tags": source.get("tags", []),
            "base_trust_score": source.get("base_trust_score", 20),
            "user_role": "",
            "stats": {},
            "crawled_at": datetime.now().isoformat(),
        }

    def _get_text(self, parent, tag):
        el = parent.find(tag)
        return el.get_text(strip=True) if el else ""

    def _clean_html(self, html):
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "img", "iframe"]):
            tag.decompose()
        for br in soup.find_all("br"):
            br.replace_with("\n")
        text = soup.get_text(separator="\n", strip=True)
        return re.sub(r"\n{3,}", "\n\n", text)
