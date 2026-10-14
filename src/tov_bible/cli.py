import argparse
import difflib
import json
import sys
from pathlib import Path

from . import __version__
from .core import Bible, TovError, markdown_quotes


def output_options(parser):
    parser.add_argument("--json", action="store_true", help="AI용 JSON 출력")
    parser.add_argument("--format", choices=["text", "json", "md"], default="text")


def parser():
    p = argparse.ArgumentParser(prog="tov", description="토브성경 개역한글 전용. 계정·로그인·네트워크 없이 로컬 조회/검증.")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("verse", "passage", "books", "book", "chapter", "search", "batch", "verify", "info"):
        s = sub.add_parser(name)
        output_options(s)
        if name in ("verse", "passage"):
            s.add_argument("reference")
        elif name == "book":
            s.add_argument("book")
        elif name == "chapter":
            s.add_argument("book")
            s.add_argument("chapter", type=int)
        elif name == "search":
            s.add_argument("query")
            mode = s.add_mutually_exclusive_group()
            for m in ("all", "any", "phrase"):
                mode.add_argument("--" + m, dest="mode", action="store_const", const=m)
            s.set_defaults(mode="all")
            s.add_argument("--book")
            s.add_argument("--testament", choices=["구약", "신약"])
            s.add_argument("--limit", type=int, default=100, help="0이면 전체 결과")
            s.add_argument("--offset", type=int, default=0)
        elif name == "batch":
            s.add_argument("file", help="JSON 문자열 목록 또는 한 줄에 한 성구. - 는 표준입력")
        elif name == "verify":
            s.add_argument("file", nargs="?", help="설교 MD 또는 reference/quote 객체 JSON 목록")
            s.add_argument("--reference")
            s.add_argument("--quote")
            s.add_argument("--allow-formatting", action="store_true", help="공백/NFC 차이를 명시적으로 허용")
    data = sub.add_parser("data")
    data.add_argument("action", choices=["info", "check", "diff"])
    data.add_argument("other", nargs="?", help="diff: 다른 데이터 패키지 디렉터리")
    output_options(data)
    return p


def read_input(filename):
    return sys.stdin.read() if filename == "-" else Path(filename).read_text(encoding="utf-8")


