"""One-time research check; requires downloaded upstream files in research/."""

import json
from pathlib import Path
import re
import sys
import unicodedata
from urllib.request import urlopen

root = Path(__file__).parent
if "--fetch" in sys.argv:
    sources = json.loads((root / "sources.json").read_text(encoding="utf-8"))
    for name, url in sources.items():
        with urlopen(url) as response:
            (root / name).write_bytes(response.read())
np2 = (root / "keytable.res").read_text(encoding="utf-8")
blocks = re.findall(r"\{\s*//[^\n]*\n(.*?)\n\s*\}", np2, re.S)


def values(block):
    block = re.sub(r"//[^\n]*", "", block)
    return [int(value, 16) if value.startswith("0x") else ord(__import__('ast').literal_eval(value))
            for value in re.findall(r"0x[0-9a-fA-F]+|'(?:\\.|[^'\\])*'", block)]


normal, kana, shifted = (values(blocks[i]) for i in (0, 4, 5))
assert len(normal) == len(kana) == len(shifted) == 96
expected = {}
for i, byte in enumerate(kana[:0x35]):
    if 0xa1 <= byte <= 0xdf:
        label = chr(normal[i]).upper()
        if i == 0x0d:
            label = "¥"
        if i == 0x33:
            label = "\\"
        expected[byte] = label
assert len(expected) == 48

fm7 = (root / "fm7.cpp").read_text(encoding="utf-8")
rows = re.findall(r"\{(0x[0-9a-f, x]+)\}", fm7.split("fm7_key_list", 1)[1].split("};", 1)[0])
fm = {}
for row in rows:
    codes = [int(v, 16) for v in row.split(",")]
    if 0xa1 <= codes[4] <= 0xdf:
        fm[codes[4]] = codes
assert set(fm) == set(expected)
for byte, label in expected.items():
    if byte == 0xdb:  # FM-7 prints a quote on its legacy RO key.
        continue
    assert fm[byte][0] == (0x5c if label == "¥" else ord(label.lower())), (byte, label)

x1 = (root / "x1.cpp").read_text(encoding="utf-8")
xrows = re.findall(r"\{(0x[0-9a-f,x]+)\}", x1.split("kanatable[52][3]", 1)[1].split("};", 1)[0])
xt = {codes[1]: codes for row in xrows if (codes := [int(v, 16) for v in row.split(",")])[1] >= 0xa1}
for byte, label in expected.items():
    if byte in (0xb0, 0xdb):
        assert xt[byte][0] == {0xb0: 0x5c, 0xdb: 0x5f}[byte]
    else:
        assert xt[byte][0] == ord(label), (byte, label)

fixture = []
for byte, label in expected.items():
    character = unicodedata.normalize("NFKC", bytes([byte]).decode("cp932"))
    if character == "\u3099":
        character = "゛"
    if character == "\u309a":
        character = "゜"
    fixture.append([character, label])
for i, byte in enumerate(shifted[:0x35]):
    if 0xa1 <= byte <= 0xaf:
        character = unicodedata.normalize("NFKC", bytes([byte]).decode("cp932"))
        fixture.append([character, "Shift+" + expected[kana[i]]])
fixture.append([" ", "Space"])

# Check Shift kana against both independently implemented source tables.
for character, display in fixture:
    if display.startswith("Shift+"):
        half = next(b for b in range(0xa1, 0xb0) if unicodedata.normalize("NFKC", bytes([b]).decode("cp932")) == character)
        label = display.removeprefix("Shift+")
        base_byte = next(b for b, l in expected.items() if l == label)
        assert fm[base_byte][5] == xt[base_byte][2] == half

# QUASI88: a kana macro selects a matrix port/bit; keyboard.c names that key.
qt = (root / "quasi88-romaji-table.h").read_text(encoding="utf-8")
qk = (root / "quasi88-keyboard.c").read_text(encoding="utf-8")
ports = {}
for port, bit, code in re.findall(r"\{ Port(\d+), Bit(\d) \}.*?KEY88_\w+\s*=\s*(\d+)", qk):
    code = int(code)
    if code == 32 or 44 <= code <= 59 or 64 <= code <= 95:
        ports[(int(port), int(bit))] = {32: "Space", 92: "¥", 95: "\\"}.get(code, chr(code))
macros = {name: (int(port), int(bit), int(shift)) for name, port, bit, shift in re.findall(r"#define\s+(XR_\w+)\s+RJ\(P(\d+),(\d),(\d)\)", qt)}
checked = set()
for hiragana, macro in re.findall(r"/\*\s*([ぁ-ん])\s*\*/\s*\{\s*\"[^\"]+\",\s*\{\s*(XR_\w+),\s*\}", qt):
    character = chr(ord(hiragana) + 0x60)
    if character in dict(fixture):
        port, bit, shift = macros[macro]
        display = ("Shift+" if shift else "") + ports[(port, bit)]
        assert dict(fixture)[character] == display, (character, display)
        checked.add(character)
assert len(checked) >= 46, len(checked)
for macro, character in (("XR_rr", "ー"), ("XR_jj", "゛"), ("XR_pp", "゜"), ("XR_aa", "「"), ("XR_ee", "」"), ("XR_xx", "。"), ("XR_yy", "、"), ("XR_oo", "・")):
    port, bit, shift = macros[macro]
    assert dict(fixture)[character] == ("Shift+" if shift else "") + ports[(port, bit)]
target = root.parent / "tests" / "fixtures" / "jis-kana.json"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"NP2/FM-7/X1/QUASI88 layouts agree; wrote {len(fixture)} source-derived cases")
