#!/usr/bin/env python3
"""Block a release when a QS citation cannot resolve to portable evidence.

This is a package-build check.  It uses only the installation folder, so a
passing result proves that buyers do not need any seller-side source folder.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

CASE_ID = re.compile(r"\bQS-\d{3}\b")
ABSOLUTE_PATH = re.compile(r"(?:^|[\s\"'])/(?:Users|Volumes|private|home)/")
REQUIRED_FIELDS = ("case_id", "source_file", "sheet", "row", "text")


def default_paths(skill_root: Path) -> tuple[Path, Path]:
    if (skill_root / "references" / "qiushi-method-library.md").exists():
        return (
            skill_root / "references" / "qiushi-method-library.md",
            skill_root / "references" / "method-card-evidence.jsonl",
        )
    return (
        skill_root / "knowledge" / "qiushi-full-library" / "qiushi-method-library.md",
        skill_root / "knowledge" / "evidence" / "method-card-evidence.jsonl",
    )


def load_records(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}:{line_no} is not valid JSONL: {exc}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"{path.name}:{line_no} is not an object")
            records.append(item)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--method-library", type=Path)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    root = args.root.resolve()
    default_library, default_evidence = default_paths(root)
    library = (args.method_library or default_library).resolve()
    evidence = (args.evidence or default_evidence).resolve()
    errors: list[str] = []

    if not library.is_file():
        errors.append(f"method library missing: {library}")
    if not evidence.is_file():
        errors.append(f"canonical evidence missing: {evidence}")
    if errors:
        return report(args.as_json, root, library, evidence, [], {}, errors)

    citations = sorted(set(CASE_ID.findall(library.read_text(encoding="utf-8"))))
    if not citations:
        errors.append("no QS case citations found in method library")
        return report(args.as_json, root, library, evidence, citations, {}, errors)

    try:
        records = load_records(evidence)
    except ValueError as exc:
        return report(args.as_json, root, library, evidence, citations, {}, [str(exc)])

    grouped: dict[str, list[dict]] = defaultdict(list)
    invalid_records = 0
    path_leaks = 0
    for item in records:
        case_id = item.get("case_id")
        if isinstance(case_id, str):
            grouped[case_id].append(item)
        if any(not str(item.get(field, "")).strip() for field in REQUIRED_FIELDS):
            invalid_records += 1
        for value in item.values():
            if isinstance(value, str) and ABSOLUTE_PATH.search(value):
                path_leaks += 1

    unresolved = [case_id for case_id in citations if not grouped.get(case_id)]
    if unresolved:
        errors.append("unresolved QS citations: " + ", ".join(unresolved))
    if invalid_records:
        errors.append(f"{invalid_records} evidence records lack required source fields")
    if path_leaks:
        errors.append(f"{path_leaks} absolute seller-side path values found in canonical evidence")

    counts = {case_id: len(grouped.get(case_id, [])) for case_id in citations}
    return report(args.as_json, root, library, evidence, citations, counts, errors)


def report(as_json: bool, root: Path, library: Path, evidence: Path, citations: list[str], counts: dict[str, int], errors: list[str]) -> int:
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "skill_root": str(root),
        "method_library": str(library.relative_to(root)) if library.is_relative_to(root) else str(library),
        "canonical_evidence": str(evidence.relative_to(root)) if evidence.is_relative_to(root) else str(evidence),
        "method_card_case_citation_count": len(citations),
        "resolved_case_counts": counts,
        "errors": errors,
    }
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif errors:
        print("FAIL｜方法卡证据完整性校验未通过", file=sys.stderr)
        for error in errors:
            print("- " + error, file=sys.stderr)
    else:
        print(
            "PASS｜方法卡引用 %d 个案例编号，均可在内置主证据库追溯；无绝对路径泄漏。"
            % len(citations)
        )
        print("证据记录数：" + str(sum(counts.values())))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