def perform(bible, args):
    command = args.command
    result = {"ok": True, "source": bible.source(), "command": command}
    if command in ("info", "data"):
        result["manifest"] = bible.manifest
        if command == "data" and args.action == "diff":
            if not args.other:
                raise TovError("data diff에는 비교 데이터 디렉터리가 필요합니다.")
            other = Bible(args.other)
            left, right = {r["code"]: r["sentence"] for r in bible.rows}, {r["code"]: r["sentence"] for r in other.rows}
            result["other_source"] = other.source()
            result["changes"] = [{"code": c, "before": left.get(c), "after": right.get(c)} for c in sorted(left.keys() | right.keys()) if left.get(c) != right.get(c)]
            result["labels_changed"] = bible.data["labels"] != other.data["labels"]
        return result, 0
    if command == "books":
        result["books"] = list(bible.labels.values())
        return result, 0
    if command == "book":
        result["book"] = bible.labels[bible.book_id(args.book)]
        return result, 0
    if command in ("verse", "passage", "chapter"):
        reference = f"{args.book}{args.chapter}장" if command == "chapter" else args.reference
        rows = bible.parse(reference)
        if command == "verse" and len(rows) != 1:
            raise TovError("verse는 한 절만 조회합니다. 범위는 passage를 사용하세요.")
        result.update(verses=[bible.present(r) for r in rows], count=len(rows))
        return result, 0
    if command == "search":
        if args.offset < 0 or args.limit < 0:
            raise TovError("offset/limit은 0 이상이어야 합니다.")
        rows = bible.search(args.query, args.mode, args.book, args.testament)
        selected = rows[args.offset:] if args.limit == 0 else rows[args.offset:args.offset + args.limit]
        next_offset = args.offset + len(selected)
        result.update(query=args.query, mode=args.mode, total=len(rows), returned=len(selected), offset=args.offset, truncated=next_offset < len(rows), next_offset=next_offset if next_offset < len(rows) else None, verses=[bible.present(r) for r in selected])
        return result, 0
    if command == "batch":
        text = read_input(args.file)
        refs = json.loads(text) if text.lstrip().startswith("[") else [s.strip() for s in text.splitlines() if s.strip()]
        if not isinstance(refs, list) or not all(isinstance(r, str) for r in refs):
            raise TovError("batch 입력은 성구 문자열 목록이어야 합니다.", "invalid_input")
        result["results"] = []
        for ref in refs:
            try:
                result["results"].append({"reference": ref, "ok": True, "verses": [bible.present(r) for r in bible.parse(ref)]})
            except TovError as exc:
                result["results"].append({"reference": ref, "ok": False, "error": {"code": exc.code, "message": str(exc)}})
        result["ok"] = all(r["ok"] for r in result["results"])
        return result, 0 if result["ok"] else 2
    if command == "verify":
        if args.reference is not None or args.quote is not None:
            if args.file or args.reference is None or args.quote is None:
                raise TovError("file 또는 --reference와 --quote 한 쌍을 선택하세요.", "invalid_input")
            items = [{"reference": args.reference, "quote": args.quote}]
        elif args.file:
            text = read_input(args.file)
            items = json.loads(text) if text.lstrip().startswith("[") else markdown_quotes(text)
        else:
            raise TovError("검증할 파일 또는 --reference/--quote가 필요합니다.", "invalid_input")
        if not isinstance(items, list) or not items:
            raise TovError("검증할 성구 인용이 없습니다. PASS로 처리하지 않습니다.", "no_quotations")
        checks = []
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("reference"), str) or not isinstance(item.get("quote"), str):
                raise TovError("검증 입력에는 문자열 reference와 quote가 필요합니다.", "invalid_input")
            kind = item.get("kind", "quotation")
            if kind not in ("quotation", "mention", "paraphrase"):
                raise TovError("알 수 없는 인용 유형", "invalid_input")
            try:
                check = bible.verify(item["reference"], item["quote"], kind, args.allow_formatting)
                if not check["verified"]:
                    check["diff"] = list(difflib.ndiff([check["expected"]], [check["quote"]]))
            except TovError as exc:
                check = {"reference": item["reference"], "verified": False, "status": exc.code, "error": str(exc)}
            if "line" in item:
                check["line"] = item["line"]
            checks.append(check)
        result.update(ok=all(c["verified"] for c in checks), checks=checks, checked=len(checks), passed=sum(c["verified"] for c in checks), allow_formatting=args.allow_formatting)
        return result, 0 if result["ok"] else 1
    raise TovError("알 수 없는 명령")


def render(result, fmt):
    if fmt == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif "error" in result:
        print(f'ERROR [{result["error"]["code"]}] {result["error"]["message"]}')
    elif "verses" in result:
        for row in result["verses"]:
            print(f'> **{row["reference"]}**\n> {row["text"]}\n' if fmt == "md" else f'({row["reference"]}) {row["text"]}')
        if "total" in result:
            print(f'검색 {result["total"]}건 / 반환 {result["returned"]}건 / 다음 offset: {result["next_offset"]}')
    elif "books" in result:
        for book in result["books"]:
            print(f'{book["book"]:02d} {book["long_label"]} ({book["short_label"]}) {book["last_chapter"]}장')
    elif "checks" in result:
        for check in result["checks"]:
            print(f'{"PASS" if check["verified"] else "FAIL"} {check["reference"]}: {check["status"]}')
            if not check["verified"]:
                for line in check.get("diff", []):
                    print(line)
        print(f'{result["passed"]}/{result["checked"]} 인용 검증 통과')
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    if fmt != "json" and "source" in result:
        src = result["source"]
        print(f'기준: 토브성경 개역한글 / {src["dataset_version"]} / SHA256 {src["dataset_sha256"]}')


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    fmt = "json" if args.json else args.format
    try:
        result, code = perform(Bible(), args)
    except TovError as exc:
        result, code = {"ok": False, "error": {"code": exc.code, "message": str(exc)}}, exc.exit_code
    except (OSError, ValueError, TypeError) as exc:
        result, code = {"ok": False, "error": {"code": "invalid_input", "message": str(exc)}}, 2
    render(result, fmt)
    return code
