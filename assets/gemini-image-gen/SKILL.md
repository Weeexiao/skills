---
name: gemini-image-gen
description: 通过 browser-skill (bsk) 操控用户已登录的 Chrome 中的 Google Gemini 网页生成图片，并保存全尺寸原图到指定目录（分辨率与比例随提示词而定，如 2816×1536 横版、1536×2816 竖版 9:16、3:4 等）。当用户要求"用 Gemini 生成图片"、"打开 Gemini 帮我画一张图"等时使用。包含已验证正确的完整流程与命令，无需试错。
---

# Gemini 网页生图（bsk 自动化，已验证流程）

前提：用户已打开且已登录 Gemini（gemini.google.com）的浏览器，bsk 守护进程与扩展已连接。注意**不一定是 Chrome**——本机实际是夸克浏览器（窗口标题带「夸克」），不要因此以为没连上。
本流程在 2026-09-20 经 30+ 张实拍验证（含单张与最多 7 张参考图的批量任务），直接照做，**不要尝试下述"已知失败做法"**。

**生成耗时要有耐心：单次出图可能 20 秒，也可能 10 分钟以上（参考图多、或模型先被安全系统拦下再兜底回复）。不要把"等得久"当成失败。**

## 正确流程（7 步，一条路走到底）

### 1. 环境检查与会话

```sh
BSK_AUTO_START=0 bsk status --json          # 确认 browsers 列表非空
bsk session start --json                    # 记下 session_id（下称 <sid>）
bsk tab list --scope user --session <sid>   # 找到 URL 含 gemini.google.com 的标签页
bsk tab borrow <tab-id> --session <sid>     # 借用该标签页
```

### 2. 输入提示词（不要用 bsk fill！）

Gemini 的富文本编辑器会让 `bsk fill` 持续报 `fill_target_changed`，必须用 evaluate 注入：

```sh
bsk evaluate --session <sid> --timeout 30s "(function(){
  const el = document.querySelector('rich-textarea div[contenteditable=\"true\"]');
  if (!el) return {ok:false, reason:'editor not found'};
  el.focus();
  document.execCommand('insertText', false, '<用户提示词>');
  return {ok:true, len: el.textContent.length};
})()"
```

### 3. 发送

```sh
bsk observe --session <sid> --max-tokens 1500   # 取新鲜引用
bsk click @e<N> --session <sid>                  # 点击 "Send message" 按钮
```

若页面残留上次打开的图片查看器（Lightbox dialog），先点它的 "Close" 按钮再发送。

### 4. 等待生成完成（20 秒 ~ 10 分钟以上，参考图越多越慢）

轮询检测（不要只看 observe 文本，最后的 "Gemini said" 区块可能延迟渲染）：

```sh
bsk evaluate --session <sid> --timeout 30s "(function(){
  const r = Array.from(document.querySelectorAll('model-response'));
  const l = r[r.length-1]; const t = l ? (l.innerText||'').trim() : '';
  return {responses: r.length,
          lastImgs: l ? l.querySelectorAll('img').length : -1,
          spinner: document.querySelectorAll('loading-indicator, .loading-spinner').length,
          prog: document.querySelectorAll('mat-progress-spinner,[role=progressbar]').length,
          creating: /正在创建您的图片|Creating your image|正在生成图片/i.test(t),
          textLen: t.length};
})()"
```

**完成判据只有一个：`lastImgs >= 1`。**

⚠️ **不要用 spinner 判完成——这是本流程最容易踩的坑。** 出图前的长时间里 Gemini 显示的是「正在创建您的图片 / Creating your image」，此状态下：

- `loading-indicator / .loading-spinner` 计数 = **0**（选择器完全不匹配）
- 真正带 `aria-busy` 的是 `mat-progress-spinner` / `[role=progressbar]`，计数 = 1
- `lastImgs` = 0

所以「spinner==0 就算完成」会把**正在生成**误判成**已完成但没有图**，然后提前放弃并重跑（实测 E03/S14/S15/S17/S11 全部因此被误判为 "generation timeout"）。判断"是否还在生成"要看 `prog > 0` 或 `creating == true`；判断"是否出图"只看 `lastImgs`。

等待期间用 `ping -n N 127.0.0.1 > /dev/null` 代替 sleep（本机 bash 缺 coreutils，sleep/ls/wc 均不可用）。

