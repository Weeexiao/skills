import { resolve, dirname, join } from "node:path";
import { access, link, unlink } from "node:fs/promises";

const options = new Map<string, string>();
for (let index = 2; index < process.argv.length; index += 2) {
  if (!process.argv[index].startsWith("--") || !process.argv[index + 1]) throw new Error("参数应为 --key value");
  options.set(process.argv[index].slice(2), process.argv[index + 1]);
}
const videoArg = options.get("video");
const audioArg = options.get("audio");
const outputArg = options.get("out");
if (!videoArg || !audioArg || !outputArg) throw new Error("用法：bun trimToAudio.ts --video native.mp4 --audio audio.wav --out clip.mp4");
const video = resolve(videoArg);
const audio = resolve(audioArg);
const output = resolve(outputArg);
if ([video.toLowerCase(), audio.toLowerCase()].includes(output.toLowerCase())) throw new Error("输出不能覆盖输入");
try { await access(output); throw new Error("输出已存在，请使用新的文件名"); } catch (error: any) { if (error.code !== "ENOENT") throw error; }

async function run(args: string[]) {
  const child = Bun.spawn(args, { stdout: "pipe", stderr: "pipe" });
  const [stdout, stderr, code] = await Promise.all([new Response(child.stdout).text(), new Response(child.stderr).text(), child.exited]);
  if (code) throw new Error(`${args[0]} 失败：${stderr}`);
  return stdout;
}
async function probe(path: string) {
  return JSON.parse(await run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path]));
}
const reference = await probe(audio);
const original = await probe(video);
const videoStream = original.streams.find((stream: any) => stream.codec_type === "video");
const audioStream = original.streams.find((stream: any) => stream.codec_type === "audio");
const duration = Number(reference.format.duration);
if (!reference.streams.some((stream: any) => stream.codec_type === "audio") || !videoStream || !audioStream || !Number.isFinite(duration) || duration <= 0) throw new Error("需要有效参考音频及自带音轨的视频");
const rate = videoStream.r_frame_rate.split("/").map(Number);
const fps = rate[0] / rate[1];
if (!Number.isFinite(fps) || fps <= 0 || videoStream.r_frame_rate !== videoStream.avg_frame_rate) throw new Error("需固定且有效帧率，变帧率视频请人工处理");
const videoDuration = Number(videoStream.duration ?? original.format.duration);
const audioDuration = Number(audioStream.duration ?? original.format.duration);
if (Math.min(videoDuration, audioDuration) + 0.001 < duration) throw new Error("原生音视频短于参考音频，不能通过裁尾补齐");
const frames = Math.floor(duration * fps);
if (frames < 1) throw new Error("参考长度不足一帧");
const temporary = join(dirname(output), `trim${crypto.randomUUID().replaceAll("-", "")}.mp4`);
try {
  await run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-n", "-i", video, "-map", "0:v:0", "-map", "0:a:0", "-vf", `trim=end_frame=${frames},setpts=PTS-STARTPTS`, "-af", `atrim=end=${duration},asetpts=PTS-STARTPTS`, "-t", String(duration), "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", temporary]);
  const result = await probe(temporary);
  const actual = Number(result.format.duration);
  if (!Number.isFinite(actual) || Math.abs(actual - duration) > 0.01 || result.streams.filter((stream: any) => ["audio", "video"].includes(stream.codec_type)).length !== 2) throw new Error("输出时长或音视频流验证失败");
  // 同目录硬链接以独占方式发布成片，避免并发覆盖已有输出。
  await link(temporary, output);
  console.log(JSON.stringify({ output, referenceDuration: duration, outputDuration: actual, frames, fps, soundtrack: "nativeVideoAudio" }, null, 2));
} finally {
  await unlink(temporary).catch((error: any) => { if (error.code !== "ENOENT") throw error; });
}
