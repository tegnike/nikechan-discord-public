#!/usr/bin/env bash
set -euo pipefail

profile_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
label="ai.hermes.gateway-nikechan-discord-public"
plist_src="$profile_dir/launchd/$label.plist"
plist_dst="/Library/LaunchDaemons/$label.plist"

if [[ ! -f "$plist_src" ]]; then
  echo "missing plist: $plist_src" >&2
  exit 1
fi

sudo launchctl bootout system "$plist_dst" 2>/dev/null || true
sudo cp "$plist_src" "$plist_dst"
sudo chown root:wheel "$plist_dst"
sudo chmod 644 "$plist_dst"
sudo launchctl bootstrap system "$plist_dst"
sudo launchctl kickstart -k "system/$label"
echo "installed and started $label"
