#!/usr/bin/env python
"""歪嘴龙王1 生图任务批量驱动。

按 README 顺序执行: A01-A03 -> P01-P03 -> E01-E03 -> S01-S18。
- 每个任务使用精确的参考图清单（按生图说明的依赖关系，不盲目上传全部）
- 生成的前置资产会按 README 要求复制进 dependent 任务的 参考图/ 目录（前缀 10-生成-）
- 已有输出的任务自动跳过（断点续跑）
- 单任务失败重试一次，依赖任务失败则跳过其下游
- 进度写入 batch_status.json

用法: python batch.py [起始任务ID]   （如 python batch.py S05）
"""
import json
import os
import shutil
import sys
import time

import runtask as R

BASE = r"F:/AI短片/歪嘴龙王1"
TASKS_DIR = BASE + "/2.资产/生图任务"
ASSETS = BASE + "/2.资产"
STORYBOARD = BASE + "/3.分镜脚本/逐镜草图"
STATUS_FILE = os.path.join(R.TMP_DIR, "batch_status.json")

REF = TASKS_DIR + "/%s/参考图/"
PENDING_COPIES = []

# 生成的资产路径
A_S2 = ASSETS + "/人物/S2-苏婉-复用小雅-酒红礼服.jpg"
A_S4 = ASSETS + "/人物/S4-王总-复用赵叔-深蓝西装.jpg"
A_S5 = ASSETS + "/人物/S5-黑衣护卫群像-复用角色.jpg"
P_P1 = ASSETS + "/道具/P1-黑金阎罗怀表.jpg"
P_P2 = ASSETS + "/道具/P2-黑色银行卡.jpg"
P_P3 = ASSETS + "/道具/P3-联姻协议.jpg"
E_E2 = ASSETS + "/场景/E2-包厢门口反打.jpg"
E_E3 = ASSETS + "/场景/E3-会所顶层走廊.jpg"
E_E4 = ASSETS + "/场景/E4-主位反打.jpg"

BOX = "00-已有-包厢主场景.jpg"
CHEN = "00-已有-陈默身份四视图.jpg"
CHEN_FACE = "00-已有-陈默歪嘴表情.jpg"
LIN = "00-已有-林浩身份四视图.jpg"


def box(task):
    return REF % task + BOX


def chen(task):
    return REF % task + CHEN


def chen_face(task):
    return REF % task + CHEN_FACE


def lin(task):
    return REF % task + LIN


def asset_copy_name(path):
    return "10-生成-" + os.path.basename(path)


def copy_into(task, asset_path):
    """登记"把生成资产复制进任务参考图目录"的意图，返回目标路径。
    实际复制推迟到该任务运行时执行（资产此时可能尚未生成）。"""
    dst = REF % task + asset_copy_name(asset_path)
    PENDING_COPIES.append((asset_path, dst))
    return dst


def materialize_copies():
    for src, dst in PENDING_COPIES:
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)


