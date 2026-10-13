import unittest
from unittest.mock import patch

from retrokey import UnsupportedCharacter, convert
from retrokey.gui import error_message, format_keys


class GuiLogicTests(unittest.TestCase):
    def test_shared_core_and_clipboard_text(self):
        with patch("retrokey.gui.convert", return_value={"keys": ["D", "¥", "H", "\\", "Y"]}) as core:
            self.assertEqual(format_keys("しーくろん"), "D → ¥ → H → ＼ → Y")
            core.assert_called_once_with("しーくろん")

    def test_input_variants(self):
        for variants, expected in (
            (("シークロン", "ｼｰｸﾛﾝ", "しーくろん"), ["D", "¥", "H", "\\", "Y"]),
            (("スターアーサー", "ｽﾀｰｱｰｻｰ", "すたーあーさー"), ["R", "Q", "¥", "3", "¥", "X", "¥"]),
            (("ガパヴァッャー", "ｶﾞﾊﾟｳﾞｧｯｬｰ", "がぱゔぁっゃー", "カ\u3099ハ\u309aウ\u3099ァッャー"), ["T", "@", "F", "[", "4", "@", "Shift+3", "Shift+Z", "Shift+7", "¥"]),
        ):
            for text in variants:
                with self.subTest(text=text):
                    self.assertEqual(convert(text)["keys"], expected)
                    self.assertEqual(format_keys(text), " → ".join(expected).replace("\\", "＼"))

    def test_readable_error(self):
        with self.assertRaises(UnsupportedCharacter) as caught:
            format_keys("ア漢")
        message = error_message(caught.exception)
        self.assertIn("漢", message)
        self.assertIn("2文字目", message)
        self.assertNotIn("Traceback", message)


if __name__ == "__main__":
    unittest.main()
