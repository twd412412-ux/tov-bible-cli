import importlib.util
import unittest
from pathlib import Path

from tov_bible.core import Bible, markdown_quotes


SKILL = Path(__file__).parents[1] / "skills/youtube-video-transcript"
spec = importlib.util.spec_from_file_location("sermon_notes", SKILL / "scripts/export_apple_notes.py")
notes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notes)


class SermonBundleTests(unittest.TestCase):
    def test_notes_conversion_preserves_tov_quotation(self):
        bible = Bible()
        text = bible.parse("벧전1:13")[0]["sentence"]
        study = (
            "# 형식 변환 시험\n\n"
            "## 1. 말씀을 바랍니다 (약 00:00~01:00)\n\n"
            "==주어진 은혜를 바랍니다.==\n\n"
            "> [!info] **베드로전서 1:13**\n"
            f"> “{text}”\n"
        )
        converted = notes.convert(study)
        self.assertEqual(notes.content(study), notes.content(converted))
        self.assertNotIn("[!info]", converted)
        self.assertIn("**주어진 은혜를 바랍니다.**", converted)
        for document in (study, converted):
            quotations = markdown_quotes(document)
            self.assertEqual(len(quotations), 1)
            item = quotations[0]
            self.assertTrue(bible.verify(item["reference"], item["quote"])["verified"])

    def test_unknown_callout_is_not_silently_dropped(self):
        with self.assertRaises(ValueError):
            notes.convert("> [!unknown] 알 수 없는 표시\n> 원문\n")


if __name__ == "__main__":
    unittest.main()
