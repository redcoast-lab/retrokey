"""Deterministic Japanese kana to JIS physical-key conversion."""

import unicodedata

from .mapping import MAPPING, Stroke
from .normalize import normalize

__all__ = ["UnsupportedCharacter", "convert", "key_sequence", "normalize"]


class UnsupportedCharacter(ValueError):
    def __init__(self, character: str, index: int):
        self.character = character
        self.index = index
        visible = repr(character) if character.isspace() or unicodedata.category(character).startswith("C") else character
        super().__init__(f"unsupported character: {visible} (U+{ord(character):04X}, normalized position {index + 1})")


# Only representable voiced kana. ヴ is exactly ウ + dakuten in JIS X 0201.
_VOICED = frozenset("ガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポヴ")
_MARKS = {"\u3099": "゛", "\u309a": "゜"}


def key_sequence(text: str) -> tuple[Stroke, ...]:
    strokes = []
    for index, character in enumerate(normalize(text)):
        parts = unicodedata.normalize("NFD", character) if character in _VOICED else character
        for part in parts:
            key = _MARKS.get(part, part)
            if key not in MAPPING:
                raise UnsupportedCharacter(character, index)
            strokes.append(MAPPING[key])
    return tuple(strokes)


def convert(text: str) -> dict[str, object]:
    keys = [stroke.display for stroke in key_sequence(text)]
    return {"input": text, "keys": keys, "display": " -> ".join(keys)}
