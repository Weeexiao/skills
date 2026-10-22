# pov-shortdrama

创作、改写及制作严格第一人称短片，支持历史逃生、人生体验、沉浸叙事和逆袭爽文。可以从一个主题开始，也可以接手用户已有剧本、素材和采用版本。

## 核心边界

- 摄影机就是主角眼睛，不拍主角头脸、肩膀、躯干、背影或自身映像；手/短前臂按动作需要从下缘进入。
- 其他路人的背影可以出现，但不能让一个持续居中、与镜头同速的背影成为隐形主角。
- 只对“你”交互的人看镜头；逃跑的人看危险/出口，拍照的人看手机屏幕。
- 选择适合故事的曲线，爽文的羞辱、反转和加冕不是历史逃生的必选段落。
- 已有设定直接沿用，只问实质缺项。用户只改一段或一个动作，不重做已采用片段。

## 实际制作

先读真实项目和任务记录，按当前模型能力选择单幅、多宫格、实际尾帧或可选预演。四宫格要逐格成为全屏；简单展陈镜头出现分屏/横框时，检查并简化参考本身。关键动作不能省略，道具被忽略时将正确持物状态放进参考图。

已采用旁白保存成真实音频资产。提交前校验，提交后保存请求ID；状态不明先查原任务，不重复收费提交。区分已生成、已检查、用户采用；不能根据最新版或成功数量直接导出/宣布完成。

## 参考入口

- [SKILL.md](SKILL.md)：任务分流、严格POV、题材选择和验收。
- [分镜设计](references/pov-shot-design.md)：运动、人物反应、空间、动作和构图。
- [生产流程](references/productionWorkflow.md)：本次庞贝制作沉淀的参考策略、音频、恢复、计费与采用规则。
- [爽文叙事](references/pov-narrative-engine.md) 与 [题材卡](references/genre-library.md)：仅逆袭/成功人生需要时读取。
- [Toonflow格式](references/toonflow-format.md)：用户或应用需要该格式时读取。

## 文本自检器

scripts/check_pov_script.py 是原有Toonflow爽文模板的离线文本检查器，保留三处卡点和短台词等旧模板阈值。非爽文、解说或模型提示词不强行套用。现在严格POV的主角抽离镜默认0；独立路人背影不按主角C类镜计算。

脚本只能提示文本风险，不能证明画面、音色、空间或动作已通过。没有听验就不声称检查过声音，仅抽帧就如实说明抽帧范围。

## 安装

本技能位于合集仓库 [Weeexiao/skills](https://github.com/Weeexiao/skills) 的 `scriptwriting/pov-shortdrama/`。用稀疏检出只拉这一个技能：

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/Weeexiao/skills.git /tmp/skills
cd /tmp/skills && git sparse-checkout set scriptwriting/pov-shortdrama
cp -r scriptwriting/pov-shortdrama ~/.agents/skills/
```

```powershell
git clone --depth 1 --filter=blob:none --sparse https://github.com/Weeexiao/skills.git $env:TEMP\skills
cd $env:TEMP\skills; git sparse-checkout set scriptwriting/pov-shortdrama
Copy-Item -Recurse scriptwriting\pov-shortdrama "$env:USERPROFILE\.agents\skills\"
```

目标目录按运行时替换：DSH 用 `~/.agents/skills/`，WorkBuddy 用 `~/.workbuddy/skills/`，Codex 用 `~/.codex/skills/`。

仅使用旧文本自检器时需要 Python 3。

## 与其他短剧技能的关系

- **shortdrama-topic-script**：反诈/消费陷阱题材的系列短剧，走选题与剧本台账流程；本 Skill 负责第一人称叙事与制作约束。
- **minimax-h3-storyboard-director**：把剧本转成电影分镜与 H3 提示词。本 Skill 自带 POV 分镜体系，已把可迁移的镜头语言改写为第一人称版本，不依赖该技能。
- **qiushi-ai-script-director**：通用短片分镜与拉片，POV 场景下按本 Skill 的规则覆盖。

## 关于提问工具

使用当前环境实际提供的提问工具，仅问影响结果的缺项。已有剧本、已确认设定或持续修订时直接沿用，不固定要求3—4题，不假定任何工具名。
