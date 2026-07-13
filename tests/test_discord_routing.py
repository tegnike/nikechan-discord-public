import importlib.util
import re
import tempfile
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


def discord_event(channel_id=HOME_CHANNEL, text="", media_urls=None, media_types=None):
    source = SimpleNamespace(
        platform="discord",
        chat_id=channel_id,
        guild_id=GUILD,
        user_id="123456789012345678",
    )
    return SimpleNamespace(
        source=source,
        text=text,
        media_urls=list(media_urls or []),
        media_types=list(media_types or []),
    )


class DiscordRoutingHistoryTests(unittest.TestCase):
    def setUp(self):
        routing._ROUTE_INTENT_CACHE.clear()
        with routing._REFERENCE_IMAGE_CONTEXT_LOCK:
            routing._REFERENCE_IMAGE_CONTEXTS.clear()

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

    def test_attached_character_image_routes_with_opaque_reference_token(self):
        png = bytes.fromhex(
            "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
            "890000000d49444154789c6300010000000500010d0a2db40000000049454e44"
            "ae426082"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / "image_cache"
            cache.mkdir()
            reference = cache / "attached.png"
            reference.write_bytes(png)
            event = discord_event(
                text="この画像のキャラが海辺で遊んでいるイラストを作成して",
                media_urls=[str(reference)],
                media_types=["image/png"],
            )
            with mock.patch.object(routing, "_profile_root", return_value=root):
                result = routing._rewrite(event)
                token_match = re.search(r"reference_token: (\S+)", result["text"])
                self.assertIsNotNone(token_match)
                resolved = routing._resolve_reference_context(token_match.group(1))

            self.assertIsNotNone(result)
            self.assertIn("[REFERENCE_IMAGE_REQUEST]", result["text"])
            self.assertNotIn(str(reference), result["text"])
            self.assertEqual(resolved, [reference.resolve()])

    def test_attached_reference_rejects_paths_outside_profile_cache(self):
        png = b"\x89PNG\r\n\x1a\n" + b"0" * 32
        with tempfile.TemporaryDirectory() as profile_tmp, tempfile.TemporaryDirectory() as outside_tmp:
            profile = Path(profile_tmp)
            (profile / "image_cache").mkdir()
            outside = Path(outside_tmp) / "outside.png"
            outside.write_bytes(png)
            event = discord_event(
                text="この画像のキャラを描いて",
                media_urls=[str(outside)],
                media_types=["image/png"],
            )
            with mock.patch.object(routing, "_profile_root", return_value=profile):
                result = routing._rewrite_reference_image_request(event.text, event)

            self.assertIsNone(result)

    def test_nikechan_requests_keep_official_model_sheet_priority(self):
        event = discord_event(text="AIニケちゃんの自画像を作って")
        result = routing._rewrite(event)
        self.assertIsNotNone(result)
        self.assertIn("[NIKECHAN_REFERENCED_IMAGE_REQUEST]", result["text"])
        self.assertNotIn("[REFERENCE_IMAGE_REQUEST]", result["text"])

    def test_reference_tool_schema_never_accepts_a_file_path(self):
        properties = routing.REFERENCE_IMAGE_SCHEMA["parameters"]["properties"]
        self.assertEqual(
            set(properties),
            {"prompt", "reference_token", "aspect_ratio"},
        )


if __name__ == "__main__":
    unittest.main()
