#!/usr/bin/env python3
"""Detect likely shot boundaries and extract one source frame per shot.

Usage:
  python3 extract_video_shots.py <video> <output-dir> [--threshold 0.28]

Requires ffmpeg and ffprobe. It never modifies the source video. A JSON manifest
contains the candidate boundaries and the extracted screenshots for review.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def executable(env_name: str, fallback_name: str) -> str:
    value = os.environ.get(env_name) or shutil.which(fallback_name)
    if not value:
        raise RuntimeError(f"未找到 {fallback_name}。请设置 {env_name} 或在环境中提供 {fallback_name}。")
    return value


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def video_duration(ffprobe: str, video: Path) -> float:
    result = run([ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(video)])
    return float(result.stdout.strip())


def scene_candidates(ffmpeg: str, video: Path, threshold: float) -> list[float]:
    command = [
        ffmpeg, "-hide_banner", "-i", str(video), "-filter:v", f"select='gt(scene,{threshold})',showinfo",
        "-an", "-f", "null", "-",
    ]
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-1200:])
    points = []
    for raw in re.findall(r"pts_time:([0-9.]+)", result.stderr):
        value = float(raw)
        if not points or value - points[-1] > 0.08:
            points.append(value)
    return points


def timestamp(seconds: float) -> str:
    minutes, remainder = divmod(max(seconds, 0), 60)
    return f"{int(minutes):02d}:{remainder:05.2f}"


def main() -> int:
    parser = argparse.ArgumentParser(description="初筛视频镜头并提取逐镜截图")
    parser.add_argument("video", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--threshold", type=float, default=0.28, help="场景切换阈值；越低越敏感")
    args = parser.parse_args()
    source = args.video.expanduser().resolve()
    if not source.is_file():
        parser.error(f"找不到视频：{source}")
    if not 0 < args.threshold < 1:
        parser.error("--threshold 必须在 0 和 1 之间")

    try:
        ffmpeg = executable("FFMPEG_BIN", "ffmpeg")
        ffprobe = executable("FFPROBE_BIN", "ffprobe")
        duration = video_duration(ffprobe, source)
        cuts = scene_candidates(ffmpeg, source, args.threshold)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 2

    boundaries = [0.0] + [cut for cut in cuts if 0.08 < cut < duration - 0.08] + [duration]
    boundaries = sorted(set(round(item, 3) for item in boundaries))
    output = args.output_dir.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest = []
    for index, (start, end) in enumerate(zip(boundaries, boundaries[1:]), start=1):
        frame_time = min(end - 0.04, max(start + 0.04, (start + end) / 2))
        target = output / f"shot_{index:03d}_{timestamp(start).replace(':', '-')}.jpg"
        try:
            run([ffmpeg, "-hide_banner", "-ss", f"{frame_time:.3f}", "-i", str(source), "-frames:v", "1", "-q:v", "2", "-n", str(target)])
        except subprocess.CalledProcessError as error:
            print(error.stderr[-1200:], file=sys.stderr)
            return 3
        manifest.append({
            "shot": index,
            "start_seconds": start,
            "end_seconds": end,
            "duration_seconds": round(end - start, 3),
            "start_timecode": timestamp(start),
            "end_timecode": timestamp(end),
            "frame_time_seconds": round(frame_time, 3),
            "screenshot": str(target),
        })
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
