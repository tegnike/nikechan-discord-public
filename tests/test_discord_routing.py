import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "nikechan_discord_routing",
    ROOT / "plugins" / "nikechan-discord-routing" / "__init__.py",
)
routing = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(routing)


HOME_CHANNEL = "1404724174890602496"
GUILD = "1404689195150217217"


def discord_event(channel_id=HOME_CHANNEL):
    source = SimpleNamespace(
        platform="discord",
        chat_id=channel_id,
        guild_id=GUILD,
        user_id="123456789012345678",
    )
    return SimpleNamespace(source=source, text="")


class DiscordRoutingHistoryTests(unittest.TestCase):
    def setUp(self):
        routing._ROUTE_INTENT_CACHE.clear()

    def test_deep_history_phrase_routes_without_terminal_exploration(self):
        text = "もっとずっと古い記憶にリーチして"
        self.assertTrue(routing._looks_like_search_request(text))

        with (
            mock.patch.object(
                routing,
                "_load_env",
                return_value={"DISCORD_ALLOWED_GUILDS": GUILD},
            ),
            mock.patch.object(
                routing,
                "_history_search_channel_ids",
                return_value={HOME_CHANNEL},
            ),
            mock.patch.object(routing.subprocess, "run") as run,
        ):
            result = routing._rewrite_discord_search(text, discord_event())

        self.assertIsNotNone(result)
        self.assertIn("DISCORD_HISTORY_QUERY_REQUIRED", result["text"])
        self.assertIn("Supabase", result["text"])
        run.assert_not_called()

    def test_history_search_rejects_another_channel(self):
        other = "1404724174890602497"
        with mock.patch.object(
            routing,
            "_history_search_channel_ids",
            return_value={HOME_CHANNEL},
        ):
            channel, _label, error = routing._history_channel_scope(
                f"<#{other}>の履歴を検索して",
                discord_event(),
            )

        self.assertIsNone(channel)
        self.assertIn("別チャンネル", error)

    def test_message_link_fetch_rejects_another_channel(self):
        other = "1404724174890602497"
        text = f"https://discord.com/channels/{GUILD}/{other}/123456789012345678"
        with (
            mock.patch.object(
                routing,
                "_load_env",
                return_value={"DISCORD_ALLOWED_GUILDS": GUILD},
            ),
            mock.patch.object(routing, "_fetch_discord_message_link") as fetch,
        ):
            result = routing._rewrite_discord_message_url(text, discord_event())

        self.assertIsNotNone(result)
        self.assertIn("limited to the current channel", result["text"])
        fetch.assert_not_called()

    def test_history_helper_timeout_is_returned_as_data(self):
        with mock.patch.object(
            routing.subprocess,
            "run",
            side_effect=routing.subprocess.TimeoutExpired("discord-history", 20),
        ):
            payload, _notes = routing._search_history(
                "めい",
                [],
                HOME_CHANNEL,
                GUILD,
                None,
                None,
            )

        parsed = routing.json.loads(payload)
        self.assertEqual(parsed["timeout_seconds"], 20)
        self.assertIn("タイムアウト", parsed["error"])


if __name__ == "__main__":
    unittest.main()
