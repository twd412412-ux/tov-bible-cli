#!/usr/bin/env python3
"""Convert the approved Obsidian study's formatting without rewriting content."""

import argparse
import re
from pathlib import Path


TIMESTAMP = r"\(약 \d{2,3}:\d{2}~\d{2,3}:\d{2}\)"


def content(text):
    """Ignore only the presentation markers used by the two study formats."""
    lines = []
    for line in text.splitlines():
        if line == "---":
            continue
        line = re.sub(r"^(?:#{1,6} +|> ?|- +)", "", line)
        line = re.sub(r"^\[!(?:info|example)\] ", "", line)
        line = line.replace("**", "").replace("==", "")
        line = re.sub(r"^\*(" + TIMESTAMP + r")\*$", r"\1", line)
        lines.append(line)
    return re.sub(r"\s+", "", "".join(lines))


def convert(study):
    notes = re.sub(
        r"^> \[!info\] (\*\*[^*\n]+\*\*)[ \t]*$",
        r"> \1\n>", study, flags=re.MULTILINE,
    )
    notes = re.sub(
        r"^> \[!example\] 외부 보충[ \t]*$",
        "> **외부 보충**\n>", notes, flags=re.MULTILINE,
    )
    notes = re.sub(r"==([^=\n]+)==", r"**\1**", notes)
    notes = re.sub(
        r"^(## \d+\. .+?) (" + TIMESTAMP + r")$",
        r"\1\n\n*\2*", notes, flags=re.MULTILINE,
    )
    notes = "\n".join(line.rstrip() for line in notes.splitlines()) + "\n"
    if re.search(r"\[![^\]\n]+\]|==", notes):
        raise ValueError("변환되지 않은 콜아웃 또는 형광펜 표시가 있습니다.")
    if content(study) != content(notes):
        raise ValueError("변환 전후의 내용 또는 순서가 다릅니다.")
    return notes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--check", action="store_true", help="검사만 수행하고 파일을 수정하지 않음")
    args = parser.parse_args()
    try:
        if args.study.resolve() == args.output.resolve():
            raise ValueError("기준 정리본과 메모용 출력 경로는 달라야 합니다.")
        study = args.study.read_text(encoding="utf-8")
        notes = convert(study)
        if args.check:
            if args.output.read_text(encoding="utf-8") != notes:
                raise ValueError("메모용 파일이 기준 정리본의 변환 결과와 다릅니다. 다시 변환하세요.")
        else:
            args.output.write_text(notes, encoding="utf-8")
        if content(study) != content(args.output.read_text(encoding="utf-8")):
            raise ValueError("최종 두 파일의 내용 또는 순서가 다릅니다.")
    except (OSError, ValueError) as error:
        print("FAIL:", error)
        raise SystemExit(1)
    quotations = len(re.findall(r"^> “[^\n]+", notes, flags=re.MULTILINE))
    sections = len(re.findall(r"^## \d+\. ", notes, flags=re.MULTILINE))
    links = len(re.findall(r"\]\((https?://[^)]+)\)", notes))
    print(f"PASS: 대단락 {sections}개, 성구 인용 {quotations}개, 링크 {links}개 — 두 MD의 전체 내용·순서 동일")


if __name__ == "__main__":
    main()
