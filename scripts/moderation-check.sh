#!/usr/bin/env bash
set -euo pipefail

export HERMES_HOME="/Users/nikenike/.hermes/profiles/nikechan-discord-public"

/Users/nikenike/.hermes/bin/discord-autofreeze \
  --guild 1404689195150217217 \
  --window-minutes "${DISCORD_AUTOFREEZE_WINDOW_MINUTES:-5}" \
  --duration "${DISCORD_AUTOFREEZE_DURATION:-12h}" \
  --quiet