def build_plan():
    """返回有序任务列表: (id, task_dir, out_path, refs, deps)"""
    plan = []

    def add(tid, out, refs, deps=()):
        plan.append({"id": tid, "dir": TASKS_DIR + "/" + tid, "out": out,
                     "refs": refs, "deps": list(deps)})

    # ---- A 角色 ----
    add("A01-苏婉-复用小雅换装", A_S2, [REF % "A01-苏婉-复用小雅换装" + "01-小雅身份四视图.jpg"])
    add("A02-王总-复用赵叔换装", A_S4, [REF % "A02-王总-复用赵叔换装" + "01-赵叔身份四视图.png"])
    add("A03-黑衣护卫群像-复用阿强与大鹏", A_S5,
        [REF % "A03-黑衣护卫群像-复用阿强与大鹏" + "01-阿强身份四视图.png",
         REF % "A03-黑衣护卫群像-复用阿强与大鹏" + "02-大鹏身份四视图.png"])

    # ---- P 道具 ----
    add("P01-黑金阎罗怀表", P_P1, [])
    add("P02-黑色银行卡", P_P2, [])
    add("P03-联姻协议", P_P3, [])

    # ---- E 场景 ----
    add("E01-包厢门口反打", E_E2, [REF % "E01-包厢门口反打" + "01-已有-包厢主场景.jpg"])
    add("E02-会所顶层走廊", E_E3,
        [REF % "E02-会所顶层走廊" + "01-已有-包厢主场景.jpg", copy_into("E02-会所顶层走廊", E_E2)],
        deps=["E01-包厢门口反打"])
    add("E03-主位反打", E_E4,
        [REF % "E03-主位反打" + "01-已有-包厢主场景.jpg",
         copy_into("E03-主位反打", P_P2), copy_into("E03-主位反打", P_P3)],
        deps=["P02-黑色银行卡", "P03-联姻协议"])

    # ---- S 逐镜首帧 (依赖: 0=苏婉 1=王总 2=护卫 3=怀表 4=银行卡 5=协议 6=门口) ----
    S = [
        ("S01-逐镜首帧", [box, lin, chen], [0, 5]),
        ("S02-逐镜首帧", [box, lin], [4, 5]),
        ("S03-逐镜首帧", [box, lin, chen], [4]),
        ("S04-逐镜首帧", [box, chen], [0, 4]),
        ("S05-逐镜首帧", [box, lin], [0, 4]),
        ("S06-逐镜首帧", [box, lin, chen], [0]),
        ("S07-逐镜首帧", [box, chen], [0]),
        ("S08-逐镜首帧", [box, lin], [5]),
        ("S09-逐镜首帧", [box, lin], []),
        ("S10-逐镜首帧", [box, lin, chen], [0]),
        ("S11-逐镜首帧", [box, chen], [1, 2, 6]),
        ("S12-逐镜首帧", [box, lin, chen], [0, 1, 2, 6]),
        ("S13-逐镜首帧", [box], [1]),
        ("S14-逐镜首帧", [box, chen], [1, 3]),
        ("S15-逐镜首帧", [box, lin, chen], []),
        ("S16-逐镜首帧", [box, lin, chen], [4]),
        ("S17-逐镜首帧", [box, lin, chen], [4]),
        ("S18-逐镜首帧", [box, chen, chen_face], [0, 1, 2, 6]),
    ]
    gen_assets = [A_S2, A_S4, A_S5, P_P1, P_P2, P_P3, E_E2]
    dep_ids = ["A01-苏婉-复用小雅换装", "A02-王总-复用赵叔换装", "A03-黑衣护卫群像-复用阿强与大鹏",
               "P01-黑金阎罗怀表", "P02-黑色银行卡", "P03-联姻协议", "E01-包厢门口反打"]
    for sid, base_fns, dep_idx in S:
        refs = [fn(sid) for fn in base_fns]
        deps = [dep_ids[i] for i in dep_idx]
        for i in dep_idx:
            refs.append(copy_into(sid, gen_assets[i]))
        add(sid, STORYBOARD + "/" + sid[:3] + ".jpg", refs, deps)

    return plan


def load_status():
    if os.path.exists(STATUS_FILE):
        return json.load(open(STATUS_FILE, encoding="utf-8"))
    return {}


