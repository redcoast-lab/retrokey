import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from retrokey import UnsupportedCharacter
from retrokey.history import HistoryStore


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "settings/history.json"
        self.store = HistoryStore(self.path)

    def test_twenty_fifo_entries_and_independent_pin(self):
        self.store.pin("シークロン")
        for length in range(1, 26):
            self.store.record("ア" * length)
        self.assertEqual(self.store.history, ["ア" * length for length in range(6, 26)])
        self.assertEqual(self.store.bookmarks, ["シークロン"])
        self.store.record("ア" * 25)
        self.assertEqual(self.store.history[-2:], ["ア" * 25, "ア" * 25])
        self.assertEqual(len(self.store.history), 20)

    def test_pins_deduplicate_normalized_kana_and_can_be_removed(self):
        self.assertTrue(self.store.pin("しーくろん"))
        self.assertFalse(self.store.pin("ｼｰｸﾛﾝ"))
        self.assertFalse(self.store.pin("シークロン"))
        self.assertTrue(self.store.pin("スターアーサー"))
        self.store.unpin(0)
        self.assertEqual(self.store.bookmarks, ["スターアーサー"])

    def test_round_trip_and_limits_on_load(self):
        self.store.history = ["ア" * length for length in range(1, 24)]
        self.store.bookmarks = ["シークロン", "しーくろん", "レイソード"]
        self.store.save()
        loaded = HistoryStore(self.path)
        self.assertEqual(loaded.history, self.store.history[-20:])
        self.assertEqual(loaded.bookmarks, ["シークロン", "レイソード"])
        self.assertFalse(loaded.load_error)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_invalid_history_is_recoverable(self):
        self.path.parent.mkdir()
        for content in ("broken", "[]", '{"version":1,"history":[42]}', '{"version":1,"bookmarks":["漢字"]}'):
            with self.subTest(content=content):
                self.path.write_text(content, encoding="utf-8")
                loaded = HistoryStore(self.path)
                self.assertTrue(loaded.load_error)
                self.assertEqual(loaded.history, [])
                self.assertEqual(loaded.bookmarks, [])
                loaded.record("ア")
                loaded.save()
                self.assertEqual(HistoryStore(self.path).history, ["ア"])

    def test_invalid_input_does_not_enter_history(self):
        self.store.record("")
        self.store.record("　 ")
        self.assertFalse(self.store.pin(""))
        with self.assertRaises(UnsupportedCharacter):
            self.store.record("漢")
        self.assertEqual(self.store.history, [])

    def test_failed_save_keeps_previous_file(self):
        self.store.record("ア")
        self.store.save()
        self.store.record("イ")
        with patch("retrokey.history.os.replace", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                self.store.save()
        self.assertEqual(HistoryStore(self.path).history, ["ア"])
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])


if __name__ == "__main__":
    unittest.main()
