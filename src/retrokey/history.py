"""GUI history: twenty successful conversions, plus independent bookmarks."""

import json
import os
from pathlib import Path
import sys
import tempfile

from . import convert, normalize

HISTORY_LIMIT = 20


def state_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local")))
    elif sys.platform == "darwin":
        base = Path.home() / "Library/Application Support"
    else:
        base = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state")))
    return base / "retrokey" / "history.json"


class HistoryStore:
    def __init__(self, path: Path | None = None):
        self.path = path if path is not None else state_path()
        self.history: list[str] = []  # oldest first
        self.bookmarks: list[str] = []
        self.load_error = False
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or data.get("version") != 1:
                raise ValueError("Invalid saved history")
            for field in ("history", "bookmarks"):
                items = data.get(field, [])
                if not isinstance(items, list):
                    raise ValueError("Invalid saved history list")
                validated = []
                for text in items:
                    if not isinstance(text, str) or not text.strip():
                        raise ValueError("Invalid saved text")
                    convert(text)
                    validated.append(text)
                if field == "history":
                    self.history = validated[-HISTORY_LIMIT:]
                else:
                    for text in validated:
                        if not any(normalize(pinned) == normalize(text) for pinned in self.bookmarks):
                            self.bookmarks.append(text)
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError):
            self.history = []
            self.bookmarks = []
            self.load_error = True

    def record(self, text: str) -> None:
        convert(text)
        if not text.strip():
            return
        self.history.append(text)
        self.history = self.history[-HISTORY_LIMIT:]

    def pin(self, text: str) -> bool:
        convert(text)
        if not text.strip() or any(normalize(item) == normalize(text) for item in self.bookmarks):
            return False
        self.bookmarks.append(text)
        return True

    def unpin(self, index: int) -> None:
        del self.bookmarks[index]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent, delete=False) as output:
                temporary = Path(output.name)
                json.dump({"version": 1, "history": self.history, "bookmarks": self.bookmarks}, output, ensure_ascii=False)
                output.write("\n")
            os.replace(temporary, self.path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
