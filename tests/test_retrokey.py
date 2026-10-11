import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from retrokey import UnsupportedCharacter, convert, key_sequence, normalize
from retrokey.mapping import MAPPING


class ConversionTests(unittest.TestCase):
    def test_source_derived_layout(self):
        rows = json.loads((Path(__file__).parent / "fixtures/jis-kana.json").read_text(encoding="utf-8"))
        self.assertEqual(set(MAPPING), {row[0] for row in rows})
        for kana, expected in rows:
            with self.subTest(kana=kana):
                self.assertEqual(convert(kana)["keys"], [expected])

    def test_game_fixtures(self):
        cases = {
            "シークロン": ["D", "¥", "H", "\\", "Y"],
            "スターアーサー": ["R", "Q", "¥", "3", "¥", "X", "¥"],
            "レイソード": [";", "E", "C", "¥", "S", "@"],
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(convert(text)["keys"], expected)

    def test_voiced_kana(self):
        for voiced, base in zip("ガギグゲゴザジズゼゾダヂヅデドバビブベボヴ", "カキクケコサシスセソタチツテトハヒフヘホウ", strict=True):
            with self.subTest(voiced=voiced):
                self.assertEqual(convert(voiced)["keys"], convert(base)["keys"] + ["@"])
        for voiced, base in zip("パピプペポ", "ハヒフヘホ", strict=True):
            self.assertEqual(convert(voiced)["keys"], convert(base)["keys"] + ["["])

    def test_normalization(self):
        for text in ("ガパヴァ", "カ\u3099ハ\u309aウ\u3099ァ", "カ゛ハ゜ウ゛ァ", "ｶﾞﾊﾟｳﾞｧ", "がぱゔぁ"):
            with self.subTest(text=text):
                self.assertEqual(convert(text)["keys"], ["T", "@", "F", "[", "4", "@", "Shift+3"])
                self.assertEqual(normalize(normalize(text)), normalize(text))
        self.assertEqual(convert(" ア　イ ")["keys"], ["Space", "3", "Space", "E", "Space"])
        self.assertEqual(convert("゛゜\u3099\u309a")["keys"], ["@", "[", "@", "["])

    def test_unsupported(self):
        for text in ("漢", "ヮ", "ヵ", "ヶ", "ヷ", "ヸ", "ヹ", "ヺ", "ヰ", "ヱ", "A", "-", "㋐", "㌀", "\n", "\t", "😀"):
            with self.subTest(text=text), self.assertRaises(UnsupportedCharacter):
                convert(text)
        with self.assertRaisesRegex(UnsupportedCharacter, "normalized position 2"):
            convert("ア漢")

    def test_positions_and_empty(self):
        self.assertEqual([s.position for s in key_sequence("ーロム゛゜")], ["IntlYen", "IntlRo", "Backslash", "BracketLeft", "BracketRight"])
        self.assertEqual(convert(""), {"input": "", "keys": [], "display": ""})


class CliTests(unittest.TestCase):
    def invoke(self, *args):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        return subprocess.run([sys.executable, "-m", "retrokey", *args], capture_output=True, text=True, encoding="utf-8", env=env)

    def test_human_output(self):
        result = self.invoke("シークロン")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "シークロン\nQWERTY: D -> ¥ -> H -> \\ -> Y\n")
        self.assertEqual(result.stderr, "")

    def test_json(self):
        result = self.invoke("--json", "ｽﾀｰｱｰｻｰ")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), convert("ｽﾀｰｱｰｻｰ"))
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout, self.invoke("--json", "ｽﾀｰｱｰｻｰ").stdout)

    def test_error_streams(self):
        for args, code in ((["--json", "ア漢"], 1), ([], 2), (["--machine", "fm7", "ア"], 2)):
            result = self.invoke(*args)
            self.assertEqual(result.returncode, code)
            self.assertEqual(result.stdout, "")
            self.assertTrue(result.stderr)

    def test_empty_and_metacharacters(self):
        self.assertEqual(json.loads(self.invoke("--json", "").stdout)["keys"], [])
        self.assertEqual(self.invoke("$(echo test)").returncode, 1)

    def test_legacy_windows_pipe_encoding(self):
        result = subprocess.run(
            [sys.executable, "-m", "retrokey", "シークロン"],
            capture_output=True, text=True, encoding="utf-8",
            env=dict(os.environ, PYTHONIOENCODING="cp932"),
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("D -> ¥ -> H -> \\ -> Y", result.stdout)


if __name__ == "__main__":
    unittest.main()
