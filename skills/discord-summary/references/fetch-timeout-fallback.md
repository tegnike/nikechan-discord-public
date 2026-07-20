# Discord summary: bounded fetch timeout fallback

## When this applies

Use this when `discord-history fetch --from ... --to ...` times out on an active/high-volume channel, but unbounded latest fetches work.

This is a workflow fallback, not a conclusion that `discord-history` is broken.

## Pattern

1. Resolve the channel ID first. If a `#name` lookup is slow or ambiguous, use `list-channels --guild <guild_id>` and then fetch by raw channel ID.
2. Fetch recent messages without a time range:
   ```bash
   /Users/nikenike/.hermes/profiles/nikechan-discord-public/bin/discord-history fetch \
     --channel <channel_id> --guild <guild_id> --limit 200
   ```
   Increase to 500 only if the returned `first` timestamp is newer than the requested start.
3. Filter the returned raw JSON client-side by the requested UTC/offset timestamps. Example:
   ```bash
   python3 - <<'PY'
   import subprocess, json, datetime, collections
   cmd = [
       '/Users/nikenike/.hermes/profiles/nikechan-discord-public/bin/discord-history',
       'fetch', '--channel', '<channel_id>', '--guild', '<guild_id>', '--limit', '200'
   ]
   data = json.loads(subprocess.check_output(cmd, text=True))
   start = datetime.datetime.fromisoformat('<start_iso>')
   end = datetime.datetime.fromisoformat('<end_iso>')
   msgs = []
   for m in data['messages']:
       ts = datetime.datetime.fromisoformat(m['timestamp'])
       if start <= ts <= end and not m['author'].get('bot'):
           msgs.append(m)
   print('count', len(msgs), 'first', msgs[0]['timestamp'] if msgs else None, 'last', msgs[-1]['timestamp'] if msgs else None)
   print('authors', collections.Counter((m['author'].get('display_name') or m['author'].get('username')) for m in msgs).most_common())
   for m in msgs:
       name = m['author'].get('display_name') or m['author'].get('username')
       content = (m.get('content') or '').replace('\n', ' / ')
       if content or m.get('attachments'):
           print(m['timestamp'][11:19], name + ':', content[:180], '[att]' if m.get('attachments') else '')
   PY
   ```
4. Summarize from the filtered output. If the terminal truncates the raw JSON, rely on the filtered digest and counts instead of the truncated JSON.

## Reporting caveat

If the latest fetch did not reach the requested start timestamp, explicitly say the summary is partial and offer to widen the limit or narrow the time range.
