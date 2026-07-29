# 📋 海水水族智能爬虫 — 详细规划文档

## 一、信息源全景分析

### 1. 国际水族论坛（社区经验类）

| 来源 | URL | 类型 | 内容特点 | 爬取优先级 |
|------|-----|------|----------|-----------|
| **Reef2Reef** | reef2reef.com | XenForo论坛 | 全球最大珊瑚礁论坛之一，专业度高，含设备评测、鱼病诊断、珊瑚养殖 | 🔴 高 |
| **Aquarium Advice** | aquariumadvice.com | XenForo论坛 | 综合水族论坛，海水板块活跃，新手友好 | 🔴 高 |
| **Humblefish** | humble.fish | XenForo论坛 | 检疫/鱼病专家社区，Humblefish 本人是行业权威 | 🔴 高 |
| **FishLore** | fishlore.com | XenForo论坛 | 综合论坛，海水板块质量稳定 | 🟡 中 |
| **TCMAS** | tcmas.org | XenForo论坛 | 明尼苏达海水水族协会，74K+帖子 | 🟡 中 |
| **Nano-Reef** | nano-reef.com | vBulletin | 微型缸专题，SPS/LPS 精品内容 | 🟡 中 |
| **Reef Builders** | reefbuilders.com | WordPress博客 | 海水行业新闻、新品发布、珊瑚品种介绍 | 🟡 中 |
| **BRStv / Bulk Reef Supply** | brstv.com | YouTube+博客 | 设备评测、DIY教程、水质管理 | 🟢 低（视频为主） |

### 2. 国内水族论坛（中文社区类）

| 来源 | URL | 类型 | 内容特点 | 爬取优先级 |
|------|-----|------|----------|-----------|
| **CMF海水观赏鱼论坛** | cmfish.com | Discuz论坛 | 国内最大海水论坛，15年+历史，繁殖/造景/鱼病全覆盖 | 🔴 高 |
| **海水领域 SeaFishZone** | seafishzone.com | Discuz论坛 | 台湾海水社区，饲养心得/水质/饲料 | 🟡 中 |
| **AquaForum** | aquaforum.net | 论坛 | 中文水族综合论坛 | 🟡 中 |
| **百度贴吧-海水鱼吧** | tieba.baidu.com | 贴吧 | 新手提问多，混杂大量无效信息 | 🟢 低 |
| **南美水族** | southamericaaquarium.com | 论坛 | 综合水族，海水板块 | 🟢 低 |

### 3. 学术研究机构（权威知识类）

| 来源 | URL | 类型 | 内容特点 | 爬取优先级 |
|------|-----|------|----------|-----------|
| **NOAA Coral Reef Conservation** | coralreef.noaa.gov | 政府机构 | 珊瑚礁保护数据、研究白皮书、保育政策 | 🔴 高 |
| **Frontiers in Marine Science** | frontiersin.org | 开放获取期刊 | 珊瑚礁研究板块，566+篇论文，CC许可 | 🔴 高 |
| **Nature Scientific Reports** | nature.com/srep | 期刊 | 海洋生物学论文，开放获取 | 🔴 高 |
| **Springer Marine Biology** | link.springer.com | 期刊聚合 | 海洋生物学最新研究 | 🔴 高 |
| **Coral Reef Research Hub** | thecoralreefresearchhub.com | 研究社区 | Coral Matters 杂志，全球珊瑚科学社区 | 🟡 中 |
| **ResearchGate** | researchgate.net | 学术社交 | 珊瑚生物技术论文 | 🟡 中 |

### 4. 海洋生物实验室/研究所

| 机构 | 位置 | 研究方向 | 网站 |
|------|------|----------|------|
| **Hawaii Institute of Marine Biology (HIMB)** | 夏威夷 | 珊瑚礁生态、鱼类系统发育 | himb.hawaii.edu |
| **Mote Marine Laboratory** | 佛罗里达 | 珊瑚繁殖、珊瑚疾病 | motemarine.org |
| **Nova Southeastern Univ. National Coral Reef Institute** | 佛罗里达 | 珊瑚礁监测与修复 | nova.edu |
| **Australian Institute of Marine Science (AIMS)** | 澳大利亚 | 大堡礁研究 | aims.gov.au |
| **Max Planck Institute for Marine Microbiology** | 德国 | 海洋微生物、珊瑚共生 | mpi-bremen.de |
| **中国科学院南海海洋研究所** | 广州 | 南海珊瑚礁生态 | scsio.ac.cn |
| **自然资源部第三海洋研究所** | 厦门 | 海洋生物多样性 | tio.org.cn |

