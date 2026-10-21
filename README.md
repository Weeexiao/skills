# Skills 合集

覆盖 AI 短剧制作及 DSH 工具协作的 Agent Skills 合集，按生产环节与工程用途分类存放。

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
│   ├── audio-driven-mv/
│   └── blender-previs/
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
| [blender-previs](production/blender-previs/) | Blender 白模预演：低精度体块验证站位、走位、构图、景别、路径、运镜与时间轴，输出预演 MP4 作 H3 运动参考；不验证表情口型 | "白模"、"预演"、"走位验证"、"运镜会不会穿墙" |

### 工程与协作 · `tooling/`

| 技能 | 解决什么 | 典型触发 |
| --- | --- | --- |
| [dsh-orchestrator](tooling/dsh-orchestrator/) | 检查、安装并部署 DSH 桌面插件；**派单前先验证技能注册、运行时可用与路径可写**；含 30 个 Blender 内置技能的用途速查与路由表；小任务直接完成，大块独立任务才交模型，以减少 Codex 用量 | "部署 DSH 协作"、"连接 DSH 桌面"、"新电脑迁移"、"委派执行"、"该用哪个 Blender 技能" |

### DSH 协作与新电脑部署

安装 [dsh-orchestrator](tooling/dsh-orchestrator/README.md) 后，对 Codex 发送：

> 使用 $dsh-orchestrator，检查本机是否已有 DSH 和 dsh-as-mcp；已有就复用，没有则按技能下载安装并部署，完成认证、只读工具调用和桌面记录验证。小任务直接做，大块独立任务才委派模型。

代理按[完整部署流程](tooling/dsh-orchestrator/references/connection.md)执行：检查插件与运行状态 → 下载缺失组件 → 合并配置 → 安装命令行依赖 → 验证接口及桌面记录。默认复用 `dsh-as-mcp`，支持不经过 DSH 模型的直接工具调用；需要自主完成整块工作时才调用模型。

技能安装后由代理执行后续部署；账户登录、系统授权及等待其他桌面任务结束可能需要用户配合。新桌面链路仍需在目标电脑实测，安装技能本身不代表已经连通。

## 生产链路

技能之间不是并列关系，正常使用顺序如下：

```text
选题            shortdrama-topic-script / pov-shortdrama / crowd-scale-shorts
  ↓
剧本            同上（阶段 B：扩写、时长预算、台词台账）
  ↓
分镜            minimax-h3-storyboard-director / qiushi-ai-script-director
  ↓
可选预演        blender-previs（复杂走位/运镜先验证再生成）
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
- 要**先验证走位运镜再花钱生成**：`blender-previs`

### Blender 技能怎么选

DSH 内置 30 个 Blender 技能（`create-3d-model` 总入口 + 29 个领域模块），不在本仓库。要建模、改场景、材质灯光、动画、渲染、导出时，先看 [dsh-orchestrator 的 Blender 路由表](tooling/dsh-orchestrator/references/blenderSkills.md)：它给出按任务意图的完整对照、推荐链路，以及**派单前如何确认这些技能与 Blender 本体真的可用**。

常见陷阱：技能全部注册成功，但 `blender` 不在 PATH（如装在 `D:\Blender\` 却未加入环境变量），此时 `blender_status` 返回 `spawn blender ENOENT`，任何 Blender 任务都产不出文件。技能注册 ≠ 能运行，两者必须分别验证。

## 安装

将具体技能子目录放到运行时的用户级 skills 路径下，不能把合集根目录直接当成一个技能安装。已有克隆和目录联接时优先复用，避免重复复制或覆盖本地修改。

默认路径如下（Codex 设置了 `CODEX_HOME` 时使用其 `skills/` 子目录）：

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

### 推荐：单克隆 + 目录联接（一次更新全部）

复制安装会产生 10 份互不同步的副本。更省事的做法是**只保留一个克隆**，技能目录用目录联接（junction）指向克隆里的子目录：`git pull` 一次，全部技能同时更新，也不会出现副本漂移。

Windows（PowerShell，管理员权限不需要）：

```powershell
$repo = "$env:USERPROFILE\.agents\skill-sources\skills"
$link = "$env:USERPROFILE\.agents\skills"

