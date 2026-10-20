# pov-shortdrama

POV 第一人称「成功人生」爽文短剧剧本生成器。

用户给一个主题（「修仙者POV」「足球运动员POV」「创业POV」），Skill 问 3-4 题锁定世界观、起点、高光时刻和篇幅，然后直接产出符合 Toonflow 短剧模板格式的完整分场剧本。

## 它解决什么

POV 短剧最常见的失败是两个：

1. **只是把机位放低**：摄影机跟着主角走，但主角照样露脸、照样正反打，观众没有"我在场"的代入感。
2. **爽点不成曲线**：被轻视、反转、高光都写了，但顺序和节奏不对，看到最后不"出气"。

这个 Skill 把 POV 的镜头约束写成硬规则（主角零正脸、三类镜配比、视线驱动运镜、五幕各自的分镜策略），并配一个离线自检脚本，把"有没有违规"从主观判断变成可执行的检查。

## 工作流

1. **锁定题材**：读 `references/genre-library.md`，命中题材卡就直接用它的角色卡、术语库和默认高光时刻；没命中就按模板现场推导。
2. **问答确认**：一次性抛出世界观、主角起点与被轻视的场景、高光时刻形态、篇幅与结尾处理四题。
3. **写剧本**：按五幕爽点曲线铺场，逐幕选镜头策略，再套 `references/toonflow-format.md` 的格式。
4. **自检**：过一遍清单，跑 `scripts/check_pov_script.py`。
5. **交付**：剧本正文 + 写入 `pov剧本/{标题}.md` + 一段可复用的 POV 画面提示词包；需要时补分镜设计表。

## 核心约束

- 五幕曲线固定：**被轻视 → 伏笔 → 反转 → 集体崇拜 → 高光定格**
- 主角以「我」出现，只用**手、手臂、鞋、影子、镜中虚影**表现，**绝不写正脸**；背影镜全片 ≤2 次
- 三类镜配比约 **A 主观镜 80% / B 身体镜（手·脚入画）15% / C 背影抽离镜 ≤2 次**
- 全片台词 ≤12 句，单句 ≤15 字；主角台词近乎为零，情绪交给旁白（内心）和他人反应
- 对手角色要演出「轻蔑 → 惊愕 → 仰望」三次看向镜头的眼神
- 反转那一镜固定用「骤稳」：从手持晃动骤然变稳

## 目录结构

```text
pov-shortdrama/
├── SKILL.md                        # 主流程：五步，含自检清单
├── references/
│   ├── genre-library.md            # 20 类题材卡 + 题材卡模板
│   ├── pov-narrative-engine.md     # 五幕爽点曲线、POV 铁律、卡点与台词规范
│   ├── pov-shot-design.md          # POV 分镜体系：三类镜、视线驱动运镜、替身技法
│   └── toonflow-format.md          # Toonflow 短剧格式规范 + 完整成品样例
├── scripts/
│   └── check_pov_script.py         # 剧本自检器（只读、离线）
└── agents/
    └── openai.yaml                 # Codex 界面元数据（可选）
```

## 自检脚本

```bash
python scripts/check_pov_script.py "pov剧本/世界杯POV.md"
python scripts/check_pov_script.py --json "pov剧本/世界杯POV.md"   # 机器可读输出
```

确定性检查以下项：

- 场次编号是否连续
- 每场必备元素（场景行 / 人物行 / `[音效：…]`）
- 台词句数与单句长度上限
- `△ 卡点：` 数量
- 三类镜配比、A/B/C 镜统计
- 主角是否出镜（正脸 / 回头 / 过肩 / 正反打）
- 主角替身种类

出现 `[FAIL]` 必须改到通过再交付；`[WARN]` 逐条判断。脚本只用 Python 标准库（`argparse`、`json`、`re`、`sys`），无需安装依赖。

## 安装

```bash
# DeepSeek Harness
git clone git@github.com:Weeexiao/pov-shortdrama.git ~/.agents/skills/pov-shortdrama

# WorkBuddy
git clone git@github.com:Weeexiao/pov-shortdrama.git ~/.workbuddy/skills/pov-shortdrama

# Codex
git clone git@github.com:Weeexiao/pov-shortdrama.git ~/.codex/skills/pov-shortdrama
```

需要 Python 3。

## 与其他短剧技能的关系

- **shortdrama-topic-script**：反诈/消费陷阱题材的系列短剧，走选题与剧本台账流程；本 Skill 走 POV 爽文题材，两者题材线不同。
- **minimax-h3-storyboard-director**：把剧本转成电影分镜与 H3 提示词。本 Skill 自带 POV 分镜体系，已把可迁移的镜头语言改写为第一人称版本，不依赖该技能。
- **qiushi-ai-script-director**：通用短片分镜与拉片，POV 场景下按本 Skill 的规则覆盖。

## 关于提问工具

第 2 步要求"一次性抛出 3-4 题"。具体工具按运行环境切换：DSH 用 `ask_user_question`，Codex 用 `AskUserQuestion`；两者都是一次多题，不要一问一答消耗用户耐心。
