# 硬件型号与登记频次审校

核验日期：2026-09-14。数据快照锁定于05:29:45 UTC；读取`data/equipment/devices.jsonl`、`usage-evidence.jsonl`及公开equipment API，并复核厂商与论文正文。**身份审校不改权威数据；页面展示的实施另行记录。**

实施验收：已使用既有证据建立型号频次视图，具体型号与未明系列分开，支持完整出处清单和连续追加。G1实测展开16项研究、22条用途证明；WUJI Hand多词搜索可找到单独的仿真记录并自动展开；PiPER-X大小写检索通过。360、390、768、1440像素页面无横向溢出。840项Python、153项Node测试及完整构建/公开频次复算审计通过。A100显示归组、4090组合配置拆分等下述建议未作为自动身份合并实施。

## 1. 频次结论

下表按公开API中**不同canonical work数**降序排列；A100两条记录按已知产品名称作审校汇总，未合并原始ID。统计限定当前登记证据，不是42,000余条研究的全文普查、设备台数或市场份额。真机与仿真可属于同一论文，不能相加得到总数。

| 当前型号/产品记录 | 当前`identity_level` | API已纳入work / 全部authority work | 真机 / 仿真登记work（API） | 训练 / 推理work（API） | 仅对照 / 校准work |
|---|---|---:|---:|---:|---:|
| Unitree G1 | `model_specified` | **16 / 18** | **14 / 8** | — | 0 / 0 |
| NVIDIA A100（两个ID合看） | 两条均`family_only` | **2 / 2** | 不适用 | **2 / 0** | 0 / 0 |
| AgileX PiPER-X | `model_specified` | **1 / 1** | **1 / 0** | — | 0 / 0 |
| RTX 4090 / Core i9-14900K desktop workstation | `model_specified`，但这是组合配置名 | **1 / 2** | 不适用 | **0 / 1** | 0 / 0 |
| Fetch mobile manipulator model | `model_specified` | **1 / 1** | **0 / 1** | — | 0 / 0 |
| WUJI 20-DoF hand（型号代际待确认） | `family_only` | **1 / 1** | **0 / 1** | — | 0 / 0 |

G1的16项由8项仅登记真机、2项仅登记仿真、6项同时登记两者组成。其中CoorDex的真机记录是**轨迹回放**，不能称14项全部闭环自主验证。完整authority中的G1为15项真机、10项仿真、18项去重研究。

DoorMan（`arxiv:2512.01061`）与DreamMimic（`arxiv:2608.22278`）当前canonical状态均为`manual_review`、`low_confidence_review`。因此公开included使用集合没有它们：G1从18降至16；RTX 4090从2降至1。证据仍在authority，不应通过硬件审校自动promote这两篇。

## 2. 型号判定与不丢证据的规范建议