**超时不要直接判定"模型慢"。** 先抓最后一条响应的正文，区分「模型只回了文字/拒绝/报错」和「单纯还在画」：

```sh
bsk evaluate --session <sid> --timeout 30s "(function(){
  const r = Array.from(document.querySelectorAll('model-response'));
  const l = r[r.length-1]; const t = (l ? l.innerText : '').trim();
  return {responses:r.length, queries:document.querySelectorAll('user-query').length,
          len:t.length, head:t.slice(0,400)};
})()"
```

若 `lastImgs` 长期为 0 而 `responses` 已有值、`spinner` 也是 0，说明响应早已结束但没有图片——多半是模型回了纯文本或需要改写提示词，重跑同样的提示词通常不会好。把 `head` 内容记录下来再决定。

### 安全过滤拒绝（"generation timeout" 的常见真凶）

实测提示词涉及**跪地、跪拜、被胁迫、群殴/打手涌入、把物品怼到人嘴边**等羞辱或暴力画面时，Gemini 会拒绝出图，回复：

> 身为一个语言模型，我没办法提供这方面的帮助。

**它的表现和"生成慢"完全一样**：先经历约 5–10 分钟的「正在创建您的图片」，然后正文被替换成拒绝话术，`lastImgs` 始终为 0。若只按超时处理，会白等十几分钟还误判成"模型慢"。

因此必须把拒绝话术作为独立判据（见上面的 `refused` 字段），命中就立即返回，让上层**重试或改写提示词**。两点经验：

- 这类拒绝**有一定随机性**：同一个提示词先失败两次、第三次成功的情况真实存在，所以先原样重试 2–3 次是值得的。
- 若连续被拒，就该改词：保留构图与人物（`<Subject>` 绑定、站位、景别、光线），把**羞辱/痛苦的表演描述换中性说法**——例如「跪地不敢动、眼泪将出」→「屈身低头、神情克制」，「打手涌入」→「数名随行人员静止站立于后景」。改词后务必告知用户改了哪里。

### 5. 记录下载目录基线（点击下载之前做！）

```sh
"C:/Users/shizh/.workbuddy/binaries/python/versions/3.13.12/python.exe" -c "
import os, json
d = r'C:/Users/shizh/Downloads'
json.dump({f: os.path.getmtime(os.path.join(d,f)) for f in os.listdir(d)}, open(r'<工作区>/dl_before.json','w'))
"
```

### 6. 触发下载（不要用 bsk download！）

```sh
bsk evaluate --session <sid> --timeout 30s "(function(){
  const resp = Array.from(document.querySelectorAll('model-response'));
  const last = resp[resp.length-1];
  const btns = Array.from(last.querySelectorAll('button')).filter(b => (b.getAttribute('aria-label')||'').includes('Download'));
  if (!btns.length) return {ok:false, reason:'download btn not found'};
  btns[btns.length-1].click();
  return {ok:true};
})()"
```

### 7. 检测落盘文件并复制到目标位置

用 scripts/watch_downloads.py 轮询（传入基线文件与目标输出路径）：

```sh
python scripts/watch_downloads.py <基线json> <输出目标路径>
# 例：
python scripts/watch_downloads.py C:/Users/shizh/WorkBuddy/<会话>/dl_before.json C:/Users/shizh/Desktop/my_image.jpg
```

成功判据：Downloads 目录出现新图片文件（命名形如 `Gemini_Generated_Image_*.jpg`），大小稳定且 >100KB，并已复制到目标路径。
最后 `bsk session stop <sid>` 归还标签页。

### 关于尺寸与比例（重要）

**不要假定固定尺寸**。输出分辨率随提示词里的比例要求变化，常见情况：

| 提示词比例 | 全尺寸原图（实测/常见） | 页面缩略图（blob，勿采用） |
| --- | --- | --- |
| 横版 16:9（默认） | 2816×1536 | 1024×559 |
| 竖版 9:16 | 1792×3200 / 1536×2816 | 559×1024 |
| 3:4 / 4:3 | 约 1728×2304 / 2304×1728 | 对应缩小 |
| 1:1 | 约 2048×2048 | 对应缩小 |

