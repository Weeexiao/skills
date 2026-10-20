# Skills 合集

AI 短剧制作全流程的 Agent Skills 合集，按生产环节分类存放。

每个技能是一个自包含目录：`SKILL.md`（技能定义与流程）+ `README.md`（用途、安装、边界）+ 可选的 `references/`、`scripts/`、`agents/`。

## 目录结构

```text
skills/
├── README.md                          # 本文件：总索引
├── scriptwriting/                     # 剧本与选题
│   ├── shortdrama-topic-script/
│   ├── pov-shortdrama/
│   └── crowd-scale-shorts/
├── storyboard/                        # 分镜与提示词
│   ├── minimax-h3-storyboard-director/
│   ├── h3-prompt-writing/
│   └── qiushi-ai-script-director/
├── assets/                            # 场景与图像资产
│   ├── ai-short-drama-scene-assets/
│   └── gemini-image-gen/
├── production/                        # 成片制作
│   └── audio-driven-mv/
└── tooling/                           # 工程与协作
    └── dsh-orchestrator/
```

## 技能索引

### 剧本与选题 · `scriptwriting/`

| 技能 | 解决什么 | 典型触发 |
| --- | --- | --- |
| [shortdrama-topic-script](scriptwriting/shortdrama-topic-script/) | 系列短剧从「下一集拍什么」到能配音的剧本：机制台账防撞车、五维加权选题材、时长预算与台词台账、片段切分 | "选个新一集题材"、"这个骗局能不能拍"、"把选题写成剧本" |
| [pov-shortdrama](scriptwriting/pov-shortdrama/) | POV 第一人称「成功人生」爽文短剧剧本，输出 Toonflow 短剧模板格式；主角零正脸、三类镜配比、五幕爽点曲线 | "XX POV"、"第一人称分镜"、"逆袭剧本"、"体验不同人生" |
| [crowd-scale-shorts](scriptwriting/crowd-scale-shorts/) | 「离谱人数」荒诞生活系列短片：参考片拆解、选题避重、人数后果递进、人物对白与 AI 分镜 | "假如某个场景有离谱人数"、"人数放大的生活喜剧" |

### 分镜与提示词 · `storyboard/`

| 技能 | 解决什么 | 典型触发 |
| --- | --- | --- |
| [minimax-h3-storyboard-director](storyboard/minimax-h3-storyboard-director/) | 剧本 → 中文电影分镜规格书 + MiniMax H3 Ref2VA 六段式提示词；镜头语言、运镜多样性、景深与纵深、台词逐字保留 | "分镜设计"、"电影化镜头"、"运镜优化"、"H3 提示词" |
| [h3-prompt-writing](storyboard/h3-prompt-writing/) | H3 五种输入模式（T2VA / I2VA / FL2VA / L2VA / Ref2VA）的提示词结构与字段顺序，避免参考素材被模型忽略 | "改写成 H3 提示词"、"这段首帧往后推 8 秒"、"Ref2VA 提示词" |
| [qiushi-ai-script-director](storyboard/qiushi-ai-script-director/) | 秋拾 AI 脚本编导 V3.5：故事板预览、Excel 分镜表、完整制作包、单场景故事板、原片拉片 | "6 宫格故事板"、"表格分镜"、"完整拍摄方案"、"拉片" |

### 场景与图像资产 · `assets/`

| 技能 | 解决什么 | 典型触发 |
| --- | --- | --- |
| [ai-short-drama-scene-assets](assets/ai-short-drama-scene-assets/) | 把场景当固定三维空间，按 V1→V2→V3→V4 链式生成正视图、反向平视、45° 斜俯、90° 俯视，交付 2×2 四宫格 | "场景资产"、"四视角参考"、"空间一致性" |
| [gemini-image-gen](assets/gemini-image-gen/) | 通过 browser-skill 操控已登录的 Gemini 网页生图，保存全尺寸原图；含已验证的 7 步流程与失败规避 | "用 Gemini 生成图片"、"打开 Gemini 帮我画一张" |

### 成片制作 · `production/`

| 技能 | 解决什么 | 典型触发 |
| --- | --- | --- |
| [audio-driven-mv](production/audio-driven-mv/) | 已有歌曲驱动的对口型 MV：分段送 MiniMax H3、逐字唱词、角色场景参考、任务恢复、按原音频裁尾 | "对口型 MV"、"音乐数字人"、"按歌曲分段生成" |

### 工程与协作 · `tooling/`

| 技能 | 解决什么 | 典型触发 |
| --- | --- | --- |
| [dsh-orchestrator](tooling/dsh-orchestrator/) | 把建模、批处理、编码任务委派给 DeepSeek Harness，由宿主负责分流、方案与验收 | "DSH 协作"、"委派执行"、"迁移部署" |

## 生产链路

