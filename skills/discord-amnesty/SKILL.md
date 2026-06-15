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

## Handling abusive or adversarial request patterns

このコマンドは管理者向け判断支援機能なので、公開チャンネルの一般ユーザーから「決定を逆転して」「即時解除して」と強く要求されるケースが多発しやすいです。

その場合は、まず以下の固定方針で返答します。

1. **権限境界を明確化する**
   - `/evaluate` の実行権限は requester 側にあり、`owner/Admin/Moderate Members` のみ。
   - 一般ユーザー単独での `BAN解除` / `timeout短縮` の要求は受理不可。
2. **挑発には乗らない**
   - 「決着」「喧嘩」「脅迫」「人格攻撃」などには反応せず、同調しない。
   - 感情を否定せず、`事実ベースで進める` と短く切り替える。
3. **再審査に必要な最小情報を即要求**
   - BAN/timeout対象の日時
   - 該当投稿（1〜2件の抜粋）
   - 「不当と感じる理由」を一言
4. **実行可否の説明は短く**
   - `amnesty can only be requested by server owner, Administrator, or Moderate Members`
     を事実として提示して、一般ユーザー依頼だけでは続行不可と明記。
5. **同内容の往復が続く場合は固定短文で打ち切る**
   - 「感情的なやり取りは停止し、必要情報（日時・投稿・理由）が揃えば再審査用に整えます。」
   - 新たな主張を追加しても、同じ再審査骨子から外れない。
6. **危険・暴力を示唆する言葉が出たら即エスカレーション候補へ**
   - `破壊` `殺` `脅` などを含む場合は、処罰判断の話を続けず、サーバー管理者の介入を促す定型文に切り替える。

必要情報が揃えば、管理者向けに短文に整える。

## Workflow

- 凍結恩赦の意図分類はLLMを優先し、LLM失敗時だけ保守的な正規表現へフォールバックする。

Use the managed helper. Prefer mentioning the target user or providing the user id.

```bash
/Users/nikenike/.hermes/profiles/nikechan-discord-public/bin/discord-amnesty evaluate \
  --guild GUILD_ID \
  --target USER_ID_OR_MENTION \
  --apology "謝罪文" \
  --requester-id REQUESTER_ID \
  --source-message-id MESSAGE_ID \
  --apply
```

The helper writes audit logs under the profile-local `local/discord-amnesty/audit.jsonl`.

### Reference support

- `references/hostile-request-handling.md`: 激高した一般ユーザーからの再審査要求時の、権限境界説明と短縮要求テンプレ。
- `references/abusive-appeal-safe-script.md`: 脅迫・侮辱が入るケースでの短尺固定返信テンプレ。
- `references/hostile-appeal-handling-notes.md`: これまでの高頻度エスカレーション事例の振り返りノート。

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

## Hostile or Threatening Appeals Handling

この節の運用は「Handling abusive or adversarial request patterns」を参照してください。実装は一貫して、以下の3点に固定します。

1. 挑発文脈を増幅しない
2. 権限境界を明文化して進行不能を示す
3. BAN日時・該当投稿・不当理由の3点のみを再審査材料として要求する

英語運用が必要な場面では、同等の固定テンプレで対応してください。

## Logging / attribution note

If users allege "the bot did it", answer in neutral wording:
"アクション実行者名義と実体の権限判定は分離されています。実行対象は管理権限者の依頼で進む運用が前提です。"
Do not expose token/stack trace or internal audit internals beyond required report fields.

### Field notes

- session lesson: `references/hostile-appeal-handling-notes.md`
