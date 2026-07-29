"""信任度评估引擎"""
import json
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class TrustEvaluator:
    def __init__(self):
        self.rules = self._load_rules()

    def _load_rules(self):
        rules_path = Path(__file__).parent.parent / "config" / "trust_rules.json"
        with open(rules_path) as f:
            return json.load(f)

    def evaluate(self, article):
        """评估单篇文章的信任度，返回 (score, level, reasons)"""
        score = 0
        reasons = []

        # === A. 来源可信度 (max 40) ===
        source_score = self._score_source(article)
        score += source_score
        reasons.append(f"来源: +{source_score}")

        # === B. 内容科学性 (max 40) ===
        content_score, content_reasons = self._score_content(article)
        score += content_score
        reasons.extend(content_reasons)

        # === C. 社区验证 (max 20) ===
        community_score = self._score_community(article)
        score += community_score
        reasons.append(f"社区: +{community_score}")

        # 检查红线（违反生物学常识）
        red_flag_penalty = self._check_red_flags(article)
        if red_flag_penalty:
            score += red_flag_penalty
            reasons.append(f"⚠️ 红线: {red_flag_penalty}")

        # 限制分数范围
        score = max(0, min(100, score))

        # 确定信任等级
        level = self._get_trust_level(score)

        return {
            "score": score,
            "level": level,
            "reasons": reasons,
            "source_score": source_score,
            "content_score": content_score,
            "community_score": community_score,
        }

    def _score_source(self, article):
        """来源可信度评分"""
        category = article.get("category", "")
        base = article.get("base_trust_score", 10)

        # 学术/机构类自动高分
        if category in ("academic_journal", "research_institution"):
            return min(40, base)

        # 论坛类看用户角色
        user_role = article.get("user_role", "")
        if any(kw in user_role for kw in ["版主", "moderator", "admin", "senior", "expert"]):
            return min(35, base + 10)
        elif any(kw in user_role for kw in ["member", "regular"]):
            return min(25, base + 5)

        return min(20, base)

    def _score_content(self, article):
        """内容科学性评分"""
        score = 0
        reasons = []
        content = article.get("content", "").lower()

        # 正面信号
        # 有数据支撑（包含数字+单位）
        if re.search(r"\d+\.?\d*\s*(ppm|dkh|°[cC]|mg/l|par|sg\s*1\.\d+)", content):
            score += 15
            reasons.append("数据支撑: +15")

        # 有文献引用
        if re.search(r"(研究|study|paper|journal|doi|reference|引用|论文)", content):
            score += 10
            reasons.append("文献引用: +10")

        # 符合生物学原理
        bio_score = self._check_biology_match(content)
        score += bio_score
        if bio_score > 0:
            reasons.append(f"生物学匹配: +{bio_score}")

        # 有操作步骤
        if re.search(r"(步骤|step|方法|method|how to|how do|教程|guide)", content):
            score += 5
            reasons.append("可操作性: +5")

        # 负面信号
        if re.search(r"(广告|推广|优惠|折扣|购买链接|affiliate|shop now)", content):
            score -= 10
            reasons.append("商业推广: -10")

        if re.search(r"(我觉得|我认为|听说|maybe|I think|probably|可能|大概)", content[:200]):
            score -= 5
            reasons.append("无来源断言: -5")

        return max(0, min(40, score)), reasons

    def _score_community(self, article):
        """社区验证评分"""
        score = 0
        stats = article.get("stats", {})

        likes = stats.get("likes", 0)
        if likes >= 50:
            score += 10
        elif likes >= 20:
            score += 7
        elif likes >= 5:
            score += 3

        return min(20, score)

    def _check_biology_match(self, content):
        """检查内容是否符合生物学原理"""
        score = 0
        rules = self.rules.get("biology_rules", {})
        params = rules.get("water_params", {})

        # 检查是否提到合理的水质参数
        sg_match = re.search(r"1\.0[12]\d", content)
        if sg_match:
            sg_val = float(sg_match.group())
            if 1.020 <= sg_val <= 1.028:
                score += 3  # 合理的盐度范围

        temp_match = re.search(r"(\d{2})\s*°?\s*[cC]", content)
        if temp_match:
            temp_val = int(temp_match.group(1))
            if 24 <= temp_val <= 28:
                score += 3  # 合理的温度
            elif 20 <= temp_val <= 32:
                score += 1  # 边缘温度

        ph_match = re.search(r"ph\s*[=:]\s*(\d\.\d)", content, re.IGNORECASE)
        if ph_match:
            ph_val = float(ph_match.group(1))
            if 8.0 <= ph_val <= 8.4:
                score += 3  # 合理的pH

        return min(10, score)

    def _check_red_flags(self, article):
        """检查红线言论"""
        content = article.get("content", "")
        red_flags = self.rules.get("biology_rules", {}).get("red_flags", [])

        penalty = 0
        for flag in red_flags:
            if flag in content:
                penalty -= 15
                logger.warning(f"Red flag detected in {article.get('url', '')}: {flag}")

        return penalty

    def _get_trust_level(self, score):
        """根据分数确定信任等级"""
        levels = self.rules["scoring"]["trust_levels"]
        for level in levels:
            if score >= level["min_score"]:
                return level
        return levels[-1]

    def evaluate_directory(self, input_dir):
        """评估目录中的所有文章"""
        from storage.sqlite_store import SQLiteStore
        store = SQLiteStore("data/crawler.db")

        articles = store.get_unevaluated_articles()
        logger.info(f"Evaluating {len(articles)} articles")

        for article_data in articles:
            article = json.loads(article_data["data_json"])
            result = self.evaluate(article)
            store.save_evaluation(article_data["content_hash"], result)

        logger.info("Evaluation complete")
