# MiniMax H3 Ref2VA 格式与模式边界

## 固定结构

仅全能参考按以下六段输出。说明用英文，对白、歌词和可见文字保留原语言。无时间轴是本技能默认审阅样式；官方允许 Shot 和切点，实际节点要求时遵循其合约。歌曲数字人不使用本模板，见 [workflowSelection.md](workflowSelection.md)。

```text
subject_definitions:
...
summary:
...
retention_analysis:
...
detailed_description:
...
overall_soundscape:
...
non_diegetic_music:
None.
```

## 参考素材声明

按上传顺序声明，编号不可换义：

```text
<Subject 1> is Zhao Shu, preserving facial identity, hairstyle, age, build, and wardrobe from the reference.
<Picture 1> is the locked scene reference for layout, walls, windows, furniture, light direction, and palette.
<Video 1> is used only for the demonstrated body movement and camera rhythm.
<Audio 1> is the voice of <Subject 1> (S1), preserving vocal identity, timbre, cadence, age, and accent.
```

`<Subject N>` 用于角色；`<Picture N>` 用于场景、道具、服装或构图；`<Video N>` 用于动作、运镜、节奏或表演；`<Audio N>` 用于音色、语速、口音、情绪或环境声。说话人 `(S1)`、`(S2)` 全程不变。

## summary 与保留分析

summary 示例：

```text
[reference generation + audio reference] A cinematic live-action scene with precise identity, location, performance, voice ownership, and hard-cut continuity.
```

只写实际存在的参考类型。`retention_analysis` 对每项素材说明保留强度和用途：视觉使用 `fully_preserved`、`partially_preserved`、`attribute_transfer`、`weak_reference`；音频使用 `fully_copy`、`partially_copy`、`reference`、`weak_reference`。

```text
<Subject 1>: fully_preserved for facial identity, age, hairstyle, and build; partially_preserved for wardrobe when the script changes costume.
<Picture 1>: fully_preserved for architecture, furniture, light-source direction, color, and spatial anchors; weak_reference for exact framing.
<Audio 1>: reference - use the speaker's vocal identity and accent for the new dialogue without copying the original signal.
```

完整歌曲复用才使用 `<Audio 1>: fully_copy - use the complete source recording as the entire final soundtrack.`；只借音色不能写 fully_copy。复制部分音层、片段或另加声音用 partially_copy。定义中尽早说明歌曲或音色样本的角色，不要求把关键字置顶，也不把关键字当作程序开关。summary 对应 audio reuse 或 audio reference。

只用于身份或环境外观的图片在 Subject 内引用来源，不必另造 Picture；Picture 独立用于实际帧或构图锚点。Subject 也可表示场景、物件等可见内容，不能限定为人物。音频不强制绑定人物图：没有视觉 Subject 的旁白使用稳定声音描述加实际说话人编号；纯配乐不虚构说话人。

## detailed_description

写成连续、依次展开的英文电影调度。使用 `The scene opens...`、`Hard cut to...`、`The next composition...`、`On the following cut...` 表达构图变化。每次硬切后重新说明可见角色及数量、站位锚点、景别与焦段感、机位与构图、运镜方式及幅度、景深策略、单一纵深主层机制、表演动作、背景与光线连续、对白归属。固定镜头也要明确写为 stable static composition，并说明它承担强调、留白或对峙中的哪一种功能。

把中文分镜的运镜统计落实到 H3 描述：对话段落至少出现一个运动构图；运动镜头写明起点、路径、速度或晃动幅度、终点和情绪功能。重技法只有通过叙事理由、重锤资格和频率确认后才写入提示词。用户要求硬切或排除长镜头时，使用离散构图和 `Hard cut to...`，不使用一镜到底式描述。

把群像分级和状态账本同步到H3：A档构图明确可见总人数、每个角色的锚点位置与动作；B档只锁当前主体，并说明其余人物由构图裁切或留在可辨／虚化背景。每个新构图继承上一构图的镜尾状态，尤其核对左右手占用、道具数量和朝向、动作完成度、服装、背景结构、主光方向与跨镜声音。

对话先建立空间关系并保留双人同框，面部近景和特写保持克制。长台词优先让说话人的声音在有意义的物件、局部肢体、环境、光影或反应局部上画外延续，并用同一 `(Sx)` 保持说话归属。情绪重锤之后描述一个节奏明显放缓的留白构图，默认审阅版不写时长；执行格式需要明确切点时据实际音频安排。

```text
(S1), visible on camera with synchronized lips: <d>[Chinese] 台词原文</d>
(S2), heard off-screen while the visible listener keeps their lips closed: <d>[Chinese] 台词原文</d>
```

切到听者而说话者继续画外音时，明确听者嘴唇闭合，只用眼神或身体反应。用一次清楚的正向指令，不反复堆叠禁令。

## 重复人物与连续性

```text
Only one instance of <Subject 1> is present in the composition. The same person continues from the previous composition, entering through the anchored doorway and stopping beside the same table.
```

同场景硬切锁定建筑、墙面、门窗、家具、光源、时间、天气、服装、发型、人物关系、视线轴和动作状态。起始帧负责当前构图，场景资产图负责空间背景，在保留分析中分开说明。

## 声音

`overall_soundscape` 写对白、动作声、环境声和空间声学，让声音跟随镜头并保持音色稳定。无参考音频时描述自然音色供 H3 生成。默认不添加字幕、旁白或音乐。`non_diegetic_music` 在普通无配乐剧情中写 `None.`（节点要求 N/A 时按接口）；已有歌曲复用时写仅保留原伴奏。歌词与具体发声写在 detailed_description，环境与物理声音放 overall_soundscape，观众可闻配乐放 non_diegetic_music，不重复整段歌词。完整原音轨复用时不再另加环境、脚步或新配乐。
