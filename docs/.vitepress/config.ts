import { defineConfig } from 'vitepress'

export default defineConfig({
  title: '具身智能研究雷达',
  description: '论文、技术报告、研究趋势与全球关键研究组的可追溯研究情报系统',
  lang: 'zh-CN',
  base: '/embodied-ai-radar/',
  lastUpdated: true,
  cleanUrls: true,
  router: { prefetchLinks: false },
  transformHead({ page, head }) {
    // VitePress 1.x includes every global async component in every page's
    // preload list. Keep only the component actually rendered by this route;
    // other components remain available through their normal dynamic import.
    const component = page === 'hardware/index.md' ? 'HardwareRadar'
      : page === 'trends/loco-manip/index.md' ? 'LocoManipRadar'
      : page === 'organizations/people/index.md' ? 'PeopleRadar' : page === 'index.md' || /^(trends|monthly|organizations)\//.test(page)
      ? 'RadarDashboard'
      : page === 'database/index.md' ? 'DatabaseExplorer'
        : page === 'pulse/index.md' ? 'PulseFeed'
          : page === 'pulse/corl-2026.md' ? 'ConferenceRadar'
            : page === 'methods/coverage.md' ? 'OrganizationCoverage' : null
    for (let index = head.length - 1; index >= 0; index--) {
      const [tag, attrs] = head[index]
      const href = String(attrs?.href || '')
      const match = href.match(/\/(RadarDashboard|PeopleRadar|HardwareRadar|LocoManipRadar|DatabaseExplorer|PulseFeed|ConferenceRadar|OrganizationCoverage|VPLocalSearchBox)\.[^/]+\.js$/)
      const chartDependency = /\/(echarts|ChartFrame|useEChart)\.[^/]+\.js$/.test(href)
      const trendDependency = /\/(DirectionTrendGrid|DirectionTrendChart|monthlySeries)\.[^/]+\.js$/.test(href)
      const overviewDependency = /\/v3-overview\.[^/]+\.js$/.test(href)
      const reportCoverageDependency = /\/ReportCoverage\.[^/]+\.js$/.test(href)
      const feedDependency = /\/ResearchFeed\.[^/]+\.js$/.test(href)
      const mediaDependency = /\/(SourceImage|ResearchCard|useVisualMedia|research-card)\.[^/]+\.js$/.test(href)
      const shareOverviewDependency = /\/DirectionShareOverview\.[^/]+\.js$/.test(href)
      if (tag === 'link' && attrs?.rel === 'modulepreload' && (
        (match && match[1] !== component)
        || (chartDependency && !['RadarDashboard', 'PeopleRadar', 'HardwareRadar', 'LocoManipRadar'].includes(component || ''))
        || (trendDependency && component !== 'RadarDashboard')
        || (overviewDependency && component !== 'RadarDashboard')
        || (feedDependency && !['RadarDashboard', 'PulseFeed'].includes(component || ''))
        || (mediaDependency && !['RadarDashboard', 'PeopleRadar', 'HardwareRadar', 'LocoManipRadar', 'DatabaseExplorer', 'PulseFeed'].includes(component || ''))
        || (shareOverviewDependency && page !== 'index.md')
        || (reportCoverageDependency && (component !== 'RadarDashboard' || !page.startsWith('organizations/') || page === 'organizations/collaboration.md'))
      )) head.splice(index, 1)
    }
  },
  srcExclude: [
    'analysis/**', 'frontiers/**', 'groups/**', 'questions/**', 'quarterly/**', 'social/**',
    'monthly/20*.md', 'database/20*.md', 'database/publications.md', 'database/publications/**', 'references.md',
  ],
  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/embodied-ai-radar/favicon.svg' }],
    ['meta', { name: 'theme-color', content: '#4338ca' }],
    ['meta', { name: 'color-scheme', content: 'light dark' }],
  ],
  markdown: { math: true },
  vite: {
    build: {
      chunkSizeWarningLimit: 500,
      rollupOptions: { output: { manualChunks(id) {
        if (id.includes('/node_modules/echarts/') || id.includes('/node_modules/zrender/')) return 'echarts'
      } } },
    },
  },
  themeConfig: {
    logo: '/favicon.svg',
    siteTitle: '研究雷达',
    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜索页面', buttonAriaLabel: '搜索页面' },
          modal: { noResultsText: '未找到页面', resetButtonTitle: '清除', footer: { selectText: '选择', navigateText: '导航', closeText: '关闭' } },
        },
      },
    },
    nav: [
      { text: '总览', link: '/' },
      { text: '趋势', activeMatch: '^/trends/', items: [{ text: '趋势总览', link: '/trends/' }, { text: '移动与全身操作', link: '/trends/loco-manip/' }] },
      { text: '月度', link: '/monthly/' },
      { text: '人物与组织', items: [{ text: '人物与代表作', link: '/organizations/people/' }, { text: '公司与研究组', link: '/organizations/' }, { text: '合作关系', link: '/organizations/collaboration' }] },
      { text: '研究库', activeMatch: '^/(database|hardware)/', items: [{ text: '全文检索', link: '/database/' }, { text: '研究设备', link: '/hardware/' }] },
      { text: '动态', link: '/pulse/' }, { text: '方法', link: '/methods/' },
    ],
    sidebar: {
      '/methods/': [{
        text: '方法与数据',
        items: [
          { text: '方法总览', link: '/methods/' }, { text: '纳排规则', link: '/methods/inclusion' },
          { text: '语料扩充协议', link: '/methods/expansion-protocol' }, { text: '研究组归属', link: '/methods/research-groups' },
          { text: '覆盖审计与发现池', link: '/methods/coverage' },
          { text: '人物、贡献与影响', link: '/methods/people' },
          { text: '研究设备与联合操作', link: '/methods/equipment-loco' },
          { text: '视觉设计与配图口径', link: '/methods/visual-design' },
        ],
      }],
    },
    outline: { level: [2, 3], label: '本页目录' },
    lastUpdated: { text: '最后更新' },
    docFooter: { prev: '上一篇', next: '下一篇' },
    socialLinks: [{ icon: 'github', link: 'https://github.com/JoenHune/embodied-ai-radar' }],
    footer: { message: '所有统计均可由公开 JSONL 与 SQLite 复算', copyright: 'MIT License © 2026' },
  },
})
