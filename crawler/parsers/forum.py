"""论坛解析器 - 支持 XenForo / Discuz / Flarum

增强功能：
- 优先抓取置顶帖/精华帖
- 标题关键词预过滤（优先知识类帖子）
- 识别帖子类型（教程/讨论/求助/晒帖）
"""
import re
from datetime import datetime
from bs4 import BeautifulSoup

from readability import Document
import trafilatura


# 知识类标题关键词（优先抓取）
KNOWLEDGE_TITLE_PATTERNS = [
    r"(?:tutorial|guide|how[\s-]to|complete\s+guide|beginner|walkthrough)",
    r"(?:教程|指南|手把手|入门|进阶|保姆级|详解|全面)",
    r"(?:study|research|experiment|analysis|data|results|findings)",
    r"(?:研究|实验|数据|分析|测试|验证|实测)",
    r"(?:species\s+profile|care\s+sheet|husbandry|requirement)",
    r"(?:物种|养护|参数|百科|评测|对比|推荐)",
    r"(?:step[\s-]by[\s-]step|detailed|comprehensive|in[\s-]depth)",
    r"(?:设备|器材|蛋白分离器|造浪|灯光|LED|PAR)",
]

# 低价值标题关键词（降优先级或跳过）
LOW_VALUE_TITLE_PATTERNS = [
    r"(?:help|emergency|urgent|sick|dying|died|dead|problem|issue|trouble)",
    r"(?:求助|急|病|死|挂了|出问题|怎么办|怎么回事)",
    r"(?:show\s+off|look\s+at|check\s+out|my\s+tank|my\s+reef|progress)",
    r"(?:晒缸|上图|我的缸|我的 reef|进展|Day\s+\d+|Week\s+\d+)",
    r"(?:new\s+to|first\s+reef|just\s+started|just\s+bought|newbie)",
    r"(?:新手|刚入|刚开|第一次|小白)",
    r"(?:recommend|suggestion|what\s+should|best\s+for|which\s+one)",
    r"(?:推荐|建议|选哪个|用什么|哪个好)",
]


class ForumParser:
    def extract_article_links(self, html, base_url):
        """从论坛列表页提取文章链接，优先置顶帖和知识类帖子"""
        soup = BeautifulSoup(html, "lxml")
        pinned_links = []    # 置顶/精华帖
        knowledge_links = []  # 标题含知识关键词
        normal_links = []     # 普通帖子

        # XenForo pattern
        for item in soup.select(".structItem, .structItem--thread"):
            a = item.select_one(".structItem-title a[href]")
            if not a:
                continue
            href = a.get("href", "")
            if not href or ("/threads/" not in href and "/topic/" not in href):
                continue
            if not href.startswith("http"):
                href = base_url.rstrip("/") + "/" + href.lstrip("/")

            title_text = a.get_text(strip=True).lower()
            is_pinned = bool(item.select_one(".structItem-status--sticky, .structItem-status--iconic"))
            is_prefix = bool(item.select_one(".label--accent, .label--success, .label--primary"))

            # 根据标题和状态分类
            if is_pinned or is_prefix:
                pinned_links.append(href)
            elif any(re.search(p, title_text, re.IGNORECASE) for p in KNOWLEDGE_TITLE_PATTERNS):
                knowledge_links.append(href)
            elif any(re.search(p, title_text, re.IGNORECASE) for p in LOW_VALUE_TITLE_PATTERNS):
                continue  # 跳过低价值帖子
            else:
                normal_links.append(href)

        # Discuz pattern
        for item in soup.select("tbody[id^='normalthread_'], li.pbw"):
            a = item.select_one("a[href*='thread-'], a[href*='tid=']")
            if not a:
                continue
            href = a["href"]
            if not href.startswith("http"):
                href = base_url.rstrip("/") + "/" + href.lstrip("/")
            if "redirect" in href:
                continue

            title_text = a.get_text(strip=True).lower()
            # Discuz 置顶帖通常在 table 有特殊 class
            is_sticky = bool(item.select_one(".stick, .colorboard, .xi2"))

            if is_sticky:
                pinned_links.append(href)
            elif any(re.search(p, title_text, re.IGNORECASE) for p in KNOWLEDGE_TITLE_PATTERNS):
                knowledge_links.append(href)
            elif any(re.search(p, title_text, re.IGNORECASE) for p in LOW_VALUE_TITLE_PATTERNS):
                continue
            else:
                normal_links.append(href)

        # Generic fallback
        if not pinned_links and not knowledge_links and not normal_links:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if any(p in href for p in ["thread-", "tid="]):
                    if not href.startswith("http"):
                        href = base_url.rstrip("/") + "/" + href.lstrip("/")
                    if "redirect" not in href:
                        normal_links.append(href)

        # 合并：置顶帖 + 知识帖 + 普通帖（限制数量）
        result = pinned_links + knowledge_links + normal_links
        return result[:50]  # 最多50个链接

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

        # 检测是否为置顶帖/精华帖
        is_pinned = self._is_pinned_post(soup)

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
            "is_pinned": is_pinned,
            "crawled_at": datetime.now().isoformat(),
        }

    def _is_pinned_post(self, soup):
        """检测是否为置顶帖/精华帖"""
        selectors = [
            ".structItem-status--sticky",
            ".structItem-status--iconic",
            ".label--accent",
            ".label--success",
            ".stick",
            ".colorboard",
            ".thread-status-sticky",
        ]
        for sel in selectors:
            if soup.select_one(sel):
                return True
        return False

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
