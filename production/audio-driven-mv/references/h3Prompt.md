# 按实际工作流编写提示词

先读节点 getConfig，按下面模式选模板。英文是全能参考官方规范及本技能的默认正文语言，中文成功样本不证明语言等效；六段式用于匹配接口，不能保证音轨或口型。中文歌词保持人工核准原文，不翻译后让模型重唱。

## 默认：歌曲音频驱动数字人

输入为一张合成好的身份、服装、场景、构图参考图，加一份完整原唱及伴奏音频。原始角色图和场景图用于制作这张图，不再作为额外图片输入。不要接白模、额外音色或整段文本节点。当前 h3DigitalHuman 使用普通动作描述，不能套六段、三段或 H3 引用标签。确认歌词用于人工核查，实际音频驱动发声时序。

```text
Animate the singer in the supplied image using the complete supplied song audio. The original audio is the master clock for all lip and jaw motion. Follow each vocal onset, syllable, consonant closure, vowel length, breath and pause at its original timing. Preserve the original performance and accompaniment without re-singing or retiming.

Maintain the singer's identity, outfit and the reference location. [Describe the approved expression and gaze.] Keep the mouth clearly visible.

[Describe the shot size, composition, physical camera path and performance.] Let gestures follow the actual sung phrase naturally, without imposing a separate gesture timeline.
```

外景正面跟随示例：人物持续向前走，摄影机位于人物前方等速后退，头肩与上臂保持入画，街景相对人物向后移动；允许直视镜头时明确写出。不要把侧向平移误写成正面后退跟拍。机位不能穿墙，路径避开障碍。

室内示例：人物开场即在棚内，话筒位于嘴部高度且不遮口型，明确静止机位或轻微上摇，不混入街景。视线按用户要求，不固定要求闭眼或不看镜头。

## 全能参考：需要多图、视频运镜或白模

该模式当前通常为 h3-video / h3VoidFold，必须先核对实际输入预算和引用映射。把定义绑定到 validatePrompt 的真实标签；以下两输入 token 仅为示例。加入白模后按实际顺序重排，声明白模只提供动作与运镜、不提供声音或最终外观。

```text
subject_definitions:
{{ref 2}} Original song recording — The complete original vocal and accompaniment, reused as the sole final soundtrack for the visible singer (S1).
{{ref 1}} Singer and composition reference — [identity, outfit, approved location and framing].

summary:
[reference generation + audio reuse] The singer performs in the approved location, with lip movements following the original recording.

retention_analysis:
{{ref 2}}: fully_copy - use the complete original recording as the entire final soundtrack, preserving its timing, pitch, vocal performance and mix.
{{ref 1}}: fully_preserved - retain identity, wardrobe and the defined scene anchors while allowing the planned camera movement.

detailed_description:
[Shot 1] [Visual style, visible singer, composition, lighting, action and feasible camera movement.] {{ref 1}} (S1) sings <d>[Chinese]人工核准的逐字唱词。</d> following the original syllable timing in {{ref 2}}. Gestures follow the actual vocal phrase without retiming the song.

overall_soundscape:
No additional ambience or effects are mixed into the copied soundtrack.

non_diegetic_music:
Use only the existing accompaniment within {{ref 2}}, with its original balance and timing.
```

音频定义靠前只是让意图清晰，不是程序开关；`fully_copy` 在 retention_analysis 中明确一次，后文保持一致即可。不要同时写“参考曲风重新演唱”、新配乐或额外脚步声。多镜头按已确认切点描述并保持音频连续；单镜不要添加多余 Shot。具体类型与跨切声音见 [workflowSelection.md](workflowSelection.md)。

## 首尾帧与普通生成

FL2VA 用真实首帧、尾帧与当前工作流要求的时长；T2VA/I2VA/L2VA 使用对应普通视频模式。上述模型的官方扩写通常为 integrated_multimodal_description、overall_soundscape、non_diegetic_music 三段，不能用全能参考六段替代。没有实际 drivingAudio 能力时，不能承诺原曲驱动口型；首尾图也不保证中间口型对齐。
