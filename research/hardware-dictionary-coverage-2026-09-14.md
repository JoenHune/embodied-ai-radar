# 全库硬件发现词典：覆盖与名称审校

> 日期：2026-09-14
>
> 词典：`config/hardware-dictionary.json`，schema/version 均为 `1`
>
> 审校对象：具名硬件名称、系列/型号边界、发现别名及原设备 ID 关联。按 content-audit 的确认错误/待确认/可接受微调三级原则处理。
> 重要边界：本文件只登记**发现词典覆盖**，不登记论文使用频次，不新增硬件使用事实，不修改四表权威数据。

## 1. 语料与结果

采用 `data/catalog/works/*.jsonl` 的 256 个分片，共 **42,720** 个 canonical work，其中 **41,082** 个摘要非空。标题/摘要中的具名硬件线索用于决定扩词方向。旧 `data/works.json` 只有 42,083 项且没有摘要，是迁移输入，未用作本轮语料分母。

词典目前 **263** 个型号或具名系列，含 150 个 `model_specified`、113 个 `family_only`。79 个词典组关联已有的 86 个设备 ID，184 个条目没有既有设备 ID；后者是发现入口，**不是新登记的使用设备**。共有 132 个去重名称来源 URL。全库检测及正文可用性/命中统计由独立 census 流程生成，不在此报告中混入。

| 沿用的九类 | 词典条目 | 覆盖举例 |
|---|---:|---|
| 人形与移动机器人 `robot_platform` | 63 | G1/H1/H1-2、Go1/Go2/A1/B1/B2、ANYmal、Digit/Cassie、Fetch、TIAGo、Stretch、ALOHA 系统、TurtleBot、Jackal/Husky、Crazyflie、Tello、BlueROV2 |
| 机械臂 `robot_arm` | 49 | Panda/FR3、UR3/5/10 及 e 系列、xArm、WidowX/ViperX、Kinova、iiwa、Baxter/Sawyer、RealMan、AUBO |
| 算力平台 `compute_platform` | 48 | A100/H100/H200/V100、RTX 4090/3090/3080、RTX A6000、Jetson Orin/Xavier/Nano/TX2、TPU |
| 视觉与空间传感器 `vision_sensor` | 32 | RealSense、ZED、Azure Kinect、Livox、Velodyne VLP-16、Ouster OS0/1/2、Hesai XT16/32 |
| 数采与遥操作设备 `data_collection` | 30 | UMI、VIVE/PICO/Quest、Apple Vision Pro、OptiTrack/Vicon/Xsens、Dobot X-Trainer |
| 灵巧手 `dexterous_hand` | 19 | Allegro、LEAP、Shadow、Inspire、WUJI、Dex3、SCHUNK SVH、BarrettHand、TriFinger、D'Claw |
| 触觉传感器 `tactile_sensor` | 11 | DIGIT、GelSight、GelSlim、TacTip、BioTac、uSkin、FlexiTac |
| 夹爪 `gripper` | 7 | Robotiq 2F、Dex1、已有具名自制夹爪 |
| 力与力矩传感器 `force_sensor` | 4 | Robotiq FT300、ATI Nano17/Mini45、ATI F/T 系列 |

九类名称兼容现有设备结构。无人机、水下 ROV 和地面底盘都归 `robot_platform`，不暗示其属于人形。机器人系统、灵巧操作实验平台的分类只是检索入口，不是商业型号或市场分段。

## 2. 已直接修正与保留的身份边界

