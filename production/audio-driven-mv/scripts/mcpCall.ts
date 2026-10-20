import { readFile, writeFile } from "node:fs/promises";

const options = new Map<string, string>();
for (let index = 2; index < process.argv.length; index += 2) {
  if (!process.argv[index].startsWith("--") || !process.argv[index + 1]) throw new Error("参数应为 --key value");
  options.set(process.argv[index].slice(2), process.argv[index + 1]);
}
const runtimePath = options.get("runtime");
const method = options.get("method");
const paramsPath = options.get("params");
if (!runtimePath || !method || !paramsPath) throw new Error("用法：bun mcpCall.ts --runtime runtime.json --method tools/call --params request.json [--out response.json]");
const runtime = JSON.parse(await readFile(runtimePath, "utf8"));
if (typeof runtime.url !== "string" || typeof runtime.token !== "string" || !runtime.token) throw new Error("运行时文件缺少 url 或 token");
const url = new URL(runtime.url);
if (!["localhost", "127.0.0.1", "[::1]"].includes(url.hostname) || !["http:", "https:"].includes(url.protocol)) throw new Error("此助手仅用于本机 Toonflow MCP");
const params = JSON.parse(await readFile(paramsPath, "utf8"));
const headers: Record<string, string> = { "Content-Type": "application/json", Accept: "application/json, text/event-stream", Authorization: `Bearer ${runtime.token}` };

function parseResponse(body: string) {
  if (!body.trimStart().startsWith("event:") && !body.trimStart().startsWith("data:")) return JSON.parse(body);
  const blocks = body.replaceAll("\r\n", "\n").split("\n\n");
  for (const block of blocks) {
    const data = block.split("\n").filter(line => line.startsWith("data:")).map(line => line.slice(5).trimStart()).join("\n");
    if (data && data !== "[DONE]") {
      const parsed = JSON.parse(data);
      if (parsed.id !== undefined) return parsed;
    }
  }
  throw new Error("MCP 响应中没有 JSON-RPC 结果");
}

async function request(id: number, requestMethod: string, requestParams: unknown) {
  const response = await fetch(url, { method: "POST", headers, signal: AbortSignal.timeout(120000), body: JSON.stringify({ jsonrpc: "2.0", id, method: requestMethod, params: requestParams }) });
  const session = response.headers.get("mcp-session-id");
  if (session) headers["mcp-session-id"] = session;
  const body = await response.text();
  if (!response.ok) throw new Error(`MCP HTTP ${response.status}；请检查本机应用和授权配置`);
  const payload = parseResponse(body);
  if (payload.error) throw new Error(`MCP JSON-RPC 错误 ${payload.error.code}：${payload.error.message}`);
  return payload;
}

await request(0, "initialize", { protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "audioDrivenMv", version: "1.0.0" } });
const notification = await fetch(url, { method: "POST", headers, signal: AbortSignal.timeout(30000), body: JSON.stringify({ jsonrpc: "2.0", method: "notifications/initialized" }) });
await notification.text();
if (!notification.ok) throw new Error(`MCP 初始化通知失败：HTTP ${notification.status}`);
const payload = await request(1, method, params);
const output = options.get("out");
if (output) await writeFile(output, JSON.stringify(payload, null, 2), { flag: "wx" });
else console.log(JSON.stringify(payload.result?.structuredContent ?? payload));
if (payload.result?.isError) process.exitCode = 1;
