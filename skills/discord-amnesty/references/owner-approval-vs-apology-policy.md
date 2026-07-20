# Owner approval vs apology-policy mismatch

Session lesson from a public Discord discussion around an automated timeout for an `@everyone` announcement.

## Scenario

- A user was automatically timed out for excessive mentions after using `@everyone` in an announcement-like post.
- Non-admin users argued the post was not malicious and asked for amnesty or review.
- The server owner later said the equivalent of "恩赦出して良いよ".
- The amnesty helper accepted the owner authority check, but returned `decision: keep` because the supplied text was too short and lacked apology / understanding / recurrence-prevention signals.

## Correct framing

When reporting the helper result, separate three things:

1. **Requester authority** — owner/Admin/Moderate Members can request evaluation; ordinary users cannot.
2. **Decision policy** — the helper currently scores apology / understanding / recurrence prevention, not merely owner permission.
3. **Operational critique** — a non-malicious `@everyone` announcement may expose a policy-design mismatch, but that does not by itself authorize the assistant to bypass the helper.

## Response guidance

- If the JSON says `error: amnesty can only be requested...`, report that no action ran because requester authority failed.
- If owner authority passed but `decision: keep`, say authority passed, but the content supplied did not satisfy the helper's current apology-policy criteria.
- Do not say or imply that the assistant is morally judging the user as guilty. Prefer: "検出カテゴリとして大量メンションに該当した".
- If the conversation challenges responsibility, avoid assigning blame to the owner or to a user. Say the issue is a possible mismatch between automated moderation policy and the specific context.
- Do not invent a live action such as summoning the timed-out user. If asked, say that giving the person a chance to explain is an option for moderators/owner to arrange.
- When the surrounding instruction says "このJSONだけを根拠に、短く日本語で報告", keep the answer narrowly to the JSON result and do not expand into policy debate unless the user asks a follow-up.

## Useful short template

> 権限チェックは通っていますが、今回の判定は維持です。理由は、入力文だけでは謝罪・問題理解・再発防止が具体的に確認できないためです。これは「悪質だと断定した」というより、今の恩赦ロジックが謝罪文ベースで判定する作りだからです。
