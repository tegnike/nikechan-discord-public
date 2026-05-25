#!/usr/bin/env bash
set -euo pipefail

PROFILE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export HERMES_HOME="${HERMES_HOME:-$PROFILE_DIR}"

"$PROFILE_DIR/bin/discord-autofreeze" \
  --guild 1404689195150217217 \
  --window-minutes "${DISCORD_AUTOFREEZE_WINDOW_MINUTES:-5}" \
  --duration "${DISCORD_AUTOFREEZE_DURATION:-12h}" \
  --quiet
