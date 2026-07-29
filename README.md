# 🐠 Marine Aquarium Intelligent Crawler

海水水族智能爬虫 — 自动化采集、评估、归档国内外海水水族知识

## 项目概述

这是一个**长期运行的智能爬虫系统**，由 AI Agent 自主调度，定期爬取国内外海水水族论坛、研究机构、实验室的文章，经过信任度评估、格式整理后归档到知识库。

### 核心特性

- 🔍 **多源采集**：国内外 20+ 海水水族信息源
- 🧠 **智能信任评估**：基于科学原理的内容评级系统
- 📝 **原文保真**：保持原文语言和格式排版
- 🤖 **自主运行**：Agent 定时调度，无需人工干预
- 📚 **知识归档**：自动整理到 My-vault 知识库

## 架构设计

```
marine-aquarium-crawler/
├── config/
│   ├── sources.json          # 信息源注册表
│   └── trust_rules.json      # 信任度评估规则
├── crawler/
│   ├── __init__.py
│   ├── engine.py             # 爬虫引擎（调度+采集）
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── forum.py          # 论坛解析器（Discuz/XenForo/Flarum）
│   │   ├── blog.py           # 博客/文章解析器
│   │   ├── academic.py       # 学术论文解析器
│   │   └── news.py           # 新闻/资讯解析器
│   └── pipeline.py           # 数据处理管线
├── trust/
│   ├── __init__.py
│   ├── evaluator.py          # 信任度评估引擎
│   ├── biology_rules.py      # 生物学知识规则库
│   └── credibility.py        # 来源可信度评分
├── storage/
│   ├── __init__.py
│   ├── sqlite_store.py       # SQLite 本地存储
│   └── git_sync.py           # Git 同步到 My-vault
├── agent/
│   ├── __init__.py
│   ├── scheduler.py          # Agent 调度器
│   └── processor.py          # Agent 内容处理器
├── output/                   # 处理后的文章输出
├── data/                     # 爬取的原始数据 + 数据库
├── logs/                     # 运行日志
├── main.py                   # 主入口
├── requirements.txt
└── PLAN.md                   # 详细规划文档
```

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 首次运行（全量爬取）
python main.py --mode full

# 增量爬取（日常运行）
python main.py --mode incremental

# 仅评估信任度
python main.py --mode evaluate --input data/raw/

# 同步到 My-vault
python main.py --mode sync
```

## 信息源

详见 `config/sources.json`，覆盖：

| 类别 | 来源数 | 代表 |
|------|--------|------|
| 国际论坛 | 6+ | Reef2Reef, Aquarium Advice, Humblefish |
| 国内论坛 | 4+ | CMF海水观赏鱼论坛, AquaForum, 海水领域 |
| 学术期刊 | 4+ | Frontiers, Nature, Springer |
| 研究机构 | 5+ | NOAA, HIMB, Mote Marine Lab |
| 知识库 | 2+ | ReefBase, Coral Reef Hub |

## 信任度系统

详见 `trust/` 目录，5级评分：

| 等级 | 分数 | 描述 |
|------|------|------|
| ⭐⭐⭐⭐⭐ | 90-100 | 权威科研机构论文 |
| ⭐⭐⭐⭐ | 75-89 | 专业论坛资深用户/有引用 |
| ⭐⭐⭐ | 60-74 | 有经验的爱好者分享 |
| ⭐⭐ | 40-59 | 普通经验帖，需交叉验证 |
| ⭐ | 0-39 | 存疑/违反生物学常识，忽略 |

## License

Private - 仅限个人使用
