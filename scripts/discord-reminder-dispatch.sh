#!/usr/bin/env bash
set -euo pipefail

export HERMES_HOME="${HERMES_HOME:-/Users/nikenike/.hermes/profiles/nikechan-discord-public}"
/Users/nikenike/.hermes/bin/discord-reminder dispatch
