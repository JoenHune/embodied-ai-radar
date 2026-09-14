# Canonical arXiv字段为空研究的原文入口盘点

> **本报告只是只读入口盘点，不是已访问、已下载或已读原文的证明。** 未联网、未开发适配器、未修改canonical或硬件权威数据。URL路径和网站类型只用于安排后续验证，不能据此认定HTTP可达、开放获取、付费墙或全文完整。

## 1. 范围与独立研究分母

以 `data/catalog/works` 中 `identifiers.arxiv` 为空为口径，而不是按work ID前缀或“是否真的没有arXiv版本”判断。

| 项目 | 独立canonical work数 |
| --- | ---: |
| 全库 | 42,720 |
| canonical arXiv字段为空 | 7,602 |
| 其中已纳入 included | 1,641 |
| 待人工复核 manual_review | 4,734 |
| 候选 candidate | 1,226 |
| 已排除 excluded | 1 |
| 具有canonical DOI标识 | 6,250 |
| 具有至少一个manifestation | 7,602 |
| 具有已关联source record及至少一个记录URL | 7,602 |
| 完全没有记录URL | 0 |

本组关联8,265条manifestations、24,066个独立source record ID；已引用source record ID缺失数为0。**有URL不等于有单篇原文入口**：其中包括会议目录、DOI整卷记录、公司首页、实验室主页，甚至招聘入口。

### 必须先分出的身份映射缺口

**8项虽然canonical arXiv字段为空，但manifestation/source-record中已有arxiv.org论文URL，且aliases也有对应arXiv标识。** 其中5项manual_review、3项candidate，included为0；7项还有`official_arxiv_version_metadata`来源，另1项来自既有paper来源。

这些8项不能标成“真正非arXiv”。在已填canonical arXiv字段的研究中，本次未找到这些arXiv ID的另一个owner，但这不等于已完成去重或身份核验。建议另作有来源的字段映射复核，不在本轮自动补值。扣除这8项后，其余7,594项也只能称为“本次关联表未找到arXiv URL”，不能断言不存在arXiv版本。

## 2. 已记录入口的互斥分组

优先级为：arXiv映射候选 → 显式PDF路径 → PMLR/RSS论文页 → 出版商landing → 仅DOI → 会议目录 → 其他网站。每work只进入一行，合计严格为7,602；included合计1,641。

| 优先入口类别 | 全组 | included | 目前能说明什么 |
| --- | ---: | ---: | --- |
| 其他表已有arXiv URL，canonical字段未补 | 8 | 0 | 待身份映射复核，不是确认非arXiv |
| 已记录显式PDF入口线索 | 4 | 3 | 路径为PDF或明确PDF路由；本次未请求/验证文件 |
| 已记录PMLR/RSS单篇论文页，未优先归入上两类 | 289 | 115 | 可继续解析真实PDF/正文链接；不是已获得全文 |
| 出版商landing，未记录上述直达全文线索 | 6,138 | 1,252 | 可能开放、订阅或混合授权；付费/可读状态未知 |
| 只有DOI URL | 4 | 0 | 本轮发现均为会议整卷/会议信息记录，不能直接当独立论文全文 |
| 只有会议program入口 | 1,104 | 240 | 尚缺明确的单篇原文下载入口 |
| 其他企业、项目、实验室等网站 | 55 | 31 | 需区分技术报告原文、新闻、项目页与非研究条目 |
| 无URL | 0 | 0 | 这里只说明链接字段非空，不说明来源质量 |

4个显式PDF候选为：一份实验室托管期刊PDF、一份官方模型卡PDF、两份PMLR对应的仓库PDF。它们是**不同文档类型**，不应统一称为4篇已读论文。

采用非互斥口径，PMLR/RSS论文页涉及292个work、117个included；其中与PDF和arXiv映射候选有交叉。两个域名的 `.html` 页面首先按论文信息页处理，不假设其中已经包含整篇正文。

## 3. 域名、venue与manifestation类型

以下均按组内独立work去重。一个work可关联多个域名、venue或类型，因此**各行不可相加为总库**。

### 主要入口域名

