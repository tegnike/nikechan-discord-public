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


def discord_event(channel_id=HOME_CHANNEL, text="", media_urls=None, media_types=None, user_id="123456789012345678"):
    source = SimpleNamespace(
        platform="discord",
        chat_id=channel_id,
        guild_id=GUILD,
        user_id=user_id,
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
        with routing._PENDING_IMAGE_REFERENCE_LOCK:
            routing._PENDING_IMAGE_REFERENCES.clear()

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

    def test_attached_character_image_exposes_opaque_reference_token_to_agent_llm(self):
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
                rewritten = routing._with_image_generation_policy(event.text, event)
                token_match = re.search(r"reference_token: (\S+)", rewritten)
                self.assertIsNotNone(token_match)
                resolved = routing._resolve_reference_context(token_match.group(1))

            self.assertIn("[IMAGE_GENERATION_SEMANTIC_POLICY]", rewritten)
            self.assertIn("LLM自身が判断", rewritten)
            self.assertNotIn(str(reference), rewritten)
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
                rewritten = routing._with_image_generation_policy(event.text, event)

            self.assertIn("current_discord_attachment_reference_count: 0", rewritten)
            self.assertNotIn("reference_token:", rewritten)

    def test_nikechan_image_intent_is_left_to_agent_llm(self):
        event = discord_event(text="AIニケちゃんの自画像を作って")
        self.assertIsNone(routing._rewrite(event))
        rewritten = routing._with_image_generation_policy(event.text, event)
        self.assertIn("LLM自身が判断", rewritten)
        self.assertIn("nikechan_image_generate", rewritten)

    def test_reference_intent_phrasing_is_not_classified_by_regex(self):
        png = b"\x89PNG\r\n\x1a\n" + b"0" * 32
        phrases = [
            "じゃあ今度はこの子をホラー映像に写した画像を",
            "このコを使って雰囲気を変えたやつ出して",
            "この画像を参照して別の場面にして",
            "この子が海辺にいたらどんな感じ？絵で見たい",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / "image_cache"
            cache.mkdir()
            reference = cache / "attached.png"
            reference.write_bytes(png)
            with mock.patch.object(routing, "_profile_root", return_value=root):
                for phrase in phrases:
                    with self.subTest(phrase=phrase):
                        event = discord_event(
                            text=phrase,
                            media_urls=[str(reference)],
                            media_types=["image/png"],
                        )
                        self.assertIsNone(routing._rewrite(event))
                        rewritten = routing._with_image_generation_policy(phrase, event)
                        self.assertIn("reference_token:", rewritten)
                        self.assertIn("LLM自身が判断", rewritten)

    def test_gateway_hook_gives_attached_request_to_agent_llm(self):
        class FakePluginContext:
            def register_tool(self, **_kwargs):
                pass

            def register_hook(self, _name, hook):
                self.hook = hook

        png = b"\x89PNG\r\n\x1a\n" + b"0" * 32
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / "image_cache"
            cache.mkdir()
            reference = cache / "attached.png"
            reference.write_bytes(png)
            event = discord_event(
                text="じゃあ今度はこの子をホラー映像に写した画像を",
                media_urls=[str(reference)],
                media_types=["image/png"],
            )
            ctx = FakePluginContext()
            routing.register(ctx)
            with (
                mock.patch.object(routing, "_profile_root", return_value=root),
                mock.patch.object(routing, "_config_bool", return_value=False),
                mock.patch.object(routing, "_with_person_context", side_effect=lambda text, _event: text),
            ):
                result = ctx.hook(event=event)

        self.assertEqual(result["action"], "rewrite")
        self.assertIn("[IMAGE_GENERATION_SEMANTIC_POLICY]", result["text"])
        self.assertIn("reference_token:", result["text"])
        self.assertIn(event.text, result["text"])

    def test_gateway_hook_carries_image_only_message_into_same_user_followup(self):
        class FakePluginContext:
            def register_tool(self, **_kwargs):
                pass

            def register_hook(self, _name, hook):
                self.hook = hook

        png = b"\x89PNG\r\n\x1a\n" + b"0" * 32
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / "image_cache"
            cache.mkdir()
            reference = cache / "mountain.png"
            reference.write_bytes(png)
            image_event = discord_event(
                text="(The user sent a message with no text content)",
                media_urls=[str(reference)],
                media_types=["image/png"],
            )
            followup_event = discord_event(text="この山の画像に君を追加した画像を生成して")
            ctx = FakePluginContext()
            routing.register(ctx)
            with (
                mock.patch.object(routing, "_profile_root", return_value=root),
                mock.patch.object(routing, "_config_bool", return_value=False),
                mock.patch.object(routing, "_with_person_context", side_effect=lambda text, _event: text),
            ):
                held = ctx.hook(event=image_event)
                result = ctx.hook(event=followup_event)

        self.assertEqual(held, {"action": "skip", "reason": "pending_image_followup"})
        self.assertEqual(result["action"], "rewrite")
        self.assertIn("current_discord_attachment_reference_count: 1", result["text"])
        self.assertIn("reference_token:", result["text"])
        self.assertEqual(followup_event.media_urls, [str(reference.resolve())])

    def test_pending_image_is_not_exposed_to_another_user(self):
        class FakePluginContext:
            def register_tool(self, **_kwargs):
                pass

            def register_hook(self, _name, hook):
                self.hook = hook

        png = b"\x89PNG\r\n\x1a\n" + b"0" * 32
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / "image_cache"
            cache.mkdir()
            reference = cache / "private.png"
            reference.write_bytes(png)
            image_event = discord_event(
                text="(The user sent a message with no text content)",
                media_urls=[str(reference)],
                media_types=["image/png"],
                user_id="owner",
            )
            other_user_event = discord_event(text="画像を作って", user_id="other")
            ctx = FakePluginContext()
            routing.register(ctx)
            with (
                mock.patch.object(routing, "_profile_root", return_value=root),
                mock.patch.object(routing, "_config_bool", return_value=False),
                mock.patch.object(routing, "_with_person_context", side_effect=lambda text, _event: text),
            ):
                ctx.hook(event=image_event)
                result = ctx.hook(event=other_user_event)

        self.assertEqual(result["action"], "rewrite")
        self.assertIn("current_discord_attachment_reference_count: 0", result["text"])
        self.assertNotIn("reference_token:", result["text"])

    def test_nikechan_and_attached_character_use_both_references(self):
        png = bytes.fromhex(
            "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
            "890000000d49444154789c6300010000000500010d0a2db40000000049454e44"
            "ae426082"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / "image_cache"
            assets = root / "assets"
            cache.mkdir()
            assets.mkdir()
            attached = cache / "attached-girl.png"
            official = assets / "nikechan-model-sheet.png"
            attached.write_bytes(png)
            official.write_bytes(png)
            event = discord_event(
                text="この添付画像の女の子とAIニケちゃんが遊んでいる画像を作成して",
                media_urls=[str(attached)],
                media_types=["image/png"],
            )
            with (
                mock.patch.object(routing, "_profile_root", return_value=root),
                mock.patch.object(
                    routing,
                    "_generate_with_references",
                    return_value={"success": True, "delivery": "MEDIA:/tmp/result.png"},
                ) as generate,
            ):
                rewritten = routing._with_image_generation_policy(event.text, event)
                token_match = re.search(r"reference_token: (\S+)", rewritten)
                self.assertIsNotNone(token_match)
                result = routing.json.loads(
                    routing._nikechan_with_reference_generate(
                        {
                            "prompt": event.text,
                            "reference_token": token_match.group(1),
                            "aspect_ratio": "landscape",
                        }
                    )
                )

            self.assertTrue(result["success"])
            references = generate.call_args.args[2]
            self.assertEqual(references, [attached.resolve(), official.resolve()])
            self.assertEqual(result["attached_reference_count"], 1)
            self.assertEqual(result["nikechan_reference_used"], str(official.resolve()))

    def test_reference_tool_schema_never_accepts_a_file_path(self):
        properties = routing.REFERENCE_IMAGE_SCHEMA["parameters"]["properties"]
        self.assertEqual(
            set(properties),
            {"prompt", "reference_token", "aspect_ratio"},
        )
        mixed_properties = routing.NIKECHAN_MIXED_IMAGE_SCHEMA["parameters"]["properties"]
        self.assertEqual(
            set(mixed_properties),
            {"prompt", "reference_token", "aspect_ratio"},
        )


if __name__ == "__main__":
    unittest.main()
