---
outline: deep
---

# 评估基准与证据门槛

> benchmark 的作用是让不同方法可比较，不是替代真实部署。本站尤其关注测试任务泄漏、控制频率、长时失败和跨本体可比性。

| Benchmark / 评测 | 主要覆盖 | 优点 | 不能证明什么 | 官方入口 |
|---|---|---|---|---|
| LIBERO | 语言条件、多任务、持续学习 | 任务组合清晰、VLA 使用广 | 真机动力学与开放世界 | [GitHub](https://github.com/Lifelong-Robot-Learning/LIBERO) |
| CALVIN | 长时语言条件桌面操作 | 支持多步序列 | 机器人/场景单一 | [GitHub](https://github.com/mees/calvin) |
| RLBench | 多任务仿真操作 | 任务数量大、接口成熟 | sim-to-real 与真实接触 | [GitHub](https://github.com/stepjam/RLBench) |
| ManiSkill | 高性能仿真与 manipulation | 并行仿真、可复现 | 人类环境长尾 | [官网](https://maniskill.ai/) |
| RoboCasa | 日常场景与大规模仿真 | 场景多样、数据生成 | 真实家庭鲁棒性 | [官网](https://robocasa.ai/) |
| LIBERO-PRO | VLA 记忆与公平性压力测试 | 检查训练泄漏与鲁棒性 | 真实硬件故障 | [arXiv](https://arxiv.org/abs/2510.03827) |
| ManipArena | 推理型 generalist manipulation 真机评测 | 更接近真实执行 | 仍受具体硬件和任务集限制 | [arXiv](https://arxiv.org/abs/2603.28545) |

## 建议的下一代评测矩阵

| 维度 | 最低报告项 | 为什么重要 |
|---|---|---|
| 执行 | 成功率、控制频率、端到端延迟 | 区分“能推理”与“能实时控制” |
| 长时 | 子任务完成曲线、失败位置、恢复率 | 避免平均成功率掩盖级联失败 |
| 泛化 | 新任务、新场景、新物体、新本体分别报告 | “泛化”不是一个单一维度 |
| 世界模型 | 同算力控制收益、roll-out 漂移、model bias | 生成质量不等于规划价值 |
| 触觉/灵巧 | 跨传感器和跨手型迁移、接触失败恢复 | 防止硬件专用结果被误读为通用能力 |
| 开放性 | 代码、数据、权重、硬件配置与评测脚本 | 支持独立复现和后续采用 |
