<script setup lang="ts">
import { withBase } from 'vitepress'
import { eventDate } from '../lib/dates'

defineProps<{ device: any; categoryLabel?: string; expanded?: boolean; provisionalMonth?: string }>()
const emit = defineEmits<{ papers: [hardwareId: string]; sources: [open: boolean] }>()
const roleLabels: Record<string, string> = { real_robot: '真机使用', simulated_robot: '仿真机器人', training_compute: '训练算力', inference_compute: '推理算力', control_compute: '控制计算', model_fitting_compute: '模型参数拟合', experiment_compute: '实验计算（环节未细分）', data_collection: '数据采集', sensing: '感知', dataset_source: '数据来源' }
const settingLabels: Record<string, string> = { real: '真实设备', simulation: '仿真环境', dataset: '数据集', unknown: '环境未说明' }
const scopeLabels: Record<string, string> = { baseline: '仅对照基线', calibration: '仅标定 / 校准', replay: '仅轨迹回放', replay_only: '仅轨迹回放' }
const validationLabels: Record<string, string> = { closed_loop_real: '真机闭环', replay_only_real: '真机仅回放', simulation_only: '仅仿真', unclear: '验证方式未明确' }
const validationContextLabels: Record<string, string> = { real_to_sim_trajectory_replay: '真实轨迹采集→仿真回放，不等于策略真机闭环', real_robot_closed_loop: '真机闭环', real_robot_closed_loop_offline_reference: '真机闭环；离线参考', real_robot_closed_loop_with_operator_supervision: '真机闭环；操作员监督', real_robot_trajectory_replay: '真机轨迹回放，不等于真机闭环策略验证', simulation_and_real_trajectory_replay: '仿真与真机轨迹回放，不等于真机闭环策略验证', simulation_and_real_robot_closed_loop: '仿真与真机闭环', simulation_only: '仅仿真' }
const hasContext = (device: any, contexts: string[]) => device.sources.some((source: any) => source.usages.some((usage: any) => contexts.includes(usage.validation_context)))
Object.assign(validationContextLabels, {
  closed_loop_real: '真机闭环；具体控制与验证条件见下方出处',
  measurement_calibration: '真实测量与离线标定，不等于在线完整状态验证',
  planned_trajectory_execution_feedback_not_established: '真机执行规划轨迹；在线反馈重规划尚未验证',
  planning_computation_benchmark: '规划计算评测，不等于训练或机载部署',
  learned_alignment_then_demonstration_replay: '学习接近阶段，再回放示教完成末段',
  gravity_compensation_demonstration_collection: '重力补偿模式下的引导示教采集',
  eye_in_hand_alignment_visual_input: '眼在手上视觉输入；末段改用回放',
  deployed_policy_workstation: '策略部署工作站，不等于机载GPU',
  human_operated_dual_robot_teleoperation: '人类低层遥操作双机器人，不是自主策略',
  VR_teleoperation_input_not_policy_training: 'VR遥操作输入，不代表已训练或发布策略数据',
  tablet_teleoperation_baseline: '平板遥操作对照组',
  onboard_RGBD_for_exocentric_teleoperation: '机载RGB-D构建遥操作外部视角',
  gripper_camera_close_up_teleoperation: '夹爪相机提供遥操作近景',
  LiDAR_ICP_inter_robot_alignment: '机载LiDAR用于双机器人坐标配准',
  depth_completion_inference_and_VR_rendering: '深度补全推理与VR渲染，型号未明确',
  physiology_recording_not_real_time_robot_adaptation: '生理数据研究记录，不实时调节机器人',
  web_orchestration_and_local_browser_processing: '网页编排与轻量本地处理；LLM由云端调用',
  audiovisual_research_recording_not_speech_input: '音视频研究记录，不代表支持语音输入',
  external_camera_for_user_study_recording: '外置相机记录用户研究，不是机器人视觉输入',
  alternating_dual_arm_multiview_data_acquisition: '双臂交替移动采集多视角，不是同时操作',
  RGBD_IR_dataset_capture_with_calibrated_camera_poses: '标定相机位姿下的RGB-D/红外数据采集',
  epoch_specific_hand_eye_and_cross_arm_calibration: '安装时期限定的手眼与跨臂标定',
  real_robot_qualitative_transfer_only: '真机定性迁移展示，不提供可靠性估计',
  simulation_quantitative_policy_evaluation: '仿真策略定量评估，不是真机成功率',
  offline_policy_training: '离线策略训练',
  real_robot_policy_visual_input: '真机策略视觉输入',
  real_robot_closed_loop_with_manual_initialization: '真机闭环；需要人工初始化',
  fixed_wrist_mount_not_active_arm_policy: '固定手腕支撑，不代表策略主动控制机械臂',
  real_robot_object_pose_estimation: '真机物体位姿估计',
  camera_extrinsic_startup_calibration: '运行开始时的相机外参标定',
  deployment_workstation_allocation_unspecified: '部署工作站配置；各模块分工未明确',
  simulation_hand_morphology_comparison: '仿真手型比较，不是真手部署',
  real_robot_object_tracking_and_reconstruction: '真机物体跟踪与重建',
  simulation_policy_training: '仿真策略训练',
  real_deployment_compute_allocation_unspecified: '真实部署计算配置；环节未细分',
  evaluation_ground_truth_mesh_acquisition: '评测真值网格采集，不是在线感知输入',
  low_level_reorientation_tactile_input_only: '仅低层转动策略使用触觉，重建不直接融合',
  real_field_soil_manipulation_with_calibrated_supervisor: '现场土体操作；使用标定接口与传统上层控制',
  real_tabletop_soil_manipulation_with_interface_calibration: '桌面土体操作；需要接口标定',
  modified_arm_as_tabletop_excavator_base: '改装机械臂作为桌面挖掘平台基础',
  tabletop_terrain_height_scanning: '桌面地形高度扫描',
  offline_soil_policy_training: '离线土体交互策略训练',
  simulation_throughput_benchmark: '仿真吞吐测试，不是机载推理',
  onboard_machine_control_interface: '机载机器控制接口',
  field_terrain_and_machine_pose_sensing: '现场地形与机器位姿感知',
  real_brachiation_with_manual_command_switches: '真机横杆移动；人工切换指令',
  real_brachiation_with_goal_and_passive_hooks: '真机横杆移动；操作员指定目标、使用被动挂钩',
  onboard_lidar_for_sparse_structure_control: '机载激光雷达用于稀疏结构感知控制',
  'real_handheld_demonstration_capture_and_teleoperation_input;not_autonomous_robot_execution': '手持示教采集与遥操作输入，不是自主执行',
  'real_robot_gripper_in_reported_policy_execution_and_force_characterization;success_rate_not_reported': '真实夹爪执行与力度评测；策略成功率未报告',
  'real_policy_execution_with_impedance_control;rollout_count_and_success_rate_not_reported': '阻抗控制下真实策略执行；次数和成功率未报告',
  'real_capture_device_pose_sensing;not_a_claim_of_robot_execution_sensor_installation': '采集器位姿感知；不代表同款设备用于机器人执行',
  'real_gripper_system_multiview_visual_input;individual_capture_execution_unit_counts_not_separately_reported': '夹爪系统多视角输入；采集端与执行端数量未分别说明',
  'real_bench_force_parity_measurement_only;not_closed_loop_policy_sensor;not_sensor_calibration': '仅台架力度对照测量，不是策略反馈或传感器校准',
  manual_discrete_command_input_not_demonstration_capture: '人工离散指令输入，不是动作示范采集',
  real_granular_terrain_locomotion: '真机颗粒地形运动',
  offline_teacher_student_policy_training: '离线教师—学生策略训练',
  real_manipulation_reported_model_identity_pending: '真实操作；如报型号的厂商身份待核',
  experimental_GPU_allocation_not_fully_separated: '实验GPU配置；模块分配未明确',
  real_perceptive_control_with_task_specific_policies: '真机感知控制；分别训练任务策略',
  offline_training_across_alternative_GPUs: '不同GPU条件下的离线训练',
  real_robot_synchronous_chunk_control: '真机同步动作块控制',
  real_robot_synchronous_policy_inference: '真机同步策略推理',
  simulation_world_model_and_policy_evaluation: '仿真世界模型与策略评测',
  real_robot_recordings_for_offline_world_model_evaluation: '真实机器人轨迹采集，供离线世界模型评测',
  offline_world_model_training: '离线世界模型训练',
  world_model_generation_inference_benchmark: '世界模型生成推理测试，不是完整控制闭环',
})
const vendorLabels: Record<string, string> = { unknown: '厂商未明确', authors: '作者自建平台' }
const roleWorkCount = (device: any, role: string) => device.sources.filter((source: any) => source.usages.some((usage: any) => usage.role === role)).length
const computeRoles = ['training_compute', 'inference_compute', 'control_compute', 'model_fitting_compute', 'experiment_compute']
const publicUrl = (value: unknown): string | undefined => typeof value === 'string' && /^https?:\/\//i.test(value) ? value : undefined
const workUrl = (source: any) => publicUrl(source.original_url) || withBase(`/database/?${new URLSearchParams({ work: source.work_id, relevance: 'all' })}`)
const configurationText = (value: unknown) => value == null || value === '' ? '' : typeof value === 'string' ? value : JSON.stringify(value)
</script>

