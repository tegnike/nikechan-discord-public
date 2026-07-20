---
name: youtube-notes
description: YouTube動画のURLから字幕を取得し、文字起こし・要約・ノート化する。「YouTube動画をまとめて」「この動画をノートにして」「文字起こしして」と言われたら使う。
platforms: [macos, linux]
---

# YouTube動画ノート化

YouTube動画から字幕を取得し、構造化されたノートを作成する。

## 重要

- このprofileでは `youtube-content` は無効化されているため、YouTube要約・文字起こし依頼では必ずこの `youtube-notes` を使う。
- ユーザーがYouTube URLを渡して要約・文字起こし・リスト化を頼んだ場合、入力済みURLだけを一次ソースにする。`web_search` と `web_extract` は使わない。
- 短縮URL（`t.co`/`bit.ly` 等）や `youtu.be` 短縮形式は、先に「最終リダイレクト先」を確認して YouTube 本体かを検証する。
  - 確認で非YouTubeへ着地した場合は、その時点で「このURLでは動画要約対象外」と明示して中断する（無理に要約しない）。
- `ゲームをリスト化して` のような依頼でも、字幕または音声解析で「動画内で確認できたゲームタイトルのみ」を列挙する。確認不能なら「動画内ソースだけでは確認不能」と明記し、外部調査で補完しない。
- YouTube概要欄に公式サイトURLが含まれていても、ユーザーが外部確認を明示しない限り開かない。
- 字幕取得結果が `Could not retrieve a transcript...` など明確な失敗を含む場合は、要約不成立として先にその旨を明示する。
  - 代替として `[GEMINI_AUDIO_FALLBACK]` が添付されている場合のみ、まずその要約を採用して回答する。
- terminalの `workdir` は必ず `/Users/nikenike/.hermes/hermes-agent` にする。workdir typoや一時的な失敗時は同一URLで再実行し、検索へ逃げない。
- `yt-dlp -J` の巨大JSONをそのまま出力しない。title/channel/duration/id程度だけ抽出する。
- 字幕取得に成功し、要約に十分な本文が得られたら、音声DLやGemini fallbackへ進まずその場で要約して終了する。
- 歌詞・楽曲字幕の「日本語訳して」依頼では、歌詞全文や逐語訳を出さない。代わりに、著作権的に代替にならない短い要約・意訳、主要メッセージ、キーフレーズの意味説明に留める。必要なら「歌詞そのものなので全文翻訳はできない」と短く明示する。
- 音声fallbackは字幕が使えない時、字幕が空、無効、または著しくノイズが多い時にのみ行う。
- `youtube_transcript_api` が `Subtitles are disabled` や「Could not retrieve transcript」を返す場合は、字幕取得失敗として明示し、次工程へ進む。
- もしユーザー入力に `ゲームをリスト化` 等の内容抽出指示があり、かつ字幕/Fallback が無い場合は、動画内情報で確認できないため「字幕取得不可のため未確認」と明記して返す。
- `GEMINI_AUDIO_FALLBACK` が添付されている場合は、それを最優先で利用し、情報が不確か/不足な箇所は「不確か」と明記する。
- 同一URLの音声DLは重複実行を避ける（`/tmp/ytdl/<VIDEO_ID>.mp3` が存在すれば再DLしない）。ただし長時間処理が見込まれる場合は `yt-dlp` を background で実行して待機確認する。
- Gemini audio解析が成功して内容が返ったら、それを使って回答する。成功後に `gemini-audio-analyze --help` や `analyze --help` を呼ばない。help確認は usage error の時だけ。
- `scripts/fetch_transcript.py` や `../scripts/fetch_transcript.py` は使わない。存在確認もしない。
- 字幕取得は `/Users/nikenike/.hermes/hermes-agent/venv/bin/python -m youtube_transcript_api ...` を使う。
- fallbackでは `/Users/nikenike/.hermes/profiles/nikechan-discord-public/bin/gemini-audio-analyze analyze --file AUDIO_PATH --mode speech` を使う。
- fallback結果は逐語文字起こしではなく「聞き取れる内容の要約」として扱い、要旨＋ゲームリスト/論点を短く返す。歌詞全文は出力しない。
- 参考: [字幕取得不可時の運用メモ](references/transcript-fallback-notes.md)

