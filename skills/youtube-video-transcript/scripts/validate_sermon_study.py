#!/usr/bin/env python3
"""Check the sermon study's fixed delivery structure, not theological accuracy."""

import argparse
import json
import re
from pathlib import Path


def fail(errors, message):
    errors.append(message)


def timestamp_seconds(value):
    minutes, seconds = map(int, value.split(":"))
    if seconds > 59:
        raise ValueError(value)
    return minutes * 60 + seconds


def validate(study_path, transcript_path, audit_path, captions_path, attachment_name):
    errors = []
    study = study_path.read_text(encoding="utf-8")
    transcript = transcript_path.read_text(encoding="utf-8")
    audit = audit_path.read_text(encoding="utf-8")
    captions = json.loads(captions_path.read_text(encoding="utf-8"))
    raw_text = "".join(
        "".join(segment["utf8"] for segment in event.get("segs", []))
        for event in captions["events"]
        if event.get("segs") and not event.get("aAppend")
    )
    raw_chars = len(re.sub(r"\s", "", raw_text))
    transcript_chars = len(re.sub(r"\s", "", transcript))
    if raw_chars and transcript_chars < raw_chars * 0.65:
        fail(errors, "교정 전문이 원시 자막에 비해 지나치게 짧습니다. 요약이 아닌 전체 전문인지 다시 대조하세요.")

    if study_path.name != attachment_name:
        fail(errors, "최종 파일명과 첨부파일 표시명이 다릅니다.")
    if not study.startswith("# "):
        fail(errors, "공식 설교 제목으로 시작해야 합니다.")
    if re.search(r"<[^>]+>", study):
        fail(errors, "템플릿 자리표시자가 남아 있습니다.")

    headings = re.findall(r"^## (.+)$", study, flags=re.MULTILINE)
    fixed = ["설교 정보", "한 문장 주제", "설교의 결론", "한 문장 결론"]
    for heading in fixed:
        if headings.count(heading) != 1:
            fail(errors, f"필수 제목이 하나여야 합니다: {heading}")
    numbered = []
    pattern = re.compile(r"^(\d+)\. (.+) \(약 (\d{2,3}:\d{2})~(\d{2,3}:\d{2})\)$")
    for heading in headings:
        match = pattern.fullmatch(heading)
        if match:
            numbered.append(match)
        elif heading not in fixed:
            fail(errors, f"허용되지 않는 2단계 제목: {heading}")
    if headings != ["설교 정보", "한 문장 주제"] + [m.group(0) for m in numbered] + ["설교의 결론", "한 문장 결론"]:
        fail(errors, "문서 제목 순서가 고정 템플릿과 다릅니다.")
    if not numbered or [int(m.group(1)) for m in numbered] != list(range(1, len(numbered) + 1)):
        fail(errors, "시간순 대단락 번호가 1부터 연속되어야 합니다.")
    last_start = -1
    for match in numbered:
        try:
            start = timestamp_seconds(match.group(3))
            end = timestamp_seconds(match.group(4))
            if start >= end or start < last_start:
                fail(errors, f"시간 구간 순서가 잘못되었습니다: {match.group(0)}")
            last_start = start
        except ValueError:
            fail(errors, f"시간 형식이 잘못되었습니다: {match.group(0)}")

    info = study.split("## 설교 정보", 1)[-1].split("## 한 문장 주제", 1)[0]
    for key in ["설교자", "일자", "채널", "영상", "핵심 본문", "정리 기준"]:
        if f"**{key}:**" not in info:
            fail(errors, f"설교 정보가 빠졌습니다: {key}")
    date = re.search(r"\*\*일자:\*\*\s*(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", info)
    if date:
        expected_prefix = f"{date.group(1)}-{int(date.group(2)):02d}-{int(date.group(3)):02d}_"
        if not study_path.name.startswith(expected_prefix):
            fail(errors, "최종 파일명이 설교 날짜로 시작하지 않습니다.")
    speaker = re.search(r"\*\*설교자:\*\*\s*([^\n]+)", info)
    if speaker and speaker.group(1).split()[0] not in study_path.name:
        fail(errors, "최종 파일명에 설교자 이름이 없습니다.")

    # Accept the existing blockquote and Obsidian's always-open info callout.
    scripture_blocks = re.findall(r"^> (?:\[!info\] )?\*\*(?!보충 확인\(외부 자료\)|설교와의 연결|출처)([^*]+)\*\*\s*\n> (.+)$", study, flags=re.MULTILINE)
    if not scripture_blocks:
        fail(errors, "설교에 직접 인용된 성구의 본문 블록이 없습니다.")
    for label, quote in scripture_blocks:
        if "“" not in quote or "”" not in quote:
            fail(errors, f"성구 인용문을 확인하세요: {label}")
        if "==" in label or "==" in quote:
            fail(errors, f"성구 본문과 장절에는 형광펜을 넣지 마세요: {label}")

    if re.search(r"^> \[!info\][+-]", study, flags=re.MULTILINE):
        fail(errors, "성구 콜아웃은 접기 기호 없이 펼쳐 두세요.")
    callout_headers = re.findall(r"^> \[!info\] .+$", study, flags=re.MULTILINE)
    complete_callouts = re.findall(r"^> \[!info\] \*\*[^*\n]+\*\*[ \t]*\n> .+$", study, flags=re.MULTILINE)
    if len(callout_headers) != len(complete_callouts):
        fail(errors, "성구 콜아웃에 장절 또는 다음 줄의 인용 본문이 없습니다.")
    if study.count("==") % 2:
        fail(errors, "형광펜 표시의 여닫는 == 수가 맞지 않습니다.")
    for section in re.split(r"^## ", study, flags=re.MULTILINE)[1:]:
        heading = section.splitlines()[0]
        if pattern.fullmatch(heading):
            highlights = re.findall(r"==([^=\n]+)==", section)
            if len(highlights) > 1:
                fail(errors, f"형광펜은 대단락당 최대 한 문장만 사용하세요: {heading}")

    fact_labels = ["보충 확인(외부 자료)", "설교와의 연결", "출처"]
    counts = [len(re.findall(r"^> \*\*" + re.escape(label) + r":\*\*", study, flags=re.MULTILINE)) for label in fact_labels]
    if len(set(counts)) != 1:
        fail(errors, "외부 보충 블록의 세 항목 수가 맞지 않습니다.")
    if counts[0]:
        complete_blocks = re.findall(
            r"^> \*\*보충 확인\(외부 자료\):\*\* [^\n]+\n"
            r"> \*\*설교와의 연결:\*\* [^\n]+\n"
            r"> \*\*출처:\*\* [^\n]+$",
            study,
            flags=re.MULTILINE,
        )
        if len(complete_blocks) != counts[0]:
            fail(errors, "외부 보충의 확인·연결·출처를 연속된 한 블록으로 작성하세요.")
        for source in re.findall(r"^> \*\*출처:\*\* (.+)$", study, flags=re.MULTILINE):
            if not re.search(r"https?://", source):
                fail(errors, "외부 보충 출처에 링크가 없습니다.")

    if not transcript.startswith("# 내부 교정 전문"):
        fail(errors, "내부 교정 전문 파일의 제목을 확인하세요.")
    if re.search(r"\[(?:음악|노래)\]|^>>", transcript, flags=re.MULTILINE):
        fail(errors, "내부 교정 전문에 자막 잡음이 남아 있습니다.")
    raw_blocks = re.findall(r"^## \d{2}:\d{2}$", transcript, flags=re.MULTILINE)
    if len(raw_blocks) >= 5:
        paragraphs = [part for part in re.split(r"\n\s*\n", transcript) if part and not part.startswith("#")]
        if paragraphs and sum(len(part) > 700 for part in paragraphs) * 2 >= len(paragraphs):
            fail(errors, "내부 전문이 5분 단위 자막 이어 붙이기처럼 보입니다. 문장·문단별 교정을 다시 확인하세요.")

    required_audit = ["전 구간 대조", "성구 대조", "예화·외부 사실", "최종 판정"]
    for heading in required_audit:
        if f"## {heading}" not in audit:
            fail(errors, f"내부 검수 기록 항목이 없습니다: {heading}")
    if re.search(r"<[^>]+>|- \[ \]", audit):
        fail(errors, "내부 검수 기록에 미작성 항목이 남아 있습니다.")
    if len(re.findall(r"^- \[x\] ", audit, flags=re.MULTILINE)) != 6:
        fail(errors, "내부 검수 기록의 최종 판정 6개를 모두 확인하세요.")
    duration = re.search(r"\*\*영상 길이:\*\*\s*(\d{2,3}:\d{2})", audit)
    coverage = re.findall(r"^\|\s*(\d{2,3}:\d{2})~(\d{2,3}:\d{2})\s*\|[^\n]+$", audit, flags=re.MULTILINE)
    if not duration or not coverage:
        fail(errors, "영상 길이 또는 전 구간 대조표가 없습니다.")
    else:
        end = 0
        for start_text, end_text in coverage:
            start, next_end = timestamp_seconds(start_text), timestamp_seconds(end_text)
            if start != end or next_end <= start:
                fail(errors, f"전 구간 대조표의 시간에 공백·역전이 있습니다: {start_text}~{end_text}")
            end = next_end
        if end < timestamp_seconds(duration.group(1)):
            fail(errors, "전 구간 대조표가 영상 끝까지 닿지 않습니다.")
    scripture_audit = audit.split("## 성구 대조", 1)[-1].split("## 예화·외부 사실", 1)[0]
    scripture_rows = re.findall(r"^\|\s*\d{2,3}:\d{2}\s*\|[^\n]+$", scripture_audit, flags=re.MULTILINE)
    if len(scripture_rows) < len(scripture_blocks):
        fail(errors, "내부 성구 대조표의 행이 정리본 성구 인용 수보다 적습니다.")
    facts_audit = audit.split("## 예화·외부 사실", 1)[-1].split("## 최종 판정", 1)[0]
    fact_rows = re.findall(r"^\|\s*\d{2,3}:\d{2}\s*\|[^\n]+$", facts_audit, flags=re.MULTILINE)
    if counts[0] and (len(fact_rows) < counts[0] or "http" not in facts_audit):
        fail(errors, "외부 확인 내용을 내부 예화·사실 대조표에도 기록하세요.")

    return errors, len(numbered), len(scripture_blocks), counts[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--study", required=True, type=Path)
    parser.add_argument("--transcript", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--captions", required=True, type=Path)
    parser.add_argument("--attachment-name", required=True)
    args = parser.parse_args()
    errors, sections, quotations, fact_blocks = validate(args.study, args.transcript, args.audit, args.captions, args.attachment_name)
    if errors:
        for error in errors:
            print("FAIL:", error)
        raise SystemExit(1)
    print(f"PASS: 대단락 {sections}개, 성구 인용 {quotations}개, 외부 확인 {fact_blocks}개 — 구조·검수 기록·분량 검사 통과 (내용 정확성은 별도 대조)")


if __name__ == "__main__":
    main()