<template>
  <article class="hardware-model" :class="{ 'is-unresolved': device.identity_level !== 'model_specified' }" tabindex="-1">
    <header>
      <div class="model-identity"><h3>{{ device.name }}</h3><p>{{ categoryLabel || device.category }}<span v-if="device.vendor"> · {{ vendorLabels[device.vendor] || device.vendor }}</span></p></div>
      <div class="model-frequency"><strong>{{ device.work_count }}</strong><span>项研究使用</span></div>
    </header>
    <p v-if="device.identity_level !== 'model_specified'" class="identity-boundary"><strong>{{ device.identity_level === 'family_only' ? '系列 · 具体版本待明确' : '型号未公开' }}</strong> · 不计入具体型号榜，不根据当前产品名补推代际。</p>
    <div class="model-settings"><template v-if="device.category === 'compute_platform'"><template v-for="role in computeRoles" :key="role"><span v-if="roleWorkCount(device, role)">{{ roleLabels[role] }} {{ roleWorkCount(device, role) }}</span></template><span v-if="!computeRoles.some(role => roleWorkCount(device, role))">计算设备使用 {{ device.work_count }}</span></template><template v-else><span>真机 / 真实设备 {{ device.real_work_count }}</span><span>仿真 {{ device.simulation_work_count }}</span></template><span v-if="device.baseline_work_count">含对照基线 {{ device.baseline_work_count }}</span><span v-if="device.calibration_work_count">含校准 {{ device.calibration_work_count }}</span><span v-if="hasContext(device, ['real_robot_trajectory_replay', 'simulation_and_real_trajectory_replay'])">含真机轨迹回放</span><span v-if="hasContext(device, ['real_robot_closed_loop_offline_reference'])">含离线参考条件</span></div>
    <div class="model-actions"><button type="button" @click="emit('papers', device.hardware_id)">查看 {{ device.work_count }} 项研究卡片</button><a v-if="publicUrl(device.official_url)" :href="device.official_url" target="_blank" rel="noopener noreferrer">身份依据 ↗</a></div>
    <details class="model-sources" :open="expanded" @toggle="emit('sources', ($event.target as HTMLDetailsElement).open)">
      <summary>完整论文出处与使用证据 · {{ device.sources.length }} 项研究 / {{ device.source_count }} 条来源</summary>
      <p v-if="device.aliases?.length" class="model-aliases">检索别名：{{ device.aliases.join(' · ') }}</p>
      <ol class="source-list">
        <li v-for="source in device.sources" :key="source.work_id">
          <h4><a :href="workUrl(source)" :target="publicUrl(source.original_url) ? '_blank' : undefined" rel="noopener noreferrer">{{ source.title || source.work_id }}</a></h4>
          <p class="source-date">首次公开 {{ eventDate(source.first_public_date, source.first_public_date_precision) }}<span v-if="source.first_public_date?.slice(0, 7) === provisionalMonth" class="provisional-label">暂行月份</span></p>
          <section v-for="(usage, i) in source.usages" :key="usage.usage_id || i" class="source-usage">
            <p class="usage-meta"><span>{{ roleLabels[usage.role] || usage.role || '用途未明确' }}</span><span>{{ settingLabels[usage.setting] || settingLabels.unknown }}</span><strong v-if="scopeLabels[usage.usage_scope]">{{ scopeLabels[usage.usage_scope] }}</strong><strong v-if="validationLabels[usage.validation]">{{ validationLabels[usage.validation] }}</strong></p>
            <p v-if="usage.validation_context" class="validation-context">实验背景：{{ validationContextLabels[usage.validation_context] || usage.validation_context }}</p>
            <p class="source-statement">{{ usage.statement || '原文说明待补充' }}</p>
            <p v-if="configurationText(usage.configuration)" class="source-configuration">配置 / 条件：{{ configurationText(usage.configuration) }}</p>
            <p class="source-location">原文定位：{{ usage.source_locator || '未提供定位' }}<span v-if="usage.reviewed_at"> · 复核 {{ eventDate(usage.reviewed_at) }}</span><span v-else-if="usage.observed_at"> · 记录日期 {{ eventDate(usage.observed_at) }}</span></p>
            <p v-if="usage.reviewed_at && usage.observed_at" class="source-location">来源记录 {{ eventDate(usage.observed_at) }}<span v-if="usage.extends_review_id"> · 后续增补复核，原记录保留</span></p>
            <a v-if="publicUrl(usage.source_url)" class="source-url" :href="usage.source_url" target="_blank" rel="noopener noreferrer">{{ usage.source_url }} ↗</a>
            <p v-else class="source-location">原文链接暂未提供，不从设备名称补猜。</p>
          </section>
        </li>
      </ol>
      <p class="source-note">保留原文中的基线、标定、数据采集或轨迹回放条件；“真机使用”不自动等于自主闭环验证。</p>
    </details>
  </article>
