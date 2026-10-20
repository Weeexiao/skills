#!/usr/bin/env python
"""Gemini 图片下载检测脚本（配合 gemini-image-gen skill 使用）。

用法:
    python watch_downloads.py <baseline_json> <output_path> [downloads_dir] [timeout_sec] [--min-long-side N]

参数:
    baseline_json  点击下载按钮之前生成的基线文件（记录 Downloads 目录文件名->mtime）
    output_path    检测到新图后复制到的目标路径（如桌面）
    downloads_dir  可选，默认 C:/Users/shizh/Downloads
    timeout_sec    可选，默认 90 秒
    --min-long-side  可选，判定"全尺寸原图"的长边阈值，默认 1200

逻辑:
    轮询比对 Downloads 目录与基线的新增图片文件，等文件大小稳定（2 秒内不变）
    且 >100KB 后，校验尺寸（纯 struct 解析 PNG/JPEG 头，无需 PIL），
    然后复制到 output_path 并打印 JSON 结果。检测到 .crdownload 会继续等待。

    尺寸不固定：横版约 2816x1536、竖版 9:16 约 1536x2816、3:4、1:1 等均正常。
    长边 < 阈值时仍会复制，但结果里 is_full_size=false 并给出提示
    （通常意味着拿到的是页面缩略图，而全尺寸应走 "Download full-sized image"）。
"""
import json
import os
import shutil
import struct
import sys
import time

MANAGED_PYTHON = r"C:/Users/shizh/.workbuddy/binaries/python/versions/3.13.12/python.exe"  # noqa: F401 (文档用途)

DEFAULT_DOWNLOADS = r"C:/Users/shizh/Downloads"
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")
STABLE_CHECK_SEC = 2


def png_size(path):
    with open(path, "rb") as fp:
        head = fp.read(33)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", head[16:24])
    return w, h


def jpg_size(path):
    with open(path, "rb") as fp:
        data = fp.read()
    i = 2
    n = len(data)
    while i < n - 9:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                      0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        seglen = struct.unpack(">H", data[i + 2:i + 4])[0]
        i += 2 + seglen
    return None


def image_size(path):
    try:
        if path.lower().endswith(".png"):
            return png_size(path)
        return jpg_size(path)
    except Exception:
        return None


def main():
    argv = sys.argv[1:]
    if "--min-long-side" in argv:
        i = argv.index("--min-long-side")
        try:
            min_long_side = int(argv[i + 1])
            del argv[i:i + 2]
        except (IndexError, ValueError):
            min_long_side = 1200
    else:
        min_long_side = 1200

    if len(argv) < 2:
        print(json.dumps({"ok": False, "reason": "usage: watch_downloads.py <baseline_json> <output_path> [downloads_dir] [timeout_sec] [--min-long-side N]"}))
        sys.exit(2)

    baseline_path = argv[0]
    output_path = argv[1]
    downloads_dir = argv[2] if len(argv) > 2 else DEFAULT_DOWNLOADS
    timeout_sec = float(argv[3]) if len(argv) > 3 else 90.0

    with open(baseline_path, "r", encoding="utf-8") as fp:
        baseline = set(json.load(fp).keys())

    deadline = time.time() + timeout_sec
    result = {"ok": False, "reason": "timeout: no new stable image file"}

    while time.time() < deadline:
        try:
            current = set(os.listdir(downloads_dir))
        except FileNotFoundError:
            print(json.dumps({"ok": False, "reason": "downloads dir not found: " + downloads_dir}))
            sys.exit(1)

        added = [f for f in current - baseline
                 if f.lower().endswith(IMAGE_EXTS) and not f.endswith(".crdownload")]

        for name in added:
            path = os.path.join(downloads_dir, name)
            try:
                s1 = os.path.getsize(path)
            except OSError:
                continue
            time.sleep(STABLE_CHECK_SEC)
            try:
                s2 = os.path.getsize(path)
            except OSError:
                continue
            if s1 != s2 or s1 < 100 * 1024:
                continue
            size = image_size(path)
            if not size:
                continue
            w, h = size
            shutil.copy2(path, output_path)
            long_side = max(w, h)
            result = {
                "ok": True,
                "source": path,
                "copied_to": output_path,
                "bytes": s2,
                "dimensions": "%dx%d" % (w, h),
                "orientation": "portrait" if h > w else ("landscape" if w > h else "square"),
                "is_full_size": long_side >= min_long_side,
            }
            if not result["is_full_size"]:
                result["warning"] = (
                    "long side %d < %d: 可能拿到的是页面缩略图；"
                    "请确认点击的是 'Download full-sized image'" % (long_side, min_long_side)
                )
            print(json.dumps(result, ensure_ascii=False))
            return
        time.sleep(3)

    print(json.dumps(result, ensure_ascii=False))
    sys.exit(1)


if __name__ == "__main__":
    main()
