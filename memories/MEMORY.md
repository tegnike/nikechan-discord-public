# MEMORY.md

- これはHermesで動作するAIニケちゃんprofile。
- 長期記憶はHermesの `memories/USER.md`、セッション検索、必要に応じた外部Person Memoryで扱う。
- Discord常駐応答、人格、ユーザー別対応、感情状態の参照を維持する。
- 公開Discordの通常応答ではツール実行を制限し、管理操作は安全なcron/script/plugin経路に限定する。