</template>

<style scoped>
.hardware-model { min-width: 0; border: 1px solid var(--vp-c-divider); border-radius: 12px; padding: 18px 20px; background: var(--vp-c-bg); scroll-margin-top: 100px; }
.hardware-model :is(h3, h4, p, a, span, summary) { overflow-wrap: anywhere; }
.hardware-model > header { display: flex; gap: 20px; align-items: flex-start; justify-content: space-between; }
.model-identity { min-width: 0; }
.model-identity h3 { font-size: 20px; margin: 0 0 6px; line-height: 1.4; }
.model-identity p { margin: 0; font-size: 12px; color: var(--vp-c-text-2); }
.model-frequency { display: flex; flex-direction: column; align-items: flex-end; flex: none; }
.model-frequency strong { font-size: 30px; line-height: 1.2; font-weight: 600; color: var(--vp-c-brand-1); }
.model-frequency span { margin-top: 4px; font-size: 12px; color: var(--vp-c-text-2); }
.model-settings, .model-actions, .usage-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 7px 15px; }
.model-settings { margin: 14px 0 6px; font-size: 12px; color: var(--vp-c-text-2); }
.model-settings span { background: var(--vp-c-bg-soft); border-radius: 4px; padding: 3px 7px; }
.model-actions { font-size: 13px; }
.model-actions button { cursor: pointer; min-height: 44px; padding: 5px 0; color: var(--vp-c-brand-1); }
.model-actions a { display: inline-flex; align-items: center; min-height: 44px; }
.model-sources { border-top: 1px solid var(--vp-c-divider); margin-top: 6px; }
.model-sources summary { cursor: pointer; padding: 12px 0 2px; min-height: 44px; font-size: 13px; line-height: 1.7; }
.identity-boundary { margin: 12px 0 4px; color: var(--vp-c-text-2); font-size: 12px; line-height: 1.7; }
.identity-boundary strong { font-weight: 500; color: var(--vp-c-text-1); background: var(--vp-c-warning-soft); padding: 3px 6px; border-radius: 4px; }
.hardware-model.is-unresolved { border-left: 3px dashed var(--vp-c-warning-1); }
.model-aliases, .source-note { font-size: 12px; color: var(--vp-c-text-2); line-height: 1.7; }
.source-list { padding-left: 21px; margin: 14px 0 0; }
.source-list > li { padding: 0 0 18px 4px; margin-bottom: 18px; border-bottom: 1px solid var(--vp-c-divider); }
.source-list > li:last-child { margin-bottom: 0; }
.source-list h4 { font-size: 15px; line-height: 1.6; margin: 0 0 5px; }
.source-date, .source-location, .source-configuration { font-size: 12px; line-height: 1.7; color: var(--vp-c-text-2); margin: 5px 0; }
.source-usage { padding: 10px 13px; margin-top: 10px; background: var(--vp-c-bg-soft); border-radius: 6px; }
.usage-meta { font-size: 12px; margin: 0; color: var(--vp-c-text-2); }
.usage-meta strong { color: var(--vp-c-text-1); font-weight: 600; }
.source-statement { font-size: 13px; line-height: 1.75; margin: 8px 0; }
.validation-context { font-size: 12px; line-height: 1.7; margin: 7px 0; color: var(--vp-c-text-1); }
.source-url { display: block; font-size: 12px; line-height: 1.7; margin-top: 5px; }
.provisional-label { margin-left: 7px; padding: 2px 5px; border: 1px dashed var(--vp-c-warning-1); border-radius: 3px; }
.hardware-model :is(button, a, summary, [tabindex]):focus-visible, .hardware-model:focus-visible { outline: 3px solid var(--vp-c-brand-1); outline-offset: 3px; }
@media (max-width: 550px) { .hardware-model { padding: 15px; } .model-identity h3 { font-size: 18px; } .model-frequency strong { font-size: 26px; } .model-frequency span { max-width: 66px; text-align: right; } .source-usage { padding: 10px; } }
</style>
