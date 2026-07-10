import datetime as dt
import importlib.machinery
import importlib.util
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
LOADER = importlib.machinery.SourceFileLoader(
    "discord_history",
    str(ROOT / "bin" / "discord-history"),
)
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
discord_history = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(discord_history)


class DiscordHistoryTests(unittest.TestCase):
    def test_numeric_db_channel_resolution_does_not_call_discord_api(self):
        with mock.patch.object(discord_history, "request") as request:
            channel = discord_history.resolve_db_channel(
                "1404724174890602496",
                "1404689195150217217",
            )

        self.assertEqual(channel["id"], "1404724174890602496")
        self.assertEqual(channel["guild_id"], "1404689195150217217")
        request.assert_not_called()

    def test_invalid_rpc_json_is_reported_as_discord_error(self):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b"not-json"
        response.__exit__.return_value = False
        with (
            mock.patch.object(discord_history, "SUPABASE_URL", "https://example.invalid"),
            mock.patch.object(discord_history, "SUPABASE_ANON_KEY", "anon"),
            mock.patch.object(discord_history, "SUPABASE_BOT_KEY", "bot"),
            mock.patch.object(discord_history.urllib.request, "urlopen", return_value=response),
        ):
            with self.assertRaisesRegex(discord_history.DiscordError, "invalid JSON"):
                discord_history.supabase_rpc("example", {})

    def test_api_fallback_stops_when_cursor_does_not_advance(self):
        batch = [
            {
                "id": str(1_000_000 + index),
                "timestamp": "2026-01-07T00:00:00Z",
                "author": {},
            }
            for index in range(100)
        ]
        channel = {
            "id": "1404724174890602496",
            "name": "ai-nikechan-bot",
            "guild_id": "1404689195150217217",
            "type": 0,
        }
        with (
            mock.patch.object(discord_history, "resolve_channel", return_value=channel),
            mock.patch.object(discord_history, "request", return_value=batch) as request,
            mock.patch.object(discord_history.time, "sleep"),
        ):
            result = discord_history.fetch_messages_api(
                channel["id"],
                channel["guild_id"],
                dt.datetime(2025, 8, 12, tzinfo=dt.timezone.utc),
                dt.datetime(2025, 8, 31, tzinfo=dt.timezone.utc),
                100,
            )

        self.assertEqual(result["count"], 0)
        self.assertEqual(result["pages"], 2)
        self.assertEqual(result["stop_reason"], "no_progress")
        self.assertEqual(request.call_count, 2)

    def test_db_search_caps_results_and_uses_bounded_rpcs(self):
        channel = {
            "id": "1404724174890602496",
            "name": "ai-nikechan-bot",
            "guild_id": "1404689195150217217",
            "type": 0,
        }
        calls = []

        def rpc(name, payload):
            calls.append((name, payload))
            return []

        with (
            mock.patch.object(discord_history, "resolve_db_channel", return_value=channel),
            mock.patch.object(discord_history, "supabase_rpc", side_effect=rpc),
        ):
            result = discord_history.db_search_messages(
                channel["id"],
                channel["guild_id"],
                None,
                None,
                ["ニケ", "nikechan"],
                999,
                "desc",
            )

        self.assertEqual(result["source"], "supabase_history_db")
        self.assertEqual([name for name, _ in calls], [
            "search_discord_history_v2",
            "search_discord_summaries_v2",
        ])
        self.assertEqual(calls[0][1]["p_limit"], 30)
        self.assertEqual(calls[0][1]["p_sort"], "desc")
        self.assertEqual(calls[0][1]["p_channel_ids"], [channel["id"]])

    def test_oldest_first_search_does_not_mix_newest_summaries(self):
        channel = {
            "id": "1404724174890602496",
            "name": "ai-nikechan-bot",
            "guild_id": "1404689195150217217",
            "type": 0,
        }
        with (
            mock.patch.object(discord_history, "resolve_db_channel", return_value=channel),
            mock.patch.object(discord_history, "supabase_rpc", return_value=[]) as rpc,
        ):
            result = discord_history.db_search_messages(
                channel["id"],
                channel["guild_id"],
                None,
                None,
                ["めい"],
                30,
                "asc",
            )

        rpc.assert_called_once()
        self.assertEqual(rpc.call_args.args[0], "search_discord_history_v2")
        self.assertEqual(result["summary_result_count"], 0)
        self.assertEqual(
            result["summaries_skipped_reason"],
            "oldest_first_exact_messages_only",
        )

    def test_summary_failure_preserves_exact_message_results(self):
        channel = {
            "id": "1404724174890602496",
            "name": "ai-nikechan-bot",
            "guild_id": "1404689195150217217",
            "type": 0,
        }
        exact_row = {
            "message_id": "1",
            "channel_id": channel["id"],
            "channel_name": channel["name"],
            "author_name": "めい",
            "content_snippet": "過去のメッセージ",
            "message_at": "2026-02-15T00:00:00Z",
            "reply_to_message_id": None,
            "attachment_count": 0,
            "jump_url": "https://discord.com/channels/g/c/1",
        }

        def rpc(name, _payload):
            if name == "search_discord_history_v2":
                return [exact_row]
            raise discord_history.DiscordError("summary unavailable")

        with (
            mock.patch.object(discord_history, "resolve_db_channel", return_value=channel),
            mock.patch.object(discord_history, "supabase_rpc", side_effect=rpc),
        ):
            result = discord_history.db_search_messages(
                channel["id"],
                channel["guild_id"],
                None,
                None,
                ["めい"],
                30,
                "desc",
            )

        self.assertEqual(result["result_count"], 1)
        self.assertEqual(result["results"][0]["id"], "1")
        self.assertIn("summary unavailable", result["summary_error"])


if __name__ == "__main__":
    unittest.main()
