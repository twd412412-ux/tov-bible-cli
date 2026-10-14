import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tov_bible.cli import main
from tov_bible.core import Bible, TovError, markdown_quotes


class BibleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bible = Bible()

    def test_dataset_shape(self):
        self.assertEqual(len(self.bible.rows), 31101)
        self.assertEqual(len(self.bible.labels), 66)
        self.assertEqual(len(self.bible.chapters), 1189)
        self.assertEqual(len(self.bible.by_key), 31101)

    def test_every_stored_verse_round_trip(self):
        # Test every declared address, not a guessed external canonical verse count.
        for row in self.bible.rows:
            b, c, v = row["book"], row["chapter"], row["paragraph"]
            self.assertEqual(self.bible.by_key[(b, c, v)]["sentence"], row["sentence"])
            self.assertEqual(row["code"], f"{b:02d}{c:03d}{v:03d}")

    def test_aliases_and_digit_books(self):
        for ref in ("요3:16", "요한복음 3:16", "요한복음3장16절", "요3.16"):
            self.assertEqual(self.bible.parse(ref)[0]["code"], "43003016")
        for ref in ("요일1:6", "요한1서1:6", "요한일서1:6"):
            self.assertEqual(self.bible.parse(ref)[0]["code"], "62001006")
        self.assertEqual(self.bible.parse("고전13:4")[0]["book"], 46)
        self.assertEqual(self.bible.parse("요한2서1장")[0]["book"], 63)

    def test_range_and_cross_chapter(self):
        self.assertEqual(len(self.bible.parse("요3:16~18")), 3)
        self.assertEqual(len(self.bible.parse("창1장")), 31)
        self.assertEqual(len(self.bible.parse("요3:36-4:2")), 3)
        self.assertEqual(len(self.bible.parse("요3장16절-18절")), 3)

    def test_compound_reference_preserves_stated_order(self):
        rows = self.bible.parse("마태복음 24:36, 33")
        self.assertEqual([r["paragraph"] for r in rows], [36, 33])
        rows = self.bible.parse("요3:16; 창1:1")
        self.assertEqual([r["book"] for r in rows], [43, 1])
        with self.assertRaises(TovError):
            self.bible.parse("요3:16,")

    def test_omission_without_ellipsis_is_not_full_quote(self):
        text = self.bible.parse("히2:3")[0]["sentence"]
        first = text.split(" 이 구원은", 1)[0]
        self.assertFalse(self.bible.verify("히2:3", first)["verified"])
        self.assertTrue(self.bible.verify("히2:3", first + " …")["verified"])

    def test_bad_reference_never_falls_back(self):
        for ref in ("요3:0", "요3:999", "요999장", "요3:18-16", "가짜3:16", "고13:4", "요3:16 garbage"):
            with self.subTest(ref=ref), self.assertRaises(TovError):
                self.bible.parse(ref)

    def test_search_and_or_phrase(self):
        both = self.bible.search("기도 감사", "all")
        either = self.bible.search("기도 감사", "any")
        self.assertTrue(both)
        self.assertGreater(len(either), len(both))
        self.assertTrue(all("기도" in r["sentence"] and "감사" in r["sentence"] for r in both))
        self.assertTrue(all(r["book"] == 43 for r in self.bible.search("하나님", book="요")))
        self.assertTrue(all(r["book"] <= 39 for r in self.bible.search("하나님", testament="구약")))

    def test_exact_and_wrong_quote(self):
        text = self.bible.parse("창1:1")[0]["sentence"]
        self.assertTrue(self.bible.verify("창1:1", text)["verified"])
        self.assertFalse(self.bible.verify("창1:1", text.replace("천지", "하늘"))["verified"])

    def test_formatting_explicit_only(self):
        text = self.bible.parse("창1:1")[0]["sentence"].replace(" ", "")
        result = self.bible.verify("창1:1", text)
        self.assertEqual(result["status"], "formatting_difference")
        self.assertFalse(result["verified"])
        self.assertTrue(self.bible.verify("창1:1", text, allow_formatting=True)["verified"])

    def test_ordered_excerpt_and_reversed_excerpt(self):
        text = self.bible.parse("요3:16")[0]["sentence"]
        first, last = text[:12], text[-12:]
        self.assertTrue(self.bible.verify("요3:16", first + " … " + last)["verified"])
        self.assertFalse(self.bible.verify("요3:16", last + " … " + first)["verified"])
        self.assertFalse(self.bible.verify("요3:16", "…")["verified"])

    def test_reference_only_does_not_claim_verified(self):
        self.assertFalse(self.bible.verify("요3:16", "사랑에 대한 말씀", "paraphrase")["verified"])

    def test_md_formats(self):
        text = '# 설교\n> [!info] **창세기 1:1**\n> “태초에 하나님이 천지를 창조하시니라”\n\n설명\n> **요3:16**\n>\n> “하나님이 … 하심이니라”\n'
        items = markdown_quotes(text)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["line"], 2)
        self.assertEqual(items[1]["reference"], "요3:16")

    def test_corrupt_package_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(__file__).parents[1] / "src/tov_bible/data"
            dest = Path(tmp)
            shutil.copy(src / "manifest.json", dest)
            shutil.copy(src / "kor.json.gz", dest)
            with (dest / "kor.json.gz").open("ab") as f:
                f.write(b"corruption")
            with self.assertRaises(TovError) as cm:
                Bible(dest)
            self.assertEqual(cm.exception.exit_code, 3)

    def run_cli(self, argv):
        out = io.StringIO()
        # Socket access forbidden throughout CLI operation, even with no environment credentials.
        with patch("socket.socket", side_effect=AssertionError("Network prohibited")), contextlib.redirect_stdout(out):
            exit_code = main(argv)
        return exit_code, json.loads(out.getvalue())

    def test_cli_without_network(self):
        code, obj = self.run_cli(["verse", "요3:16", "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(obj["source"]["language"], "kor")
        self.assertEqual(obj["verses"][0]["code"], "43003016")

    def test_search_pagination(self):
        _, obj = self.run_cli(["search", "하나님", "--json", "--limit", "2"])
        self.assertEqual(obj["returned"], 2)
        self.assertGreater(obj["total"], 100)
        self.assertTrue(obj["truncated"])
        self.assertEqual(obj["next_offset"], 2)

    def test_exit_code_mismatch(self):
        code, obj = self.run_cli(["verify", "--reference", "창1:1", "--quote", "잘못된 본문", "--json"])
        self.assertEqual(code, 1)
        self.assertFalse(obj["ok"])

    def test_no_quotes_cannot_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "empty.md"
            file.write_text("성구 인용 없음", encoding="utf-8")
            code, obj = self.run_cli(["verify", str(file), "--json"])
            self.assertEqual(code, 2)
            self.assertEqual(obj["error"]["code"], "no_quotations")

    def test_batch_reports_each_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "references.json"
            file.write_text(json.dumps(["요3:16", "요3:999"]), encoding="utf-8")
            code, obj = self.run_cli(["batch", str(file), "--json"])
            self.assertEqual(code, 2)
            self.assertTrue(obj["results"][0]["ok"])
            self.assertFalse(obj["results"][1]["ok"])


if __name__ == "__main__":
    unittest.main()
