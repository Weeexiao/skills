# -*- coding: utf-8 -*-
"""POV 短剧剧本自检器（只读）

检查 Toonflow 格式合规性 + POV 分镜规则。不联网、不写文件、不执行外部命令。

用法:
    python check_pov_script.py <剧本.md> [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TITLE_RE = re.compile(r"^\d+\.\s+\S")
SCENE_RE = re.compile(r"^###\s*场\s*(\d+)\s*-\s*(\d+)\s*$")
PLACE_RE = re.compile(r"^\S+\s+(内|外)\s+\S+")
CAST_RE = re.compile(r"^出场人物：\s*\S")
SFX_RE = re.compile(r"^\[音效：")
BEAT_RE = re.compile(r"^△\s*卡点：")
SHOT_RE = re.compile(r"^△\s+")
DIALOG_RE = re.compile(r"^([^\s（(]+)（([^）]*)）：(.+)$")
NARR_RE = re.compile(r"^旁白（([^）]*)）：(.+)$")

BODY_PREFIX = ("手部", "脚部", "前景肩影")
BODY_RE = re.compile(r"(手部|脚部|前景肩影|我的手|我的脚|我的鞋)")
FORBIDDEN_CHARS = "→●■"
BAD_SHOT_PATTERNS = [
    (re.compile(r"我的(脸|正脸|表情|神情|全身|五官)"), "主角正脸/表情出镜"),
    (re.compile(r"我(回头|扭头|转身)"), "用第三人称写主角动作（回头/转身），应改为「视线急甩」等镜头行为"),
    (re.compile(r"过肩"), "出现 POV 禁用的过肩镜"),
    (re.compile(r"正反打|反打镜头"), "出现 POV 禁用的正反打"),
]
HALF_WIDTH_RE = re.compile(r"[\u4e00-\u9fa5][,;?!]|[,;?!][\u4e00-\u9fa5]")
STANDBODY_WORDS = {"手": "手部", "脚": "脚部", "鞋": "脚部", "影": "影子",
                   "呼吸": "画外呼吸", "喘息": "画外呼吸", "目光": "视线", "视线": "视线"}


def parse(text: str):
    scenes, cur, order, errors = [], None, [], []
    for i, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("## ") or line.startswith("---"):
            break  # 剧本正文结束（后面的附录不校验）
        m = SCENE_RE.match(line)
        if m:
            cur = {"idx": int(m.group(2)), "line": i, "cast": False, "place": False,
                   "sfx": 0, "shots": [], "beats": 0, "dialogs": [], "narr": []}
            scenes.append(cur)
            order.append(cur["idx"])
            continue
        if cur is None:
            continue
        if PLACE_RE.match(line):
            cur["place"] = True
        elif CAST_RE.match(line):
            cur["cast"] = line
        elif SFX_RE.match(line):
            cur["sfx"] += 1
        elif BEAT_RE.match(line):
            cur["beats"] += 1
        elif SHOT_RE.match(line):
            cur["shots"].append((i, line))
        elif NARR_RE.match(line):
            cur["narr"].append((i, line))
        else:
            d = DIALOG_RE.match(line)
            if d:
                cur["dialogs"].append((i, d.group(1), d.group(3)))
            elif not (line.startswith("#") or TITLE_RE.match(line)):
                errors.append((i, "无法识别的行（既非场次/场景/人物/音效/△/台词/旁白）", line[:40]))
    return scenes, order, errors


def check(path: str):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    hard, warn, ok = [], [], []
    scenes, order, errors = parse(text)

    if not scenes:
        hard.append("未找到任何 `### 场1-N` 场次行")
        return hard, warn, ok, {}

    # 标题
    if not TITLE_RE.match(text.lstrip().splitlines()[0]):
        warn.append("首行不是 `1. {标题}` 形式的标题")

    # 场次连续性
    if order != list(range(1, len(order) + 1)):
        hard.append(f"场次编号不连续或非从 1 开始：{order}")
    else:
        ok.append(f"场次编号连续：场1-1 … 场1-{len(order)}")

    # 禁用符号
    bad = [c for c in FORBIDDEN_CHARS if c in text]
    if bad:
        hard.append(f"出现禁用符号：{''.join(bad)}")
    for i, why, _l in errors:
        warn.append(f"第 {i} 行：{why}")

    # 半角标点
    hw = [i for i, ln in enumerate(text.splitlines(), 1) if HALF_WIDTH_RE.search(ln)]
    if hw:
        warn.append(f"疑似中文里混入半角标点，行号：{hw}")

    # 逐场检查
    total_dialog = 0
    beat_total = 0
    kind = {"A": 0, "B": 0, "C": 0}
    standbys = set()
    for s in scenes:
        tag = f"场1-{s['idx']}"
        if not s["place"]:
            hard.append(f"{tag} 缺少场景行（`时间 内/外 地点`）")
        if not s["cast"]:
            hard.append(f"{tag} 缺少 `出场人物：` 行")
        elif "我" not in s["cast"]:
            warn.append(f"{tag} 出场人物里没有「我」")
        if s["sfx"] < 1:
            hard.append(f"{tag} 缺少 `[音效：…]`")
        if not s["shots"]:
            hard.append(f"{tag} 没有任何 `△` 镜头行")
        if s["beats"] > 1:
            warn.append(f"{tag} 有 {s['beats']} 处卡点（每场最多 1 处）")
        beat_total += s["beats"]
        total_dialog += len(s["dialogs"])

        for ln, txt in s["shots"]:
            body = txt[1:].strip()
            for pat, why in BAD_SHOT_PATTERNS:
                if pat.search(txt):
                    hard.append(f"{tag} 第 {ln} 行：{why}")
            if "背影" in body:
                kind["C"] += 1
            elif BODY_RE.search(body):
                kind["B"] += 1
            else:
                kind["A"] += 1
            for k, label in STANDBODY_WORDS.items():
                if k in txt:
                    standbys.add(label)
            if "——" not in txt:
                warn.append(f"{tag} 第 {ln} 行 △ 未用「看的方式——画面」句式，可能写成了小说句")

        for ln, who, line in s["dialogs"]:
            n = len(re.sub(r"[，。！？、…—「」]", "", line))
            if len(line) > 15 or n > 15:
                warn.append(f"{tag} 第 {ln} 行台词 {len(line)} 字（上限 15）：{line[:20]}")
            if who in ("我", "主角"):
                warn.append(f"{tag} 第 {ln} 行主角开口了（POV 应近乎不说话，改用旁白）")

    if beat_total < 3:
        hard.append(f"全片卡点仅 {beat_total} 处（要求 ≥3）")
    else:
        ok.append(f"卡点 {beat_total} 处（≥3）")

    if total_dialog > 12:
        hard.append(f"全片台词 {total_dialog} 句（上限 12）")
    else:
        ok.append(f"台词 {total_dialog} 句（≤12）")

    if kind["C"] > 2:
        hard.append(f"背影抽离镜 {kind['C']} 个（上限 2）")

    shot_total = sum(kind.values())
    if shot_total:
        a = kind["A"] / shot_total
        if not (0.6 <= a <= 0.9):
            warn.append(f"A 主观镜占比 {a:.0%}（建议 60%-90%）")
        else:
            ok.append(f"A 主观镜占比 {a:.0%}")
    ok.append(f"三类镜：A {kind['A']} ｜ B {kind['B']} ｜ C {kind['C']}（共 {shot_total} 镜）")

    if len(standbys) < 2:
        warn.append(f"「主角替身」只用到 {sorted(standbys) or '无'}（建议 ≥2 种）")
    else:
        ok.append(f"主角替身：{'、'.join(sorted(standbys))}")

    stats = {"scenes": len(scenes), "shots": shot_total, "dialogs": total_dialog,
             "beats": beat_total, "kinds": kind}
    return hard, warn, ok, stats


def main() -> int:
    ap = argparse.ArgumentParser(description="POV 短剧剧本自检器（只读）")
    ap.add_argument("script", help="剧本 Markdown 文件路径")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    hard, warn, ok, stats = check(args.script)

    if args.json:
        print(json.dumps({"hard": hard, "warn": warn, "ok": ok, "stats": stats},
                         ensure_ascii=False, indent=2))
        return 1 if hard else 0

    print(f"== POV 剧本自检：{args.script} ==")
    for m in ok:
        print(f"  [OK]   {m}")
    for m in warn:
        print(f"  [WARN] {m}")
    for m in hard:
        print(f"  [FAIL] {m}")
    print(f"-- 结果：{len(hard)} 项不合格，{len(warn)} 项建议 --")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
