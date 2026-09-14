# 八月公司缓存的公开哈希与历史正文可恢复性

核查日期：2026-09-06。范围：DYNA、Generalist、Figure，另核对同批PI缓存；只读分析后保存本报告，没有新增文本snapshot/schema、修改日期或写入authority。

## 结论

11份 `*-2026-08-26.html` 的原始响应体SHA-256，全部与公开提交 `7ed6bedcd6bcdf8730e8012e28dcb81994176773` 中对应 `source_id` 的 `content_hash` 完全相同。不是根据文件名或mtime判定。

**GEN-1.5已有可恢复的历史正文级文本**：它藏在Generalist研究索引的 `data-search` 属性，不在可见卡片中，也不是script节点。可以恢复当时已公布的实验数字与限制。**本批Dyna-2、Dyna客户部署及Figure INDEX没有找到完整报告正文**，只能恢复主页/索引中实际存在的宣告或简介。

## 时间证据链

1. [公开提交中的原始状态文件](https://github.com/JoenHune/embodied-ai-radar/blob/7ed6bedcd6bcdf8730e8012e28dcb81994176773/data/group-source-status.json)固定了source ID、官方URL与内容哈希；共有150个来源状态。
2. 本地 `git show` 返回该提交的author/committer时间均为2026-08-27T01:20:26+08:00，即2026-08-26 17:20:26 UTC。Git自报时间本身不单独充当可信公布时间。
3. 主流程随后直接查询[GitHub部署记录](https://github.com/JoenHune/embodied-ai-radar/actions/runs/32994514392)：对应head SHA一致，build与deploy均成功。任务创建于2026-08-26T17:30:09Z，deploy完成于**2026-08-26T17:31:56Z**；创建时间不冒充部署完成时间。逐字段结果保存于同目录 `august-cache-deployment-proof.json`。
4. 状态文件自报 `last_checked/last_success=2026-08-26T14:29:04.760164+00:00`。该时间可保留为采集记录，但保守内容存在上界采用已核验部署完成时间：**2026-08-26T17:31:56Z（北京时间8月27日01:31:56）**。正式snapshot应同时引用run、提交中的原始状态文件和相同缓存哈希，不把这个时间提前到报告页标注日期。

`git show <commit>:data/group-source-status.json` 的原始字节SHA-256为：
`f928256bed8469fa24648ab28d1c713d5adb67fd0901dc28a89aa7ed53abaf70`。

以上建立的是“这些完全相同的缓存字节不晚于公开哈希时间已经存在”的可审计链。没有证明每个正文句段最初何时写成，也不自动提供作者实验真伪或外部复现证据。

## 逐文件映射与精确哈希

下表所有行的缓存SHA均等于旧提交登记值；路径位于 `data/raw/organizations/`，被Git忽略并不削弱已公开哈希的对账意义，但缓存本身仍须保留以便重算。

| 本地缓存 | 官方URL | 字节数 | 匹配SHA-256 | 内容层级 |
| --- | --- | ---: | --- | --- |
| [28863a8431f1](</Users/joen/Projects/基金战略/papers/arXiv/data/raw/organizations/dyna-robotics/28863a8431f1-2026-08-26.html>) | [/research](https://www.dyna.co/research) | 160215 | `c26bb55594ed7ecf59ca01344ea4d4ee9d882b6224f9f4cef531ad2018373154` | 研究索引；Dyna-2/基础设施标题、直链及08.15/08.17标签 |
| [635d4673ef05](</Users/joen/Projects/基金战略/papers/arXiv/data/raw/organizations/dyna-robotics/635d4673ef05-2026-08-26.html>) | [/news](https://www.dyna.co/news) | 140984 | `b6d1a3ddc3593be7fafdb7fc81f3ce581b982d4dfbc54975142c467f307787d9` | 新闻索引；同上，不含完整实验 |
| [6fd37836085e](</Users/joen/Projects/基金战略/papers/arXiv/data/raw/organizations/dyna-robotics/6fd37836085e-2026-08-26.html>) | [/company](https://www.dyna.co/company) | 171033 | `c576132574f49aac44dd15f0454ebc5b0f73a270f96a68bbadb6a0edfb3f2531` | 公司介绍＋报告卡片；不是报告正文 |
| [7eb4d4a58ff7](</Users/joen/Projects/基金战略/papers/arXiv/data/raw/organizations/dyna-robotics/7eb4d4a58ff7-2026-08-26.html>) | [/](https://www.dyna.co/) | 167382 | `44d3eaf2878c383dcb2c66bb41c18b2266f497e9d037392f958e66e27c1b694e` | 主页简介；百万小时人类视频说法，不含14任务结果 |
| [198d445139e8](</Users/joen/Projects/基金战略/papers/arXiv/data/raw/organizations/generalist-ai/198d445139e8-2026-08-26.html>) | [/blog/research](https://generalistai.com/blog/research) | 112474 | `6c49daf1cea8d5927ff89fd8be8ee4df281f99830e13ceaae6f20e8c1183f35d` | 研究索引＋GEN-1.5 data-search内嵌正文级文本 |
| [27fa60f6f2e2](</Users/joen/Projects/基金战略/papers/arXiv/data/raw/organizations/generalist-ai/27fa60f6f2e2-2026-08-26.html>) | [/](https://generalistai.com/) | 45175 | `5890f7167608d8b2980d25abc1af79ea7cc62c072d3defc9717ef3ebca67f6d1` | 主页卡片；12秒/1–10梯度步简介 |
| [88248d3e2c79](</Users/joen/Projects/基金战略/papers/arXiv/data/raw/organizations/generalist-ai/88248d3e2c79-2026-08-26.html>) | [/about](https://generalistai.com/about) | 24539 | `d2e03b7a4dcbcd3990f412aabcfb4f7903c08944d718860bb125d813443fed41` | About/团队介绍；非GEN-1.5正文 |
| [48e4987cfc1e](</Users/joen/Projects/基金战略/papers/arXiv/data/raw/organizations/figure-ai/48e4987cfc1e-2026-08-26.html>) | [/](https://www.figure.ai/) | 39177 | `5095c978fe2bbe7356cba1c6739d68369f28ca7f49ee8ffcd7ee50447cc042b3` | 主页；Figure03/Helix简介 |
| [5add14b1e834](</Users/joen/Projects/基金战略/papers/arXiv/data/raw/organizations/figure-ai/5add14b1e834-2026-08-26.html>) | [/news](https://www.figure.ai/news) | 54345 | `c0fb7b14534446153efe76c803d88c893e3dc2906597805b55bd54c3efe966cd` | 新闻索引；INDEX 8/25，非INDEX完整正文 |
| [9963ab514787](</Users/joen/Projects/基金战略/papers/arXiv/data/raw/organizations/physical-intelligence/9963ab514787-2026-08-26.html>) | [/](https://www.pi.website/) | 47901 | `9250b02c07c2a605a5ccc12bfa8e98842fe52b16eb6583539d2338c590083590` | PI主页；组织/项目简介 |
| [ed91f76f79a1](</Users/joen/Projects/基金战略/papers/arXiv/data/raw/organizations/physical-intelligence/ed91f76f79a1-2026-08-26.html>) | [/research](https://www.pi.website/research) | 13737 | `253c92fb8350a33d359be1143254b599a0d76c61be822071d824adf6d815dd79` | PI论文链接列表；非报告正文 |

## GEN-1.5：可以恢复什么

对应work：`report:de9e41b42353bf59a7e3`。归属URL是 `https://generalistai.com/blog/research`，文章链接是 `/blog/gen-1.5`；不能把整个研究索引伪装成对文章URL的直接抓取。

- 定位：`a.blog-entry[href="/blog/gen-1.5"]` 的 `data-search` 属性。
- DOM实体解码后的属性长度为25,639字符；进一步做一次明确的HTML实体解码后为25,536字符。
- 后一种文本UTF-8 SHA-256为 `8d3339242ab917d5c80080e73066b464af7929dca5aafaa13552ffabbf8d63c5`。
- 这是官网自行生成的小写、扁平化搜索文本，带前置卡片信息、正文章节、图注与参考文献；**不是文章原始HTML版式、所有图表数据、图像或视频的完整副本**。
- 已直接检查到：3–12秒单次示教、零训练；10项任务59%（±10% std. dev.）；5分钟约50示教、10梯度步83%（±9%）；短时/简单任务与有限成功率的限制。另有30秒记忆、100Hz动作轨迹、单步适配66.5%与参数变化小于0.15%等文本。
- 复算定位示例：在“进一步实体解码”的文本内，`59%`始于字符6404，`83%`始于6558，`3 to 12`始于4465。后续snapshot必须记录所用提取/实体解码规则，不能把这些offset直接套到原HTML。
- **发布日期与文本可用日期分开**：索引明确写2026-08-19；正文级缓存最迟存在时间按上述公开锚点。可以进入8月31日视角，但不能凭这个缓存把正文可用时间回填到8月19日。

因此，此前“GEN-1.5只有九月当前正文，八月历史原文不可用”的阻碍已经部分解除；准确替代描述是“八月底前已公开哈希锚定的官方索引内嵌正文文本可恢复”。摘录仍为公司自报，不获得人工verified、peer-review或独立验证身份。

## Dyna：不能恢复完整实验，但新增索引日期证据

四份缓存分别对应research、news、company、首页。检查了可见正文、原始HTML、较长属性及内联script/JSON；没有找到Dyna-2的14任务53%或39任务实验段落，也没有客户部署报告95条/小时、1,590条/日的正文。

可以恢复的内容：

- 研究、新闻、公司页均有Dyna-2标题与 `/dyna-2` 直链，索引日期为 **08.15.26**。
- 同时有基础设施报告直链 `/research/dyna-2-infrastructure` 及 **08.17.26**。
- 首页已有Dyna-2从百万小时人类活动视频训练、进行预测后动作的简述。

**本轮不改当前月精度**。旧索引的8月15日宣告标签与报告正文只写“August 2026”是两条不同来源事实；前者值得下一轮作为显式来源修订候选，但不能在此次缓存审计中静默把canonical或报告正文日期改回15日。索引宣布报告存在，也不意味着链接所指全文字节全部已被本批缓存保存。

Dyna客户部署报告的目标URL `/research/scaling-customer-deployments` 在这四份缓存中未找到相应报告文本/卡片；继续视为历史完整正文缺口，不用其他Dyna页面代替。

## Figure与PI：仅元数据/简介恢复

Figure新闻页及其 `__NEXT_DATA__` 保存文章列表、日期与媒体缩略信息，INDEX条目写8月25日；没有找到INDEX正文中的上传数量、数据处理或实验内容。可以恢复“当时已列出该发布”的证据，不能补造其完整报告摘录。

PI两份缓存是主页和旧论文列表，不包含RLT或π0.7完整正文；不能据此把九月捕获的公司报告正文提前。它们仍可服务于历史组织与论文发现记录。

## 后续最小安全动作建议

1. 先以GEN-1.5作为公司历史摘录试点：绑定索引源ID、文章href、HTML原始SHA、公开提交与部署时间锚、提取规则和摘录SHA；正文类型明确为 `official_embedded_search_text`。
2. 只摘录被缓存实际覆盖的方法、指标与限制；不要用当前网页补齐缺失图表、大小写版式或新增句段。
3. Dyna和Figure目前只恢复索引/简介级证据；其报告正文继续等待其他内容相符且带历史时间锚的档案。
4. 保留原始报告发布日期与 `text_available_by` 的独立字段，不复制发布日期当正文存在时间；以后若找到更早档案，走显式修订，不覆盖本链。
5. 不继承arXiv CC0标签；公开派生物只保留有必要的短摘录、来源与哈希，不将整篇公司网页当作可任意再发布的CC0语料。

本报告只证明可恢复性与时间/来源链，不自动改变月报结论状态、评审状态、公司信息披露级别或数据库事实。
