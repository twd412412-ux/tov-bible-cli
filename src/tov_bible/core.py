import gzip
import hashlib
import json
import re
import unicodedata
from pathlib import Path


class TovError(Exception):
    def __init__(self, message, code="invalid_reference", exit_code=2):
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_payload(data):
    """Reject malformed identities; do not substitute a different Bible corpus."""
    if data.get("language") != "kor" or data.get("source_url") != "https://bible.jbch.org/":
        raise ValueError("Expected Tov source and kor language")
    labels, verses = data["labels"], data["verses"]
    books = {x["book"]: x for x in labels}
    if len(labels) != 66 or set(books) != set(range(1, 67)):
        raise ValueError("Expected 66 unique books")
    codes, chapters = set(), set()
    for row in verses:
        b, c, v = row["book"], row["chapter"], row["paragraph"]
        if row.get("lang") != "kor" or b not in books or not 1 <= c <= books[b]["last_chapter"] or v < 1:
            raise ValueError("Invalid verse identity")
        if row["code"] != f"{b:02d}{c:03d}{v:03d}" or row["code"] in codes:
            raise ValueError("Invalid or duplicate code")
        if not isinstance(row["sentence"], str) or not row["sentence"].strip():
            raise ValueError("Empty verse text")
        codes.add(row["code"])
        chapters.add((b, c))
    expected_chapters = {(b, c) for b in books for c in range(1, books[b]["last_chapter"] + 1)}
    if chapters != expected_chapters or len(chapters) != 1189:
        raise ValueError("Missing or unexpected chapter")
    return {"books": len(books), "chapters": len(chapters), "verses": len(verses), "unique_codes": len(codes)}


def key(text):
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", text))


