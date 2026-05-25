---
name: discord-todo
description: "Discordで上がった要望・改善案・作業依頼を、ニケちゃんのSupabase local_tasksにtodoとして追加する。"
platforms: [macos, linux]
metadata:
  hermes:
    tags: [discord, todo, request, task]
    category: discord
---

# Discord Todo

Discordで上がった要望、改善案、作業依頼をニケちゃんのtodoに追加する。
公開Discordでは通常のtodo/file/terminal toolsetを開放せず、専用helperだけを使う。

## Trigger

Use this skill when the user asks to add a Discord request to todo, including:

- `これtodoに追加して`
- `この要望をタスクに入れて`
- `〇〇できるようにして、todo登録して`
- `今の話を要望として残して`
- `改善案として追加しておいて`
- `バックログに入れて`

Do not use this skill for:

- 単なる質問や雑談
- リマインダー登録
- 凍結/timeout/ban/kick/mute/削除などのモデレーション操作
- todo化する内容が不明な発言

## Workflow

- 意図分類とtodo抽出はLLMを優先し、LLM失敗時だけ保守的な正規表現へフォールバックする。
- 保存先は Supabase `local_tasks`。
- Discord上の元投稿、投稿者、チャンネル、jump URL などの詳細は `local_notes` に `task_id` 付きで保存する。
- 公開DiscordにはDB内部情報やSupabaseの詳細を出さない。

Use the managed helper:

```bash
/Users/nikenike/.hermes/profiles/nikechan-discord-public/bin/discord-todo add \
  --text "元のDiscordメッセージ" \
  --guild GUILD_ID \
  --channel CHANNEL_ID \
  --requester-id REQUESTER_ID \
  --source-message-id MESSAGE_ID
```

## Output

短く自然に報告する。

- 追加できた場合: todoに追加したこと、タイトル
- 内容が曖昧な場合: どの内容をtodoにするか確認
- エラーの場合: 追加できなかった理由だけ

Example:

```text
todoに追加しました！
タイトル: Discordの要望をtodo登録できるようにする
```