校验原则（脚本已内置）：**长边 ≥ 1200 即视为全尺寸原图**；若长边仅 ~1024，说明拿到的是页面显示的缩略版本，应检查是否点错了按钮（要的是 "Download full-sized image"）。
用户想要特定比例时，在提示词里明确写出（如"竖屏 9:16 构图""3:4 竖构图"），或在发送前用 `@e<N> button "Open mode picker"` 附近的设置确认；生成后用脚本报告的 `dimensions` 字段如实告知用户实际尺寸，不要自行宣称固定分辨率。

## 参考图上传（v2 实测：剪贴板粘贴是唯一可靠通道）

Gemini 的「上传和工具」按钮打开的是菜单而非文件选择器，`bsk upload`（input/drop 两种模式）都会失败。
可靠做法：把文件放进 Windows 剪贴板（CF_HDROP），聚焦输入框后 Ctrl+V，Gemini 会自动挂为附件。

```python
# ctypes 设置 CF_HDROP（注意 64 位下必须声明 GlobalAlloc/GlobalLock 等的 argtypes/restype）
# 完整实现见本技能 scripts/reference/runtask.py 的 set_clipboard_files()
user32.SetClipboardData(15 /*CF_HDROP*/, hglobal)
# 然后聚焦 rich-textarea 的 contenteditable，bsk press Ctrl+V
```

**上传完成判据（关键！）：**
- 附件缩略图（blob img）粘贴后 1-3 秒即出现，但后台上传还要继续
- 可靠判据：附件区域内 `mat-progress-spinner / [role=progressbar]` 存在 = 仍在上传；消失 = 上传完成
- 实测单张 1.6-2.5MB 需 16-32 秒；多张图必须逐张等待，全部完成后再发送
- 发送按钮的 `aria-disabled` 不可靠（上传中也是 false），不能作为判据

**发送的红线：** 发送键在生成中会变成「停止生成」，脚本重试发送时绝不能在生成中出现时点击，否则会把进行中的生成打断，页面留下 "You stopped this response"。
判断"生成中"要用 `prog`（`mat-progress-spinner / [role=progressbar]`）或响应数增加，**不要用 `loading-indicator / .loading-spinner`**（见第 4 步的坑）。

**账号与语言：**
- 会员(Pro)账号界面为英文，普通账号为中文；按钮 aria-label 必须中英双语匹配（Send message/发送、Download/下载）
- `navigate` 必须用 `https://gemini.google.com/u/1/app`（带 /u/1），不带会落到另一个账号
- 新对话可能默认非 Pro 模式，发送前检查 mode picker 标签并切回 Pro
- 生成耗时随参考图数量增加：超时建议 **900s + 60s×参考图数**。实测同一批任务里，4 张参考图可能 30 秒出图，5 张参考图可能 10 分钟后才给拒绝话术；余量给足，宁等勿误判重跑。

## 批量任务驱动模式（多任务 + 依赖 + 断点续跑）

任务量大时（本项目 27 个任务）不要一个个手敲上面的命令行，用批量驱动脚本。**可直接复用的参考实现就在本技能目录下**：

- `scripts/reference/runtask.py`：单任务完整流程 —— 剪贴板贴参考图 / 等附件区 spinner 消失 / 注入提示词 / 只按 `lastImgs` 判完成 / 拒绝早停 / 基线+轮询收图 / 落盘到指定路径。
- `scripts/reference/batch.py`：任务编排 —— 有序任务表 + 依赖图 + 状态表 + 断点续跑 + `--limit` / `--attempts`。
- `scripts/reference/harvest.py`：把页面上**正在进行或已完成但没被收走**的生成结果补下来（中止任务后抢救用）。
- `scripts/reference/soften_prompts.py`：批量把被安全过滤的提示词改成中性说法（见上文"安全过滤拒绝"）。

⚠️ 这几个脚本里的路径（`BASE`、`TASKS_DIR`、`SESSION`、输出目录）是**歪嘴龙王项目的硬编码值**，复用前先改这几个常量。

设计要点（踩过坑才总结出来的，务必照做）：

