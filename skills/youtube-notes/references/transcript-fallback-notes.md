# YouTube字幕フォールバック運用メモ（A/V取得障害時）

- `youtube_transcript_api` が `Subtitles are disabled for this video` を返す場合、字幕取得は原則不可扱いにする。
- `Could not retrieve a transcript ...` だけで終了ではなく、
  1) 字幕取得不可と明示
  2) 音声抽出
  3) Gemini音声要約
  の順で進める。
- `yt-dlp` の音声抽出は、短時間で終わらないケースがある。標準実行タイムアウトの影響を避ける場合は、
  - まず `yt-dlp ...` を background で実行
  - 完了ログ（`100.0% ... Destination:`）を確認
  - 成功したMP3を再利用する（`/tmp/ytdl/<VIDEO_ID>.mp3`）
  の順を推奨。
- 音声解析結果は逐語ではないため、ゲーム名・イベント名・数値などは「確認できた範囲」に限定し、
  不確かな箇所は明示する。
- ユーザー提示の `[GEMINI_AUDIO_FALLBACK]` はこのセッション内の高優先情報として扱う。結果がある場合は、通常字幕よりこちらを優先して回答要約を作る。
- URL短縮（t.co等）で解決先がYouTubeでない場合（例: 別ドメイン記事へリダイレクト）、そのままの要約は行わず「対象外」として終了する。
- 明示的に `Could not retrieve a transcript` のブロックを受け取った場合、まずその失敗内容をユーザーにそのまま示してから次手順へ進む（勝手な中身推定をしない）。