"""Shared JIS kana layout. Positions are independent of printed labels."""

from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class Stroke:
    position: str
    label: str
    shift: bool = False

    @property
    def display(self) -> str:
        return f"Shift+{self.label}" if self.shift else self.label


# MAME fm7_key_list, X1 kanatable, NP2 keytable and QUASI88 XR_*.
_ROWS = (
    ("ヌフアウエオヤユヨワホヘー", "1 2 3 4 5 6 7 8 9 0 - ^ ¥"),
    ("タテイスカンナニラセ゛゜", "Q W E R T Y U I O P @ ["),
    ("チトシハキクマノリレケム", "A S D F G H J K L ; : ]"),
    ("ツサソヒコミモネルメロ", "Z X C V B N M , . / \\"),
)
_SPECIAL_POSITIONS = {
    "-": "Minus", "^": "Equal", "¥": "IntlYen", "@": "BracketLeft",
    "[": "BracketRight", ";": "Semicolon", ":": "Quote",
    "]": "Backslash", ",": "Comma", ".": "Period", "/": "Slash",
    "\\": "IntlRo", "Space": "Space",
}


def _position(label: str) -> str:
    if label in _SPECIAL_POSITIONS:
        return _SPECIAL_POSITIONS[label]
    return f"Digit{label}" if label.isdigit() else f"Key{label}"


_mapping = {}
for kana, labels in _ROWS:
    for character, label in zip(kana, labels.split(), strict=True):
        _mapping[character] = Stroke(_position(label), label)
_mapping[" "] = Stroke("Space", "Space")
for small, base in zip("ァィゥェォャュョッヲ「」、。・", "アイウエオヤユヨツワ゜ムネルメ", strict=True):
    stroke = _mapping[base]
    _mapping[small] = Stroke(stroke.position, stroke.label, shift=True)

MAPPING = MappingProxyType(_mapping)
