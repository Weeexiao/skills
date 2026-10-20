import { readFile } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const [command, name, json = "{}"] = process.argv.slice(2);
if (!command || command === "help") {
  console.log("dshControl list [关键词] | describe <工具名> | call <工具名> '<JSON参数>'\n直接工具调用不经过 DSH 模型；session_prompt 才启动模型。\n环境：DSH_HOME、DSH_AS_MCP_URL、DSH_AS_MCP_TOKEN。仅连接本机 HTTP。输出不自动截断；优先使用工具自身的分页和 limit。");
} else {
  const client = new Client({ name: "dshControl", version: "0.1.0" });
  try {
    if (!["list", "describe", "call"].includes(command)) throw new Error("未知命令，请使用 help");
    if (command !== "list" && !name) throw new Error("缺少工具名");
    const args: unknown = command === "call" ? JSON.parse(json) : {};
    if (!args || typeof args !== "object" || Array.isArray(args)) throw new Error("参数必须是 JSON 对象");
    const endpoint = new URL(process.env.DSH_AS_MCP_URL || "http://127.0.0.1:8790/mcp");
    if (endpoint.protocol !== "http:" || !["127.0.0.1", "[::1]"].includes(endpoint.hostname) || endpoint.username || endpoint.password) {
      throw new Error("仅允许无 URL 凭据的本机 HTTP 地址（127.0.0.1 或 [::1]）");
    }
    const tokenPath = join(process.env.DSH_HOME || join(homedir(), ".dsh"), "dsh-as-mcp", "token");
    const token = process.env.DSH_AS_MCP_TOKEN?.trim() || (await readFile(tokenPath, "utf8").catch((error: NodeJS.ErrnoException) => {
      if (error.code === "ENOENT") throw new Error("桌面插件尚未生成认证令牌；请先加载 dsh-as-mcp，或检查 DSH_HOME 是否对应桌面实例");
      throw error;
    })).trim();
    if (!token) throw new Error("未找到插件认证令牌，请先加载桌面插件");
    await client.connect(new StreamableHTTPClientTransport(endpoint, {
      requestInit: { headers: { Authorization: `Bearer ${token}` }, redirect: "error" },
    }));
    if (command === "call") {
      // ACT: 不重试写入或派单，超时后先查询原任务，防止重复副作用。
      const result = await client.callTool({ name, arguments: args as Record<string, unknown> }, undefined, { timeout: 180000 });
      console.log(JSON.stringify(result));
      if (result.isError) process.exitCode = 1;
    } else {
      let cursor: string | undefined;
      let found = false;
      do {
        const page = await client.listTools(cursor ? { cursor } : {});
        for (const tool of page.tools) {
          if (command === "describe" ? tool.name === name : !name || `${tool.name} ${tool.description || ""}`.toLowerCase().includes(name.toLowerCase())) {
            console.log(JSON.stringify(command === "describe" ? tool : { name: tool.name, description: tool.description }));
            found = true;
          }
        }
        cursor = page.nextCursor;
      } while (cursor);
      if (command === "describe" && !found) throw new Error("工具不存在或尚未授权");
    }
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  } finally {
    await client.close();
  }
}
