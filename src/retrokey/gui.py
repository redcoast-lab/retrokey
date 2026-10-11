"""Small native GUI sharing the CLI's conversion API."""

import json
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk

from . import UnsupportedCharacter, convert


def format_keys(text: str) -> str:
    """The same string is displayed, selected, and copied."""
    return " → ".join(convert(text)["keys"])


def error_message(error: UnsupportedCharacter) -> str:
    character = repr(error.character) if error.character.isspace() else error.character
    return f"「{character}」は変換できません（{error.index + 1}文字目）。\nカナで入力できる言葉か確認してください。"


class RetrokeyApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("retrokey")
        root.geometry("510x340")
        root.minsize(420, 320)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        frame = ttk.Frame(root, padding=18)
        frame.grid(sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(4, weight=1)
        ttk.Label(frame, text="ゲームで入力したい言葉").grid(row=0, column=0, sticky="w")
        self.input = tk.StringVar(root)
        self.entry = ttk.Entry(frame, textvariable=self.input, font=("", 14))
        self.entry.grid(row=1, column=0, sticky="ew", pady=(6, 10))
        self.entry.bind("<Return>", self.on_convert)
        self.input.trace_add("write", self.on_edit)
        ttk.Button(frame, text="変換", command=self.on_convert).grid(row=2, column=0, sticky="e")
        ttk.Label(frame, text="押すキー:").grid(row=3, column=0, sticky="w", pady=(12, 6))
        self.output = tk.Text(frame, height=3, wrap="word", font=("", 15), state="disabled", relief="solid", borderwidth=1)
        self.output.grid(row=4, column=0, sticky="nsew")
        self.copy_button = ttk.Button(frame, text="コピー", command=self.on_copy, state="disabled")
        self.copy_button.grid(row=5, column=0, sticky="e", pady=(8, 4))
        self.status = tk.StringVar(root)
        ttk.Label(frame, textvariable=self.status, wraplength=470).grid(row=6, column=0, sticky="w")
        ttk.Label(frame, text="¥ は上段、\\ は右 Shift の左のキーです。\nゲーム側のカナ入力を有効にして使います。", wraplength=470).grid(row=7, column=0, sticky="w", pady=(10, 0))
        self.result = ""
        root.report_callback_exception = self.on_unexpected_error
        root.after_idle(self.entry.focus_force)

    def set_result(self, text: str) -> None:
        self.result = text
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)
        self.output.configure(state="disabled")
        self.copy_button.configure(state="normal" if text else "disabled")

    def on_edit(self, *_args) -> None:
        self.set_result("")
        self.status.set("")

    def on_convert(self, _event=None) -> str:
        self.set_result("")
        if not self.input.get().strip():
            self.status.set("入力したい言葉を入れてください。")
            return "break"
        try:
            self.set_result(format_keys(self.input.get()))
            self.status.set("")
        except UnsupportedCharacter as error:
            self.status.set(error_message(error))
        return "break"

    def on_copy(self) -> None:
        if not self.result:
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.result)
            self.status.set("押すキーをコピーしました。")
        except tk.TclError:
            self.status.set("コピーできませんでした。結果を選択してコピーしてください。")

    def on_unexpected_error(self, *_args) -> None:
        self.set_result("")
        self.status.set("処理できませんでした。もう一度お試しください。")


def smoke_test(root: tk.Tk, app: RetrokeyApp, report: Path) -> None:
    """Build verification: exercise real widgets and clipboard, then close."""
    try:
        root.update()
        assert root.focus_get() == app.entry, "Input field did not receive initial focus"
        for variants, expected in (
            (("シークロン", "ｼｰｸﾛﾝ", "しーくろん"), "D → ¥ → H → \\ → Y"),
            (("スターアーサー", "ｽﾀｰｱｰｻｰ", "すたーあーさー"), "R → Q → ¥ → 3 → ¥ → X → ¥"),
        ):
            for text in variants:
                app.input.set(text)
                app.on_convert()
                assert app.result == expected, f"Conversion mismatch for {text}"
                assert app.input.get() == text, "Input was changed"
                assert app.output.get("1.0", "end-1c") == expected, "Result widget mismatch"
                app.on_copy()
                assert root.clipboard_get() == expected, "Clipboard text mismatch"
        app.input.set("漢字")
        app.on_convert()
        assert not app.result and "変換できません" in app.status.get()
        assert str(app.copy_button["state"]) == "disabled"
        app.input.set("")
        app.on_convert()
        assert "入れてください" in app.status.get()
        report.write_text(json.dumps({"ok": True, "inputs": 6, "clipboard": True}), encoding="utf-8")
    except Exception as error:
        report.write_text(json.dumps({"ok": False, "error": str(error)}), encoding="utf-8")
    finally:
        root.destroy()


def main() -> int:
    try:
        root = tk.Tk()
    except tk.TclError:
        return 1
    app = RetrokeyApp(root)
    # Internal packaging check; normal desktop startup has no arguments.
    if len(sys.argv) == 3 and sys.argv[1] == "--smoke-test":
        root.after(300, smoke_test, root, app, Path(sys.argv[2]))
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
