# 草图绘制规范

## 目标

每张图只解释一个镜头组的拍法。优先清楚，不追求精美，不把多个互不相干的镜头塞进同一张图。

## 默认视觉语言

- 黑白铅笔或马克笔手绘分镜，白色纸张背景，低细节、清晰轮廓。
- 默认横向 16:9；竖屏项目使用 9:16。按用户的发布平台决定。
- 不含文字、字幕、品牌、logo、片名、页码或水印。
- 画出主体位置、前中后景关系、关键道具、视线/行动方向；确有必要才用简单箭头表示镜头运动。
- 同一项目的人物外观、地点与光线方向保持一致。用户未提供人物图片时，以不具辨识度的简笔角色呈现。

## 单镜头组提示词骨架

```text
Use case: illustration-story
Asset type: short-film storyboard frame
Primary request: [镜头组的叙事任务]
Scene/backdrop: [场地与关键物件]
Subject: [人物数量、位置、动作、朝向]
Style/medium: simple monochrome hand-drawn storyboard sketch, clear pencil or marker lines
Composition/framing: [16:9 或 9:16] [景别] [机位/角度] [前中后景] [镜头运动箭头，如需]
Lighting/mood: [情绪与光线]
Constraints: one coherent shot group only; no text, no captions, no logos, no watermark; readable composition over detail
```

不要让图像模型生成多格漫画、分镜编号或文字说明；这些内容由脚本正文承担。用户明确要求单场景故事板时，先逐格生成 6 张或 9 张独立草图，再按 3×2 或 3×3 合成为总览；总览必须同时保留每格的文字说明。具体格数判断和连续性规则见 [单场景故事板规范](single-scene-storyboards.md)。

## 生成与交付

- 使用图像生成工具时，每次只生成一个镜头组或故事板格；不要把彼此独立的场景交给同一张图，也不要一次生成完整九宫格。
- 先展示生成的草图，再把选中的最终草图保存到当前项目可交付的位置；需要时在脚本中以 Markdown 图片直接显示。
- 草图若遗漏构图重点、画成多格漫画、带有文字或无法读出人物动作，针对该问题重试一次。
- 不用拉片原片截图充当用户项目的分镜图，也不把生成草图伪称为实拍画面。

## 与秋拾方法库的关系

内置秋拾方法库只提供镜头语言与结构方法。新草图必须围绕当前用户的场地、人物、道具和条件重新绘制，不模仿参考片画面、角色造型、logo、文案或独特美术设计。
