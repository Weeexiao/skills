# DSH Orchestrator

目标：减少 Codex 用量，同时保持成果质量。

- 小任务：Codex 直接调用本机工具。
- DSH 独有能力：通过 MCP 直接调工具，不额外调用 DSH 模型。
- 大块独立任务：交 DSH 模型闭环执行；复杂任务先确定方案，最后做一次必要验收。

选用 [dsh-as-mcp](https://github.com/xiseliuli/dsh-as-mcp) 复用桌面宿主、会话与认证，附带 TypeScript 命令行客户端。详细安装、命令、候选对比及验证状态见 [连接说明](references/connection.md)；行为规则见 [SKILL.md](SKILL.md)。

将本目录（合集内 `tooling/dsh-orchestrator`）放入 Codex 的 skills 目录。命令行依赖需在 scripts 中显式安装；技能本身不自动安装桌面插件、不赋予权限。当前桌面链路仍待插件加载后实测，不能把客户端检查通过当作已经接通。

不上传凭据、node_modules、会话日志或业务文件，不承诺固定节省比例。

## 新电脑使用

将仓库安装到目标 Codex 技能目录后，对 Codex 发送：

> 使用 $dsh-orchestrator，检查这台电脑是否已有 DSH 和 dsh-as-mcp。已有就复用，没有则按技能下载安装并部署；完成认证、只读工具调用与桌面记录验证。小任务直接做，大块独立任务才委派模型。

技能包含检查、固定版本下载、普通 profile/桌面 profile 两条安装路径、配置合并、客户端依赖安装、可选 MCP 注册、故障处理和回滚。代理应执行这些步骤；登录、系统权限或桌面有活跃任务等无法自动解决的环节会明确报告，安装技能本身不等于所有软件已经安装。

## 安装与依赖

本技能已并入 `Weeexiao/skills`，旧独立仓库地址不再使用。优先复用你已有的合集克隆和目录联接；新增机器可按合集根 README 的单克隆方案安装。只安装本技能的 macOS/Linux 示例：

```bash
git clone --depth 1 --filter=blob:none --sparse git@github.com:Weeexiao/skills.git "$HOME/skillsSource"
git -C "$HOME/skillsSource" sparse-checkout set tooling/dsh-orchestrator
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
ln -s "$HOME/skillsSource/tooling/dsh-orchestrator" "${CODEX_HOME:-$HOME/.codex}/skills/dsh-orchestrator"
```

目标目录已存在时先检查，不覆盖；Windows 按合集 README 创建指向同一子目录的 junction。SSH 未配置时可改用 HTTPS 克隆。安装后让客户端发现技能，必要时新开对话。

依赖：兼容插件要求的 Node.js、npm、已安装的 DSH，以及 `scripts/package.json` 中的 MCP SDK/tsx。由代理在 scripts 目录显式执行 `npm ci --ignore-scripts`；随后按连接说明检测并部署桌面插件。

## 文件

- `SKILL.md`：分流、节约用量规则与派单前的技能到位检查。
- `references/connection.md`：检测、下载、部署、验证、故障处理及回滚。
- `references/blenderSkills.md`：DSH 内置 30 个 Blender 技能的用途速查、"什么情况调用哪个"路由表，以及协作前的到位检查清单。
- `references/desktopConfig.json`：用于合并的插件配置对象。
- `scripts/dshControl.ts` 及依赖清单：按需发现和调用接口的命令行入口。

## 派单前先查技能

技能注册、运行时可用、路径可写是三件独立的事。典型陷阱：Blender 技能全部注册成功，但 `blender` 不在 PATH，`blender_status` 返回 `spawn blender ENOENT`，此时任何 Blender 任务都产不出文件。

要 Blender 就查 `blender_status.available` 且版本真实；要命令就跑一次最小调用；确认隔离目录可写。三项全过再派单。详见 [Blender 技能路由](references/blenderSkills.md)。
