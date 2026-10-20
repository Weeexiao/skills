#!/usr/bin/env python3
"""Compose four scene views into a fixed-order 2x2 PNG grid."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compose four scene views into a 2x2 grid.")
    parser.add_argument("front", type=Path)
    parser.add_argument("reverse", type=Path)
    parser.add_argument("oblique", type=Path)
    parser.add_argument("top_down", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--cell-width", type=positive_int, default=2048)
    parser.add_argument("--cell-height", type=positive_int, default=1152)
    parser.add_argument("--fit", choices=("crop", "contain"), default="crop")
    parser.add_argument("--background", default="#000000")
    return parser.parse_args()


def prepare(image_path: Path, size: tuple[int, int], fit: str, background: str) -> Image.Image:
    with Image.open(image_path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        if fit == "crop":
            return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        contained = ImageOps.contain(image, size, method=Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", size, background)
        offset = ((size[0] - contained.width) // 2, (size[1] - contained.height) // 2)
        canvas.paste(contained, offset)
        return canvas


def main() -> None:
    args = parse_args()
    inputs = (args.front, args.reverse, args.oblique, args.top_down)
    missing = [str(path) for path in inputs if not path.is_file()]
    if missing:
        raise SystemExit("Missing input file(s): " + ", ".join(missing))

    cell_size = (args.cell_width, args.cell_height)
    grid = Image.new("RGB", (args.cell_width * 2, args.cell_height * 2), args.background)
    positions = ((0, 0), (args.cell_width, 0), (0, args.cell_height), (args.cell_width, args.cell_height))
    for path, position in zip(inputs, positions):
        grid.paste(prepare(path, cell_size, args.fit, args.background), position)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    grid.save(args.output, format="PNG", optimize=True)
    print(f"Saved {grid.width}x{grid.height} grid to {args.output}")


if __name__ == "__main__":
    main()
