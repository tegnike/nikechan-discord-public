---
name: discord-amnesty
description: "管理者が共有した謝罪内容をもとに、Discord timeout凍結の恩赦を判定し、短縮または解除する。管理者権限がある投稿者だけ実行可能。"
platforms: [macos, linux]
metadata:
  hermes:
    tags: [discord, moderation, amnesty, timeout]
    category: discord
---

# Discord Amnesty

凍結されたユーザーから管理者へ謝罪が来た場合に、管理者が対象チャンネルでニケちゃんへ共有した謝罪内容をもとに、timeoutの短縮または完全解除を行う。

## Trigger

Use this skill when a server administrator says things like:

- `@ユーザーからこういう謝罪が来たので恩赦判定して`
- `この人の凍結を謝罪文から判断して短縮/解除して`
- `凍結された人から反省文が来た。ニケちゃん判断して`
- `timeout解除してよいか見て`

## Authority Boundary

This is not a normal user command.
The helper checks the requester on Discord and only runs when the requester is one of:

- server owner
- Administrator
- Moderate Members

Non-admin users cannot shorten or release their own timeout by asking in Discord.

## Decision Policy

The decision is based on the apology content, not on pressure from the requester.

- 完全解除: 謝罪、問題行為の理解、反省、再発防止が具体的に含まれる
- 短縮: 謝罪意思はあるが、再発防止や問題理解が少し弱い
- 維持: 謝罪が短すぎる、責任転嫁が強い、反省が不明確

## Workflow

- 凍結恩赦の意図分類はLLMを優先し、LLM失敗時だけ保守的な正規表現へフォールバックする。

Use the managed helper. Prefer mentioning the target user or providing the user id.

```bash
/Users/nikenike/.hermes/bin/discord-amnesty evaluate \
  --guild GUILD_ID \
  --target USER_ID_OR_MENTION \
  --apology "謝罪文" \
  --requester-id REQUESTER_ID \
  --source-message-id MESSAGE_ID \
  --apply
```

The helper writes audit logs under `~/.hermes/local/discord-amnesty/audit.jsonl`.

## Output

Report:

- ユーザ名
- 判断: 完全解除 / 短縮 / 維持
- 元の解除時間
- 新しい解除時間
- 元の罪状 if available
- 理由
- audit_id

Keep the report short. Do not expose tokens or internal stack traces.