### 5. 珊瑚/海水知识库

| 来源 | URL | 内容 |
|------|-----|------|
| **ReefBase** | reefbase.org | 全球珊瑚礁数据（TNC维护） |
| **CORAL Magazine** | coral-magazine.com | 珊瑚杂志，品种百科 |
| **LiveAquaria** | liveaquaria.com | 物种百科（鱼/珊瑚/无脊椎） |
| **FishBase** | fishbase.org | 全球鱼类数据库 |
| **World Register of Marine Species (WoRMS)** | marinespecies.org | 海洋物种名录 |

## 二、信任度评级系统设计

### 评分维度（满分100）

#### A. 来源可信度（40分）

| 来源类型 | 基础分 | 说明 |
|----------|--------|------|
| 同行评审学术论文 | 40 | Nature/Frontiers/Springer 等 |
| 政府/研究机构报告 | 35 | NOAA/AIMS/研究所官方 |
| 专业论坛资深用户 | 25 | 积分>10K，版主，发帖>500 |
| 专业论坛普通用户 | 15 | 有一定活跃度的用户 |
| 个人博客/自媒体 | 10 | 需交叉验证 |
| 匿名帖子/贴吧 | 5 | 默认不信任，需强证据 |

#### B. 内容科学性（40分）

| 评估项 | 分值 | 评判标准 |
|--------|------|----------|
| 有数据支撑 | +15 | 包含具体参数（温度、盐度、pH等） |
| 有文献引用 | +10 | 引用学术论文或权威来源 |
| 符合生物学原理 | +10 | 不违反渗透压、氮循环、共生关系等 |
| 可复现性 | +5 | 提供具体操作步骤 |
| **扣分项** | | |
| 违反已知科学事实 | -20 | 如"盐度可以随意变化" |
| 明显商业推广 | -10 | 软文/广告性质 |
| 无来源的经验断言 | -5 | "我觉得/听说"式表达 |

#### C. 社区验证（20分）

| 指标 | 计算方式 |
|------|----------|
| 点赞/感谢数 | 高赞内容+10 |
| 回复互动量 | 多人讨论+5 |
| 被引用次数 | 被其他帖子引用+5 |
| 版主标记 | 精华帖+10 |

### 信任等级

| 等级 | 分数范围 | 标签 | 处理方式 |
|------|----------|------|----------|
| 🏆 权威 | 90-100 | `trust:authoritative` | 直接入库，标记为参考文献 |
| ✅ 可信 | 75-89 | `trust:reliable` | 入库，标记为可靠来源 |
| 📝 参考 | 60-74 | `trust:reference` | 入库，标记为参考 |
| ⚠️ 待验 | 40-59 | `trust:unverified` | 入库但标记需验证 |
| ❌ 忽略 | 0-39 | `trust:ignored` | 不入库，记录原因 |

### 生物学常识规则库（自动检测）

系统内置以下生物学规则，违反则自动扣分/忽略：

```yaml
# 水质参数规则
water_params:
  salinity:
    normal_range: [1.020, 1.028]  # 比重
    safe_range: [1.023, 1.026]
    note: "偏离安全范围需说明理由"
  temperature:
    tropical_range: [24, 28]  # 摄氏度
    critical_low: 20
    critical_high: 32
    note: "超过30°C或低于22°C需要特别说明"
  pH:
    normal_range: [8.0, 8.4]
    note: "海水pH低于7.8或高于8.5均异常"
  ammonia: {max: 0.02, unit: "ppm"}
  nitrite: {max: 0.1, unit: "ppm"}
  nitrate:
    coral_tank_max: 5
    fish_only_max: 40
    unit: "ppm"

# 生物学原理
biology_principles:
  nitrogen_cycle: "必须理解硝化循环，否则忽略相关建议"
  osmosis: "海水鱼渗透压调节原理"
  symbiosis: "珊瑚与虫黄藻共生关系"
  lighting: "PAR值与珊瑚光合需求"
  flow: "水流与营养输送/废物排除"
  
# 违反常识的典型言论（自动标记为低信任）
red_flags:
  - "加盐可以治所有病"
  - "不需要蛋白分离器"
  - "海水缸不需要光照"
  - "珊瑚不需要水流"
  - "硝化细菌不重要"
  - "水温35度没问题"
  - "自来水可以直接用"
```