class Bible:
    def __init__(self, directory=None):
        directory = Path(directory) if directory else Path(__file__).parent / "data"
        try:
            self.manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
            compressed = (directory / "kor.json.gz").read_bytes()
            if sha256(compressed) != self.manifest["compressed_sha256"]:
                raise ValueError("Compressed data hash mismatch")
            raw = gzip.decompress(compressed)
            if sha256(raw) != self.manifest["dataset_sha256"]:
                raise ValueError("Dataset hash mismatch")
            self.data = json.loads(raw)
            stats = validate_payload(self.data)
            if stats != self.manifest["counts"]:
                raise ValueError("Manifest counts mismatch")
            if self.manifest["source_url"] != self.data["source_url"] or self.manifest["language"] != "kor":
                raise ValueError("Manifest source mismatch")
        except (OSError, ValueError, KeyError, TypeError, EOFError) as exc:
            raise TovError(f"기준 데이터 검증 실패: {exc}", "data_integrity", 3) from exc
        self.labels = {r["book"]: r for r in self.data["labels"]}
        self.rows = sorted(self.data["verses"], key=lambda r: (r["book"], r["chapter"], r["paragraph"]))
        self.by_key = {(r["book"], r["chapter"], r["paragraph"]): r for r in self.rows}
        self.chapters = {}
        for row in self.rows:
            self.chapters.setdefault((row["book"], row["chapter"]), []).append(row)
        self.aliases = {}
        for row in self.labels.values():
            for alias in (row["long_label"], row["short_label"]):
                self.aliases.setdefault(key(alias), set()).add(row["book"])
        for alias, book in {"요한일서": 62, "요한이서": 63, "요한삼서": 64}.items():
            self.aliases.setdefault(alias, set()).add(book)

    def source(self):
        return {k: self.manifest[k] for k in ("source_url", "translation", "language", "dataset_version", "dataset_sha256", "acquired_at")}

    def book_id(self, name):
        matches = self.aliases.get(key(name), set())
        if not matches:
            raise TovError(f"알 수 없는 권명: {name}", "unknown_book")
        if len(matches) != 1:
            raise TovError(f"모호한 권명: {name}", "ambiguous_book")
        return next(iter(matches))

    def parse(self, reference):
        text = key(reference).replace("–", "-").replace("~", "-")
        if "," in text or ";" in text:
            parts = re.split(r"[,;]", text)
            if any(not part for part in parts):
                raise TovError(f"빈 성구가 포함된 목록: {reference}")
            rows = self.parse(parts[0])
            for part in parts[1:]:
                if re.fullmatch(r"\d+(?:[:.]\d+)?(?:-\d+)?", part):
                    previous = rows[-1]
                    name = self.labels[previous["book"]]["long_label"]
                    part = name + (part if ":" in part or "." in part else f'{previous["chapter"]}:' + part)
                rows.extend(self.parse(part))
            return rows
        found = [(alias, ids) for alias, ids in self.aliases.items() if text.startswith(alias) and text[len(alias):len(alias)+1].isdigit()]
        if not found:
            raise TovError(f"권명과 장절을 확인하세요: {reference}")
        alias, ids = max(found, key=lambda x: len(x[0]))
        if len(ids) != 1:
            raise TovError(f"모호한 권명: {alias}", "ambiguous_book")
        book = next(iter(ids))
        rest = text[len(alias):]
        # 장 전체, 단일 절, 같은 장 범위, 여러 장 범위. 부분 권명 추측 금지.
        m = re.fullmatch(r"(\d+)(?:장)?(?:(?::|\.)(\d+)(?:절)?(?:-(?:(\d+)[:.])?(\d+)(?:절)?)?|(?<=장)(\d+)절(?:-(\d+)절)?)?", rest)
        if not m:
            raise TovError(f"지원하지 않는 장절 표기: {reference}")
        chapter = int(m[1])
        rows = self.chapters.get((book, chapter))
        if not rows:
            raise TovError(f"없는 장: {reference}", "not_found")
        start = int(m[2] or m[5] or rows[0]["paragraph"])
        end_chapter = int(m[3] or chapter)
        end = int(m[4] or m[6] or m[2] or m[5] or rows[-1]["paragraph"])
        if (book, chapter, start) not in self.by_key or (book, end_chapter, end) not in self.by_key:
            raise TovError(f"없는 절: {reference}", "not_found")
        if (end_chapter, end) < (chapter, start):
            raise TovError(f"역순 범위: {reference}")
        selected = [r for r in self.rows if r["book"] == book and (chapter, start) <= (r["chapter"], r["paragraph"]) <= (end_chapter, end)]
        # Declared ranges with holes are not silently shortened.
        for c in range(chapter, end_chapter + 1):
            chapter_rows = self.chapters[(book, c)]
            lo = start if c == chapter else chapter_rows[0]["paragraph"]
            hi = end if c == end_chapter else chapter_rows[-1]["paragraph"]
            if any((book, c, v) not in self.by_key for v in range(lo, hi + 1)):
                raise TovError(f"기준 데이터에 없는 절이 포함된 범위: {reference}", "not_found")
        return selected

    def present(self, row):
        book = self.labels[row["book"]]
        return {"reference": f'{book["long_label"]} {row["chapter"]}:{row["paragraph"]}', "book": row["book"], "chapter": row["chapter"], "verse": row["paragraph"], "code": row["code"], "text": row["sentence"], "source_url": f'https://bible.jbch.org/index.php?code={row["code"]}'}

    def search(self, query, mode="all", book=None, testament=None):
        query = unicodedata.normalize("NFC", query).strip()
        if not query:
            raise TovError("검색어가 비었습니다.", "empty_query")
        terms = [query] if mode == "phrase" else query.split()
        selected_book = self.book_id(book) if book else None
        results = []
        for row in self.rows:
            if selected_book and row["book"] != selected_book:
                continue
            if testament and self.labels[row["book"]]["testament"] != testament:
                continue
            hits = [term.casefold() in row["sentence"].casefold() for term in terms]
            if (any(hits) if mode == "any" else all(hits)):
                results.append(row)
        return results

    def verify(self, reference, quote, kind="quotation", allow_formatting=False):
        rows = self.parse(reference)
        expected = " ".join(r["sentence"] for r in rows)
        quoted = quote.strip()
        pairs = [("“", "”"), ('"', '"'), ("‘", "’")]
        for left, right in pairs:
            if quoted.startswith(left) and quoted.endswith(right) and len(quoted) >= 2:
                quoted = quoted[1:-1]
                break
        result = {"reference": reference, "kind": kind, "quote": quote, "expected": expected, "verses": [self.present(r) for r in rows]}
        if kind in ("mention", "paraphrase"):
            status, verified = "reference_only", False
        elif not quoted:
            status, verified = "missing_quote", False
        elif quoted == expected:
            status, verified = "exact", True
        elif key(quoted) == key(expected):
            status, verified = "formatting_difference", bool(allow_formatting)
        elif re.search(r"…|\.{3,}", quoted):
            parts = [p for p in re.split(r"…+|\.{3,}", quoted) if p.strip()]
            cursor, matched = 0, bool(parts)
            haystack = key(expected) if allow_formatting else expected
            for part in parts:
                needle = key(part) if allow_formatting else part.strip()
                position = haystack.find(needle, cursor)
                if position < 0:
                    matched = False
                    break
                cursor = position + len(needle)
            status, verified = ("ordered_excerpt", True) if matched else ("mismatch", False)
        else:
            status, verified = "mismatch", False
        result.update(status=status, verified=verified)
        return result


def markdown_quotes(text):
    lines = text.splitlines()
    results = []
    i = 0
    while i < len(lines):
        match = re.match(r"^>\s*(?:\[!info\]\s*)?\*\*(.+?)\*\*\s*$", lines[i], re.I)
        if not match:
            i += 1
            continue
        line_number = i + 1
        reference = match[1]
        i += 1
        body = []
        while i < len(lines) and lines[i].startswith(">"):
            fragment = re.sub(r"^>\s?", "", lines[i]).strip()
            if fragment:
                body.append(fragment)
            i += 1
        if reference == "외부 보충":
            continue
        results.append({"reference": reference, "quote": " ".join(body), "line": line_number})
    return results
