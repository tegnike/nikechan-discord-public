#!/usr/bin/env bash
set -euo pipefail

PROFILE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export HERMES_HOME="${HERMES_HOME:-$PROFILE_DIR}"

"$PROFILE_DIR/bin/discord-reminder" dispatch
