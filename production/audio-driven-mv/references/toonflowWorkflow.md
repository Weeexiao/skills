# Toonflow 当前接口经验

以下为实际使用过的接口形态，版本变化时以 tools/list、getAppState 和节点返回的 schema 为准，不硬编码旧连接。

## 本机连接与画布

- MCP `tools/call` 参数：`{name:"getAppState",arguments:{}}`。
- 从 connections 按用户目标 directory、canvasId 选择；多个匹配时不要随机操作。
- 其他命令常见参数：`{name,arguments:{target:{connectionId},args:{...}}}`。
- `getCanvas` 读取当前画布；`addNode` 创建节点；`connectNodes` 接线；`fitCanvas` 定位新节点。
- 结果可能在 structuredContent.details 或 details 中，检查 isError，不能只看 HTTP 200。

## 节点与引用

当前节点类型包括 remote-imageNode、remote-audioNode、remote-textNode、remote-videoGenerationNode。`addNode` 使用 `{type,label,position:{x,y}}`，返回实际 node.id。

`nodeTools` 的参数为 `{nodeId,name,args}`：

| 函数 | 常见参数 |
| --- | --- |
| node:setImage / node:setAudio / node:setVideo | `{path:"assets/segmentOne/frame.png",mimeType:"image/png"}`，类型对应实际媒体 |
| node:setText | `{text}` |
| node:getConfig | `{}`，发现工作流与参数 |
| node:setConfig | providerId、modelId、ratio、duration、parameters，以当前 schema 为准 |
| node:setPrompt | `{prompt}` |
| node:validatePrompt | `{}`，返回编译后的 prompt 和 references |
| node:generateVideo | `{}`，立即保存 requestId；此动作可能付费 |
| node:getGenerationStatus | `{}`，查询本地状态和输出 |
| node:recoverVideo | `{}`，查询并接回原任务，不重新生成 |

`connectNodes` 常见参数：

```json
{"connections":[
  {"source":"图片节点ID","sourceHandle":"image","target":"生成节点ID","targetHandle":"in"},
  {"source":"音频节点ID","sourceHandle":"audio","target":"生成节点ID","targetHandle":"in"}
]}
```

该接线顺序下通常 `{{ref 1}}` 为图、`{{ref 2}}` 为音频。必须查看 validatePrompt 的实际映射。图像引用可能编译为 Subject/Picture，音频为 Audio。定义使用“引用 + 简短稳定名称 + 破折号 + 解释”，帮助身份名称校验。

歌曲对口型默认使用当前可用的 runningHub / h3DigitalHuman。当前接口示例：一张图片映射 picture1，一段实际歌曲映射 audio1；parameters 为 duration、audioStart、longEdge、fps。完整分段 WAV 通常使用 duration=0、audioStart=0；1280 长边、24fps 是验证过的规格示例，不覆盖用户选择。不要给它传通用工作流的 megapixels、upscale 或把 0 强行改成 4–15 秒。

validatePrompt 应返回普通动作正文、一图一音频的真实槽位；不应被扩写成六段。h3-video 的 duration、megapixels、upscale 仅适用于该通用全能参考路径。实例、远端任务和本机连接 ID 不随包分发。

“无限分段长视频”是工作流标称能力，不是模型单次无限生成的证明。完整音频参数已验证；内部如何分块、承接尾帧、融合画面或封装原音轨尚未查证。长片先核对平台实际上限和消耗，检查分段接缝、口型漂移与身份变化。

## 任务恢复

如果前端报文件占用但上游已有 taskId：优先 recoverVideo，等待恢复，再查状态。不要点 generateVideo。

支持任务中心的版本可刷新原任务；原项目 tasks/refresh 接口为 POST，接收 `{directory,id,refreshUsage?}`，其中 id 是本地任务记录 ID，非 requestId。必须通过目标应用提供的授权方式访问，不猜端口或绕过访问限制。直接调用需先查看该版本路由定义。

成功后保存原生输出；裁尾版本通过 setVideo 绑定，保留原生历史。如果恢复操作回填了原生视频，再将裁尾版重新绑定。确认画布保存后备份 JSON 和 assets。