技能之间不是并列关系，正常使用顺序如下：

```text
选题            shortdrama-topic-script / pov-shortdrama / crowd-scale-shorts
  ↓
剧本            同上（阶段 B：扩写、时长预算、台词台账）
  ↓
分镜            minimax-h3-storyboard-director / qiushi-ai-script-director
  ↓
提示词          h3-prompt-writing（结构） + minimax-h3-storyboard-director（镜头）
  ↓
资产            ai-short-drama-scene-assets（场景） / gemini-image-gen（任意图）
  ↓
成片            audio-driven-mv（MV）或直接走 H3 生成
```

- 只要**结构正确**（H3 能听懂）：`h3-prompt-writing`
- 只要**这场戏怎么拍**：`minimax-h3-storyboard-director`
- 已经**有系列、要下一集**：`shortdrama-topic-script`
- 做 **POV 爽文题材**：`pov-shortdrama`

## 安装

技能目录需要被放到运行时的用户级 skills 路径下：

| 运行时 | 路径 |
| --- | --- |
| DeepSeek Harness | `~/.agents/skills/` |
| WorkBuddy | `~/.workbuddy/skills/` |
| Codex | `~/.codex/skills/` |

### 安装单个技能

```bash
# 示例：安装分镜导演
git clone --depth 1 https://github.com/Weeexiao/skills.git /tmp/skills
cp -r /tmp/skills/storyboard/minimax-h3-storyboard-director ~/.agents/skills/
```

```powershell
# Windows PowerShell
git clone --depth 1 https://github.com/Weeexiao/skills.git $env:TEMP\skills
Copy-Item -Recurse "$env:TEMP\skills\storyboard\minimax-h3-storyboard-director" "$HOME\.agents\skills\"
```

### 安装全部

```bash
git clone --depth 1 https://github.com/Weeexiao/skills.git /tmp/skills
cp -r /tmp/skills/*/*/ ~/.agents/skills/
```

```powershell
git clone --depth 1 https://github.com/Weeexiao/skills.git $env:TEMP\skills
Get-ChildItem "$env:TEMP\skills" -Directory | Where-Object { $_.Name -ne ".git" } |
  ForEach-Object { Get-ChildItem $_.FullName -Directory } |
  ForEach-Object { Copy-Item -Recurse $_.FullName "$HOME\.agents\skills\" -Force }
```

技能目录名必须与 `SKILL.md` 里的 `name` 字段一致，否则部分运行时无法识别（本仓库已保证一致）。

## 依赖说明

| 技能 | 依赖 |
| --- | --- |
| `shortdrama-topic-script` | Python 3（`scripts/` 下两个脚本，纯标准库） |
| `pov-shortdrama` | Python 3（自检脚本，纯标准库） |
| `qiushi-ai-script-director` | Python 3 + openpyxl（生成 Excel 分镜表）；抽帧脚本另需 ffmpeg |
| `ai-short-drama-scene-assets` | Python 3 + Pillow（`compose_grid.py` 拼四宫格） |
| `gemini-image-gen` | `bsk`（browser-skill）守护进程 + 已登录 Gemini 的浏览器 |
| 其余技能 | 纯文档，无运行时依赖 |

## 维护约定

新增技能时：

1. 目录名 = `SKILL.md` 的 `name` 字段，kebab-case。
2. 放到语义最接近的现有分类；确实不属于五类之一时再新建分类，不要为单个技能开一类。
3. 必须有 `README.md`，至少包含：用途、触发场景、目录结构、安装方式、依赖。
4. `references/` 只放流程会读到的文件，`scripts/` 只放可执行脚本，不放临时产物。
5. 提交信息用 `feat: add <skill-name> skill` / `fix: <skill> <改动>`。

## 迁移对照

原单仓库已并入本合集，仓库名 → 新路径：

| 原仓库 | 现在的位置 |
| --- | --- |
| `crowdScaleShorts` | `scriptwriting/crowd-scale-shorts/` |
| `shortdrama-topic-script` | `scriptwriting/shortdrama-topic-script/` |
| `pov-shortdrama` | `scriptwriting/pov-shortdrama/` |
| `minimax-h3-storyboard-director` | `storyboard/minimax-h3-storyboard-director/` |
| `h3-prompt-writing` | `storyboard/h3-prompt-writing/` |
| `qiushi-ai-script-director` | `storyboard/qiushi-ai-script-director/` |
| `ai-short-drama-scene-assets` | `assets/ai-short-drama-scene-assets/` |
| `gemini-image-gen` | `assets/gemini-image-gen/` |
| `audioDrivenMv` | `production/audio-driven-mv/` |
| `dsh-orchestrator` | `tooling/dsh-orchestrator/` |

`h3-video-remake` 为私有技能，**不在本仓库**，继续单独存放在其私有仓库中。