git clone https://github.com/Weeexiao/skills.git $repo

Get-ChildItem $repo -Directory | Where-Object { $_.Name -ne ".git" } | ForEach-Object {
  Get-ChildItem $_.FullName -Directory | ForEach-Object {
    $target = Join-Path $link $_.Name
    if (Test-Path $target) { Remove-Item -Recurse -Force $target }
    cmd /c mklink /J "$target" $_.FullName
  }
}
```

macOS / Linux 等价写法：

```bash
git clone https://github.com/Weeexiao/skills.git ~/.agents/skill-sources/skills
ln -s ~/.agents/skill-sources/skills/*/* ~/.agents/skills/
```

**更新全部技能：**

```powershell
git -C "$env:USERPROFILE\.agents\skill-sources\skills" pull
```

**改技能并推回仓库**——从任意技能目录进去即可，git 会自动定位到同一个仓库，工作区路径前缀就是该技能所在子目录：

```powershell
cd "$env:USERPROFILE\.agents\skills\pov-shortdrama"
git status          # 改动显示为 scriptwriting/pov-shortdrama/...
git add -A; git commit -m "fix: ..."; git push
```

#### 两处必须手工处理的地方

目录联接不会随仓库结构自动变化，下面两种情况要手动补一下：

1. **仓库新增技能**：新建目录后，要为它单独建一个联接，否则运行时看不到这个技能。

   ```powershell
   $repo = "$env:USERPROFILE\.agents\skill-sources\skills"
   cmd /c mklink /J "$env:USERPROFILE\.agents\skills\<技能名>" "$repo\<分类>\<技能名>"
   ```

2. **仓库删除或重命名技能**：旧联接会变成**悬空目录**（指向已不存在的路径）。必须删掉，否则加载器会读到一个无效技能目录、报错或跳过整批扫描。

   ```powershell
   Remove-Item -Recurse -Force "$env:USERPROFILE\.agents\skills\<旧技能名>"
   ```

> 判断某个目录是不是联接：`Get-ChildItem ~\.agents\skills | Select-Object Name, LinkType, Target`，或直接看资源管理器里目录图标带小箭头。

## 依赖说明

| 技能 | 依赖 |
| --- | --- |
| `shortdrama-topic-script` | Python 3（`scripts/` 下两个脚本，纯标准库） |
| `pov-shortdrama` | Python 3（自检脚本，纯标准库） |
| `qiushi-ai-script-director` | Python 3 + openpyxl（生成 Excel 分镜表）；抽帧脚本另需 ffmpeg |
| `ai-short-drama-scene-assets` | Python 3 + Pillow（`compose_grid.py` 拼四宫格） |
| `gemini-image-gen` | `bsk`（browser-skill）守护进程 + 已登录 Gemini 的浏览器 |
| `blender-previs` | **Blender 可执行文件**（PATH 中的 `blender` 或配置 `blenderExecutable`）+ FFmpeg |
| [dsh-orchestrator](tooling/dsh-orchestrator/) | DSH 桌面、兼容的 Node.js/npm、`dsh-as-mcp`（部署基线 0.1.5）；在技能 `scripts/` 下显式执行 `npm ci --ignore-scripts` 安装客户端依赖，详见[部署说明](tooling/dsh-orchestrator/references/connection.md) |
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

`blender-previs` 由 `audio-driven-mv/references/blenderPrevis.md` 提炼而来，成为独立的通用预演技能；MV 侧只保留音频与引用编号差异。

`h3-video-remake` 为私有技能，**不在本仓库**，继续单独存放在其私有仓库中。
