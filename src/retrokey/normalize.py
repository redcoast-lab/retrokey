"""Normalize only equivalent kana spellings, without approximations."""

import re
import unicodedata


def normalize(text: str) -> str:
    # Scope compatibility normalization to halfwidth Japanese characters.
    # Global NFKC would silently accept e.g. circled kana or ligatures.
    text = re.sub(r"[\uff61-\uff9f]+", lambda m: unicodedata.normalize("NFKC", m[0]), text)
    text = text.replace("\u3000", " ")
    text = text.replace("゛", "\u3099").replace("゜", "\u309a")
    text = unicodedata.normalize("NFC", text)
    text = "".join(chr(ord(c) + 0x60) if "ぁ" <= c <= "ゖ" else c for c in text)
    return unicodedata.normalize("NFC", text)