## 三、爬虫技术方案

### 技术栈

```
Python 3.10+
├── httpx              # 异步HTTP客户端
├── beautifulsoup4     # HTML解析
├── readability-lxml   # 正文提取
├── trafilatura        # 网页内容提取（备用）
├── sqlite3            # 本地数据库
├── schedule           # 定时任务
├── fake-useragent     # User-Agent轮换
└── hashlib            # 内容去重
```

### 爬取策略

1. **频率控制**：每源每天最多爬取 1 次，避免被封
2. **增量爬取**：基于 URL hash + 最后修改时间去重
3. **礼貌爬取**：随机延迟 2-5 秒，遵守 robots.txt
4. **错误重试**：失败后指数退避重试 3 次
5. **代理支持**：可配置 HTTP 代理（应对地区限制）

### 数据处理管线

```
原始HTML → 正文提取 → 语言检测 → 格式清洗 → 信任评估 → 
  ↓                                        ↓
保存原始数据                          评分 ≥ 40 → 归档到 output/
                                        评分 < 40 → 记录到 ignored/
```

## 四、Agent 自主调度计划

### 每日任务（凌晨 2:00 执行）

```
1. [02:00] 启动爬虫引擎
   - 按优先级遍历 sources.json
   - 爬取未更新的内容源
   - 保存原始数据到 data/raw/

2. [02:30] 启动评估管线
   - 对新爬取内容进行信任评估
   - 应用生物学规则检查
   - 生成评估报告

3. [03:00] 格式化与归档
   - 保原文格式生成 Markdown
   - 按主题分类归档
   - 同步到 My-vault（git commit + push）

4. [03:30] 生成日报
   - 统计爬取数量、通过率
   - 高信任文章推荐
   - 异常内容告警
   - 邮件发送日报
```

### 每周任务（周日 04:00）

```
1. 全量复查：重新评估所有「待验」内容
2. 规则更新：根据新发现更新生物学规则库
3. 源管理：检查各源可达性，更新失效链接
4. 知识图谱：整理主题关联，更新索引
```

## 五、My-vault 归档结构

```
My-vault/
├── 02_收获/
│   └── 海水水族/
│       ├── README.md                    # 索引目录
│       ├── 📁 珊瑚养殖/
│       │   ├── SPS养殖指南.md
│       │   ├── LPS养殖心得.md
│       │   └── 珊瑚疾病诊断.md
│       ├── 📁 海水鱼/
│       │   ├── 小丑鱼繁殖.md
│       │   ├── 吊类饲养.md
│       │   └── 鱼病治疗.md
│       ├── 📁 水质管理/
│       │   ├── 氮循环详解.md
│       │   ├── 蛋白分离器选择.md
│       │   └── 水质参数速查.md
│       ├── 📁 设备评测/
│       │   ├── 灯具对比.md
│       │   └── 造浪泵选择.md
│       ├── 📁 学术研究/
│       │   ├── 珊瑚白化研究.md
│       │   └── 海洋酸化影响.md
│       └── 📁 造景设计/
│           ├── 造景教程.md
│           └── 缸体配置方案.md
```

## 六、文件命名规范

```
{来源}_{日期}_{标题简述}.md
例：
cmfish_20260730_海水鱼繁殖手册.md
reef2reef_20260730_coral-bleaching-recovery.md
frontiers_20260730_coral-reef-connectivity.md
```

## 七、风险与合规

1. **尊重robots.txt**：所有爬虫遵守网站爬取协议
2. **不爬取付费内容**：仅采集公开可访问内容
3. **个人信息保护**：不采集用户隐私信息
4. **内容版权**：保留原文出处，供个人学习使用
5. **频率限制**：避免对目标站点造成负担