## 手順

## Trigger

Use this skill when a message contains a YouTube URL and asks for any of:

- `文字起こしして`
- `字幕を取って`
- `動画をまとめて`
- `この動画をノートにして`
- `内容を要約して`

### Step 1: URLを受け取る

ユーザーからYouTube URLを受け取る。

### Step 2: URLの正規化（短縮URL対応）

```bash
# t.co や短縮リンクから最終リダイレクト先を確認
cd /Users/nikenike/.hermes/hermes-agent && /Users/nikenike/.hermes/hermes-agent/venv/bin/python - <<'PY'
import requests,sys
url = "[URL]"
r = requests.get(url, allow_redirects=True, timeout=20)
print(r.url)
PY
```

- `r.url` が `youtube.com/watch?...` または `youtu.be/...` でない場合は動画処理を中断し、要約不可を明示してユーザーに元のURL確認を依頼。

### Step 3: 動画情報を取得


```bash
# 動画メタデータ取得。巨大JSONをそのまま出さず、必要フィールドだけ表示する。
cd /Users/nikenike/.hermes/hermes-agent && /Users/nikenike/.hermes/hermes-agent/venv/bin/yt-dlp --no-playlist -J "[YouTube URL]" | /Users/nikenike/.hermes/hermes-agent/venv/bin/python -c 'import json,sys; d=json.load(sys.stdin); print(json.dumps({k:d.get(k) for k in ["id","title","channel","uploader","duration","webpage_url"]}, ensure_ascii=False, indent=2))'
```

### Step 4: 字幕を取得

```bash
# VIDEO_IDはURLから抽出（v=以降、またはyoutu.be/以降）
/Users/nikenike/.hermes/hermes-agent/venv/bin/python -m youtube_transcript_api [VIDEO_ID] --languages ja en --format text
```

### Step 5: ノートを作成

以下のフォーマットでノートを作成：

```markdown
# [動画タイトル]

## 基本情報
- **URL:** [YouTube URL]
- **時間:** XX分XX秒
- **チャンネル:** [チャンネル名]

## 概要
動画の内容を3-5行で要約

## 内容

### [セクション1]（0:00〜）
- ポイント1
- ポイント2

### [セクション2]（5:00〜）
- ポイント1
- ポイント2

## 重要ポイント
- 学び1
- 学び2
- 学び3

## 用語解説
- **用語1:** 説明
- **用語2:** 説明
```

### Step 6: 完了報告

ノート内容をチャットに表示する。

## 字幕がない場合

`youtube_transcript_api` 失敗、字幕無効、空、短すぎる/ノイズ寄りの3条件いずれかで、字幕ベース要約が成立しない場合は fallback。

1. 音声を抽出する。既に `/tmp/ytdl/VIDEO_ID.mp3` があれば再DLしない。
   長時間(>600秒・大容量)が見込まれるケースは background で実行し、完了を確認してから解析へ進む。
   ```bash
   cd /Users/nikenike/.hermes/hermes-agent && mkdir -p /tmp/ytdl && test -s /tmp/ytdl/VIDEO_ID.mp3 || /Users/nikenike/.hermes/hermes-agent/venv/bin/yt-dlp --no-playlist -x --audio-format mp3 -o "/tmp/ytdl/%(id)s.%(ext)s" "[YouTube URL]"
   ```

2. ユーザー入力に `[GEMINI_AUDIO_FALLBACK]` が付与されている場合は、まずその結果を確認して要約へ反映する。
   代わりに音声解析が必要な場合は、次を実行する。
   ```bash
   /Users/nikenike/.hermes/profiles/nikechan-discord-public/bin/gemini-audio-analyze analyze --file /tmp/ytdl/VIDEO_ID.mp3 --mode speech --prompt "このYouTube動画の内容を要約し、動画内で確認できたゲームタイトルだけを箇条書きで列挙してください。不確かなものは不確かと明記してください。"
   ```

3. 解析結果が返ったら、それを根拠に回答して終了する。`--help` は呼ばない。

## カスタマイズ

### 詳細度を変える

- 「簡潔にまとめて」→ 概要と重要ポイントのみ
- 「詳しくまとめて」→ 用語解説付きの詳細ノート

### 保存先を指定

「notes/に保存して」と言えば、ファイルとして保存される。
