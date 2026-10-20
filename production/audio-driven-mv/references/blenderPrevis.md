# Blender 白模参考视频工作流


此参考的 H3 视频连线与六段声明仅适用于支持视频输入的全能参考路线。默认音乐数字人不连接白模视频，只接最终构图图和原歌曲音频；白模仍可用于人工预演。

## 适用范围与输入

用户需要分镜预演、构图或走位验证时使用。读取当前角色资产、场景图、分镜参考图、原 WAV 及已确认唱词。先问清当前是否只制作预演，还是授权预演之后生成 H3；制作白模本身不自动扩大付费生成范围。

输出是镜头验证用的低精度动画，不是最终角色建模或口型动画。不用白模时可直接采用参考图加原音频的路径。

## 1. 分析与确认

先输出简短搭建计划，内容包括：

| 项目 | 明确内容 |
| --- | --- |
| 人物 | 数量、关系、每人的纯色标记，全片保持一致 |
| 空间 | 地面尺度、墙门窗、台阶、桌椅及重要障碍物 |
| 动作 | 起始姿势、关键姿势、移动方向、路径与停顿 |
| 镜头 | 景别、焦段或视角、机位、朝向、运镜、主体画面位置 |
| 时间轴 | 原 WAV 时长、动作转折时点、摄影机运动起止 |

确认人物配色与时间轴后制作，已有明确确认不重复询问。动作时点只是预排时应注明，不能声称已逐字或逐拍校准。每段一个连续镜头，只描述本段场景。

## 2. 从参考图搭建

先制作或读取定妆、场景与当前镜头参考图，再还原三维站位、层次、距离与构图。记录坐标约定，例如 Z 向上、主角朝 -Y、镜头在 -Y；不要复制旧项目的绝对坐标。

- 人物用球、胶囊、圆柱等低精度几何体组成，可加简单轮廓标记区分身份，不做五官、服装、毛发和写实细节。
- 人物或阵营以不同纯色区分；“白模”不要求所有物体同白色。场景以灰白体块、设备以深灰表现。
- 只保留影响遮挡、走位或构图的物体。桌子、话筒、防喷罩、墙、门窗、台阶可简化为基础几何体。
- 话筒中心对齐角色嘴部估计高度，防喷罩避开脸部轮廓；不能默认成人话筒高度。
- 外景应有真实可行走的地面和墙体边界；行走路径平行墙面并留距离，摄影机不穿过墙、窗或角色。

## 3. 关键帧与机位

只做必要的姿势变化、位移、朝向和摄影机关键帧，省略复杂表演、步态模拟、布料、毛发及物理模拟。人物没有面部，不能用它验证闭眼、眉头或嘴型。

设原音频时长为 D，帧率为 F。使用 `frameStart = 1`、`frameEnd = ceil(D * F)`，把 t 秒事件映射为 `1 + round(t * F)` 并夹到范围内。整帧取整使预演视频可能略长于音频，记录真实时长，不拉伸原音频。

路径匀速跟拍适合 LINEAR；停下、抬手及缓推可用受控 BEZIER。检查曲线是否过冲，让人物撞墙或摄影机穿模。摄影机保持指定方向，不因自动跟踪出现意外绕拍；必要时用 Empty 作为稳定注视目标。

每段独立场景或工程；保存前检查场景名，避免清空用户已有工程。使用 MCP 时先查询现有场景，在独立场景内搭建；不要直接重置整个 Blender 文件。

## 4. 预览、保存与渲染

优先 Workbench 或低成本 Eevee，材质使用纯色和简单工作室灯光，不做高精度渲染。建议竖屏 720×1280、24或30fps，具体沿用当前项目要求。

先渲染首、中、末及关键转折帧，检查景别、主体大小、站位、遮挡、人物和话筒高度、路径及摄影机边界；通过后再渲染全段。

保存 `previs.blend` 与按当前镜头编写的 `buildPrevis.py`，脚本通过参数或配置接收输出目录，不绑定旧电脑盘符。Blender 中使用 bpy Python 是其原生 API，此步骤不使用 TypeScript 替代。

后台重建示例（脚本需自行实现 `--output` 参数）：

```powershell
blender --background --python buildPrevis.py -- --output "项目目录/segmentOne"
```

为适配 Blender 不同版本，优先渲染 PNG 帧序列，再由 FFmpeg 编码，避免依赖特定版本的 Blender 视频编码选项：

```powershell
ffmpeg -framerate 30 -start_number 1 -i "frames/frame%04d.png" -c:v libx264 -crf 20 -pix_fmt yuv420p -movflags +faststart previsSilent.mp4
```

帧率和编号与实际渲染一致；示例从第1帧开始。可另存一份带原 WAV 的审片版：

```powershell
ffmpeg -i previsSilent.mp4 -i audio.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -shortest -movflags +faststart previsReview.mp4
```

这里给白模审片配原音频是为了验证时间关系，不是给 H3 成片换轨。推荐把无声版作为 H3 运动参考；若使用带声版，必须显式忽略其声音。检查实际流时长，不强求毫秒长度与整帧数量同时完全相等。

## 5. 导入 Toonflow 与 H3

把分镜图、角色图、原 WAV、白模 MP4、工程和脚本复制到项目工作区；媒体用相对路径设置。创建分镜图节点、预演视频节点、音频节点、提示词说明节点及 H3 节点，再连接本段必需的媒体。

新增视频参考后引用序号会变化。不能假设音频仍是 `{{ref 2}}`。例如实际映射若是图片1、白模视频2、音频3，则全篇统一采用这个映射，并通过 validatePrompt 检查编译结果。

在现有六段 H3 格式中加入对应声明，例如：

```text
subject_definitions:
{{ref 1}} Final singer appearance — Character identity, outfit, finished 3D style and the single setting for this clip.
{{ref 2}} Graybox motion reference — Only composition, blocking, camera trajectory, timing and coarse body gestures. Its primitive shapes, flat colors and any soundtrack are not final appearance or audio.
{{ref 3}} Original segment recording — The sole final vocal and accompaniment, sung by {{ref 1}} (S1).

retention_analysis:
{{ref 1}}: fully_preserved for identity and final appearance.
{{ref 2}}: partially_preserved for motion and camera only; replace all primitive models with the finished singer and environment. Ignore its audio entirely.
{{ref 3}}: fully_copy, preserving all original vocal and accompaniment timing from 0.000 seconds.
```

其余 summary、detailed_description、overall_soundscape、non_diegetic_music 仍须齐全，并按实际音频编号写逐字唱词和复制声音指令。图像不足以定义最终环境时可另接场景图，重新核对全部编号。

最终角色表情、口型与原唱按独立音频执行，不让白模无口型或固定面部覆盖演唱。禁止把白模当作最终视觉风格，或把它的审片声音当成第二条音频源。

## 6. 验收与迁移

保留计划、参考图、.blend、重建脚本、帧序列或代表帧、预演 MP4、原 WAV、H3 提示词、原生输出及裁尾版。记录帧率、尺寸、参考时长、预演实际时长和引用映射。

白模验证空间和运动；H3 成片仍需人工检查口型、表情、不看镜头要求及场景连续性。迁移电脑时复制工程和资产，不仅复制预演 MP4；仅上传 Skill 不能携带这些工程。当前仓库不包含个人 Blender 工程、歌曲或视频。
