"""内容分类器 - 区分知识内容与闲聊讨论

分类目标：
- knowledge: 教程、指南、操作步骤
- scientific: 科普、原理解释、学术内容
- experimental: 实验论证、数据分析、对比测试
- reference: 物种百科、参数手册、设备评测
- discussion: 日常讨论、求助、晒帖（应过滤）
- noise: 纯闲聊、水帖（应过滤）
"""
import re
import logging

logger = logging.getLogger(__name__)


class ContentClassifier:
    """基于关键词 + 结构特征的内容分类器"""

    # 知识类关键词模式（中英文）
    KNOWLEDGE_KEYWORDS = {
        "tutorial": {
            "en": [
                r"\bhow\s+to\b", r"\bguide\b", r"\btutorial\b", r"\bstep[\s-]by[\s-]step\b",
                r"\bwalkthrough\b", r"\binstructions?\b", r"\bsetup\s+guide\b",
                r"\bbeginner'?s?\s+guide\b", r"\bhow\s+do\s+(?:I|you|we)\b",
                r"\blearn\s+how\b", r"\bmastering\b", r"\bcomplete\s+guide\b",
                r"\bhow[\s-]to[\s-]guide\b",
            ],
            "zh": [
                r"教程", r"指南", r"手把手", r"步骤", r"操作方法", r"怎么[做养设]",
                r"如何[做养设]", r"入门", r"新手[指教]", r"进阶", r"实战",
                r"一?步?步?教你", r"详细[教说]明", r"保姆级",
            ],
        },
        "scientific": {
            "en": [
                r"\bstudy\b", r"\bresearch\b", r"\bscientific\b", r"\bfindings?\b",
                r"\bpaper\b", r"\bjournal\b", r"\bdoi\b", r"\bpeer[\s-]reviewed\b",
                r"\bhypothesis\b", r"\bexperiment(?:al)?\b", r"\bobservation\b",
                r"\bdata\s+shows?\b", r"\bevidence\b", r"\bmechanism\b",
                r"\bphotosynthes\w+\b", r"\bzooxanthellae\b", r"\bsymbios\w+\b",
                r"\bnitrogen\s+cycle\b", r"\bbiological\b", r"\bphysiology\b",
                r"\becology\b", r"\becosystem\b",
            ],
            "zh": [
                r"研究", r"科学", r"论文", r"实验", r"数据", r"原理", r"机制",
                r"生物[学系]", r"生态", r"共生", r"光合", r"虫黄藻",
                r"硝化[系反]", r"氮循环", r"学术", r"期刊", r"DOI",
            ],
        },
        "experimental": {
            "en": [
                r"\btest(?:ed|ing)?\s+(?:result|show|confirm|demonstrate)\b",
                r"\bcompared?\s+to\b", r"\bexperiment(?:al)?\s+(?:setup|result|data)\b",
                r"\bmonths?\s+(?:of\s+)?(?:testing|observation|monitoring)\b",
                r"\bbefore\s+and\s+after\b", r"\bdata\s+(?:shows?|suggests?|indicates?)\b",
                r"\b(?:controlled|systematic)\s+(?:experiment|test|study)\b",
                r"\bresults?\s+(?:show|suggest|indicate|demonstrate)\b",
                r"\bquantitative\b", r"\bmeasurement\b", r"\bparameter\b",
                r"\bpar\s+meter\b", r"\bspectr(?:um|al)\b",
            ],
            "zh": [
                r"测试[结结]", r"实验[数证]", r"对比[实测]", r"前后对比",
                r"实测[数证]", r"验证", r"数据[显证]", r"监测",
                r"量化", r"测量", r"参数", r"光谱", r"PAR",
            ],
        },
        "reference": {
            "en": [
                r"\bspecies\s+profile\b", r"\bcare\s+sheet\b", r"\bspecies\s+guide\b",
                r"\bhusbandry\b", r"\bwater\s+parameter\b", r"\brequirement\b",
                r"\bcompatibility\b", r"\breef[\s-]safe\b", r"\bprofile\b",
                r"\bequipment\s+review\b", r"\bproduct\s+review\b",
                r"\bcomparison\b", r"\branking\b", r"\btop\s+\d+\b",
            ],
            "zh": [
                r"物种", r"鱼种", r"珊瑚种", r"养护", r"参数",
                r"兼容性", r"混养", r"设备[评测]", r"产品[评测]",
                r"推荐", r"对比", r"排行榜", r"百科",
            ],
        },
    }

    # 讨论/闲聊关键词模式
    DISCUSSION_KEYWORDS = {
        "en": [
            r"\bhelp\b.*\b(?:my|please|urgent|emergency)\b",
            r"\bwhat\s+do\s+(?:you|everyone|guys)\s+think\b",
            r"\blook\s+at\s+(?:my|this)\b",
            r"\bcheck\s+out\s+my\b", r"\bmy\s+(?:new|first|latest)\s+tank\b",
            r"\bany\s+suggestions?\b", r"\brecommend\b.*\bfor\s+my\b",
            r"\bwhat\s+should\s+I\b", r"\bcan\s+someone\s+help\b",
            r"\bID\s+(?:this|help)\b", r"\bwhat\s+is\s+this\b",
            r"\bnew\s+(?:to|bie)\b", r"\bfirst\s+reef\b",
            r"\bjust\s+(?:started|bought|added|got)\b",
            r"\bfinally\b", r"\bupgrade\b.*\b(?:my|tank)\b",
            r"\bshow\s+off\b", r"\bprogress\s+(?:update|shot|pic)\b",
            r"\bweek\s+\d+\b", r"\bmonth\s+\d+\b",
        ],
        "zh": [
            r"帮[忙看]", r"求助", r"急", r"怎么办", r"怎么回事",
            r"大家[看评]", r"求[推鉴]", r"有[没人谁].*推荐",
            r"新[手入]", r"刚[入开]", r"我的[缸鱼]",
            r"晒[缸鱼照]", r"上[图照]", r"进展", r"第\d+天",
            r"终于", r"升级", r"换[缸设]", r"开缸日记",
        ],
    }

    # 结构特征模式（知识内容通常有这些结构）
    STRUCTURAL_SIGNALS = {
        "has_list": r"(?:^|\n)\s*[\d\*\-•]\s*[\.\)]\s*\S",  # 有序/无序列表
        "has_numbered_steps": r"(?:^|\n)\s*(?:1|第一|首先|step\s*1)[\.\)：:]\s*\S",
        "has_headers": r"(?:^|\n)#{1,3}\s+\S|(?:(?:^|\n)[A-Z][^\n]{3,}\n[=\-]{3,})",
        "has_parameters": r"\d+\.?\d*\s*(?:ppm|dkh|°[cC]|mg[/l]|par|sg\s*1\.\d+|l/s)",
        "has_citations": r"(?:\[|\().*(?:et\s+al|doi|journal|research|\d{4})(?:\]|\))",
        "long_paragraphs": None,  # 通过长度判断
    }

    # 短内容阈值（低于此字数更可能是闲聊）
    MIN_CONTENT_LENGTH = 150
    # 知识内容理想长度
    IDEAL_CONTENT_LENGTH = 600

    def classify(self, article):
        """对文章进行分类，返回 (content_type, confidence, reasons)

        content_type: tutorial / scientific / experimental / reference / discussion / noise
        confidence: 0.0 - 1.0
        reasons: 分类依据列表
        """
        title = article.get("title", "").lower()
        content = article.get("content", "")
        content_lower = content.lower()
        combined = title + " " + content_lower

        reasons = []

        # 1. 计算知识类得分
        knowledge_scores = {}
        for ktype, lang_patterns in self.KNOWLEDGE_KEYWORDS.items():
            score = 0
            for lang, patterns in lang_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, combined, re.IGNORECASE)
                    # 标题匹配权重更高
                    title_matches = re.findall(pattern, title, re.IGNORECASE)
                    score += len(matches) + len(title_matches) * 2
            knowledge_scores[ktype] = score

        # 2. 计算讨论类得分
        discussion_score = 0
        for lang, patterns in self.DISCUSSION_KEYWORDS.items():
            for pattern in patterns:
                matches = re.findall(pattern, combined, re.IGNORECASE)
                discussion_score += len(matches)

        # 3. 结构特征得分
        structure_score = 0
        for feature, pattern in self.STRUCTURAL_SIGNALS.items():
            if pattern and re.search(pattern, content):
                structure_score += 2
        if len(content) > self.IDEAL_CONTENT_LENGTH:
            structure_score += 3

        # 4. 综合判断
        total_knowledge = sum(knowledge_scores.values())
        max_knowledge_type = max(knowledge_scores, key=knowledge_scores.get) if knowledge_scores else "noise"

        # 长度惩罚：太短的内容大概率是闲聊，但有强知识信号时不惩罚
        length_penalty = 0
        if total_knowledge < 3:  # 知识信号弱时，短内容惩罚重
            if len(content) < 100:
                length_penalty = -20
            elif len(content) < self.MIN_CONTENT_LENGTH:
                length_penalty = -10
        else:  # 知识信号强时，容忍短内容
            if len(content) < 50:
                length_penalty = -5

        # 最终得分
        knowledge_final = total_knowledge + structure_score + length_penalty
        discussion_final = discussion_score

        # 判断类型
        if knowledge_final <= 0 and discussion_final <= 0 and len(content) < 200:
            content_type = "noise"
            confidence = 0.9
            reasons.append("内容过短且无知识信号")
        elif discussion_final > knowledge_final and discussion_final >= 3:
            content_type = "discussion"
            confidence = min(0.9, 0.5 + discussion_final * 0.1)
            reasons.append(f"讨论信号({discussion_final}) > 知识信号({knowledge_final})")
        elif knowledge_final > 0 and knowledge_final >= discussion_final:
            content_type = max_knowledge_type if knowledge_scores.get(max_knowledge_type, 0) > 0 else "reference"
            confidence = min(0.95, 0.4 + knowledge_final * 0.05)
            reasons.append(f"知识信号({knowledge_final})主导，类型={content_type}")
        elif total_knowledge > 0 and structure_score > 3:
            content_type = max_knowledge_type
            confidence = 0.6
            reasons.append(f"结构特征+知识信号")
        else:
            content_type = "discussion"
            confidence = 0.5
            reasons.append(f"信号不足，默认归为讨论")

        return {
            "content_type": content_type,
            "confidence": confidence,
            "reasons": reasons,
            "knowledge_scores": knowledge_scores,
            "discussion_score": discussion_score,
            "structure_score": structure_score,
        }

    def is_knowledge_content(self, article, min_confidence=0.4):
        """快速判断是否为知识内容（用于爬取时过滤）"""
        result = self.classify(article)
        return result["content_type"] not in ("discussion", "noise"), result

    def should_keep(self, article):
        """决定是否保留文章（用于存储前过滤）"""
        result = self.classify(article)
        ctype = result["content_type"]
        conf = result["confidence"]

        # 学术/机构来源自动保留
        category = article.get("category", "")
        if category in ("academic_journal", "research_institution", "knowledge_base"):
            return True, result

        # 知识内容 + 足够置信度 → 保留
        if ctype in ("tutorial", "scientific", "experimental", "reference"):
            if conf >= 0.4:
                return True, result

        # 高置信度讨论 → 保留（可能是有价值的讨论）
        if ctype == "discussion" and conf >= 0.7 and len(article.get("content", "")) > 1000:
            return True, result

        return False, result


# 全局实例
_classifier = None

def get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = ContentClassifier()
    return _classifier
