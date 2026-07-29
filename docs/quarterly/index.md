---
outline: deep
---

# 季度演进

> 季度页观察一个信号如何从出现、扩散走向验证，避免逐月噪声掩盖方法迁移。

## 2025 Q3 · 数据入口重构

人类视频、无标签动作和 egocentric/接触表示成为弱信号主线；flow policy 扩散，触觉首次进入 VLA 统一空间，但世界模型的闭环控制证据仍弱。

| 论文候选 | 基础模型 | 双系统 | 灵巧操作 | 世界模型 | 通用学习 |
|---:|---:|---:|---:|---:|---:|
| 270 | 103 | 3 | 48 | 22 | 94 |

**阶段证据链：**

- **人类视频开始被拆成可迁移的动作先验（B）**：EC-Flow、H-RDT 与 GR-3 分别从无动作标签视频、双臂人类操作和通用数据配方切入，信号尚未形成单一范式，但都在绕开机器人示教瓶颈。
- **“大脑—小脑”正在从二层变成三系统（C）**：TriVLA 把高层语义、低层动作与 episodic world model 明确拆分；EmbodieDreamer 则让世界模型承担 real-to-sim-to-real 中介。
- **视频生成器开始越过“数据增强”，直接扮演策略（B）**：Video Generators are Robot Policies、Masquerade 与 DiWA 分别尝试直接控制、视频编辑迁移和用世界模型适配 diffusion policy。
- **触觉开始进入 VLA 统一语义空间（C）**：OmniVTLA 不再把触觉仅作为低层状态，而是与视觉、语言和动作对齐。
- **flow matching 正在成为通用策略的新执行底座（B）**：ManiFlow、EC-Flow 与 FLOWER 在通用操控、无标签视频和轻量 generalist policy 三条线上同时采用 flow。
## 2025 Q4 · 规划与预测汇合

fast–slow 形成架构簇，world model 从生成与适配转向后训练、搜索和 MPC；跨本体问题从 adapter 转向数据和动作表示。

| 论文候选 | 基础模型 | 双系统 | 灵巧操作 | 世界模型 | 通用学习 |
|---:|---:|---:|---:|---:|---:|
| 383 | 196 | 6 | 34 | 45 | 102 |

**阶段证据链：**

- **fast–slow 从隐式分工变成显式训练目标（B）**：VLA-R1、MoTVLA 与上月 VLA-Reasoner 分别用推理增强、统一快慢推理和在线搜索建立高层思考—低层动作分工。
- **世界模型开始进入 VLA 后训练（B）**：VLA-RFT 用 world simulator 给可验证奖励，Ctrl-World 强调可控生成，Latent Action Pretraining 则把预测表征回流到动作学习。
- **视频驱动双臂学习成为数据规模化的第二战场（B）**：DexMan、Parse-Augment-Distill 与真实人类活动视频预训练共同指向少机器人示教的双臂学习。
- **世界模型终于开始用规划成功率证明自己（B）**：WorldPlanner 把 action-conditioned visual world model 接入 MCTS/MPC；跨本体灵巧世界模型与 Ctrl-World 构成独立跟进。
- **跨本体迁移从模型适配转向数据分布设计（B）**：X-Diffusion、InternData-A1 与 X-VLA 分别统一人类示范、合成数据和软提示式跨本体策略。
## 2026 Q1 · 可执行性成为新门槛

latent action world model 进入 in-the-wild 与 RL simulator，Action CoT/异步触发重写大小脑接口，3 月集中出现 executable alignment、长时接触和真实评测。

| 论文候选 | 基础模型 | 双系统 | 灵巧操作 | 世界模型 | 通用学习 |
|---:|---:|---:|---:|---:|---:|
| 493 | 224 | 8 | 69 | 59 | 133 |

**阶段证据链：**

- **latent action world model 从实验室走向 in-the-wild（B）**：Learning Latent Action World Models In The Wild、Cosmos Policy 与 Motus 分别覆盖野外视频、视频模型微调和统一 latent action。
- **Action CoT 与非对称专家正在重写大小脑接口（B）**：ACoT-VLA、TwinBrainVLA 与 DualVLA 从动作链推理、非对称混合专家和部分解耦三种方式定义高低层接口。
- **人类中心数据被推到跨本体预训练主线（B）**：Being-H0.5、RoboWheel 和 InternData-A1 都把人类数据转化为 generalist policy 的可扩展监督。
- **世界模型开始承担 RL 模拟器与在线自纠错（B）**：WoVR、Self-Correcting VLA 与 World-Gymnast 分别用于后训练模拟、稀疏想象修正和世界模型内 RL。
- **快慢系统开始感知力、接触与完成状态（B）**：FAVLA 将力适应写入 fast–slow 架构，StreamVLA 用 completion-state gating 打破固定 reason–act 循环，自纠错框架补上终止判断。
## 2026 Q2 · 系统工程与触觉闭环

连续推理、coarse-to-fine 调度、3D trace 与 real-time execution 使 VLA 竞争进入系统层；触觉从融合模态升级为预测与 world model 通道。

| 论文候选 | 基础模型 | 双系统 | 灵巧操作 | 世界模型 | 通用学习 |
|---:|---:|---:|---:|---:|---:|
| 695 | 320 | 8 | 99 | 102 | 166 |

**阶段证据链：**

- **触觉与 world model 开始合流（B）**：Touch Dreaming、FingerEye 与 OmniVTA 把触觉用于未来预测、连续感知和接触世界建模。
- **双系统进入异步 coarse-to-fine 调度（B）**：Libra-VLA、Trace-Conditioned Planning 与 DIAL 不再固定每步完整推理，而是在轨迹、意图和动作层分配不同计算。
- **foundation model 开始接受垂直本体与可控行为约束（C）**：π0.7 强调 steerable generalist policy，Open-H-Embodiment 把医疗机器人纳入大规模基础模型数据。
- **视频模型正在被改造成 generalist policy，而非外置 world model（B）**：Turning Video Models into Generalist Robot Policies、τ0-WM 与 Cosmos Policy 把视频预测和动作生成压进同一训练栈。
- **连续推理开始取代离散 reason–act 循环（B）**：Continuous Reasoning、Libra-VLA 与 StreamVLA 都试图让思考与控制异步或连续发生。

## 2026 年 7 月临时完整版

截至 29 日，100K 小时级轨迹仍是数量共识；更领先的 B 级信号集中在在线评价/纠错、进度—记忆—运行时状态和视触觉 world model。Agent OS 保持 C 级，需等待第三方采用。

<!-- 更新标记：季度演进 最后更新 2026.07 -->
