"""论坛解析器 - 支持 XenForo / Discuz / Flarum"""
import re
from datetime import datetime
from bs4 import BeautifulSoup

from readability import Document
import trafilatura


class ForumParser:
    def extract_article_links(self, html, base_url):
        """从论坛列表页提取文章链接"""
        soup = BeautifulSoup(html, "lxml")
        links = set()

        # XenForo pattern
        for a in soup.select("a[data-tp-primary], a.PreviewTooltip, .structItem-title a"):
            href = a.get("href", "")
            if href and ("/threads/" in href or "/topic/" in href):
                if not href.startswith("http"):
                    href = base_url.rstrip("/") + "/" + href.lstrip("/")
                links.add(href)

        # Discuz pattern
        for a in soup.select("a[href*='thread-'], a[href*='viewthread']"):
            href = a.get("href", "")
            if href and not href.startswith("http"):
                href = base_url.rstrip("/") + "/" + href.lstrip("/")
            if href:
                links.add(href)

        # Generic fallback - find all thread-like links
        if not links:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if any(p in href for p in ["/threads/", "/topic/", "thread-", "tid="]):
                    if not href.startswith("http"):
                        href = base_url.rstrip("/") + "/" + href.lstrip("/")
                    links.add(href)

        return list(links)

    def parse_article(self, html, url, source):
        """解析单篇文章"""
        soup = BeautifulSoup(html, "lxml")

        # 提取标题
        title = ""
        for sel in ["h1.p-title-value", "h1.title", ".thread-title", "title"]:
            el = soup.select_one(sel)
            if el:
                title = el.get_text(strip=True)
                break

        # 提取作者
        author = ""
        for sel in [".message-userDetails .username", ".authi a", ".postauthor a", ".author a"]:
            el = soup.select_one(sel)
            if el:
                author = el.get_text(strip=True)
                break

        # 提取日期
        date_str = ""
        for sel in ["time[datetime]", ".message-date time", ".postdate time", ".authi time"]:
            el = soup.select_one(sel)
            if el:
                date_str = el.get("datetime", "") or el.get_text(strip=True)
                break

        # 提取正文
        content = self._extract_content(soup)

        # 提取互动数据
        stats = self._extract_stats(soup)

        # 获取用户等级信息（用于信任度评估）
        user_role = self._extract_user_role(soup)

        return {
            "title": title,
            "author": author,
            "date": date_str,
            "content": content,
            "url": url,
            "source_id": source["id"],
            "source_name": source["name"],
            "language": source.get("language", "en"),
            "category": source.get("category", ""),
            "tags": source.get("tags", []),
            "base_trust_score": source.get("base_trust_score", 10),
            "user_role": user_role,
            "stats": stats,
            "crawled_at": datetime.now().isoformat(),
        }

    def _extract_content(self, soup):
        """提取正文内容，保留格式"""
        # 移除不需要的元素
        for el in soup.select(".message-signature, .ad-block, .js-unstickTarget, nav, footer"):
            el.decompose()

        # 尝试用 readability 提取
        content_html = ""
        for sel in [".message-body .bbWrapper", ".message-content", ".postcontent",
                     "#postmessage_", ".t_f", ".post_body"]:
            el = soup.select_one(sel)
            if el:
                content_html = str(el)
                break

        if not content_html:
            # fallback to readability
            try:
                content_html = Document(str(soup)).summary()
            except Exception:
                content_html = trafilatura.extract(str(soup)) or ""

        # 转为干净文本，保留段落结构
        if content_html:
            inner_soup = BeautifulSoup(content_html, "lxml")
            # 保留列表和段落
            for br in inner_soup.find_all("br"):
                br.replace_with("\n")
            for p in inner_soup.find_all(["p", "div"]):
                p.insert_after("\n")
            text = inner_soup.get_text(separator="\n", strip=True)
            # 清理多余空行
            text = re.sub(r"\n{3,}", "\n\n", text)
            return text.strip()
        return ""

    def _extract_stats(self, soup):
        """提取互动统计"""
        stats = {"likes": 0, "replies": 0, "views": 0}

        # XenForo likes
        for el in soup.select(".reactionsBar .reactionsBar-link, .likeCount"):
            text = el.get_text(strip=True)
            nums = re.findall(r"\d+", text)
            if nums:
                stats["likes"] = max(stats["likes"], int(nums[0]))

        # Discuz
        for el in soup.select(".pi_credit em, .xi2 em"):
            text = el.get_text(strip=True)
            nums = re.findall(r"\d+", text)
            if nums:
                stats["likes"] = max(stats["likes"], int(nums[0]))

        return stats

    def _extract_user_role(self, soup):
        """提取用户角色"""
        for sel in [".message-userDetails .userTitle", ".postauthorlevel", ".postlevel"]:
            el = soup.select_one(sel)
            if el:
                return el.get_text(strip=True).lower()
        return ""
