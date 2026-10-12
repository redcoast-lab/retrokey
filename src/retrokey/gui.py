"""Small native GUI sharing the CLI's conversion API."""

import json
from pathlib import Path
import sys
import tempfile
import tkinter as tk
from tkinter import ttk

from . import UnsupportedCharacter, convert
from .history import HistoryStore


def format_keys(text: str) -> str:
    """The same string is displayed, selected, and copied."""
    return " → ".join(convert(text)["keys"])


def error_message(error: UnsupportedCharacter) -> str:
    character = repr(error.character) if error.character.isspace() else error.character
    return f"「{character}」は変換できません（{error.index + 1}文字目）。\nカナで入力できる言葉か確認してください。"


class RetrokeyApp:
    def __init__(self, root: tk.Tk, store: HistoryStore | None = None):
        self.root = root
        self.store = store if store is not None else HistoryStore()
        root.title("retrokey")
        root.geometry("780x590")
        root.minsize(650, 500)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        frame = ttk.Frame(root, padding=18)
        frame.grid(sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(8, weight=1)
        ttk.Label(frame, text="ゲームで入力したい言葉").grid(row=0, column=0, sticky="w")
        self.input = tk.StringVar(root)
        self.entry = ttk.Entry(frame, textvariable=self.input, font=("", 14))
        self.entry.grid(row=1, column=0, sticky="ew", pady=(6, 10))
        self.entry.bind("<Return>", self.on_convert)
        self.input.trace_add("write", self.on_edit)
        ttk.Button(frame, text="変換", command=self.on_convert).grid(row=2, column=0, sticky="e")
        ttk.Label(frame, text="押すキー:").grid(row=3, column=0, sticky="w", pady=(12, 6))
        self.output = tk.Text(frame, height=2, wrap="word", font=("", 15), state="disabled", relief="solid", borderwidth=1)
        self.output.grid(row=4, column=0, sticky="nsew")
        controls = ttk.Frame(frame)
        controls.grid(row=5, column=0, sticky="e", pady=(8, 4))
        self.pin_button = ttk.Button(controls, text="ピン止め", command=self.on_pin_current, state="disabled")
        self.pin_button.pack(side="left", padx=(0, 8))
        self.copy_button = ttk.Button(controls, text="コピー", command=self.on_copy, state="disabled")
        self.copy_button.pack(side="left")
        self.status = tk.StringVar(root)
        ttk.Label(frame, textvariable=self.status, wraplength=470).grid(row=6, column=0, sticky="w")
        ttk.Label(frame, text="¥ は上段、\\ は右 Shift の左のキーです。\nゲーム側のカナ入力を有効にして使います。", wraplength=470).grid(row=7, column=0, sticky="w", pady=(10, 0))
        panels = ttk.Frame(frame)
        panels.grid(row=8, column=0, sticky="nsew", pady=(14, 0))
        panels.columnconfigure(0, weight=1, uniform="lists")
        panels.columnconfigure(1, weight=1, uniform="lists")
        panels.rowconfigure(0, weight=1)
        self.history_list = self.make_list(panels, "履歴（最新20件）", 0)
        self.bookmark_list = self.make_list(panels, "ピン止め（ブックマーク）", 1)
        self.history_list.bind("<<TreeviewSelect>>", self.on_history_select)
        self.bookmark_list.bind("<<TreeviewSelect>>", self.on_bookmark_select)
        self.unpin_button = ttk.Button(panels, text="ピン止めを解除", command=self.on_unpin, state="disabled")
        self.unpin_button.grid(row=1, column=1, sticky="e", pady=(6, 0))
        ttk.Label(panels, text="選ぶと結果を呼び出せます。古い順に入れ替わります。", wraplength=330).grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.result = ""
        self.refresh_lists()
        if self.store.load_error:
            self.status.set("保存された履歴を読み込めませんでした。新しい履歴から使えます。")
        root.report_callback_exception = self.on_unexpected_error
        root.after_idle(self.entry.focus_force)

    def set_result(self, text: str) -> None:
        self.result = text
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)
        self.output.configure(state="disabled")
        self.copy_button.configure(state="normal" if text else "disabled")
        self.pin_button.configure(state="normal" if text else "disabled")

    def make_list(self, parent, title: str, column: int) -> ttk.Treeview:
        panel = ttk.LabelFrame(parent, text=title, padding=8)
        panel.grid(row=0, column=column, sticky="nsew", padx=(0, 10) if column == 0 else 0)
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(0, weight=1)
        tree = ttk.Treeview(panel, columns=("word", "keys"), show="headings", selectmode="browse", height=7)
        tree.heading("word", text="入力した言葉")
        tree.heading("keys", text="押すキー")
        tree.column("word", width=135, minwidth=90)
        tree.column("keys", width=190, minwidth=100)
        tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(panel, orient="vertical", command=tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=scroll.set)
        return tree

    def refresh_lists(self) -> None:
        for tree, items in ((self.history_list, list(reversed(self.store.history))), (self.bookmark_list, self.store.bookmarks)):
            for item in tree.get_children():
                tree.delete(item)
            for index, text in enumerate(items):
                tree.insert("", "end", iid=str(index), values=(text, format_keys(text)))
        self.unpin_button.configure(state="disabled")

    def persist(self) -> bool:
        try:
            self.store.save()
            return True
        except OSError:
            self.status.set("履歴を保存できませんでした。この画面では引き続き使えます。")
            return False

    def recall(self, text: str) -> None:
        self.input.set(text)
        self.set_result(format_keys(text))
        self.status.set("")

    def on_history_select(self, _event=None) -> None:
        selected = self.history_list.selection()
        if selected:
            self.recall(list(reversed(self.store.history))[int(selected[0])])

    def on_bookmark_select(self, _event=None) -> None:
        selected = self.bookmark_list.selection()
        self.unpin_button.configure(state="normal" if selected else "disabled")
        if selected:
            self.recall(self.store.bookmarks[int(selected[0])])

    def on_pin_current(self) -> None:
        if not self.result:
            return
        added = self.store.pin(self.input.get())
        self.refresh_lists()
        self.status.set("ピン止めしました。" if added else "この言葉はピン止め済みです。")
        self.persist()

    def on_unpin(self) -> None:
        selected = self.bookmark_list.selection()
        if selected:
            self.store.unpin(int(selected[0]))
            self.refresh_lists()
            self.status.set("ピン止めを解除しました。")
            self.persist()

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
            self.store.record(self.input.get())
            self.refresh_lists()
            self.persist()
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
        app.on_pin_current()
        assert len(app.store.bookmarks) == 1
        bookmarked = app.input.get()
        for index in range(21):
            app.input.set("ア" * (index + 1))
            app.on_convert()
        assert len(app.store.history) == 20
        assert app.store.history[0] == "アア"
        app.bookmark_list.selection_set("0")
        app.on_bookmark_select()
        assert app.input.get() == bookmarked
        assert len(app.store.history) == 20, "Recall must not append to history"
        assert HistoryStore(app.store.path).bookmarks == [bookmarked]
        app.on_unpin()
        assert not app.store.bookmarks
        app.input.set("漢字")
        app.on_convert()
        assert not app.result and "変換できません" in app.status.get()
        assert str(app.copy_button["state"]) == "disabled"
        app.input.set("")
        app.on_convert()
        assert "入れてください" in app.status.get()
        report.write_text(json.dumps({"ok": True, "inputs": 6, "clipboard": True, "history": 20, "bookmarks": True}), encoding="utf-8")
    except Exception as error:
        report.write_text(json.dumps({"ok": False, "error": str(error)}), encoding="utf-8")
    finally:
        root.destroy()


def main() -> int:
    try:
        root = tk.Tk()
    except tk.TclError:
        return 1
    # Internal packaging check; normal desktop startup has no arguments.
    if len(sys.argv) == 3 and sys.argv[1] == "--smoke-test":
        with tempfile.TemporaryDirectory(prefix="retrokey-smoke-") as directory:
            app = RetrokeyApp(root, HistoryStore(Path(directory) / "history.json"))
            root.after(300, smoke_test, root, app, Path(sys.argv[2]))
            root.mainloop()
    else:
        RetrokeyApp(root)
        root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
