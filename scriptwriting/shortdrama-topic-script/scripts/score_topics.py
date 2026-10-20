#!/usr/bin/env python3
"""加权评分与一票否决检查。

用法：
    python score_topics.py candidates.json
    python score_topics.py candidates.json --out ranking.md
    python score_topics.py --demo

输入格式（对象或数组均可）：
{
  "weights": {"hook": 0.25, "diff": 0.20, "exec": 0.20, "timely": 0.20, "emotion": 0.15},
  "candidates": [
    {"name": "存一万送一万", "hook": 9, "diff": 9, "exec": 9, "timely": 9, "emotion": 9,
     "new_scenes": 1, "new_characters": 0, "note": "预付卡"}
  ]
}

只依赖标准库。分数范围 1-10，权重合计必须为 1。
"""

import argparse
import json
import sys

DEFAULT_WEIGHTS = {
    "hook": 0.25,
    "diff": 0.20,
    "exec": 0.20,
    "timely": 0.20,
    "emotion": 0.15,
}

KEYS = ["hook", "diff", "exec", "timely", "emotion"]

LABELS = {
    "hook": "钩子",
    "diff": "差异",
    "exec": "执行",
    "timely": "时效",
    "emotion": "情感",
}


def build_demo():
    return {
        "candidates": [
            {"name": "存一万送一万", "hook": 9, "diff": 9, "exec": 9, "timely": 9,
             "emotion": 9, "new_scenes": 1, "new_characters": 0, "note": "预付资金池"},
            {"name": "视频里的孙子", "hook": 10, "diff": 10, "exec": 4, "timely": 10,
             "emotion": 10, "new_scenes": 2, "new_characters": 1, "note": "AI 换脸"},
            {"name": "我的金条在店里", "hook": 9, "diff": 7, "exec": 8, "timely": 10,
             "emotion": 8, "new_scenes": 1, "new_characters": 0, "note": "黄金托管"},
            {"name": "零门槛月入过万", "hook": 8, "diff": 8, "exec": 6, "timely": 9,
             "emotion": 7, "new_scenes": 1, "new_characters": 0, "note": "平台垫资"},
            {"name": "交十万留张床", "hook": 7, "diff": 6, "exec": 7, "timely": 8,
             "emotion": 9, "new_scenes": 1, "new_characters": 1, "note": "养老床位"},
            {"name": "九十九玩三天", "hook": 7, "diff": 6, "exec": 8, "timely": 8,
             "emotion": 7, "new_scenes": 1, "new_characters": 1, "note": "低价旅游"},
            {"name": "免费按摩", "hook": 8, "diff": 3, "exec": 7, "timely": 9,
             "emotion": 8, "new_scenes": 1, "new_characters": 1, "note": "养生馆"},
            {"name": "你家这瓶子值钱", "hook": 8, "diff": 3, "exec": 7, "timely": 8,
             "emotion": 7, "new_scenes": 1, "new_characters": 1, "note": "老物件回收"},
        ]
    }


def load(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {"candidates": data}
    return data


def validate(data):
    weights = data.get("weights", DEFAULT_WEIGHTS)
    missing = [k for k in KEYS if k not in weights]
    if missing:
        raise SystemExit("权重缺少字段: " + ", ".join(missing))
    total = sum(weights[k] for k in KEYS)
    if abs(total - 1.0) > 1e-6:
        raise SystemExit(f"权重合计必须为 1，当前为 {total:.4f}")

    candidates = data.get("candidates", [])
    if not candidates:
        raise SystemExit("没有候选，检查 candidates 字段")

    for i, c in enumerate(candidates, 1):
        if "name" not in c:
            raise SystemExit(f"第 {i} 个候选缺少 name")
        for k in KEYS:
            v = c.get(k)
            if not isinstance(v, (int, float)) or not 1 <= v <= 10:
                raise SystemExit(f"{c['name']} 的 {k} 必须是 1-10 的数字，当前为 {v!r}")
    return weights, candidates


def veto_reasons(c):
    reasons = []
    if c.get("new_scenes", 0) > 2:
        reasons.append(f"新增场景 {c['new_scenes']} 个")
    if c.get("new_characters", 0) > 1:
        reasons.append(f"新增角色 {c['new_characters']} 个")
    reasons.extend(c.get("veto_reasons", []))
    return reasons


def render(weights, candidates):
    rows = []
    for c in candidates:
        score = sum(c[k] * weights[k] for k in KEYS)
        rows.append((score, c, veto_reasons(c)))
    rows.sort(key=lambda r: r[0], reverse=True)

    head = "| 排名 | 候选 | " + " | ".join(LABELS[k] for k in KEYS) + " | 加权 | 结论 |"
    sep = "| --- | --- | " + " | ".join("---" for _ in KEYS) + " | --- | --- |"
    lines = [head, sep]

    for idx, (score, c, veto) in enumerate(rows, 1):
        if veto:
            verdict = "淘汰：" + "，".join(veto)
        elif idx == 1:
            verdict = "第一顺位"
        elif idx <= 3:
            verdict = "备选"
        else:
            verdict = "待定"
        cells = [str(c[k]) for k in KEYS]
        lines.append(
            f"| {idx} | {c['name']} | " + " | ".join(cells) + f" | {score:.2f} | {verdict} |"
        )

    valid = [r for r in rows if not r[2]]
    if valid:
        top = valid[0]
        lines.append("")
        lines.append(f"推荐：**{top[1]['name']}**（{top[0]:.2f} 分）")
        close = [r for r in valid[1:] if top[0] - r[0] < 0.3]
        if close:
            names = "、".join(r[1]["name"] for r in close)
            lines.append(f"分差小于 0.3 的候选：{names}；优先选新增资产更少的一个。")
    else:
        lines.append("")
        lines.append("所有候选均被否决，回到第 2 步重新生成。")

    return "\n".join(lines)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="系列短剧选题加权评分")
    parser.add_argument("input", nargs="?", help="候选 JSON 文件")
    parser.add_argument("--out", help="把结果写入 Markdown 文件")
    parser.add_argument("--demo", action="store_true", help="用 2026-10-19 案例跑一遍")
    args = parser.parse_args()

    if args.demo:
        data = build_demo()
    elif args.input:
        data = load(args.input)
    else:
        parser.error("需要输入文件，或加 --demo")

    weights, candidates = validate(data)
    text = render(weights, candidates)
    print(text)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")


if __name__ == "__main__":
    main()
