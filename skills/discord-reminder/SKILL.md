---
name: discord-reminder
description: "公開Discordから安全に固定文リマインダーを登録する。通常チャットにはcron/file/terminal権限を開放しない。"
platforms: [macos, linux]
metadata:
  hermes:
    tags: [discord, reminder]
    category: discord
---

# Discord Reminder

公開Discordでの自然文リマインダー登録を扱う。

## Trigger

Use this skill when the user asks for a reminder or scheduled fixed Discord notification:

- `10分後に休憩って言って`
- `明日10時にリリース確認を通知して`
- `毎日9時に朝会の準備をリマインドして`
- `毎週月曜9時に週次確認を通知して`
- `リマインダー一覧見せて`
- `10分後のリマインダー削除して`
- `このリマインダーって削除できる？`

## Public Discord Behavior

- 通常のDiscord応答からHermes cron、terminal、file toolは使わない。
- リマインダーの作成・一覧・削除・削除確認の意図分類はLLMを優先し、LLM失敗時だけ保守的な正規表現へフォールバックする。
- ルーティングプラグインが `/Users/nikenike/.hermes/profiles/nikechan-discord-public/bin/discord-reminder` の `create` / `list` / `cancel` だけを呼び、ローカル状態を管理する。
- 配信は1分ごとの `discord-reminder-dispatcher` no-agent cronが行う。
- 各リマインダーはHermes cronジョブとして増やさない。
- 通知先は、明示された `<#channel>` または依頼元チャンネル。
- 短い間隔の定期実行は作成しない。定期リマインダーは毎日・毎週のみ。
- `@everyone`、ロールメンション、凍結/timeout/ban/kick/mute/削除などのモデレーション操作は拒否する。
- `削除できる？` のような確認はdry-runで候補確認だけ行い、実削除しない。
- 削除は依頼者本人が作成した、現在のチャンネルのリマインダーだけを対象にする。

## Output

登録結果を短く返す。

- 通知予定
- 通知先
- 本文
- 作成できなかった場合は理由
- 一覧・削除・削除候補確認の結果
