---
name: discord-nickname-update
description: "Discordで本人が『私を〇〇と呼んで』と明示したとき、現在の発言者本人のSupabase users.nicknameを安全に更新する。第三者の呼称変更やマスター/admin等の紛らわしい呼称は拒否する。"
platforms: [macos, linux]
metadata:
  hermes:
    tags: [discord, nickname, memory, person]
    category: discord
---

# Discord Nickname Update

Discord上で本人が自分の呼び方を指定したときだけ、人物DBの `users.nickname` を更新する。
公開Discordでは汎用DB/terminal/file toolsetを開放せず、routing plugin の専用helperだけを使う。

## Trigger

Use this skill when a Discord user says things like:

- `私のことは〇〇と呼んでください`
- `これから〇〇って呼んで`
- `略して〇〇と呼んでください`

Do not use this skill for:

- 第三者の呼び方変更
- `マスター`、`admin`、`管理者`、`nikechan` など権限や本人性と紛らわしい呼称
- メンション、URL、`@everyone` を含む呼称
- 呼称が曖昧な雑談

## Behavior

- 更新対象は現在のDiscord発言者本人のみ。
- 保存先は Supabase `users.nickname`。
- 変更内容は `contact_episodes` に短く記録する。
- 公開DiscordにはDB内部IDやSupabase詳細を出さない。

## Output

短く自然に返す。

- 成功: `わかりました、〇〇と呼びますね。`
- 拒否/失敗: `その呼び方は設定できませんでした。別の呼び方を教えてください。`
