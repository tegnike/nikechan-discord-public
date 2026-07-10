# Efficient Discord Message Counting

Use this reference when a user asks for Discord message counts, channel activity totals, or server growth metrics.

## Key lesson

Do **not** use the normal `fetch` path as a whole-server counter with a huge limit. `discord-history fetch --limit 100000` retrieves full message payloads and then serializes them, including content, attachments, embeds, reactions, and jump URLs. For active channels this can time out and waste execution budget even when the user only wants counts.

## Preferred strategies

1. **Indexed DB count**
   - If a durable Discord message/index DB exists, use SQL counts.
   - Ideal schema for counting does not need message content: `guild_id`, `channel_id`, `message_id`, `author_id`/bot flag, `timestamp`.
   - Example:
     ```sql
     SELECT channel_id, COUNT(*)
     FROM discord_messages
     WHERE guild_id = ?
     GROUP BY channel_id;
     ```

2. **Gateway counters for future counts**
   - On message-create events, increment counters instead of fetching history.
   - Keep cumulative and daily tables:
     ```sql
     CREATE TABLE discord_channel_message_counts (
       guild_id TEXT NOT NULL,
       channel_id TEXT NOT NULL,
       total_count INTEGER NOT NULL DEFAULT 0,
       human_count INTEGER NOT NULL DEFAULT 0,
       bot_count INTEGER NOT NULL DEFAULT 0,
       webhook_count INTEGER NOT NULL DEFAULT 0,
       first_seen_at TEXT,
       last_seen_at TEXT,
       PRIMARY KEY (guild_id, channel_id)
     );

     CREATE TABLE discord_channel_daily_message_counts (
       guild_id TEXT NOT NULL,
       channel_id TEXT NOT NULL,
       date TEXT NOT NULL,
       total_count INTEGER NOT NULL DEFAULT 0,
       human_count INTEGER NOT NULL DEFAULT 0,
       bot_count INTEGER NOT NULL DEFAULT 0,
       webhook_count INTEGER NOT NULL DEFAULT 0,
       PRIMARY KEY (guild_id, channel_id, date)
     );
     ```
   - Decide up front whether deleted messages decrement counts. For community activity metrics, prefer counting posted messages and **do not decrement on delete**.
   - Consider separating `human`, `bot`, `webhook`, and self-bot counts.
   - For thread metrics, store both actual `channel_id` and `parent_channel_id` if available so reports can aggregate either way.
   - Historical totals can use a baseline, e.g. `baseline_total = 113800` at a known date, plus future Gateway increments.

3. **Dedicated lightweight REST counter**
   - If historical counting via Discord API is required, write/use a counter that pages `/channels/{channel_id}/messages?limit=100` and only accumulates `len(batch)`.
   - Do not normalize, store, or print full messages.
   - Basic algorithm:
     ```python
     total = 0
     before = None
     while True:
         params = {"limit": 100}
         if before:
             params["before"] = before
         batch = request("GET", f"/channels/{channel_id}/messages", params=params)
         if not batch:
             break
         total += len(batch)
         before = min(m["id"] for m in batch)
         if len(batch) < 100:
             break
     ```
   - This is still expensive: roughly one request per 100 messages. A 113,800-message server is about 1,138 API requests for full historical accuracy.

4. **Bounded estimates**
   - For quick community metrics, count a known recent window (7 or 30 days) and extrapolate daily average.
   - Clearly label as an estimate.

## Anti-patterns

- Do not run whole-server `fetch --limit 100000` from normal chat without explicit admin approval and clear scope.
- Do not infer message counts from Snowflake ID differences; Discord Snowflakes encode time but are not per-channel sequential counts.
- Do not output raw message contents when the user asked only for counts.

## Reporting style

- State scope: guild, channel(s), date range, exact vs estimate.
- If a count is capped, say `>= limit` rather than implying exactness.
- Prefer concise summaries and avoid turning operational counting into a long-running background task unless the user explicitly authorizes it.