- **Unitree G1：可保留这个已明确型号。** `Unitree G1 model`及带42-DoF说明的模拟配置可归到G1显示组，但保留原名、自由度和仿真角色。厂家另列G1与G1 EDU，不能仅凭论文29/42自由度便自动补写EDU。[Unitree产品表](https://www.unitree.com/g1/)
- **AgileX PiPER-X：官方拼写为PiPER-X，不是PiPer-X。** 大小写变体可作同型显示别名，但不能把无X后缀的PiPER、PiPER-H/L等顺手合并。MoPA正文明确真机搭载两只PiPER-X；仍只计1篇研究，而非2次频次。[厂家产品页](https://global.agilex.ai/products/piper-x)、[MoPA §IV-D](https://arxiv.org/html/2609.12081v1)
- **WUJI：保持待确认的产品族，不升级具体代际。** CoorDex §4与附录C明确为20-DoF WUJI仿真手；真机是G1+Dex3-1回放。厂家同时有Wuji Hand和Wuji Hand 2，均20主动自由度，所以“20-DoF”不能唯一确定产品代际。建议显示“**WUJI Hand（20-DoF，代际未明；仅仿真）**”，保留`family_only`。品牌WUJI本身不能充当具体型号。[CoorDex正文及附录C](https://arxiv.org/html/2606.23680v1)、[Wuji Hand](https://wuji.tech/en/hand)、[Wuji Hand 2](https://wuji.tech/en/hand2)
- **WUJI的动态链接尤其需谨慎。** CoorDex参考文献[38]注明访问2026-05-27的`.../wuji-hand/latest/overview/`，但该同一地址今日正文实际介绍**Wuji Hand 2 Beta 2**，并另列旧Wuji Hand归档。不能用当前`latest`页面反填论文当时所用型号；需要论文资产版本、固定版本文档或作者明确说明。[论文所引文档当前内容](https://docs.wuji.tech/docs/en/wuji-hand/latest/overview/)
- **A100：显示归组可以，型号细分不能猜。** 当前ID为`hardware:nvidia-a100-3169fc86`与`hardware:nvidia-a100-6097fb05`；“GPUs”“cluster”不是不同GPU型号。可用明确白名单归为“**NVIDIA A100（容量/封装未说明）**”，以两条usage的work并集计2，保留原ID和`family_only`。官方存在40GB/80GB及PCIe/SXM差别，论文未说明则不得补填。[NVIDIA A100规格](https://www.nvidia.com/en-us/data-center/a100/)
- **RTX 4090：已知的是GPU和CPU，不是商业整机型号。** 建议型号频次显示“**NVIDIA GeForce RTX 4090**”，将Intel Core i9-14900K、台式机、外接推理保留在configuration，并注明这是从组合配置提取的显示视图。不得把“NVIDIA / Intel”误作整机厂商，亦不得补写显卡板卡厂商或Founders Edition。[NVIDIA标准产品名](https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090/)、[VIRAL §3](https://arxiv.org/html/2511.15200v1)、[DoorMan附录D](https://arxiv.org/html/2512.01061v1)
- **Fetch：型号与仿真身份分开。** 可规范显示为“Fetch（仿真模型）”；MoPA §IV-A明确使用ManiSkill-HAB里的Fetch，§IV-D的真机却是Trigger-A3+PiPER-X。不能因同一论文有真机实验就把Fetch也记为实机；也不能把标题中的FetchMan当Fetch设备。[Fetch官方硬件说明](https://fetchrobotics.github.io/docs/robot_hardware.html)、[MoPA §IV-A、IV-D](https://arxiv.org/html/2609.12081v1)

## 3. 出处清单

G1当前API的16项登记如下；“实+仿”仍只贡献1次型号频次。

| 研究（canonical arXiv ID） | 已登记用途 | 原文定位 |
|---|---|---|
| [VisualMimic · 2509.20322](https://arxiv.org/html/2509.20322v1) | 实+仿 | §IV-B |
| [GMR · 2510.02252](https://arxiv.org/html/2510.02252v1) | 仿真 | §III-B、III-C |
| [HumanoidExo · 2510.03022](https://arxiv.org/html/2510.03022v1) | 真机 | §3.5 |
| [ResMimic · 2510.05070](https://arxiv.org/html/2510.05070v1) | 实+仿 | §IV、IV-C |
| [TWIST2 · 2511.02832](https://arxiv.org/html/2511.02832v1) | 真机 | §III-B |
| [VIRAL · 2511.15200](https://arxiv.org/html/2511.15200v1) | 实+仿 | §3 |
| [HuMI · 2602.06643](https://arxiv.org/html/2602.06643v1) | 真机 | 附录B |
| [EgoHumanoid · 2602.10106](https://arxiv.org/html/2602.10106v1) | 真机 | §III-A、III-B |
| [EgoScale · 2602.16710](https://arxiv.org/html/2602.16710v1) | 真机；不表示腿部参与操作 | §3跨形态评测、附录D.1 |
| [Ψ0 · 2603.12263](https://arxiv.org/html/2603.12263v1) | 真机 | §IV-A1 |
| [OpenHLM · 2606.22174](https://arxiv.org/html/2606.22174v1) | 真机 | 附录B.1 |
| [CoorDex · 2606.23680](https://arxiv.org/html/2606.23680v1) | 仿真+真机回放 | 附录C |
| [ω-0 · 2608.06375](https://arxiv.org/html/2608.06375v1) | 真机 | §7真机演示 |
| [FetchMan · 2608.17027](https://arxiv.org/html/2608.17027v1) | 实+仿 | §3、6.2、6.5 |
| [GLoRI · 2609.05994](https://arxiv.org/html/2609.05994v1) | 实+仿；离线参考闭环跟踪 | §IV-A、IV-C3 |
| [CHIP · 2609.06591](https://arxiv.org/html/2609.06591v1) | 仿真 | §4.1 |

其余焦点设备的完整登记来源：

- **PiPER-X、Fetch**：[MoPA · 2609.12081](https://arxiv.org/html/2609.12081v1)，分别为§IV-D真机双臂与§IV-A仿真平台。
- **WUJI 20-DoF**：[CoorDex · 2606.23680](https://arxiv.org/html/2606.23680v1)，§4、附录C，仅仿真；没有WUJI实机或仅对照记录。
- **A100**：[Ψ0 · 2603.12263](https://arxiv.org/html/2603.12263v1) §IV-A3：预训练64张、后训练32张；[Tactile-aware quadrupedal loco-manipulation · 2604.27224](https://arxiv.org/html/2604.27224v1) §IV-A1：高层策略训练、数量未说明。卡数和训练阶段均不重复增加论文频次。
- **RTX 4090组合配置**：[VIRAL · 2511.15200](https://arxiv.org/html/2511.15200v1) §3、[DoorMan · 2512.01061](https://arxiv.org/html/2512.01061v1) 附录D，均为外接工作站推理；后者当前不在included集合。
- **G1另存但未计入API频次**：[DoorMan](https://arxiv.org/html/2512.01061v1)的实+仿；[DreamMimic · 2608.22278](https://arxiv.org/html/2608.22278v1) §IV-C的42-DoF仿真配置。两项证据不删除，也不并入当前16项。

## 4. 计数与证据保留要求

型号显示组应通过**明确别名表**关联原hardware IDs；频次取筛选后的canonical work集合大小。保留全部`usage_id`、`reported_device_name`、`source_url`、`source_locator`、`observed_at`、`setting`、`usage_scope`和`validation_context`，不能用整页提及数、机器人数量、试验次数或GPU卡数排序。品牌/代际未明记录需独立标注，未知RGB相机不能仅因同名就合并。

本轮还发现**登记覆盖缺口**：[VIRAL §2](https://arxiv.org/html/2511.15200v1)明确使用L40S进行教师训练与学生蒸馏（16/64张），但当前该work的usage仅登记4090推理。可另补审核后的L40S训练关系；在真正入库前，不把这条新发现混入“当前登记频次”。

本次没有事实红项直接改写权威数据；已确认拼写和统计作为建议记录，WUJI代际与A100细分型号保持待确认。来源哈希：devices=`94acab4d123660bf77b0a72092c962b039f807dffaa11a4ee4acc0175b724adf`；usage=`ab160aa91db7484730ebadeed123651bfbda926a8b1ef9389eeb7637dcf95048`。
