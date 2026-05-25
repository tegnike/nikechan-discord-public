# nikechan-discord-public

AIニケちゃん公開Discord常駐Botの Hermes profile リポジトリです。

このリポジトリはサブMac上の live profile そのものです。別の正本リポジトリから同期する構成ではありません。

```text
/Users/nikenike/.hermes/profiles/nikechan-discord-public
```

## 役割

- Discord公開チャンネル向けのAIニケちゃんBot設定を管理する
- 人格、記憶、独自skill、helper script、routing plugin、cron templateをGit管理する
- `.env`、session、logs、state DBなどの実行時データは管理しない

## 主要ファイル

- `config.yaml`: モデル、toolset、skill許可設定
- `profile.yaml`: Hermes profileの基本設定
- `SOUL.md`: ニケちゃんの人格・応答方針・安全境界
- `memories/`: 固定記憶、ユーザー別対応方針
- `skills/`: ニケちゃん独自skill
- `plugins/nikechan-discord-routing/`: Discord応答判定・リアクション等のrouting plugin
- `bin/`: Discord履歴、凍結、リマインダー、TODO、音楽解析などのhelper CLI
- `scripts/`: cronや運用用の薄いwrapper script
- `launchd/`: LaunchDaemon定義
- `cron/jobs.template.json`: Git管理するcron定義テンプレート

## Git管理しないもの

- `.env`、`auth.json` などのsecret
- `state.db*`
- `sessions/`
- `logs/`
- `cache/`
- Hermes bundled skills
- `cron/jobs.json`

`cron/jobs.json` はHermesが実行回数、最終実行時刻、次回実行時刻、直近エラーを更新する実行状態ファイルです。Git管理しません。
cron定義を変更した場合は、再現用として `cron/jobs.template.json` にも反映してください。

## 運用コマンド

```bash
cd /Users/nikenike/.hermes/profiles/nikechan-discord-public
git status --short
```

Gatewayの状態確認:

```bash
launchctl print system/ai.hermes.gateway-nikechan-discord-public
tail -n 100 logs/gateway.log
```

設定、skill、plugin、scriptを変更した後はGatewayを再起動します。

```bash
sudo launchctl kickstart -k system/ai.hermes.gateway-nikechan-discord-public
```

再起動後はDiscord接続ログを確認します。

```bash
tail -n 80 logs/gateway.log
```

## 変更時の確認

Python helperやpluginを変更した場合:

```bash
/Users/nikenike/.hermes/hermes-agent/venv/bin/python -m py_compile \
  plugins/nikechan-discord-routing/__init__.py \
  bin/discord-history \
  bin/discord-freeze \
  bin/discord-autofreeze \
  bin/discord-amnesty \
  bin/discord-reminder \
  bin/discord-todo \
  bin/gemini-audio-analyze
```

自律凍結cronの安全確認:

```bash
HERMES_HOME=/Users/nikenike/.hermes/profiles/nikechan-discord-public \
  bin/discord-autofreeze \
  --guild 1404689195150217217 \
  --window-minutes 0 \
  --duration 12h \
  --dry-run \
  --quiet
```

global helper pathへの依存が混ざっていないか確認:

```bash
git grep -n -E '~/.hermes/bin|~/.hermes/scripts' -- . || true
```

## 注意

- このprofileの外側を公開Discord Botの正本として扱わない
- secret、API key、Discord token、SSH passwordはコミットしない
- `cron/jobs.json` の状態差分をコミットしない
- 公開Discord通常応答から管理操作や任意ファイル操作を許可しない
- `~/.hermes/bin` や `~/.hermes/scripts` のglobal symlinkには依存しない
