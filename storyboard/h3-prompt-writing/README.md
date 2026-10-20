# h3-prompt-writing

MiniMax H3 视频生成提示词编写 Skill。把文本、关键帧、参考图/视频/音频等多模态请求，改写成 H3 能直接执行的结构化提示词。

## 它解决什么

H3 有五种输入模式，每种的结构、字段顺序和参考标签都不一样。结构写错，模型不会报错，只会忽略你给的参考素材——画面看起来"生成了"，但角色不像、场景不对、音频没接上。

这个 Skill 把五种模式各自的输出结构固定下来，写提示词时只做填空和描述，不再靠记忆猜字段。

## 五种模式

| 模式 | 输入 | 用途 |
| --- | --- | --- |
| T2VA | 纯文本 | 从零构建完整视听时间线 |
| I2VA | 首帧图 + 文本 | 从首帧向前发展 |
| FL2VA | 首帧 + 尾帧 | 描述首尾之间的连续路径 |
| L2VA | 尾帧 + 文本 | 反推合理开场，收敛到给定尾帧 |
| Ref2VA | 参考图/视频/音频 + 文本 | 全能参考模式，角色、场景、音色可跨素材绑定 |

## 输出结构

**基础模式（T2VA / I2VA / FL2VA / L2VA）**，按顺序写三段：

- `integrated_multimodal_description`
- `overall_soundscape`
- `non_diegetic_music`

**全能参考模式（Ref2VA）**，按顺序写六段：

- `subject_definitions`
- `summary`
- `retention_analysis`
- `detailed_description`
- `overall_soundscape`
- `non_diegetic_music`

参考标签（`<Picture 1>`、`<Video 1>`、`<Audio 1>`）在所有段落里必须保持一致；对白、歌词、画面内的可见文字保留原始语言，其余正文用英文。

## 目录结构

```text
h3-prompt-writing/
├── SKILL.md                  # 主流程：识别模式 → 读取对应指南 → 按结构输出
├── references/
│   ├── base-en.txt           # T2VA / I2VA / FL2VA / L2VA 写作指南（222 行）
│   └── ref-en.txt            # 全能参考六段式格式指南（341 行）
└── agents/
    └── openai.yaml           # Codex 界面元数据（可选，不影响其他运行时）
```

## 使用方式

直接说需求即可，例如"把这段分镜改写成 H3 的 Ref2VA 提示词"，或"这张首帧图，往后推 8 秒"。

几条硬性习惯：

- 描述时长与请求时长对齐，H3 单段是 4–15 秒
- 每个镜头写清构图、主体、环境、动作、运镜、声音，以及参考素材生效的确切时点
- 不用"电影感""唯美"这类抽象词替代具体视觉信息
- 不写剧情摘要，不留未定义的参考标签

## 安装

克隆到用户级技能目录即可，三个运行时都认：

```bash
# DeepSeek Harness
git clone git@github.com:Weeexiao/h3-prompt-writing.git ~/.agents/skills/h3-prompt-writing

# WorkBuddy
git clone git@github.com:Weeexiao/h3-prompt-writing.git ~/.workbuddy/skills/h3-prompt-writing

# Codex
git clone git@github.com:Weeexiao/h3-prompt-writing.git ~/.codex/skills/h3-prompt-writing
```

## 与其他 H3 技能的分工

- **h3-prompt-writing**（本仓库）：管提示词的**结构与字段**，解决"H3 能不能听懂"。
- **minimax-h3-storyboard-director**：管**镜头设计与分镜规格书**，解决"这场戏怎么拍"。
- **audio-driven-mv**：管**整条 MV 的生产流程**，从分段音频到成片。

典型串联：分镜导演出分镜 → 本 Skill 把每个镜头写成 H3 提示词 → 生成或进 MV 流程。

## 说明

纯文档技能，无外部 API、无运行时依赖，不包含任何密钥或账号信息。
