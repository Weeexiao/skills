# Blender 技能路由与到位检查

DSH 内置 30 个 Blender 技能（1 个总编排 + 29 个领域模块），来源与许可见[溯源](#溯源与许可)。它们由 DSH 桌面 profile 的 `dsh-blender` 包注册，**不在本仓库**；本仓库只承载白模预演流程（`production/blender-previs/`）与这份路由表。

## 协作前：先确认技能到位

把 Blender 活交给 DSH 之前，按顺序确认。任一项不成立就先补齐，**不要假定 DSH 一定能做**。

### 1. 技能是否注册

在本会话技能目录里能按名字加载，就说明到位。抽查两个代表：

- `create-3d-model`（总入口）
- `blender-modeling`（最常用的领域模块）

加载得到内容 = 已注册；加载不到 = 该环境没有这套技能，改走"本机直接完成"或先装 `dsh-blender`。

### 2. Blender 本体是否可用

技能注册 ≠ Blender 能跑。调 `blender_status` 看两件事：

- `available` 为 `true`
- `version` 是真实版本号，而不是 `spawn blender ENOENT`

`available: false` 且 `version` 含 `ENOENT`，说明 **Blender 不在 PATH**。此时所有 `blender_*` 工具都会失败，技能写得再好也产不出文件。处理：把 Blender 目录加入 PATH，或在 bundle patch 里配置 `blenderExecutable` 指向实际可执行文件。

Windows 常见情况是 Blender 装在非默认盘（例如 `D:\Blender\blender.exe`）但从未加入 PATH。这类机器上"技能齐全"与"能出图"是两件事，必须分别验证。

### 3. 工作区与产物路径

Blender 工具的输入输出路径都在当前工作区内。委派前确认目标目录存在且可写，避免子代理在错误目录里产出后无法取回。

### 到位检查的最小结论

| 检查项 | 通过条件 | 不通过时 |
| --- | --- | --- |
| 技能注册 | 能加载 `create-3d-model` | 该环境无此套技能，改路线 |
| Blender 可用 | `blender_status.available == true` 且版本真实 | 配置 PATH 或 `blenderExecutable` |
| 路径可写 | 目标目录存在 | 先建目录再派单 |

三项全过才把 Blender 任务交出去。报告时区分"技能已注册"和"Blender 可运行"，不要用前者代替后者。

## 什么情况调用哪个技能

按任务意图查下表。技能名即 `skill` 工具的加载名。

### 总入口

| 技能 | 何时调用 |
| --- | --- |
| `create-3d-model` | 任何 3D 任务的默认入口：文本/图片/线稿/多视图/贴图/模板转模型，改现有场景，导 GLB/FBX/OBJ/USD/STL。它负责编排下列模块 |

不确定用哪个模块时，先加载 `create-3d-model` 让它分流，而不是猜。

### 核心领域

| 技能 | 何时调用 |
| --- | --- |
| `blender-modeling` | 建几何、硬表面建模、加修改器（Bevel/Subdiv/Boolean/Mirror/Array/Solidify）、bmesh 编辑、拓扑整理 |
| `blender-materials` | PBR 材质：金属、玻璃、塑料、布料、皮肤/蜡、程序化木纹/大理石/织纹 |
| `blender-lighting` | 三点光、HDRI、影棚/电影感/戏剧光、色温、软硬阴影 |
| `blender-cameras` | 焦段、构图、景深、跟踪、环绕、推轨、动画摄影机 |
| `blender-rendering` | Cycles/EEVEE 选择、采样、降噪、光路、色彩管理、静帧/序列/视频输出 |
| `blender-animation` | 关键帧、缓动、F-Curve、形态键、驱动器、NLA、循环 |
| `blender-export` | 导出 glTF/GLB、FBX、OBJ、USD、STL，轴向转换、贴图打包、减面、导出校验 |
| `blender-uv-texturing` | UV 展开/投影、图集、alpha 贴花、烘焙、光照图、glTF 贴图准备 |
| `wireframe-to-3d` | 二维三视图线稿 → 三维模型，输出 GLB |

### 参考锁定的 1:1 还原

源保真优先于"看着像"时才加载这一组。

| 技能 | 何时调用 |
| --- | --- |
| `reference-to-3d` | 参考图/模板/正交视图/贴图驱动的整体还原流程 |
| `reference-analysis-validator` | 源清单、掩膜、连通域、叠加图、IoU/SSIM、bbox、质心、导出前拦截 |
| `source-part-segmentation` | 把粘连或重叠的部件拆成结构掩膜 |
| `contour-to-mesh` | 轮廓/掩膜 → 实体网格或浅浮雕 |
| `orthographic-registration` | 前/侧/后/顶视图注册到统一坐标契约 |
| `multiview-constraint-solver` | 多视图互相矛盾时判定能否共用同一模型、选定基准视图 |
| `atlas-uv-fitting` | 贴图集分区检测，把每个部件映射到对应 UV 矩形 |
| `closed-surface-uv-coverage` | 封闭/挤出体的正反盖与侧壁贴图覆盖闸门 |
| `texture-driven-mesh-fitting` | 让网格边界贴合贴图轮廓，而不是硬拉伸贴图 |
| `landmark-fit-repair` | bbox/剪影不够用，要按具名特征点（叶尖、眼、笑口、边距）测量修复 |
| `multiview-fit-loop` | 渲染→比对→调整→再比对的闭环，直到各视图测量通过 |
| `fit-repair-optimizer` | 把校验失败转成有依赖顺序的修复队列 |
| `reference-look-calibration` | 对齐裁切、范围、亮度、饱和、色相、发光、材质与渲染设置 |

### 运动与动画质检

| 技能 | 何时调用 |
| --- | --- |
| `texture-state-animation` | 贴图/材质状态之间的过渡动画，避免整图淡入淡出、跳变、错位 |
| `orbital-hud-motion` | 光环、环形 HUD、扫描环、粒子点缀等克制的装饰运动 |
| `animation-quality-gate` | 交付动画前用接触表检查闪烁、剪影稳定性、构图、主体占比、层分离 |

### 编排与治理

| 技能 | 何时调用 |
| --- | --- |
| `blender-pro-workflow` | 跨多阶段的完整场景/主视觉，需要生产顺序、评审节奏与时间预算 |
| `blender-skill-harmonizer` | 多个模块要共用真值源、交接物、优先级或修复决策，或反复失败疑似技能打架 |
| `quality-refinement-autoloop` | 结果反复不达标，要把证据转成修复计划。**未经明确要求不要执行它里面的技能/发布改动** |
| `mascot-logo-reconstruction` | 品牌吉祥物、logo、扁平角色、徽标，需失败闸门式源匹配 |

### 推荐链路

- **通用建模或主视觉**：`blender-pro-workflow` → `blender-modeling` → `blender-cameras` → `blender-lighting` → `blender-materials` → `blender-rendering`，需要时 `blender-export`
- **改现有场景**：先查场景与物体状态 → 只加载受影响的模块 → 破坏性操作前存版本检查点 → 复验改动范围
- **线稿/工程图转 3D**：`blender-skill-harmonizer` → `reference-analysis-validator` → `wireframe-to-3d` →（多视图时）`orthographic-registration` + `multiview-constraint-solver` → `blender-modeling` → `multiview-fit-loop` → 材质/灯光/机位/渲染 → `blender-export`
- **精确吉祥物/logo/贴图包**：`blender-skill-harmonizer` → `mascot-logo-reconstruction` → `reference-to-3d` → `reference-analysis-validator` → `source-part-segmentation` → `contour-to-mesh` + `orthographic-registration` →（冲突时）`multiview-constraint-solver` → 贴图拟合与 UV 组 → 修复组 → `reference-look-calibration` → `blender-export`
- **白模预演**：`production/blender-previs/`（流程）+ `blender-modeling` + `blender-cameras` + `blender-animation` + `blender-rendering`

这些是默认顺序，不是必须全加载；不相关的闸门直接跳过。

## 辅助脚本

26 个 Python/Blender 辅助脚本通过 `blender_helper_catalog` 列清单、`blender_helper_run` 执行，不要猜包内路径。先查清单再传参。

## 精简建议

- 场景对象数多时用 `blender_rt_opt` 合并同材质同父级的对象，几何零损失。
- 反复渲染同一场景时开 `persistent_data`，避免每轮重新同步。
- 破坏性操作前用 `blender_rt_txn` 留快照；只是改 transform 用 `mark`/`revert` 更轻。

## 溯源与许可

技能栈源自 [RobLe3/cc-blender-skill](https://github.com/RobLe3/cc-blender-skill)（commit `11016c9`，release `1.3.0`，MIT），由 DSH 适配为 30 个可独立加载的技能，并对接 13 个打包工具与辅助脚本目录。

- 上游许可：MIT（Copyright (c) 2026 RobLe3）
- `dsh-blender` 包许可：MIT
- 本仓库不复制这 29 个模块的 `SKILL.md`，避免与本体注册重名和上游漂移；仓库只维护路由、到位检查与白模流程。

技能定义以目标机器实际注册的 `dsh-blender` 包为准。版本不同则模块清单可能增减，以 `blender_helper_catalog` 与实际可加载结果核实。