def save_status(st):
    json.dump(st, open(STATUS_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def refs_exist(refs):
    missing = [r for r in refs if not os.path.exists(r)]
    return missing


def run_one(t):
    log = []
    out = t["out"]
    if os.path.exists(out) and os.path.getsize(out) > 100 * 1024:
        return {"ok": True, "skipped": "output exists", "output": out}
    materialize_copies()
    missing = refs_exist(t["refs"])
    if missing:
        return {"ok": False, "error": "missing refs: " + ", ".join(os.path.basename(m) for m in missing)}

    R.wait_idle()
    R.new_chat()
    time.sleep(4)
    R.ensure_pro_mode()

    log.append("pasting %d refs" % len(t["refs"]))
    prev_n = 0
    for r in t["refs"]:
        up = {"ok": False}
        for _ in range(3):
            R.paste_file(r)
            up = R.wait_upload_done(prev_n, timeout=300)
            if up.get("ok"):
                prev_n = up["blobs"]
                break
        log.append("%s %s (%.0fs)" % ("uploaded" if up.get("ok") else "UPLOAD-FAIL",
                                      os.path.basename(r), up.get("waited", 0)))
        print("      ", log[-1], flush=True)
        if not up.get("ok"):
            return {"ok": False, "error": "upload failed: " + os.path.basename(r), "log": log}

    # 发送前最后确认：所有附件上传完成、无残留 spinner
    final = R.wait_upload_done(max(prev_n - 1, 0), timeout=180)
    if not final.get("ok"):
        return {"ok": False, "error": "attachments still uploading before send", "log": log}
    print("       all %d attachments uploaded, sending..." % final.get("blobs", 0), flush=True)

    prompt = R.extract_prompt(t["dir"])
    R.send_prompt(prompt)

    # 参考图越多，出图前 Gemini 的「正在创建您的图片」阶段越久（实测 5 张参考图可超 5 分钟）
    gen_timeout = 900 + 60 * len(t["refs"])
    gen = R.wait_generated(gen_timeout)
    if not gen.get("ok"):
        return {"ok": False,
                "error": "model refused (safety filter)" if gen.get("refused") else "generation timeout",
                "diag": gen.get("text", "")[:300], "log": log}

    before = R.baseline_downloads()
    dl = {"ok": False}
    for i in range(3):
        R.trigger_download()
        dl = R.wait_download(before, out, 100)
        if dl.get("ok"):
            break
        print("      download retry %d" % (i + 1), flush=True)
        time.sleep(5)
    if not dl.get("ok"):
        return {"ok": False, "error": "download failed", "log": log}
    return {"ok": True, "output": out, "dimensions": dl.get("dimensions"),
            "bytes": dl.get("bytes"), "log": log}


def main():
    start = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else None
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    attempts = 3
    if "--attempts" in sys.argv:
        attempts = int(sys.argv[sys.argv.index("--attempts") + 1])
    plan = build_plan()
    status = load_status()
    executed = 0

    # 补录状态表缺失但产物已存在的任务（如批处理前手动完成的 A01）
    for t in plan:
        if t["id"] not in status and os.path.exists(t["out"]) and os.path.getsize(t["out"]) > 100 * 1024:
            status[t["id"]] = {"ok": True, "skipped": "output exists (pre-batch)", "output": t["out"]}
            save_status(status)

    def dep_satisfied(d):
        # 状态表 ok，或产物文件已在磁盘上（防止历史误判把下游全部卡死）
        if status.get(d, {}).get("ok"):
            return True
        dep_task = next((x for x in plan if x["id"] == d), None)
        return bool(dep_task and os.path.exists(dep_task["out"])
                    and os.path.getsize(dep_task["out"]) > 100 * 1024)

    started = False
    for t in plan:
        if start and not started:
            started = (t["id"] == start)
            if not started:
                continue
        tid = t["id"]
        if status.get(tid, {}).get("ok"):
            print("[SKIP-OK]", tid, flush=True)
            continue
        dep_failed = [d for d in t["deps"] if not dep_satisfied(d)]
        if dep_failed:
            print("[SKIP-DEP]", tid, "deps failed:", dep_failed, flush=True)
            status[tid] = {"ok": False, "error": "deps failed: " + ", ".join(dep_failed)}
            save_status(status)
            continue

        print("[RUN]", tid, "->", os.path.basename(t["out"]), flush=True)
        result = None
        for attempt in range(1, attempts + 1):
            try:
                result = run_one(t)
            except Exception as e:
                result = {"ok": False, "error": "exception: %s" % e}
            if result.get("ok"):
                break
            print("  attempt %d failed: %s | diag=%s" % (attempt, result.get("error"),
                  str(result.get("diag", ""))[:120]), flush=True)
            time.sleep(5)
        executed += 1
        status[tid] = result
        save_status(status)
        print("[DONE]", tid, json.dumps(result, ensure_ascii=False)[:300], flush=True)
        if limit and executed >= limit:
            print("[BATCH LIMIT] 已执行 %d 个任务，本轮结束" % executed, flush=True)
            break

    ok = sum(1 for v in status.values() if v.get("ok"))
    print("=== SUMMARY: %d/%d ok ===" % (ok, len(plan)), flush=True)


if __name__ == "__main__":
    main()
