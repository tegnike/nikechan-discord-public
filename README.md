# nikechan-discord-public

AIニケちゃん公開Discord常駐Botの Hermes profile です。

このリポジトリは live profile そのものです。

```text
/Users/nikenike/.hermes/profiles/nikechan-discord-public
```

## 管理対象

- `config.yaml`
- `profile.yaml`
- `SOUL.md`
- `memories/`
- `skills/` 配下のニケちゃん独自skill
- `scripts/`
- `bin/` 配下のDiscord/音楽解析/モデレーション補助CLI
- `launchd/` のLaunchDaemon定義
- `plugins/`
- `cron/jobs.template.json`

## 管理しないもの

- `.env`、`auth.json` などのsecret
- `state.db*`
- `sessions/`、`logs/`、`cache/`
- Hermes bundled skills
- `cron/jobs.json`

`cron/jobs.json` はHermesが実行回数や次回実行時刻を毎分更新するため、Git管理しません。cron定義を変更した場合は `cron/jobs.template.json` にも反映してください。

