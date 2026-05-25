#!/usr/bin/env bash
set -euo pipefail

profile_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
hermes_root="${HERMES_ROOT:-$HOME/.hermes}"
bin_dir="$hermes_root/bin"

commands=(
  discord-amnesty
  discord-autofreeze
  discord-freeze
  discord-history
  discord-reminder
  discord-todo
  gemini-audio-analyze
  nikechan-emotion
)

mkdir -p "$bin_dir"
for command in "${commands[@]}"; do
  src="$profile_dir/bin/$command"
  dst="$bin_dir/$command"
  if [[ ! -x "$src" ]]; then
    echo "missing executable: $src" >&2
    exit 1
  fi
  ln -sfn "$src" "$dst"
  echo "linked $dst -> $src"
done

# Removed custom URL helper; URL reading uses Hermes web/search toolsets.
rm -f "$bin_dir/discord-url-reader"

ln -sfn "$profile_dir/scripts" "$hermes_root/scripts"
echo "linked $hermes_root/scripts -> $profile_dir/scripts"