| 域名 | work数 | included |
| --- | ---: | ---: |
| ieeexplore.ieee.org | 5,745 | 1,182 |
| ras.papercept.net | 1,473 | 297 |
| science.org | 253 | 38 |
| proceedings.mlr.press | 163 | 64 |
| journals.sagepub.com | 143 | 32 |
| roboticsproceedings.org | 129 | 53 |
| doi.org | 110 | 41 |
| roboticsconference.org | 40 | 12 |
| generalistai.com | 9 | 4 |
| arxiv.org | 8 | 0 |
| dyna.co | 8 | 6 |
| figure.ai | 4 | 4 |
| deepmind.google | 3 | 2 |
| sunday.ai | 3 | 2 |
| raw.githubusercontent.com | 2 | 2 |

其余为少量实验室、企业、项目或存储域名。`doi.org`关联110项，但**仅有DOI URL的只有4项**，其余还有其他入口，不应混报。

### Venue

| 记录venue | work数 | included |
| --- | ---: | ---: |
| ICRA | 2,788 | 565 |
| RA-L | 2,384 | 478 |
| IROS | 1,748 | 373 |
| T-RO | 303 | 63 |
| Science Robotics | 253 | 38 |
| RSS | 169 | 65 |
| CoRL | 163 | 64 |
| IJRR | 143 | 32 |
| 未记录venue | 65 | 32 |

### Manifestation类型

| kind | work数 | included |
| --- | ---: | ---: |
| conference | 4,868 | 1,067 |
| journal | 3,082 | 611 |
| technical_report | 18 | 18 |
| preprint | 17 | 2 |
| project | 16 | 6 |
| deployment | 11 | 4 |
| model | 7 | 7 |
| benchmark | 1 | 0 |
| dataset | 1 | 1 |

这些是当前catalog标签，不是本次重新判断的文档事实。存在把通用网站/招聘条目标为preprint的待复核例子，说明抓取队列必须先做单篇来源身份检查。

## 4. 关键缺口与可信度边界

1. **6,250项带`publisher_url_from_registered_doi`状态，其中1,293项included。** 这是既有采集器的DOI派生入口状态，不是已请求出版商页面。`scripts/collect_publications.py`的`publisher_url`明确从DOI构造landing；IEEE分支使用DOI末尾7–9位数字拼成document URL。不能先假设这些数字必然是正确Xplore文档号，应先解析真实DOI落点并核题名/作者/版本。本轮未据此判定任何具体URL已经错误。
2. **不能把6,138个出版商landing记成已确认付费。** 本轮没有联网，关联source-record中也没有足以给整组判定正文开放获取/付费状态的规范字段。元数据检索时间与元数据许可都不是全文访问成功或正文授权的证明。
3. **会议目录不是论文正文。** 1,513项关联PaperCept/RSS program域名，其中1,104项只有这类入口。后续须发现单篇论文页/出版记录，不能把program HTML本身送进“论文已读”流程。
4. **没有完全空URL，不代表没有原文缺口。** 55项其他网站中既有有价值的一手公司报告，也有主页、新闻、招聘/活动入口；应保留文档种类和身份待核状态。
5. **source-record可含元数据、节选或摘要。** 本轮只按显式关联关系收集其URL；未把`retrieved_at`、已有哈希、元数据缓存或短节选转成整篇阅读证明，也未扫描链接目标内容。

## 5. 最优下一适配器建议

**优先做一个“开放会议proceedings论文页 → 实际原文链接”的只读适配器，先覆盖PMLR与RSS两种页面配置。** 这是基于现有目录的工程优先级建议，不是本轮可达性实测：已有292个候选work、117个included，来源较集中，且290项研究带`peer_reviewed_official_proceedings`标签。适配器应从真实页面提取PDF链接和文章元数据，不靠改URL后缀猜下载地址；之后独立验证响应、来源身份、版本、哈希、提取完整性，再交给阅读者。

实施前先将8项arXiv映射候选单列复核；4个显式PDF候选可作为少量验证样本。上述集合有交叉，不能相加当新增覆盖数。

