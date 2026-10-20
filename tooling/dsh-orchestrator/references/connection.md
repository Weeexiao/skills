# 连接、部署与迁移

## 选型（2026-10-20 审计）

- [dsh-as-mcp](https://github.com/xiseliuli/dsh-as-mcp)：选用 0.1.5。宿主进程插件，支持桌面会话、文件、shell 与原生工具调用；`dsh_tool_call` 不需要模型轮次。已有 stdio 转 HTTP 入口，无需重写 MCP 服务。
- [desktop bridge](https://github.com/Cryocell77/deepseek-harness-desktop-mcp-bridge)：实验性桌面任务桥，适合整块委派；版本兼容受限制。
- [dsh-sdk-mcp](https://github.com/ELRdn/DSH-SDK-MCP)：SDK 会话与并行 worker，独立实例不等于当前桌面。
- [dsh-cursor-codex](https://github.com/jeremy9682/dsh-cursor-codex)：有 ACP/MCP 配置；未在本机验证桌面兼容，不默认采用。
- `@ipumpkin/dsh-mcp-server`：本次 npm 查询返回 404，不能按旧说明直接安装。

## 桌面插件

先核对当前 DSH 版本、Home、profile、已有插件与工作状态，不复制旧电脑的凭据。当前本机桌面版本 0.2.1-rc.2；模型以实际配置为准。安装不会因为读了技能就自动完成。

按上游 README 安装固定版本 `dsh-as-mcp@0.1.5`。桌面 profile 由应用管理，普通 CLI plugin add 可能拒绝；上游提供在实际 profile 内用包管理器添加包，再在 `cordis.patch.yml` insert 插件的方法。修改前备份依赖清单、锁文件和 patch；保留其他插件配置，不能把已有 patch 整体替换成示例，也不要同时使用 bundle 与 patch 注册同一个插件。

仅监听 `127.0.0.1`，使用自动生成的私有 token；保留 `approval.policy: inherit`。启用 `tools.agentTools`。`agentTools.allow` 非空时会替换默认名单；只有确需额外能力时明确加入原生工具，不自动关闭宿主权限保护。所谓开放接口仅限该实例已注册且已授权的能力，并非任意内部 API。

桌面需重启才能加载插件。检测到用户其他任务运行时不强制重启；完成文件和配置准备，报告尚待重启验证。回滚时仅恢复本次改动，不清空用户原配置。

## 新电脑完整部署流程

本节由使用技能的代理执行，不让用户手动转发命令。用户说“部署此 skill”即授权本技能所需的检查、下载、依赖安装及局部配置；不包括改模型费用来源、关闭认证或终止其他任务。完成一步再继续下一步，失败报告具体环节。

### 1. 先检查，不重复安装

- 找到实际技能目录、操作系统、Node/npm/pnpm、DSH CLI 和桌面应用。macOS 可检查 `/Applications/DeepSeek Harness.app/Contents/Resources/runtime/cli/bin/dsh`；其他系统从已安装应用和 PATH 发现，不能照搬此路径。
- 执行实际 CLI 的 `--version` 和 `--help`；检查桌面设置/启动配置确定 DSH Home、profile 与当前模型。默认 Home 常为 `~/.dsh`，桌面 profile 常为 `desktop`，但必须核实。
- 只读检查目标 profile 的 package.json、依赖解析出的 `dsh-as-mcp/package.json` 和 `cordis.patch.yml`。不要打印含账户信息的完整配置。区分：未安装、装了未注册、已注册未启动、端点可达但认证失败、已可正常调用。
- 插件已安装且可用：直接跳到第 5 步验证；未加载的现有插件先修配置，不重复加新桥。端口由实际配置确定；不要把“端口没监听”误判为“包没安装”。
- 检查 DSH 是否有活跃任务。下载、安装技能依赖可继续；需要重启桌面时等待空闲，不强制终止任务。

### 2. 缺少组件时从哪里下载

- DSH 桌面从 DeepSeek 官方发布渠道获取；在目标机器联网核实官方来源，不将社区桥当作 DSH 本体。账户登录和必要系统授权由用户完成，技能不能代为获得账户。
- 插件首选 npm 发布包：[dsh-as-mcp](https://www.npmjs.com/package/dsh-as-mcp)，源码：[xiseliuli/dsh-as-mcp](https://github.com/xiseliuli/dsh-as-mcp)。本流程基线固定 0.1.5，不自动追 latest；新 DSH 版本先查上游兼容说明。
- Node 需满足该版本包声明的 engines；从 [Node 官方](https://nodejs.org/) 获取，优先复用已安装兼容版本。pnpm 优先使用 DSH 自带或已经可用的版本，不为安装插件改写用户全局工具链。
- 本技能来自 [Weeexiao/skills 的 tooling/dsh-orchestrator](https://github.com/Weeexiao/skills/tree/main/tooling/dsh-orchestrator)。克隆合集后只安装这个子目录，不能把合集根目录当成技能目录；已有目录检查来源和未提交修改后再更新，禁止覆盖。

下载预编译插件（在专用下载目录执行）：

```bash
npm view dsh-as-mcp@0.1.5 version engines dist.integrity
npm pack dsh-as-mcp@0.1.5 --ignore-scripts
```

使用实际生成的绝对 tgz 路径安装。npm 不可达时可从源码构建：固定审阅过的 commit，按其 packageManager 安装依赖、执行上游 build、pack；不要把未经构建的源码当成发布包。不要无条件放行所有依赖安装脚本。上述路径不可用就报告阻碍，不从不明镜像下载。

### 3. 已有插件怎么部署；没有插件怎么安装

先备份目标 profile 的 package.json、实际锁文件和 cordis.patch.yml，保存到用户私有备份目录，记录哪些文件原本不存在。不要把备份提交 GitHub。

普通可管理 profile：按当前 `dsh plugin --help` 支持的语法安装下载的固定版本包，例如：

```bash
dsh plugin --profile <实际名称> add /绝对路径/dsh-as-mcp-0.1.5.tgz
```

此路径由 bundle 注册插件，不再手工 insert 第二份。安装后只定向核对插件注册，不将整份 `--dump-config` 输出到聊天。

桌面保留 profile 若拒绝 CLI 管理：按上游 Desktop 章节，在已确认的 profile 目录用原包管理器安装该 tgz，例如：

```bash
pnpm add /绝对路径/dsh-as-mcp-0.1.5.tgz
```

随后将下述条目合并进该 profile 的 cordis.patch.yml 顶层列表；已有同 id 则更新该条目，不追加重复项。原文件是 `[]` 时才可替换空列表；复杂配置不直接文本拼接。不要同时加入 `dsh.profile.bundles`。

```yaml
- insert:
    - id: dsh-as-mcp
      name: dsh-as-mcp
      config:
        http:
          enabled: true
          host: 127.0.0.1
          port: 8790
          path: /mcp
          mountOnWebServer: false
        tools:
          workspace: true
          session: true
          files: true
          shell: true
          agentTools: true
        agentTools:
          allow: []
          deny: []
        approval:
          policy: inherit
```

等价 config 对象见 [desktopConfig.json](desktopConfig.json)。空 allow 使用上游默认名单，不表示全部工具都已开放。若已有插件配置了自定义 allow/deny，保留原设置；能力不足时仅增加确需的工具。端口冲突时选择空闲本机端口并同步客户端，不能停止未知进程。确认单一注册后，空闲时正常退出并重新打开桌面；有活跃任务则记录“待重启”，不要声称已完成连通。

### 4. 安装技能客户端并选择调用方式

在此技能的 scripts 目录执行 `npm ci --ignore-scripts`（随技能提供锁文件）。这是显式部署步骤，不绑定到每次调用命令。先运行下文 help，然后用实际 DSH_HOME 和端口连接；自动生成 token 的文件由宿主保护，不打印内容。

默认只使用命令行入口，避免额外注入全套 MCP schema。如果用户需要将插件常驻注册到 Codex：先检查已有同名 MCP 条目，保留其他配置；使用目标环境实际支持的 MCP 注册方式，命令为 Node，参数为插件已安装位置的 `bin/mcp-stdio.mjs` 绝对路径，环境提供实际 DSH_HOME 和 DSH_AS_MCP_URL。它会自行读本地 token 文件，不把 token 写进配置。不要同时装多个重复桥。需要新开对话加载时明确告知；CLI 通道仍可直接验证。

### 5. 验证、保存本机状态及恢复

先执行 `call dsh_info '{}'`，再 `call workspace_list '{}'`。用 describe 查询 session_create 等真实参数；在专用验证目录新建独立会话，不占用用户其他会话。示例仅用于参数结构，路径和 ID 用真实返回值：

```text
session_create {"cwd":"<本机验证目录>"}
dsh_tool_list {"sessionId":"<返回的会话ID>"}
dsh_tool_call {"sessionId":"<同一ID>","name":"<已列出的只读工具>","args":{按该工具schema填写}}
```

直接工具通道不发 session_prompt。需要验证模型委派时再发送一句不改文件的短任务，使用 wait:false，保存 ID 后定向查询；不要默认开展付费大任务。新建会话的默认模型可能不同于当前打开会话，调用模型前确认 provider/model，不能推断“共享桌面”就必定共享前台模型。

在桌面核对同一 session 和调用记录。记录本机版本、Home/profile、端点、插件版本、注册方式、备份位置、session ID、通过的验证及限制；保存到私有本机记录，不将这些机器状态写回通用技能。成功标准包含认证、实际工具调用与桌面可见，少一步就报告对应未完成项。

- 401：核对 Home、token 来源与端点，不能关闭认证。
- connection refused：检查插件注册、加载日志和监听端口，不重复安装所有组件。
- 工具不可见：检查 tools.agentTools、会话 preset 及 allow/deny，保留 guard。
- 安装/启动失败：仅撤销此次插件条目与依赖；无其他并发修改时恢复备份，否则定向合并回滚，禁止整体清空 patch。
- 完成后再次部署：先检查现状，验证通过即复用，不重复建会话或安装依赖。

## 精简命令行

在技能的 `scripts` 目录显式执行一次 `npm install --ignore-scripts`。调用：

```bash
npx --no-install tsx dshControl.ts help
npx --no-install tsx dshControl.ts list session
npx --no-install tsx dshControl.ts describe dsh_tool_call
npx --no-install tsx dshControl.ts call dsh_info '{}'
```

支持 `DSH_HOME`、`DSH_AS_MCP_URL`、`DSH_AS_MCP_TOKEN`。默认从该 Home 的 `dsh-as-mcp/token` 读取，不输出令牌、不跟随 HTTP 重定向。默认连接 `http://127.0.0.1:8790/mcp`；端口按本机配置设置。不要把令牌写进命令、仓库或聊天。

依次验证：合法认证 → dsh_info 确认服务 → workspace/session 查询 → 创建独立会话 → 调用一个只读原生工具 → 桌面核对记录。只有最后验证通过才声称桌面复用成功。需要模型时再发一条短任务，不能用普通对话成功替代工具验证。

MCP 客户端需要 stdio 时直接复用上游包的 `bin/mcp-stdio.mjs`，不要另外造一套转发协议；命令行入口用于避免将整批接口 schema 反复放入 Codex 上下文。新 MCP 配置可能需新会话加载，以实际客户端为准。

失败时报告通过到哪一步，先查原任务再重试；旧独立桥可回退但必须明确不是桌面。不要关闭认证绕过 401。

## 迁移与建模

迁移技能及 scripts 的源码、依赖清单；不迁移 node_modules、token、会话日志和整份机器配置。新电脑重新安装依赖、插件并验证。Blender 能力另验本机路径、插件兼容及实际工程/渲染，不能以文字报告替代交付。
