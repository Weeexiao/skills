# shortdrama-topic-script

《赵叔踩坑日记》系列短剧的**选题 + 剧本** Skill。

把一个已经跑起来的系列短剧，从“下一集拍什么”一路做到“能直接配音、能直接拆片段”的剧本，中间不靠感觉，靠档案、评分和时长预算。

## 它解决什么

系列短剧做到第六七集，最容易出的不是创意问题，是三个工程问题：

1. **撞机制**：换了行业、换了产品，骗法还是上一集那一套。
2. **写超时**：台词写完发现 130 秒，只能加速念，观众听不清。
3. **交接断层**：剧本给到分镜，人物站位、说话人、片段边界全要重问一遍。

这个 Skill 把三件事固定成流程：机制台账防撞车、五维加权选题材、脚本估算时长并生成台账与片段表。

## 两段能力

### 阶段 A：选题

- 读系列档案，列出已用机制
- 从“机制空白 / 时效热点 / 观众日常 / 人物关系”四个来源生成候选
- 五维加权打分：钩子 25%、差异化 20%、可执行 20%、时效 20%、情感 15%
- 一票否决：撞机制、新增场景 >2、新增角色 >1、依赖特效、必须演示操作路径
- 产出八节方案：卖点、标题、三秒钩子、8 场骨架、三句关键台词、两行字幕、新增资产、合规

### 阶段 B：剧本

- 按固定格式扩写场次与台词（`△` 动作、`**角色：**` 台词、定格、字幕）
- 用脚本估算每场时长、累计时长、每个角色的说话占比
- 生成台词台账（场次/角色/原文/字数/预估秒）
- 按“一个片段一个叙事目的、2–3 镜头、8–15 秒、台词在前 85% 结束”切片段
- 交稿前过一遍检查清单（台词长度、说话人绑定、合规）

## 目录结构

```text
shortdrama-topic-script/
├── SKILL.md                          # 主流程：三铁律 + 阶段 A/B 九步
├── references/
│   ├── series-canon.md               # 系列档案：人物、场景池、七拍、机制台账
│   ├── topic-scorecard.md            # 五维评分锚点、一票否决、完整案例
│   ├── episode-outline-template.md   # 八节选题方案模板 + 已填样例
│   ├── topic-bank.md                 # 选题池：已用 / 可用 / 暂缓 / 淘汰
│   └── script-standard.md            # 剧本格式、时长预算、片段规则、自检
├── assets/
│   └── 剧本模板.md                    # 可直接复制的空白剧本
└── scripts/
    ├── score_topics.py               # 选题加权评分与一票否决
    └── estimate_duration.py          # 剧本时长估算与台词台账
```

## 安装

本技能位于合集仓库 [Weeexiao/skills](https://github.com/Weeexiao/skills) 的 `scriptwriting/shortdrama-topic-script/`。用稀疏检出只拉这一个技能：

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/Weeexiao/skills.git /tmp/skills
cd /tmp/skills && git sparse-checkout set scriptwriting/shortdrama-topic-script
cp -r scriptwriting/shortdrama-topic-script ~/.workbuddy/skills/
```

```powershell
git clone --depth 1 --filter=blob:none --sparse https://github.com/Weeexiao/skills.git $env:TEMP\skills
cd $env:TEMP\skills; git sparse-checkout set scriptwriting/shortdrama-topic-script
Copy-Item -Recurse scriptwriting\shortdrama-topic-script "$env:USERPROFILE\.workbuddy\skills\"
```

目标目录按运行时替换：DSH 用 `~/.agents/skills/`，WorkBuddy 用 `~/.workbuddy/skills/`，Codex 用 `~/.codex/skills/`。

安装后新开一个对话，说“用 shortdrama-topic-script 给赵叔选下一集”即可。

## 命令行工具

选题评分：

```bash
python scripts/score_topics.py candidates.json
python scripts/score_topics.py candidates.json --out ranking.md
python scripts/score_topics.py --demo
```

候选 JSON 格式：

```json
{
  "candidates": [
    {
      "name": "存一万送一万",
      "hook": 9, "diff": 9, "exec": 9, "timely": 9, "emotion": 9,
      "new_scenes": 1, "new_characters": 0,
      "note": "预付资金池"
    }
  ]
}
```

剧本时长：

```bash
python scripts/estimate_duration.py 剧本.md
python scripts/estimate_duration.py 剧本.md --rate 4.5 --out 时长表.md --ledger 台词台账.md
```

默认按 4.5 字/秒、每句 0.35 秒停顿、每场 1 秒转场估算。低于 60 秒或超过 110 秒会提示，单句超过 15 字、老钱单段超过 60 字会点名。

## 识别范围

`estimate_duration.py` 支持几种常见的台词写法：

```markdown
**赵叔：**
“我卡里还有八万呢！”

**赵叔**
“我卡里还有八万呢！”

**赵叔（画外音）：**
“我卡里还有八万呢！”

赵叔：
“我卡里还有八万呢！”
```

动作行 `△`、字幕行、`**画面定格。**` 不会被误算成台词。

## 适配别的系列

`references/series-canon.md` 是《赵叔踩坑日记》的档案。换系列时按同样七节重建：账号定位、固定人物、场景池与回环机位、结构拍子、已用机制台账、语言风格、资产复用清单。

档案没写完，不要开始想选题。

## 合规

- 只揭机制，不教操作路径
- 不出现真实品牌、平台、机构、地名
- 金融类不写“保本”“稳赚”，不写具体收益率承诺
- 片尾固定：剧情为虚构创作，人物与机构均为化名

## 说明

本仓库只包含方法论与脚本，不包含任何剧集成片、人物资产或未公开的项目文件。