1. **依赖判定要看磁盘，不能只看状态表的 `ok` 字段。** 状态表里的历史误判会把下游任务全部 `SKIP-DEP` 卡死。正确做法：`状态表 ok 或 依赖产物文件存在于磁盘且 >100KB` 即视为满足。
2. **产物已存在就跳过**（`out` 文件 >100KB），天然支持断点续跑；进度写 JSON 状态表，避免重复出图浪费额度。
3. **生成的资产要复制进下游任务的参考图目录**，并用统一前缀（本项目 `10-生成-`）区分"生成资产"与"已有素材"（`00-已有-`）。复制动作要延迟到该任务真正运行时执行，因为依赖资产此刻可能还没生成。
4. **任务级重试与单任务级重试分层**：任务失败重试 2–3 次（拒绝有随机性）；单张参考图上传失败重试 3 次。
5. 命令行留两个口子：`--limit N`（每批跑几个，便于分批验收）与 `--attempts N`（每任务尝试几次）。
6. 任务文件夹约定：`提示词.md`（含 `## Gemini 生图提示词` 小节，脚本从其后截取）、`生图说明.md`、`参考图/`。改提示词前先把原文件备份成 `提示词-原始备份.md`。
7. 后台跑 + 日志重定向，用 `TaskOutput` 观察；**中止用工具停任务，不要在浏览器里手动关标签页**。

## 已知失败做法（实测确认，勿再尝试）

| 做法 | 结果 |
| --- | --- |
| `bsk fill` 向 Gemini 输入框写提示词 | 必失败：`fill_target_changed`（编辑器重渲染）。用 evaluate + execCommand('insertText') |
| `bsk upload`（input/drop 模式）传参考图 | 均失败：按钮打开的是菜单而非文件选择器；必须用剪贴板 CF_HDROP + Ctrl+V 粘贴 |
| 附件缩略图一出现就点发送 | 缩略图 1-3 秒即出现，但上传还要 16-32 秒/张；必须等附件区 spinner 消失 |
| 生成中重试点击发送键 | 发送键此时是「停止生成」，会中断响应；只能以 spinner/响应数判断，绝不盲点 |
| `bsk download` 点"Download full-sized image" | 报 `download could not be attributed` 并超时，**但 Chrome 实际已下载成功**——失败的是扩展归因，不是下载本身。故一律改用"基线+目录轮询"检测 |
| `navigator.clipboard.writeText(base64)` | 60 秒超时（无用户激活授权剪贴板） |
| 页面内 `a.download` + click 触发下载 | Agent Window 中被抑制，文件不落盘 |
| canvas `toDataURL` 取 blob 图当原图 | 只能拿到页面显示的缩略版本（长边约 1024）；全尺寸原图无论横竖比例都只能走下载按钮 |
| 页面内 `fetch(blobURL)` | 报 `Failed to fetch`；用 canvas drawImage 代替（仅应急时） |
| 用 PowerShell 工具看结果 | 输出经常不回显；检查结果改用 Python `print`（走 Bash 工具）或写文件后用 Read 工具读 |
| 用 `loading-indicator / .loading-spinner` 判断"是否还在生成" | 出图前 Gemini 处于「正在创建您的图片」状态时该选择器计数为 **0**，会把"还在画"误判成"已完成无图"并提前超时重跑。必须用 `mat-progress-spinner / [role=progressbar]`，或用响应正文里的「正在创建您的图片」文案 |
| 项目目录里出现 `Gemini_Generated_Image_*.jpg` 就当成新产物 | 可能只是**输入参考图的副本**（用户手工另存或早期下载）。用 Read 工具读它和参考图：若提示 "Same image content as previously loaded"，说明内容相同，不是本次生成结果，勿重命名顶替任务产物 |
| 复用上一次的 `session_id` | 浏览器/守护进程重启后旧 session 失效，报 `session not registered or already stopped`。必须重新 `bsk session start` 拿新 id 并重新 `tab borrow` |
| `bsk evaluate` 的 JS 里出现**字面单引号**（尤其写在正则里，如 `(?:no|')t`） | 整条 eval 静默返回空串，正则解析不到、误判成"无结果"。正则里改用 `.` 通配包住该字符，或用 `\u0027` 转义 |

## 环境注意

- 本机 bash 缺 coreutils：`sleep`→`ping -n N 127.0.0.1`；`ls/wc/head/dirname`→用 Python 或 Glob/Read 工具。
- Python 用托管版：`C:/Users/shizh/.workbuddy/binaries/python/versions/3.13.12/python.exe`（无 PIL，验图尺寸用 scripts/ 里的纯 struct 解析）。
- 会话结束必须 `bsk session stop <sid>`（同时归还借用的标签页）。
- 生成内容因模型随机性每次不同；提示词由用户提供或经用户确认。