| 项目 | 发现词典的处理 | 不允许的推断 |
|---|---|---|
| WUJI Hand | 保留 `family_only`，关联已有“WUJI 20-DoF hand”ID | 不因 20-DoF 或当前 latest 文档升级成 Hand 2；不把仿真变成真机 |
| NVIDIA A100 | 两个原 ID 关联一个 A100 发现组；保留 `family_only` | 不修改原 ID，不猜 40/80GB、PCIe/SXM 或设备台数 |
| RTX 4090 组合工作站 | 以 GPU 标准名称发现，保留原组合工作站 ID 作为关联 | 关联不等于整机身份合并；不把 NVIDIA/Intel 当整机品牌，不猜板卡厂商 |
| ALOHA / ALOHA 2 / Mobile ALOHA | 分立的系统条目；ALOHA 无代际时为系列级 | 不自动展开成 WidowX、ViperX、底盘、相机使用事实 |
| Interbotix WidowX 250 / ViperX 300 | 无明确 S/6DOF 后缀的发现名保留系列级；明确 6DOF 条目分开 | 不从“WidowX”猜 250、不从“250”猜 6DOF；不改原设备 identity |
| UMI 与 UMI-style/HuMI | 原版手持接口、既有派生夹爪/设备保持分开 | 不把“UMI-style”认作相同制造型号或相同硬件配置 |
| Franka Panda / Research 3 | 分开条目；“Franka arm”仅系列入口 | 不把 Franka/Franka Emika 品牌词升级成 Panda 或 FR3 |
| Unitree G1 / H1 / H1-2 | 分开；短名要求局部上下文 | 不吞 H1-2 为 H1，不因自由度猜 EDU |
| DIGIT / Digit | 触觉传感器和 Agility 双足机器人分开，并有各自上下文 | 不靠大小写区分；不把“digit”普通词变设备 |
| Xsens MVN Link / Xsens Link | 旧 MVN Link 与新 Link 系列分开 | 不用当前重命名/新版产品页反填旧论文代际 |
| VIVE Pro | 此次核验的旧地址实际重定向到 Pro 2，只新增 Pro 2 | 不用重定向后内容证明旧 Pro 的配置 |

名称基准以厂家资料或项目原始论文为主。已登记设备中仍复用原 `official_url`；这只是保留已有名称出处，**不表示本轮重新全文核验了每篇原始论文**。厂商官网用来核对产品名，不证明任何论文使用该硬件。

## 3. 关键名称来源

