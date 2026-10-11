"""Command-line interface; conversion errors never emit partial stdout."""

import argparse
import io
import json
import sys

from . import UnsupportedCharacter, convert


def main(argv: list[str] | None = None) -> int:
    # Windows redirected stdout may otherwise use cp932, which cannot encode ¥.
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Convert Japanese kana to JIS physical keys (kana mode required).")
    parser.add_argument("--json", action="store_true", help="emit one JSON object")
    parser.add_argument("text", help="kana text; quote spaces and shell metacharacters")
    args = parser.parse_args(argv)
    try:
        result = convert(args.text)
    except UnsupportedCharacter as error:
        print(f"retrokey: {error}", file=sys.stderr)
        return 1
    if args.json:
        # ASCII escapes preserve Unicode even through legacy Windows pipes.
        print(json.dumps(result, ensure_ascii=True))
    else:
        print(args.text)
        print(f"QWERTY: {result['display']}")
    return 0
