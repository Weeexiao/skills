#!/usr/bin/env python3
"""估算中文短剧剧本的成片时长，并生成台词台账。

用法：
    python estimate_duration.py 剧本.md
    python estimate_duration.py 剧本.md --rate 4.5 --out 时长表.md
    python estimate_duration.py 剧本.md --ledger 台词台账.md

只依赖标准库。识别以下台词格式：
    **赵叔：**      + “台词”
    **赵叔**        + “台词”
    **赵叔（画外音）：** + “台词”
    赵叔：          + “台词”
"""

import argparse
import json
import math
import re
import sys

SCENE_RE = re.compile(r"^##\s+(.+)$")
LOCATION_RE = re.compile(r"^###\s+(.+)$")
BOLD_ONLY_RE = re.compile(r"^\*\*(.+?)\*\*\s*$")
SPEAKER_COLON_RE = re.compile(r"^([\u4e00-\u9fa5A-Za-z]{2,6})[：:]\s*$")
INLINE_SPEAKER_RE = re.compile(r"^(.+?)[：:]\s*$")
QUOTE_START = ("“", "\"", "‘")

SKIP_NAMES = {"字幕", "人物", "类型", "建议时长", "画面定格", "定格", "注", "时间", "地点"}
SUFFIXES = ("心想", "画外音", "内心", "旁白", "独白")


def normalize_speaker(name):
    name = name.strip().strip("*").strip()
    name = re.sub(r"[（(][^)）]*[)）]", "", name)
    name = re.split(r"[，,]", name)[0].strip()
    name = INLINE_SPEAKER_RE.sub(r"\1", name).strip()
    for suffix in SUFFIXES:
        if name.endswith(suffix) and len(name) > len(suffix):
            return name[: -len(suffix)]
    return name


def count_chars(text):
    """中文字/字母按 1 计；连续数字按每 2 位 1 个音节估。"""
    total = 0
    i = 0
    while i < len(text):
        ch = text[i]
        if ch.isdigit():
            j = i
            while j < len(text) and text[j].isdigit():
                j += 1
            total += max(1, math.ceil((j - i) / 2))
            i = j
            continue
        if "\u4e00" <= ch <= "\u9fff" or ch.isalpha():
            total += 1
        i += 1
    return total


