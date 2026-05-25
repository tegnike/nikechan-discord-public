#!/bin/bash
# Fetch recent messages from all Discord channels in the server
# Called by cron job — outputs JSON to stdout, progress to stderr

PROFILE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export DISCORD_HISTORY="$PROFILE_DIR/bin/discord-history"
GUILD_ID="1404689195150217217"
LIMIT=30
MINUTES_AGO=10

export FROM_TIME=$(date -u -v-${MINUTES_AGO}M +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d "${MINUTES_AGO} minutes ago" +%Y-%m-%dT%H:%M:%SZ)

echo "Fetching messages from last ${MINUTES_AGO} minutes (since ${FROM_TIME})..." >&2

python3 << 'PYEOF'
import json, subprocess, sys, os

history_cmd = os.environ["DISCORD_HISTORY"]
guild = "1404689195150217217"
limit = 30
from_time = os.environ.get("FROM_TIME", "")

listed = subprocess.run(
    [history_cmd, "list-channels", "--guild", guild],
    capture_output=True, text=True, timeout=30
)
if listed.returncode != 0:
    print((listed.stderr or listed.stdout or "failed to list channels").strip(), file=sys.stderr)
    sys.exit(listed.returncode)

data = json.loads(listed.stdout)
channels = data.get("channels", [])

results = []
for ch in channels:
    ch_id = ch["id"]
    ch_name = ch["name"]
    try:
        result = subprocess.run(
            [history_cmd, "fetch", "--channel", ch_id, "--guild", guild, "--from", from_time, "--limit", str(limit)],
            capture_output=True, text=True, timeout=30
        )
        if result.stdout.strip():
            resp = json.loads(result.stdout)
            messages = resp.get("messages", [])
            if messages:
                results.append({
                    "channel_id": ch_id,
                    "channel_name": ch_name,
                    "messages": messages[:limit]
                })
                print(f"  {ch_name}: {len(messages)} messages", file=sys.stderr)
            else:
                print(f"  {ch_name}: 0 messages", file=sys.stderr)
        else:
            print(f"  {ch_name}: empty response", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print(f"  {ch_name}: timeout", file=sys.stderr)
    except Exception as e:
        print(f"  {ch_name}: error - {e}", file=sys.stderr)

print(json.dumps(results, ensure_ascii=False))
PYEOF
