# retrokey

Convert Japanese text into physical key sequences for retro Japanese computers.

古い日本語 ADV に入力したい言葉から、現代の **JIS 106/109 キーボード**で押すキーを調べる小さなデスクトップアプリです。GUI と CLI が同じ配列表を使い、実行時のネットワーク通信・LLM・ゲーム知識は使いません。

## 一番簡単な使い方

1. [Releases](https://github.com/redcoast-lab/retrokey/releases/latest) から自分の OS 用 ZIP をダウンロードします。
2. ZIP を展開し、Windows は `retrokey.exe`、macOS は `retrokey.app` を開きます。
3. 入力したい言葉を入れて「変換」を押します。Enter でも変換できます。
4. 表示された「押すキー」をゲームで順番に押します。
5. 「コピー」でキー列だけをコピーできます。結果の選択・コピーも可能です。

画面下の左側に直近20件の変換履歴、右側にピン止め（ブックマーク）を表示します。成功した変換を毎回履歴へ追加し、21件目から古い順に入れ替えます。最新の履歴が上に表示されます。

履歴を選ぶと入力と結果を呼び出せます。「ピン止め」でよく使う言葉を右側に残せます。ピン止めは履歴の20件制限とは独立し、履歴から消えても残ります。同じ言葉を全角・半角・ひらがなでピン止めしても重複しません。「ピン止めを解除」で削除できます。呼び出すだけでは履歴は増えません。

履歴とピン止めはアプリを閉じても保存されます。保存先は Windows の `%LOCALAPPDATA%/retrokey/history.json`、macOS の `~/Library/Application Support/retrokey/history.json` です。データはこの端末内に保存し、外部へ送信しません。更新前のバージョンで変換した履歴は保存していなかったため復元できません。

**全角カナ・半角カナ・ひらがなのどれでも入力できます。** Python・Git・ターミナルのインストールや操作は不要です。入力した言葉は変換後も残り、変更すると古い結果を消して誤コピーを防ぎます。

```text
入力: シークロン
押すキー: D → ¥ → H → ＼ → Y
```

`ｼｰｸﾛﾝ`、`しーくろん` でも同じ結果です。`スターアーサー`、`ｽﾀｰｱｰｻｰ`、`すたーあーさー` も同じキー列になります。空欄や対応できない文字は画面内で日本語の案内を表示します。

配布ファイルは `retrokey-windows-x64.zip`、`retrokey-macos-arm64.zip`（Apple Silicon 用）、`retrokey-macos-x64.zip`（Intel Mac 用）です。アーキテクチャは実際のビルド環境から決定します。Intel Mac 版は macOS 15 の runner でビルド・起動検証します。古い macOS での互換性は未検証です。

Windows Defender / SmartScreen、macOS の Gatekeeper が警告する場合があります。現在は Windows コード署名、Apple Developer ID 署名・notarization に未対応です。管理者権限は要求しません。

**出力は実機 JIS カナ配列のキーを現代 JIS キーへ対応させたものです。実機配列として正しくても、エミュレータのホストキー設定次第で差異があります。Project EGG の文字キー対応とゲーム内入力は未検証です。** EGG で必ずこの通り入力できるという保証はありません。下記の確認状況を参照してください。

## CLI

開発者やスクリプト連携向けの既存 CLI も利用できます。

### インストール

Python 3.10 以上。実行時の外部依存はありません。

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
retrokey "スターアーサー"
```

仮想環境を有効化しない場合は `.venv\Scripts\retrokey.exe`、モジュール形式は `.venv\Scripts\python -m retrokey` で実行できます。macOS/Linux の有効化は `source .venv/bin/activate` です（出力の前提は JIS 配列）。

## 使い方

```text
retrokey "スターアーサー"
スターアーサー
QWERTY: R -> Q -> ¥ -> 3 -> ¥ -> X -> ¥

retrokey "シークロン"
シークロン
QWERTY: D -> ¥ -> H -> \ -> Y

retrokey "レイソード"
レイソード
QWERTY: ; -> E -> C -> ¥ -> S -> @
```

`->` は順番に押して離す操作、`Shift+3` は Shift を押しながら 3 を押す操作です。英字の大文字表記はキー名であり、Shift を押す指示ではありません。`Space` はスペースキーです。ゲーム側でカナ入力モードに切り替えてから使います。カナ切替・Enter による確定は出力に含めません。

引数は引用符で囲んでください。外部プログラムからはシェル文字列を組み立てず、引数配列で呼べます。

```python
import json
import subprocess

result = subprocess.run(
    ["retrokey", "--json", "レイソード"],
    check=True, capture_output=True, text=True,
)
keys = json.loads(result.stdout)["keys"]
```

## キー位置と印字

| 入力 | 表示 | 現代 JIS 上の物理キー位置 | 内部の位置識別子 |
| --- | --- | --- | --- |
| ー | `¥` | 上段、`^` の右、Backspace の左 | `IntlYen` |
| ロ | `\` | 下段、`/` の右、右 Shift の左 | `IntlRo` |
| ム | `]` | `:` の右、Enter の左 | `Backslash` |
| ゛ | `@` | `P` の右 | `BracketLeft` |
| ゜ | `[` | `@` の右 | `BracketRight` |

円記号は `¥` に統一します。実際のキー印字は `￥` や `\` の場合もあります。「ロ」のキーも円記号・バックスラッシュになり得るため、**長音は上段、ロは下段**と位置で区別してください。FM-7 の古い「ロ」キーは英数側の印字が `"` で、現代 JIS の印字とは異なります。

位置識別子は一般的な KeyboardEvent.code の名前を用いた内部識別子です。Windows の仮想キーコードやエミュレータの入力コードではありません。US 配列への読み替えには対応していません。

## JSON とエラー

```text
retrokey --json "スターアーサー"
```

JSON を読み解くと次の内容になります。

```json
{
  "input": "スターアーサー",
  "keys": ["R", "Q", "¥", "3", "¥", "X", "¥"],
  "display": "R -> Q -> ¥ -> 3 -> ¥ -> X -> ¥"
}
```

実際の stdout は ASCII の Unicode エスケープを使った JSON 一行です。古い Windows のパイプでも文字を失わず、JSON パーサーで元の文字に復元できます。`input` は原文、`keys` は順番に押すキー／Shift 組合せの配列です。JSON に説明や警告は混ぜません。

CLI の stdout/stderr は UTF-8 です。終了コードは成功 `0`、未対応文字 `1`、CLI 引数エラー `2`。エラーは stderr に出し、stdout に部分的な結果を出しません。エラーの位置は正規化後の文字列の 1 始まりです。空文字は空のキー列になります。

## 対応文字と正規化

- 基本カタカナ、ヲ、ン、長音、濁点、半濁点。
- 小書き `ァィゥェォャュョッ` は Shift 組合せ、ヲは `Shift+0`。
- 濁音／半濁音は基底カナのあとに `@`／`[`。例：ドは `S -> @`、パは `F -> [`。
- ヴは `4 -> @`（ウ＋濁点）。古い環境の表示は合成された一文字ではなく `ｳﾞ` の二文字になり得ます。ゲームがそれを受理するかは別です。
- `「」、。・` と半角／全角スペース。空白の数と順番を保ちます。
- ひらがなをカタカナへ変換。半角カナに限定した NFKC と NFC により、半角・合成済み・分解形・独立した濁点表記を受け付けます。

漢字、英数字、改行・タブ、ヰヱ、ヮヵヶ、ヷヸヹヺ、反復記号などは明示的にエラーにします。丸囲みカナ・組文字は近似展開しません。例：`retrokey "漢字"` は `unsupported character: 漢`。

## 調査結果：実機とホスト割り当てを区別する

調査日：2026-10-12。実機側の入力文字対応は MAME と別エミュレータの実装を照合しました。

| 対象 | 実機側の基本・長音・濁点・小書き対応の根拠 | ホスト側について確認したこと |
| --- | --- | --- |
| FM-7 | MAME `fm7_key_list` の kana / sh.kana | MAME はカナを右 Ctrl に割当。ロキーには既定 `PORT_CODE` がない |
| PC-8801 | QUASI88 `XR_*` のカナ入力マクロと `keyport`、MAME の実機キー行列 | MAME はロキーを `KEYCODE_DEL`、カナを左 Ctrl に割当。QUASI88 は配列設定・キー設定を持つ |
| PC-9801 | NP2kai `keytable` の kana / shift+kana と MAME のスキャン位置 | MAME の通常 PC-98 キーボードではロキーとカナ切替に既定 `PORT_CODE` がない。NP2kai は JP106/US101・フロントエンド別の割当を持つ |
| X1 | MAME `kanatable` の kana / kana+shift | MAME はカナを右 Ctrl に割当。円記号・ロキーには既定 `PORT_CODE` がない |

実機側の基本カナ、長音、濁点／半濁点、Shift による小書き・句読点の対応は共通です。実機キーの英数側印字、カナ切替、特殊キー、ファンクションキー数・テンキー・筐体形状には差がありますが、ここで対応するカナ文字列の共通 JIS キー対応を変える差分ではありません。従って **`--machine` は実装していません**。

ただし **ホスト割り当ては共通ではありません**。MAME の `KEYCODE_*` はホスト入力の識別子で、`PORT_CHAR` の実機文字や Windows/JIS の印字と同一視できません。MAME 既定割り当て用のキー列をこの CLI が返すわけではありません。QUASI88 のローマ字マクロは実機行列への入力を確認する資料として利用し、全フロントエンドの物理割り当てを検証したわけではありません。

ホスト側で実機キーを現代 JIS の同名／対応位置のキーへ割り当てた環境が、本バージョンの前提です。設定やフロントエンド別の違いを正確に指定するには emulator/profile が適切ですが、裏付けのない汎用プロファイルは追加しません。

## Project EGG での実用性と確認状況

**公開資料の調査を実施しましたが、EGG の実行環境を使った手入力検証は実施していません。**

| 項目 | 確認状況 |
| --- | --- |
| FM-7版「惑星メフィウス」のカナ切替 | D4公式サポートが右側 Ctrl と案内。これは当該タイトルの確認事項 |
| EGG 共通操作 | 公式操作説明に環境設定・仮想テンキーなどの案内あり |
| 全機種・全タイトル共通の文字キー対応 | 公開資料で確認できず、未検証 |
| 長音・ロ・濁点・半濁点・小書きの Windows/JIS 対応 | 未検証。MAME の割り当てから EGG の仕様を推測しない |
| 3つの実用 fixture のゲーム内入力 | 未検証。CLI の出力と共通実機配列はテスト済み |

EGG で試す際は同梱 Readme・操作説明でカナ切替を確認し、入力欄で `ア`、`ー`、`ロ`、`ガ`、`パ`、`ァ` がそれぞれ入力できることを確認してください。`ー` と `ロ` が合わない場合はエミュレータの対応キーを確認する必要があります。Windows IME のローマ字変換と、ゲーム内のカナモードは別です。右 Ctrl の案内を他の機種・タイトルにも適用することはできません。

## 開発者向け

GUI は `python -m retrokey.gui` または `retrokey-gui` で起動できます。Python 3.10 以上と Tkinter を使用します。Python のディストリビューションによっては Tcl/Tk の別途インストールが必要です。

GUI は `retrokey.convert()` を直接呼びます。CLI の subprocess 呼出しや独自の正規化・配列表はありません。半角カナに限定した NFKC と NFC、ひらがなのカタカナ化を共通利用します。

### 配布ビルド

対象 OS 上で実行してください。クロスコンパイルはしません。

```text
python -m pip install -e . -r packaging/requirements.txt
python packaging/build.py
```

Windows では `--onefile --windowed` の exe、macOS では `--onedir --windowed` の app bundle を PyInstaller で生成します。Python と Tcl/Tk を同梱し、コンソールを表示しません。macOS の ZIP は `ditto` で権限・シンボリックリンクを保持します。古い macOS での互換性は未検証です。

ビルドスクリプトは配布バイナリを起動し、6つの入力形式・結果表示・コピー・エラー処理を実際の Tk ウィジェットで検証してから ZIP を生成します。

### GitHub Actions

`.github/workflows/desktop.yml` は `windows-latest`、`macos-latest`（Apple Silicon）、`macos-15-intel`（Intel Mac）を使用します。

- 通常 push / PR：CLI・GUI の単体テストと、ネイティブ GUI の変換・クリップボード確認。
- main push / `v*` タグ / release / 手動実行：各 OS で配布ビルドと GUI 起動検証、ZIP の artifact 保存。
- `v*` タグ / release：GitHub Release に ZIP を添付。
- main のコミットメッセージに `[release]`：`pyproject.toml` のバージョンから Release を作成して添付。公開前にバージョンを更新してください。

PR は読み取り権限で動作し、Release 添付ジョブだけ `contents: write` を使用します。

### テストと配列表の再調査

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
```

標準ライブラリの unittest を使用。64件の資料由来の表データと既存 CLI テストに加え、GUI フォーマット・日本語エラー・全角/半角/ひらがなの一致を検証します。

`tests/fixtures/jis-kana.json` は実装のマッピングから生成していません。NP2kai の BIOS 表から作成し、FM-7/X1 の表と QUASI88 のカナ入力マクロで照合しています。照合手順は `research/check_sources.py`、固定リビジョンの取得先は `research/sources.json` に保存しています。再調査する場合のみネットワークを使用します。

```powershell
python research/check_sources.py --fetch
```

このコマンドは公開ソースを `research/` に取得し、配列を照合して fixture を再生成します。通常の CLI とテストにはダウンロードは不要です。

## Sources

- [MAME FM-7](https://github.com/mamedev/mame/blob/f9b2a9da4e937468fdd9099e8316e6ad40659f86/src/mame/fujitsu/fm7.cpp)：`fm7_key_list` と入力ポート。
- [MAME X1](https://github.com/mamedev/mame/blob/f9b2a9da4e937468fdd9099e8316e6ad40659f86/src/mame/sharp/x1.cpp)：`kanatable` と入力ポート。
- [MAME PC-88 keyboard](https://github.com/mamedev/mame/blob/f9b2a9da4e937468fdd9099e8316e6ad40659f86/src/mame/nec/pc88_kbd.cpp)、[PC-98 keyboard](https://github.com/mamedev/mame/blob/f9b2a9da4e937468fdd9099e8316e6ad40659f86/src/mame/nec/pc98_kbd.cpp)：実機のキー行列・スキャン位置とホスト割り当て。
- [NP2kai BIOS keytable](https://github.com/AZO234/NP2kai/blob/253ef651c9d5d8f6d11f9cc7326b4f05ce5c9ce4/bios/keytable.res)：PC-98 のカナ／Shift カナ出力コード。JIS X 0201 のカナコードを Python の cp932 で Unicode と照合。
- [QUASI88 romaji table](https://github.com/libretro/quasi88-libretro/blob/7884be5277776a5d8c4fdc4e574e9b5b589945c9/src/romaji-table.h)、[keyboard matrix](https://github.com/libretro/quasi88-libretro/blob/7884be5277776a5d8c4fdc4e574e9b5b589945c9/src/keyboard.c)：PC-88 のカナと入力行列の対応。
- [NP2kai keyboard mapping](https://github.com/AZO234/NP2kai/tree/253ef651c9d5d8f6d11f9cc7326b4f05ce5c9ce4)：JP106/US101、libretro/X11 のホスト割り当ての違い。
- [EGG「惑星メフィウス（FM-7）でカナ入力できない」公式サポート](https://d4ehelp.zendesk.com/hc/ja/articles/206867387)：右側 Ctrl によるカナ切替の案内。
- [EGG 公式ゲーム操作説明](https://www.amusement-center.com/project/egg/pdf/game-operation_new.pdf)、[公式ランチャー案内](https://www.amusement-center.com/en/project/egg/launcher.html)：環境設定、作品同梱 Readme の確認方法。全カナのホスト対応表は確認できませんでした。

## 制限と将来の追加

キー送信、攻略、OCR、US 配列、全角漢字入力、エミュレータ設定の自動検出には対応しません。全角カナを入力しても、古い環境では JIS X 0201 の半角カナ相当を入力するキー列になります。文字の見た目・合成、ゲームが受理する文字・長さはゲーム側の仕様です。

自然な次の追加は、EGG のタイトル・エミュレータ版・Windows/JIS 環境を記録した手入力検証です。文字キーの差分が確認された場合にだけ、共通表を共有する小さなホスト割り当てプロファイルを追加します。