- 机械臂：[Franka Research 3](https://franka.de/franka-research-3)、[UFACTORY xArm 差异说明](https://docs.supportarticle.ufactory.cc/support_articles/hardware/the-difference-between-ufactory-xarm5-xarm6-and-xarm7.html)、[Interbotix 型号规格](https://docs.trossenrobotics.com/interbotix_xsarms_docs/specifications.html)、[UR 数据表目录](https://www.universal-robots.com/manuals/EN/HTML/MainLanding/Content/Landingpages/LandingSheets.htm)、[KUKA LBR iiwa](https://www.kuka.com/en-us/products/robotics-systems/industrial-robots/lbr-iiwa)。
- 系统：[ALOHA 原始论文](https://arxiv.org/abs/2304.13705)、[ALOHA 2 原始论文](https://arxiv.org/abs/2405.02292)、[Mobile ALOHA 原始论文](https://arxiv.org/abs/2401.02117)、[UMI 原始论文](https://arxiv.org/abs/2402.10329)。
- 地面/空中/水下平台：[Unitree 产品目录](https://www.unitree.com/)、[Clearpath 官方平台文档](https://docs.clearpathrobotics.com/docs_robots/robots/)、[Crazyflie 官方硬件支持范围](https://www.bitcraze.io/documentation/repository/crazyflie-firmware/master/)、[Ryze Tello](https://www.ryzerobotics.com/tello)、[BlueROV2](https://bluerobotics.com/store/rov/bluerov2/)。
- 灵巧与触觉：[Allegro V4](https://www.allegrohand.com/sub/product/p.php?idx=1)、[LEAP Hand 原始论文](https://arxiv.org/abs/2309.06440)、[Shadow 系列](https://shadowrobot.com/dexterous-hand-series/)、[DIGIT 原始论文](https://arxiv.org/abs/2005.14679)、[TacTip 作者综述](https://arxiv.org/abs/2105.14455)、[XELA uSkin](https://xelarobotics.com/products/)。
- 算力：[NVIDIA 官方 GPU 名录](https://developer.nvidia.com/cuda/gpus)、[V100 有效官方页面](https://www.nvidia.com/en-gb/data-center/tesla-v100/)、[Jetson 模块目录](https://developer.nvidia.com/embedded/jetson-modules)、[Google TPU 代际配置](https://cloud.google.com/kubernetes-engine/docs/concepts/plan-tpus)。
- 传感与数采：[RealSense 型号合规资料](https://www.realsenseai.com/regulatory-information/)、[ZED 型号比较](https://support.stereolabs.com/hc/en-us/articles/24824513333015-Where-can-I-find-a-comparison-table-for-the-ZED-Stereo-Cameras)、[Vicon 相机](https://www.vicon.com/hardware/cameras/)、[Xsens 硬件选择](https://www.xsens.com/get-started/motion-capture)、[Hesai XT 系列](https://www.hesaitech.com/product/xt16-32-32m/)、[ATI Nano17](https://www.ati-ia.com/products/ft/ft_models.aspx?id=Nano17)。

全部条目的逐项来源保存在各条 `source_urls`。动态厂商链接只以本次可见的产品名作名称核对，不用于历史规格或历史使用归因。此次遇到美国 V100 旧路径 404，采用成功检索到的官方英国站页面；没有把失败路径当已验证来源。

## 4. 待确认、排除与不完整性

### 待确认（保留黄色边界）

- **Action 5 RGB camera**：原注册来源并未证明可唯一补全为某个 DJI Osmo Action 商品代际，词典仍标记 “as reported” 与 `family_only`。
- **WUJI**：Hand 与 Hand 2 均有 20 主动自由度；当前 latest 文档不能反向确定论文当时型号。须核对固定资产版本或作者确认。
- **Inspire/Shadow/Allegro/GoPro/PICO/RealSense/ZED/ANYmal/Jetson 等未带完整代际的提及**：只能形成具名系列候选。
- **OptiTrack/Vicon/Xsens**：无具体相机或惯性套装型号时，只保留硬件系统族；软件名或数据集来源不等于作者采集设备。
- **ALOHA、ATLAS、DIGIT、Panda、Spot、Stretch 等同形词**：必须结合局部原文排除通信协议、算法模型、普通词、引用或对照。词典提供 `context_terms`；检测器必须落实这些约束，仍需人工/正文审阅。
- **摘要只写品牌而无产品族/型号的 RealMan/Dobot/KUKA/Unitree 等**：不会凭品牌生成某个具体硬件型号。

### 明确排除

原 109 个设备 ID 中，23 个只有通用部件描述、外观/自由度说明或未具名来源，未放入发现词典；**这些权威记录和证据没有被删除**。例如 unknown PC/workstation、外部动捕、头/腕 RGB 相机、force gauge、1-DoF gripper、未具名 7-DoF 三指手、28-joint 模拟人形、仅描述 kinematically matched master arms。

不把 Isaac/Isaac Sim/Isaac Gym、MuJoCo、ROS、CUDA、仿真器、软件、数据集、VLA/策略名、电机或关节模块列成设备型号。项目名“FetchMan”不是 Fetch 别名。Jacobian/Jacobi 不命中 Jaco，UR5 不吞 UR5e，H1 不吞 H1-2。

### 覆盖不是穷尽

42,720 是**遍历语料的分母**，不是已核完全文或硬件身份的数量。263 也不是全世界硬件型号数。摘要未写出的实验硬件、只有图片/表格出现的设备、自制原型、罕见工业/医疗平台、型号 OCR 变体及新设备仍可能遗漏。扩词优先来自实际语料线索及可核对的官方名称，没有为填满数字虚构产品。

## 5. 验证与证据保留

- 词典 JSON 可解析；dictionary_id 全部唯一、以 `model:` 开头。
- 每条有非空别名及名称来源；类别严格沿用九类；身份只含 `model_specified` 与 `family_only`。
- 86 个关联 hardware_id 均在原注册表存在；新增 184 个词条 hardware_ids 为空。
- 已调用实际检测器做 Panda/G1/H100/D435i、UR5e/H1-2、A100/RTX3090/Jetson、多义 DIGIT 的正负例检查。检查暴露的 ATLAS/ALOHA 局部约束问题已交 census 实现方修正；不能把词典完整性验证说成语义误报率为零。
- 仅新增本词典与本报告；未改 `data/equipment/devices.jsonl`、`usage-evidence.jsonl` 或论文身份/收录状态，未运行大构建。
- 原设备注册表 SHA-256：`94acab4d123660bf77b0a72092c962b039f807dffaa11a4ee4acc0175b724adf`。

## 审校结论

已纠正可确认的名称/代际归组风险，保留无法确证的系列级身份。本词典足以启动跨方向全库发现，并明确留存尚需正文证据验证的边界。没有新增任何“论文实际使用硬件”的确认事实。
