#!/usr/bin/env python3
"""Turn a portable evidence index into topic-specific, readable case atlases.

The atlas is a buyer-safe reference: it contains source labels and actual
shot/analysis text, but never the maintainer's absolute local path or raw media.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


KEYWORDS = (
    "开场", "定场", "转场", "音效", "声音", "音乐", "卡点", "匹配", "构图", "特写",
    "远景", "旁白", "结尾", "结构", "叙事", "情绪", "镜头组", "动作", "遮挡", "同构",
)
SLUGS = {
    "企业、工厂宣传片": "01_企业工厂",
    "城市宣传片、旅拍短片": "02_城市旅拍",
    "婚礼类": "03_婚礼",
    "学校毕业季、宣传片、歌颂教师类": "04_学校毕业",
    "政企街道、社区公益、消防公安类短片": "05_政企公益",
    "故事、剧情片": "06_故事剧情",
    "日常vlog、生活记录": "07_Vlog生活",
    "美食类短片": "08_美食",
    "运动、成长、励志类短片": "09_运动成长",
    "露营、小清新 情绪短片": "10_露营情绪",
}


def score(record: dict, max_row: int) -> int:
    text = record["text"]
    points = sum(3 for word in KEYWORDS if word in text)
    points += min(len(text) // 80, 5)
    if record["row"] <= 24:
        points += 3
    # ensure evidence comes from throughout longer sheets, not only the opening.
    if max_row and abs(record["row"] / max_row - 0.5) < 0.08:
        points += 2
    if re.search(r"镜号|景别|时长|转场", text) and len(text) < 90:
        points -= 4
    return points


def main() -> None:
    parser = argparse.ArgumentParser(description="Build topic case-atlas Markdown files from evidence JSONL.")
    parser.add_argument("index", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--per-case", type=int, default=16)
    args = parser.parse_args()
    entries = [json.loads(line) for line in args.index.read_text(encoding="utf-8").splitlines() if line.strip()]
    by_case: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        by_case[entry["case_id"]].append(entry)
    by_topic: dict[str, list[tuple[str, list[dict]]]] = defaultdict(list)
    for case_id, records in by_case.items():
        by_topic[records[0]["topic"]].append((case_id, records))
    args.output.mkdir(parents=True, exist_ok=True)
    master = ["# 秋拾案例图谱", "", "按题材读取对应文件。每个案例都保留了来自其原始拉片表的代表性镜头/分析文字；需要更细的证据时，在 `qiushi-source-evidence.jsonl` 中按案例编号、题材或关键词检索。", ""]
    for topic in sorted(by_topic, key=lambda name: SLUGS.get(name, name)):
        slug = SLUGS.get(topic, re.sub(r"[^\w]+", "_", topic))
        filename = f"{slug}.md"
        master.append(f"- [{topic}]({filename})：{len(by_topic[topic])} 个案例")
        lines = [f"# {topic}｜案例图谱", "", "使用前先读秋拾方法库；本文件用于针对该题材选择更贴近真实案例的镜头组、画面、剪辑和声音策略。下列文字均来自主样本的实际表格行，已移除任何卖家电脑路径。", ""]
        for case_id, records in sorted(by_topic[topic]):
            first = records[0]
            max_row = max(item["row"] for item in records)
            ranked = sorted(records, key=lambda item: (-score(item, max_row), item["row"]))
            selected: list[dict] = []
            chosen_rows: set[tuple[str, int]] = set()
            # Preserve contextual early rows then fill with the best evidence.
            for item in sorted(records, key=lambda value: value["row"]):
                if item["row"] <= 8 and len(item["text"]) > 20 and (item["sheet"], item["row"]) not in chosen_rows:
                    selected.append(item)
                    chosen_rows.add((item["sheet"], item["row"]))
                if len(selected) >= min(5, args.per_case):
                    break
            for item in ranked:
                if len(selected) >= args.per_case:
                    break
                key = (item["sheet"], item["row"])
                if key not in chosen_rows:
                    selected.append(item)
                    chosen_rows.add(key)
            selected.sort(key=lambda item: (item["sheet"], item["row"]))
            lines.extend([
                f"## {case_id}｜{first['source_file']}",
                "",
                f"- 原始工作表：{', '.join(sorted({item['sheet'] for item in records}))}",
                f"- 已收录代表性证据：{len(selected)} 条（完整证据索引可按 `{case_id}` 检索）",
                "",
            ])
            for item in selected:
                lines.append(f"- `{item['sheet']}:{item['row']}`｜{item['text']}")
            lines.append("")
        (args.output / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")
    (args.output / "README.md").write_text("\n".join(master) + "\n", encoding="utf-8")
    print(json.dumps({"topics": len(by_topic), "cases": len(by_case), "entries": len(entries)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
