#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 6 条被 Gemini 安全过滤拒绝的提示词改成中性说法。

原则：只替换"羞辱/痛苦/胁迫"的表演描述，构图、站位、景别、镜头、光线、
以及第二段（<Subject> 绑定与连续性要求）完全不动。原始文件备份为
`提示词-原始备份.md`（已存在则不覆盖）。
"""
import os
import shutil

BASE = r"F:\AI短片\歪嘴龙王1\2.资产\生图任务"

NEW = {
    "S11-逐镜首帧": "9:16 写实中国都市短剧电影首帧。动作起始帧：右侧厚重木门刚打开一条大缝，王总正跨过门槛、上身前倾；门后走廊里数名黑衣随行人员安静站立等候；陈默位于左侧深处。",
    "S12-逐镜首帧": "9:16 写实中国都市短剧电影首帧。大全景终态参考：王总位于最前方、身体重心下沉且单膝着地、上身挺直，护卫在其后方排成整齐一列、同样低位俯身，全部朝向左侧陈默；林浩贴墙站立，苏婉神情紧绷。",
    "S14-逐镜首帧": "9:16 写实中国都市短剧电影首帧。动作起始帧：王总低位屈身、双手托着黑金阎罗怀表刚举到胸前，陈默的手尚未接触；焦点清楚覆盖王总脸和怀表。",
    "S15-逐镜首帧": "9:16 写实中国都市短剧电影首帧。林浩靠着深色木墙坐低身体、上身微前倾、头微微抬起望向画外的陈默，神情克制；轻微俯拍，服装整洁，无夸张污渍。",
    "S17-逐镜首帧": "9:16 写实中国都市短剧电影首帧。动作起始帧：陈默手持黑色银行卡微微俯身，卡片与人之间仍有明显空隙；林浩低位屈身、身体保持静止，神情克制，画面内无接触、无伤害。",
    "S18-逐镜首帧": "9:16 写实中国都市短剧电影首帧。门口离场首帧：陈默刚牵起苏婉的手，二人尚未迈步；后景王总和护卫处于低位屈身姿态、低头望向地面，打开的门通向冷色走廊。陈默此时保持平静表情，不提前出现歪嘴笑。",
}

MARK = "## Gemini 生图提示词"

for tid, new_line in NEW.items():
    p = os.path.join(BASE, tid, "提示词.md")
    bak = os.path.join(BASE, tid, "提示词-原始备份.md")
    if not os.path.exists(bak):
        shutil.copy2(p, bak)
    lines = open(p, encoding="utf-8").read().splitlines()
    idx = next(i for i, l in enumerate(lines) if l.strip() == MARK)
    body = idx + 1
    while body < len(lines) and not lines[body].strip():
        body += 1
    old = lines[body]
    lines[body] = new_line
    open(p, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("=" * 10, tid)
    print("  旧:", old)
    print("  新:", new_line)
    print("  备份:", bak if os.path.exists(bak) else "(exists)")