def parse(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        raw_lines = f.read().splitlines()

    scenes = []
    current = None
    speaker = None
    buffer = []

    def flush():
        nonlocal buffer
        if buffer and current is not None:
            text = "".join(buffer).strip()
            if text:
                current["lines"].append({"speaker": speaker or "旁白", "text": text})
        buffer = []

    for line in raw_lines:
        s = line.strip()

        if not s:
            flush()
            continue

        if s.startswith("# ") or s.startswith("---"):
            flush()
            speaker = None
            continue

        m = SCENE_RE.match(s)
        if m:
            flush()
            speaker = None
            current = {"title": m.group(1).strip(), "location": "", "lines": []}
            scenes.append(current)
            continue

        m = LOCATION_RE.match(s)
        if m:
            flush()
            if current is not None:
                current["location"] = m.group(1).strip()
            continue

        if s.startswith(QUOTE_START):
            buffer.append(s.strip("“”\"‘’"))
            if s.endswith(("”", "\"", "’")) and len(s) > 1:
                flush()
            continue

        flush()

        m = BOLD_ONLY_RE.match(s)
        if m:
            content = m.group(1).strip()
            name = None
            if not re.search(r"[。！？]", content):
                inline = INLINE_SPEAKER_RE.match(content)
                if inline and inline.group(1).strip() not in SKIP_NAMES:
                    name = inline.group(1).strip()
                elif len(content) <= 12 and not re.search(r"[；、]", content):
                    name = content
            if name:
                speaker = normalize_speaker(name)
                continue

        m = SPEAKER_COLON_RE.match(s)
        if m and m.group(1) not in SKIP_NAMES:
            speaker = normalize_speaker(m.group(1))
            continue

        speaker = None

    flush()
    return [sc for sc in scenes if sc["lines"] or sc["location"]]


def analyze(scenes, rate, pause, overhead):
    scene_rows = []
    ledger = []
    speakers = {}
    cumulative = 0.0
    index = 1

    for sc in scenes:
        chars = 0
        seconds = 0.0
        for item in sc["lines"]:
            c = count_chars(item["text"])
            d = c / rate + pause
            chars += c
            seconds += d
            ledger.append(
                {
                    "id": f"D{index:02d}",
                    "scene": sc["title"],
                    "speaker": item["speaker"],
                    "text": item["text"],
                    "chars": c,
                    "seconds": d,
                }
            )
            speakers.setdefault(item["speaker"], {"lines": 0, "chars": 0, "seconds": 0.0})
            speakers[item["speaker"]]["lines"] += 1
            speakers[item["speaker"]]["chars"] += c
            speakers[item["speaker"]]["seconds"] += d
            index += 1

        total_scene = seconds + (overhead if sc["lines"] else 0)
        cumulative += total_scene
        scene_rows.append(
            {
                "title": sc["title"],
                "location": sc["location"],
                "lines": len(sc["lines"]),
                "chars": chars,
                "seconds": total_scene,
                "cumulative": cumulative,
            }
        )

    return scene_rows, ledger, speakers, cumulative


def render(scene_rows, speakers, total, args):
    out = ["# 时长表", ""]
    out.append(f"口播语速 {args.rate} 字/秒，每句停顿 {args.pause} 秒，每场转场 {args.overhead} 秒。")
    out.append("")
    out.append("| 场次 | 台词条数 | 字数 | 预估秒 | 累计 |")
    out.append("| --- | --- | --- | --- | --- |")
    for row in scene_rows:
        out.append(
            f"| {row['title']} | {row['lines']} | {row['chars']} | "
            f"{row['seconds']:.1f} | {row['cumulative']:.1f} |"
        )
    out.append("")
    out.append(f"**总时长：{total:.1f} 秒**")
    out.append("")

    out.append("## 按角色统计")
    out.append("")
    out.append("| 角色 | 台词条数 | 字数 | 说话秒数 | 占比 |")
    out.append("| --- | --- | --- | --- | --- |")
    for name, data in sorted(speakers.items(), key=lambda kv: kv[1]["seconds"], reverse=True):
        share = data["seconds"] / total * 100 if total else 0
        out.append(
            f"| {name} | {data['lines']} | {data['chars']} | "
            f"{data['seconds']:.1f} | {share:.0f}% |"
        )
    out.append("")

    warnings = []
    if total < 60:
        warnings.append(f"总时长 {total:.1f} 秒，短于 60 秒：加一场加码或甜头兑现，不要拉长单句。")
    elif total > 110:
        warnings.append(f"总时长 {total:.1f} 秒，超过 110 秒：先删重复解释，再合并场次，最后才删台词。")
    else:
        warnings.append(f"总时长 {total:.1f} 秒，在可用区间内。")

    long_lines = [x for x in args.ledger_data if x["chars"] > 15]
    if long_lines:
        samples = "；".join(f"{x['id']}（{x['chars']}字）" for x in long_lines[:6])
        warnings.append(f"有 {len(long_lines)} 句超过 15 字：{samples}")

    qian = [x for x in args.ledger_data if x["speaker"] == "老钱" and x["chars"] > 60]
    if qian:
        samples = "；".join(f"{x['id']}（{x['chars']}字）" for x in qian)
        warnings.append(f"老钱有 {len(qian)} 段超过 60 字：{samples}")

    empty = [r["title"] for r in scene_rows if r["lines"] == 0]
    if empty:
        warnings.append("没有台词的场次：" + "、".join(empty))

    out.append("## 提示")
    out.append("")
    for w in warnings:
        out.append(f"- {w}")
    out.append("")
    return "\n".join(out)


def render_ledger(ledger):
    out = ["# 台词台账", ""]
    out.append("| 编号 | 场次 | 角色 | 台词 | 字数 | 预估秒 |")
    out.append("| --- | --- | --- | --- | --- | --- |")
    for row in ledger:
        text = row["text"].replace("|", "｜")
        out.append(
            f"| {row['id']} | {row['scene']} | {row['speaker']} | {text} | "
            f"{row['chars']} | {row['seconds']:.1f} |"
        )
    out.append("")
    return "\n".join(out)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="中文短剧剧本时长估算")
    parser.add_argument("input", help="剧本 Markdown 文件")
    parser.add_argument("--rate", type=float, default=4.5, help="口播语速，字/秒，默认 4.5")
    parser.add_argument("--pause", type=float, default=0.35, help="每句停顿秒数，默认 0.35")
    parser.add_argument("--overhead", type=float, default=1.0, help="每场转场秒数，默认 1.0")
    parser.add_argument("--out", help="时长表输出路径")
    parser.add_argument("--ledger", help="台词台账输出路径")
    parser.add_argument("--json", action="store_true", help="额外输出 JSON 摘要")
    args = parser.parse_args()

    scenes = parse(args.input)
    if not scenes:
        raise SystemExit("没有解析到场次或台词，检查剧本格式（场次用 ##，台词用中文引号）")

    scene_rows, ledger, speakers, total = analyze(scenes, args.rate, args.pause, args.overhead)
    args.ledger_data = ledger

    text = render(scene_rows, speakers, total, args)
    print(text)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")

    if args.ledger:
        with open(args.ledger, "w", encoding="utf-8") as f:
            f.write(render_ledger(ledger) + "\n")

    if args.json:
        print(
            json.dumps(
                {
                    "total_seconds": round(total, 1),
                    "scenes": [
                        {
                            "title": r["title"],
                            "lines": r["lines"],
                            "chars": r["chars"],
                            "seconds": round(r["seconds"], 1),
                        }
                        for r in scene_rows
                    ],
                    "speakers": {
                        k: {"lines": v["lines"], "chars": v["chars"], "seconds": round(v["seconds"], 1)}
                        for k, v in speakers.items()
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
