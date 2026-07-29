import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

export default withMermaid(defineConfig({
  title: '具身智能研究雷达',
  description: '2025.07–2026.06 具身智能月度研究趋势、同行评审锚点与结构化证据库',
  lang: 'zh-CN',
  base: '/embodied-ai-radar/',
  lastUpdated: true,
  cleanUrls: true,
  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/embodied-ai-radar/favicon.svg' }],
    ['meta', { name: 'theme-color', content: '#4f46e5' }],
  ],
  markdown: {
    math: true,
  },
  mermaid: {
    flowchart: { padding: 16, nodeSpacing: 30, rankSpacing: 40, htmlLabels: true },
  },
  vite: {
    build: { chunkSizeWarningLimit: 1600 },
  },
  themeConfig: {
    logo: '/favicon.svg',
    siteTitle: '研究雷达',
    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜索', buttonAriaLabel: '搜索' },
          modal: {
            noResultsText: '未找到结果',
            resetButtonTitle: '清除搜索',
            footer: { selectText: '选择', navigateText: '导航', closeText: '关闭' },
          },
        },
      },
    },
    nav: [
      { text: '首页', link: '/' },
      { text: '月度雷达', link: '/monthly/' },
      { text: '方向专题', link: '/directions/foundation-models' },
      { text: '年度综合', link: '/analysis/annual' },
      { text: '弱信号', link: '/analysis/weak-signals' },
      { text: '团队机构', link: '/analysis/institutions' },
      { text: '证据库', link: '/database/' },
      { text: '方法', link: '/methods/' },
    ],
    sidebar: [
      {
        text: '总览',
        collapsed: false,
        items: [
          { text: '执行摘要', link: '/analysis/executive-summary' },
          { text: '年度综合', link: '/analysis/annual' },
          { text: '弱信号与未来判断', link: '/analysis/weak-signals' },
          { text: '季度演进', link: '/quarterly/' },
        ],
      },
      {
        text: '月度研究雷达',
        collapsed: false,
        items: [
          { text: '月度总览', link: '/monthly/' },
          { text: '2025 年 7 月', link: '/monthly/2025-07' },
          { text: '2025 年 8 月', link: '/monthly/2025-08' },
          { text: '2025 年 9 月', link: '/monthly/2025-09' },
          { text: '2025 年 10 月', link: '/monthly/2025-10' },
          { text: '2025 年 11 月', link: '/monthly/2025-11' },
          { text: '2025 年 12 月', link: '/monthly/2025-12' },
          { text: '2026 年 1 月', link: '/monthly/2026-01' },
          { text: '2026 年 2 月', link: '/monthly/2026-02' },
          { text: '2026 年 3 月', link: '/monthly/2026-03' },
          { text: '2026 年 4 月', link: '/monthly/2026-04' },
          { text: '2026 年 5 月', link: '/monthly/2026-05' },
          { text: '2026 年 6 月', link: '/monthly/2026-06' },
          { text: '2026 年 7 月前瞻', link: '/monthly/2026-07' },
        ],
      },
      {
        text: '五大方向',
        collapsed: false,
        items: [
          { text: '具身基础模型', link: '/directions/foundation-models' },
          { text: '大小脑与双系统', link: '/directions/dual-system' },
          { text: '灵巧操作', link: '/directions/dexterous-manipulation' },
          { text: '世界模型', link: '/directions/world-models' },
          { text: '通用机器人学习', link: '/directions/general-robot-learning' },
        ],
      },
      {
        text: '证据与方法',
        collapsed: false,
        items: [
          { text: '同行评审锚点', link: '/analysis/peer-review' },
          { text: '团队与机构雷达', link: '/analysis/institutions' },
          { text: '评估基准', link: '/analysis/benchmarks' },
          { text: '论文数据库', link: '/database/' },
          { text: '2024 候选', link: '/database/2024' },
          { text: '2025 候选', link: '/database/2025' },
          { text: '2026 候选', link: '/database/2026' },
          { text: '检索与分类方法', link: '/methods/' },
          { text: '纳排与局限', link: '/methods/inclusion' },
          { text: '内容审校报告', link: '/methods/content-audit-report' },
          { text: '参考文献', link: '/references' },
        ],
      },
    ],
    outline: { level: [2, 3], label: '本页目录' },
    lastUpdated: { text: '最后更新' },
    docFooter: { prev: '上一篇', next: '下一篇' },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/JoenHune/embodied-ai-radar' },
    ],
    footer: {
      message: '数据与统计由结构化证据库自动生成',
      copyright: 'MIT License © 2026',
    },
  },
}))
