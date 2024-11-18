"""Rizz cog for Red-DiscordBot by Glas"""

# ruff: noqa: S311
import random
from contextlib import suppress
from typing import ClassVar

import discord
from redbot.core import commands

from .pcx_lib import type_message


class Rizz(commands.Cog):
    """Rizz."""

    __author__ = "PhasecoreX"
    __version__ = "3.0.0"

    SLANG_WORDS: ClassVar[list[str]] = [
        "gyatt",
        "stawp",
        "oof",
        "sus",
        "frfr",
        "wrizz",
        "lrizz",
        "norizz",
        "yoinked",
        "idk",
        "yeet",
        "yolo",
        "imposter",
        "crewmate",
        "anon",
        "nogatekeep",
        "fanumtax",
        "masquerade",
        "chill",
        "nerd",
        "ain’t",
        "whatever",
        "yapfor",
        "infam",
        "steal",
        "yapuntil",
        "skibidi",
        "wig",
        "yeet",
        "yap",
        "delulu",
        "vibe check",
        "vsco girl",
        "tweaking",
        "tea",
        "sussy baka",
        "skill issue",
        "stan",
        "snatched",
        "slay",
        "sksksk",
        "skibidi",
        "simp",
        "sigma",
        "slaps",
        "sook",
        "salty",
        "red flag",
        "queen",
        "pluh",
        "pookie",
        "periodt",
        "opp",
        "ok boomer",
        "ohio",
        "moot",
        "mogging",
        "mew",
        "mid",
        "looksmaxxing",
        "lit",
        "jit",
        "iykyk",
        "ick",
        "ijbol",
        "hits different",
        "gliozzy",
        "glow-up",
        "GOAT",
        "goonning",
        "gucci",
        "gagged",
        "fire",
        "finna",
        "girlboss",
        "era",
        "drip",
        "dogs",
        "dab",
        "ded",
        "cuh",
        "cap",
        "4k",
        "bussin'",
        "bussy",
        "bruh",
        "bop",
        "brainrot",
        "bffr",
        "big yikes",
        "blud",
        "basic",
        "BDE",
        "af",
        "asf",
        "asl",
        "aura",
    ]

    SLANG_REPLACEMENTS: ClassVar[dict[str, str]] = {
        "hello": "yap",
        "goodbye": "yeet",
        "insane": "delulu",
        "cool": "slay",
        "bad": "mid",
        "amazing": "fire",
        "friend": "pookie",
        "enemy": "opp",
        "liar": "cuh",
        "love": "glow-up",
        "hate": "red flag",
        "oops": "big yikes",
        "truth": "GOAT",
        "lie": "cap",
        "laugh": "ijbol",
        "boring": "basic",
        "awesome": "bussin'",
        "fancy": "gucci",
        "angry": "salty",
        "winner": "sigma",
        "loser": "skill issue",
        "beautiful": "snatched",
        "ugly": "ick",
        "awkward": "ohio",
    }

    SLANG_EXCLAMATIONS: ClassVar[list[str]] = [
        "wig snatched!",
        "yolo vibes",
        "sksksk!",
        "delulu moment",
        "bussin' asf",
        "finna tweak",
        "queen energy",
        "opp detected!",
        "red flag alert",
        "ded af",
        "GOAT frfr",
        "4k caught!",
        "big yikes!",
        "salty vibes",
        "ohio drip",
        "sigma grindset!",
        "iykyk",
        "mogging hard!",
        "pookie pls",
        "brainrot oml",
        "wig snatched!",
        "yolo vibes",
        "sksksk!",
        "delulu moment",
        "finna tweak",
        "queen energy",
        "opp detected!",
        "red flag alert",
        "ded af",
        "GOAT frfr",
        "4k caught!",
        "big yikes!",
        "salty vibes",
        "ohio drip",
        "sigma grindset!",
        "iykyk",
        "mogging hard!",
        "pookie pls",
        "brainrot oml",
    ]

    #
    # Red methods
    #

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Show version in help."""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, *, _requester: str, _user_id: int) -> None:
        """Nothing to delete."""
        return

    #
    # Command methods
    #

    @commands.command(aliases=["skibidi"])
    async def rizz(self, ctx: commands.Context, *, text: str | None = None) -> None:
        """Rizzify the replied to message, previous message, or your own text."""
        if not text:
            if hasattr(ctx.message, "reference") and ctx.message.reference:
                with suppress(
                    discord.Forbidden, discord.NotFound, discord.HTTPException
                ):
                    message_id = ctx.message.reference.message_id
                    if message_id:
                        text = (await ctx.fetch_message(message_id)).content
            if not text:
                messages = [message async for message in ctx.channel.history(limit=2)]
                # [0] is the command, [1] is the message before the command
                text = messages[1].content or "I can't translate that!"
        await type_message(
            ctx.channel,
            self.rizzify_string(text),
            allowed_mentions=discord.AllowedMentions(
                everyone=False, users=False, roles=False
            ),
        )

    #
    # Public methods
    #

    # def rizzify_string(self, string: str) -> str:
    #     """Rizzify and return a string."""
    #     converted = ""
    #     current_word = ""
    #     for letter in string:
    #         if letter.isprintable() and not letter.isspace():
    #             current_word += letter
    #         elif current_word:
    #             converted += self.rizzify_word(current_word) + letter
    #             current_word = ""
    #         else:
    #             converted += letter
    #     if current_word:
    #         converted += self.rizzify_word(current_word)
    #     return converted

    def rizzize_word(self, word: str) -> str:
        """Rizzize and return a word."""
        word = word.lower()
        rizz = word.rstrip(".?!,")
        punctuations = word[len(rizz) :]
        final_punctuation = punctuations[-1] if punctuations else ""
        extra_punctuation = punctuations[:-1] if punctuations else ""

        # Process punctuation with more chaos
        if final_punctuation == "." and not random.randint(0, 2):
            final_punctuation = random.choice(self.SLANG_EXCLAMATIONS)
        elif final_punctuation in ["?", "!"] and not random.randint(0, 2):
            final_punctuation = random.choice(self.SLANG_EXCLAMATIONS)

        # Full word exceptions
        rizz = self.SLANG_REPLACEMENTS.get(rizz, rizz)

        # Add chaos to word: random prefixes and suffixes for maximum flavor
        if not random.randint(0, 4):  # Lower probability for prefixes
            rizz = (
                random.choice(
                    [
                        "yo ",
                        "wig ",
                        "skibi ",
                        "delulu ",
                        "vibe ",
                        "sigma ",
                        "queen ",
                        "sussy ",
                        "snatched ",
                        "oop ",
                        "ded ",
                        "GOAT ",
                    ]
                )
                + rizz
            )
        if not random.randint(0, 3):  # Slightly higher probability for suffixes
            rizz += random.choice(
                [
                    " finna",
                    " sksksk",
                    " yolo",
                    " frfr",
                    " 4k",
                    " era",
                    " vibe",
                    " moment",
                    " slaps",
                    " sus",
                    " asf",
                    " drip",
                ]
            )

        # Random chance to insert full chaotic word combinations
        if not random.randint(0, 8):  # Rare addition of extra chaos
            rizz = (
                random.choice(
                    [
                        "gyatt ",
                        "stan ",
                        "lit ",
                        "no cap",
                        "mogging ",
                        "queen vibes ",
                        "big yikes ",
                        "ijbol ",
                        "brainrot ",
                        "4k caught ",
                        "GOAT ",
                    ]
                )
                + rizz
                + random.choice([" slay", " tweak", " ded af", " bussin'", " iykyk"])
            )

        # # Stutter effect
        # if (
        #     len(rizz) > 2
        #     and rizz[0].isalpha()
        #     and "-" not in rizz
        #     and not random.randint(0, 4)
        # ):
        #     rizz = f"{rizz[0]}-{rizz}"

        # Add back punctuations and return
        return rizz + extra_punctuation + final_punctuation

    def rizzify_string(self, string: str) -> str:
        """Rizzize and return a string."""
        converted = ""
        current_word = ""
        for letter in string:
            if letter.isprintable() and not letter.isspace():
                current_word += letter
            elif current_word:
                converted += self.rizzize_word(current_word) + letter
                current_word = ""
            else:
                converted += letter
        if current_word:
            converted += self.rizzize_word(current_word)

        # Inject random phrases after processing the text
        if not random.randint(0, 2):
            converted += " " + random.choice(self.SLANG_EXCLAMATIONS)
        if not random.randint(0, 3):
            converted = random.choice(self.SLANG_EXCLAMATIONS) + " " + converted

        return converted

    def rizzify_word(self, word: str) -> str:
        """Rizzify and return a word."""
        word_lower = word.lower()
        rizz = word_lower.rstrip(".?!,")
        punctuations = word[len(rizz) :]
        final_punctuation = punctuations[-1] if punctuations else ""
        extra_punctuation = punctuations[:-1] if punctuations else ""

        # Replace word with slang if in dictionary
        if rizz in self.SLANG_REPLACEMENTS:
            rizz = self.SLANG_REPLACEMENTS[rizz]
        # Add random slang exclamation for punctuation
        elif final_punctuation in ".!?":
            if not random.randint(0, 3):
                final_punctuation = random.choice(self.SLANG_EXCLAMATIONS)
        # Random substitution of generic slang
        elif not random.randint(0, 6):
            rizz = random.choice(self.SLANG_WORDS)

        # Add back punctuations and return
        return rizz + extra_punctuation + final_punctuation
