# Gemini Image Gen · 用 Gemini 网页批量出图（浏览器自动化）

<p align="center">
  <b>借你已登录的 Chrome，让 AI 直接指挥 Gemini 生成图片，并自动取回全尺寸原图。</b>
</p>

---

## 这是什么

一个给 AI 助手（Agent）用的技能包：通过 [`browser-skill`](https://github.com/Tencent/BrowserSkill)（`bsk` 命令行）操控用户**已登录**的 Chrome 浏览器，在 **Google Gemini** 网页上完成「输入提示词 → 生成图片 → 下载全尺寸原图 → 存到指定目录」的全流程。

不需要 API Key，不消耗额度，不碰你的账号密码与 Cookie——只借用你本来就开着的那个 Gemini 标签页，用完即还。

## 解决什么问题

用浏览器自动化操作 Gemini 生图，看起来简单，实则处处是坑。本技能把踩过的坑全部固化成了确定路径：

| 直觉做法 | 实际结果 | 本技能的正确做法 |
| --- | --- | --- |
| 用 `bsk fill` 写提示词 | 必失败（`fill_target_changed`，编辑器重渲染） | `evaluate` + `document.execCommand('insertText')` |
| 用 `bsk upload` 传参考图 | 必失败（按钮打开的是菜单，不是文件选择器） | 把文件写进剪贴板（CF_HDROP）+ `Ctrl+V` 粘贴 |
| 缩略图一出现就点发送 | 参考图会丢：缩略图 1–3 秒就出现，后台上传还要 13–32 秒/张 | 等附件区 `mat-progress-spinner` 消失再发送 |
| 用 `loading-indicator` 判断"还在生成" | **出图前该选择器计数为 0**，会把"还在画"误判成"已完成无图"，白等十几分钟还重跑 | 完成只看响应里有没有 `<img>`；"在画"看 `mat-progress-spinner / [role=progressbar]` |
| 生成中重试点击发送键 | 发送键此时已变成"停止生成"，会把进行中的响应打断 | 只在无 spinner 且响应数未增加时点击 |
| 用 `bsk download` 点下载按钮 | 报 `not attributed` 超时，**但浏览器其实已下载成功** | 点击前记录目录基线，点击后轮询新增文件 |
| 用 canvas 抓 blob 图当原图 | 只能拿到 1024 宽缩略版 | 走「Download full-sized image」拿 1792×3200 / 2816×1536 等真原图 |
| 假定出图固定尺寸 | 换个比例就判断失误 | 长边 ≥ 1200 即视为全尺寸，比例自适应 |
| 提示词涉及画面被拒时当成"模型慢" | 实际是安全过滤拒绝（回复"没办法提供这方面的帮助"），同样先耗 5–10 分钟 | 把拒绝话术作为独立判据，命中立刻重试或改中性措辞 |

## 特性

- **一条路走到底**：7 步固定流程，命令可直接复制执行，无需试错
- **比例自适应**：支持 16:9 / 9:16 / 3:4 / 1:1 等任意比例，不做尺寸硬编码
- **参考图上传**：最多实测 7 张参考图逐张上传、逐张确认上传完成后再发送
- **生成状态判定**：区分"还在画 / 已出图 / 被安全过滤拒绝"三种状态，不做无谓等待
- **批量驱动**：内置参考实现，支持任务依赖图、状态表、断点续跑、分批与重试
- **下载可靠性检测**：基线比对 + 轮询 + 文件大小稳定性校验，杜绝"以为失败了，其实早就下好了"的误判
- **自带校验**：纯 `struct` 解析图片头获取尺寸（无需 PIL），自动报告方向与是否全尺寸
- **安全**：不读取、不导出任何凭据；标签页借用后自动归还

## 前置条件

1. 浏览器中已安装 [BrowserSkill](https://github.com/Tencent/BrowserSkill) 扩展，且 `bsk` CLI 与守护进程已就绪
2. 浏览器已打开并登录 `gemini.google.com`（会员账号请走 `https://gemini.google.com/u/1/app`，注意**不一定是 Chrome**，夸克等 Chromium 内核浏览器同样可用）
3. 本机具备 Python（本技能默认使用托管运行时 `C:/Users/shizh/.workbuddy/binaries/python/versions/3.13.12/python.exe`）

## 使用方式

在 AI 助手中直接说：

> 用 Gemini 生成一张图片：<你的画面描述>

助手会自动加载本技能并执行以下流程：

```
环境检查 → 启动会话 → 借用 Gemini 标签页 → 确认 Pro 模式
  → 逐张粘贴参考图（剪贴板）→ 逐张等待上传完成
  → 注入提示词（execCommand insertText）
  → 点击发送 → 轮询等待生成完成（20 秒 ~ 10 分钟，按是否有 <img> 判定）
  → 记录下载目录基线 → 点击「Download full-sized image」
  → 轮询检测新文件落盘 → 校验尺寸 → 复制到目标目录
  → 归还标签页、结束会话
```

批量任务则交给 `scripts/reference/batch.py`：

```sh
BSK_SESSION=<sid> python scripts/reference/batch.py --limit 5 --attempts 3
```

`--limit` 控制每批跑几个（便于分批验收），`--attempts` 控制单任务失败重试次数。
产物已存在的任务会自动跳过，中断后重跑即续，不会重复消耗额度。

## 目录结构

```
gemini-image-gen/
├── SKILL.md                  # 技能正文：完整流程、命令、已知失败做法、环境注意
├── README.md                 # 本文件
└── scripts/
    ├── watch_downloads.py    # 下载检测脚本：基线比对 + 轮询 + 尺寸校验 + 自动复制
    └── reference/            # 多任务批量驱动参考实现（路径需按项目改常量）
        ├── runtask.py        # 单任务完整流程
        ├── batch.py          # 任务编排：依赖图 + 状态表 + 断点续跑 + 分批/重试
        ├── harvest.py        # 抢救页面上正在进行/未收走的生成结果
        └── soften_prompts.py # 被安全过滤的提示词批量改中性措辞（自动备份原文件）
```

## 关于"生成没出图"

轮询时若长时间卡在 `lastImgs = 0`，先判断是哪种情况，不要一律当超时重跑：

| 现象 | 判定 | 处理 |
| --- | --- | --- |
| 正文含「正在创建您的图片」 | 还在生成 | 继续等，参考图多时可能 10 分钟以上 |
| 正文含「没办法提供这方面的帮助」 | **被安全过滤拒绝** | 立刻重试 2–3 次（拒绝有随机性）；仍被拒则把羞辱/痛苦/胁迫类描述改成中性措辞，但保留构图、站位、景别、光线与角色绑定 |
| 正文是其它完整文字回复 | 模型没走生图 | 改写提示词，原样重跑通常无效 |

改词时务必同步告知用户改了哪几句，并保留 `提示词-原始备份.md`。

## 脚本用法

```sh
python scripts/watch_downloads.py <baseline_json> <output_path> [downloads_dir] [timeout_sec] [--min-long-side N]
```

| 参数 | 说明 |
| --- | --- |
| `baseline_json` | 点击下载**之前**记录的目录基线文件（文件名 → mtime） |
| `output_path` | 检测到新图后复制到的目标路径 |
| `downloads_dir` | 可选，默认 `C:/Users/shizh/Downloads` |
| `timeout_sec` | 可选，默认 90 秒 |
| `--min-long-side` | 可选，判定“全尺寸原图”的长边阈值，默认 1200 |

输出示例：

```json
{
  "ok": true,
  "source": "C:/Users/shizh/Downloads/Gemini_Generated_Image_xxxx.jpg",
  "copied_to": "C:/Users/shizh/Desktop/my_image.jpg",
  "bytes": 4393757,
  "dimensions": "1792x3200",
  "orientation": "portrait",
  "is_full_size": true
}
```

若长边低于阈值，会额外返回 `warning`，提示可能误拿了页面缩略图。

## 出图尺寸参考（实测）

| 提示词比例 | 全尺寸原图 | 页面缩略图（勿采用） |
| --- | --- | --- |
| 横版 16:9（默认） | 2816×1536 | 1024×559 |
| 竖版 9:16 | 1792×3200 / 1536×2816 | 559×1024 |
| 3:4 / 4:3 | 约 1728×2304 / 2304×1728 | 对应缩小 |
| 1:1 | 约 2048×2048 | 对应缩小 |

想要特定比例，请在提示词中明确写出（如“竖屏 9:16 构图”）。

## 环境适配记录

- 本机 bash 缺少 coreutils：`sleep` 用 `ping -n N 127.0.0.1 > /dev/null` 替代；`ls / wc / head` 用 Python 或 Glob/Read 工具替代
- PowerShell 工具输出常不回显：检查结果统一用 Python `print`，或写文件后用 Read 工具读取
- `bsk evaluate` 的 JS 里不要出现**字面单引号**（尤其写在正则中，如 `(?:no|')t`），会让整条 eval 静默返回空串；正则里改用 `.` 通配或 `\u0027` 转义
- 浏览器/守护进程重启后旧 `session_id` 失效，会报 `session not registered or already stopped`，需重新 `bsk session start` 并重新 `tab borrow`

## 说明

- 生成内容具有随机性，同一提示词每次结果不同
- 本技能只做浏览器操作，不涉及 Gemini 账号凭据、API Key 或其他敏感信息的读取与传输
