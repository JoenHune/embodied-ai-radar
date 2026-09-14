---
title: 人物身份、贡献与影响
outline: deep
---

<script setup>
import { withBase } from 'vitepress'
</script>

# 人物身份、贡献与影响

[人物雷达](../organizations/people/)从逐篇作品证据建立个人关系，不发布单一影响力总榜。

## 两层核验不能混同

个人主页核验确认一个人物档案有官方来源；具体作者归属仍需个人论文页、官方项目页或身份标识明确指向该 work。精确同名匹配只能形成候选，不会自动获得该人物名下的全部论文。

作者姓名原文、版本署名和核验别名分别保存。机构集体署名、标点和会员头衔不创建为自然人。论文换版本、共同一作或作者名单变更不能由简单字符串并集抹平。

## 四个观察入口

| 入口 | 当前可比较的内容 | 不能替代的判断 |
|---|---|---|
| 方向内持续贡献 | 已核验参与的作品、方向和活跃月份 | 工作数不是独立项目线数 |
| 成果外部影响 | 有直接证据的引用、独立采用和复现 | 未覆盖不是零；引用不等于认可 |
| 近期研究变化 | 最近三月与此前三月已核验公开工作数 | 小样本和采集变化不直接称为技术趋势 |
| 关键成果贡献者 | 官方贡献声明与逐篇角色证据 | 首位不自动代表主导，末位不自动代表导师 |

默认按姓名浏览，也可按已核验工作数量或活跃月份查看覆盖。后两者衡量本库核验覆盖，不是作者真实影响、研究能力或其完整发表记录。人物身份核验与人工专家评价不是同一件事；AI 审校明确记录核验者类型。

## 时间、合作与组织

最近 12 个完整月仅统计在该窗口首次公开、纳入研究范围且个人归属已核验的工作。当前未结束月不参与完整月比较。后来的评审不改写首次公开日期；已知撤回不取得验证类加分。

局部合作图只连接双方都核实到同一作品的共同署名，不能解释为独立采用、指导关系或贡献比例。人员当前官网角色保留观察日期；未知任期不填造日期，不覆盖历史论文机构归属。

## 企业与信息缺口

企业报告未披露个人名单时继续保留团队成果，不自动归给创始人、CEO 或当前负责人。人物雷达与[组织雷达](../organizations/)互补。

未核验的引用、独立项目、外部采用及角色指标显示“尚未核验”，不以零填充。每个人物详情可展开同名候选、来源、作者版本与全部发表载体。

## 可复算数据

人物审校输入通过显式导入形成四张 JSONL 权威表；日常网站生成只读权威表，不把暂存审查文件自动发布。同名发现候选只在派生页面中呈现，不自动进入已核验事实。

- <a :href="withBase('/downloads/people/persons.jsonl')" download>人物身份与来源</a>
- <a :href="withBase('/downloads/people/authorship-reviews.jsonl')" download>逐篇署名审查</a>
- <a :href="withBase('/downloads/people/organization-links.jsonl')" download>带来源的组织角色</a>
- <a :href="withBase('/downloads/people/influence-evidence.jsonl')" download>引用、采用与复现证据</a>
- [人物索引与统计](/api/v1/people/index.json)
- <a :href="withBase('/downloads/radar.sqlite')" download>完整 SQLite</a>：包含 `people_persons`、`people_authorship_reviews`、`people_organization_links`、`people_influence_evidence` 和 `people_api`。

作者与工作合并修订保留旧 ID 和来源；人物详情必须与索引的数据版本一致，否则停止混用并提示重新读取。

方法参考：[OpenAlex 作者消歧说明](https://help.openalex.org/data/authors/disambiguation/)使用多种身份信号并承认误合并与误拆分；[DORA 指标指南](https://sfdora.org/resource/guidance-on-the-responsible-use-of-quantitative-indicators-in-research-assessment/)强调情境、透明度与多维评价。