第二优先才是规模更大的**DOI-first公开原文定位器**：对出版商landing先验证DOI解析结果，再发现有明确公开访问证据的HTML/PDF或作者存档。记录OA/授权未知、无公开原文、受限、下载失败等不同状态，不绕付费或403/429。不要直接批量抓取由DOI后缀拼出的IEEE文档路径。

本轮不实现任何适配器，也不估计成功抓取率或可读全文总量。

## 6. 十个实际ID与已记录URL样例

以下恰为10个样例；链接均来自现有表，本轮未访问。

| 类别 | canonical work ID | 已记录URL |
| --- | --- | --- |
| arXiv映射缺口 | `doi:10.1177/02783649261470035` | [现有arXiv入口](https://arxiv.org/abs/2609.10400) |
| arXiv映射缺口：KOROL | `title:cc21f10a81fc21f1083979a2` | [现有arXiv入口](https://arxiv.org/abs/2407.00548) |
| 实验室PDF候选 | `doi:10.1126/scirobotics.adr5247` | [已记录PDF路径](https://autolab.berkeley.edu/assets/publications/media/Augmented-Dexterity-Science-Robotics-Oct-2024.pdf) |
| 模型卡PDF候选，不等同论文 | `official:gemini-robotics-er-2` | [已记录模型卡路径](https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-Robotics-ER-2-Model-Card.pdf) |
| PMLR论文页 | `title:741f07581b788c6b63893de1` | [已记录论文页](https://proceedings.mlr.press/v305/schwarke25a.html) |
| RSS论文页 | `doi:10.15607/rss.2024.xx.001` | [已记录论文页](https://www.roboticsproceedings.org/rss20/p001.html) |
| IEEE派生landing | `doi:10.1109/icra55743.2025.11127227` | [已记录出版商路径](https://ieeexplore.ieee.org/document/11127227) |
| 仅DOI，会议整卷记录 | `doi:10.1109/iros60139.2025` | [已记录DOI入口](https://doi.org/10.1109/iros60139.2025) |
| 仅会议program | `title:0101f7c14c4558a2635959eb` | [已记录目录定位](https://ras.papercept.net/conferences/conferences/ICRA26/program/ICRA26_ContentListWeb_3.html#tuat3_09) |
| 非论文入口待复核：招聘 | `artifact:00919efcbdc467896873` | [已记录招聘入口](https://jobs.ashbyhq.com/1x/b72d011c-6a38-48f7-ada7-1f7ce76e66bf) |

## 7. 可复算口径与数据快照

- 输入：`data/catalog/works/*.jsonl`、`manifestations.jsonl`、`source-records.jsonl`；按work ID连接manifestations，再经work/source_record_ids及manifestation/source_record_id关联来源URL。
- 同一work的同一URL只保留一次；域名、venue、类型统计以work集合去重；第二节另按公开说明的优先级生成互斥分组。
- “显式PDF”仅指记录URL的`.pdf`或明确PDF路由线索；“proceedings论文页”仅指PMLR/RSS已记录页面。没有执行网络请求、文件格式检测或全文提取。
- arXiv映射候选必须在已关联表中实际出现可解析arXiv URL；不把catalog字段空值等同于真实不存在。
- 本轮网络请求数：**0**。本轮新增原文阅读数：**0**。权威数据改动：**0**。
- 数据截至：2026-09-14；catalog ingested_at：2026-09-14T04:21:49Z。
- catalog_hash：`f3ee0fa0985b867201d5525845ad38f2fbb64d64ee886a5b9161b00ff96fc5e8`。
- works表hash：`75e869cb5cde18f430b61ec964362f81892c13e84259847d0ed8432dd08cefb2`。
- manifestations表hash：`5d1359200aa218d47084d65d597b4d9de82a81364a14ba79afa6f95b22c14016`。
- source-records表hash：`14c46329667c15caceb33cfb7aa28b417b4cc0b5cd4fe691fbaade62a39f3656`。

**结论：缺口不是“7,602项完全没有链接”，而是身份字段、原始文档定位与访问/阅读证明之间尚未闭合。当前任何入口数量都不应转成全文已读覆盖率。**
