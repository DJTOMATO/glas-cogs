from .functions import LetterDanceFunctions
import discord
from redbot.core import Config, commands
from PIL import Image


class LetterDance(commands.Cog):
    """Letterdance Commands"""

    """Letter Dance Animation!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(1, 8, commands.BucketType.user)
    @commands.command(aliases=["ld"], cooldown_after_parsing=True)
    async def letterdance(
        self,
        ctx,
        *,
        Phrase: commands.clean_content(
            fix_channel_mentions=False,
            use_nicknames=True,
            escape_markdown=False,
            remove_markdown=False,
        ) = None
    ):
        """
        Creates a letterdance gif!

        Usage: `[p]letterdance <phrase>`
        Invalid characters will be ommited!
        """
        # discord.utils.escape_mentions on phrase

        if not ctx.channel.permissions_for(ctx.me).attach_files:
            await ctx.send("I don't have permission to attach files in this channel.")
            return
        async with ctx.typing():
            if Phrase is None:
                ctx.command.reset_cooldown(ctx)
                await ctx.send("Please provide a valid phrase.")
                return
            if len(Phrase) > 25:
                await ctx.send(
                    "Phrase must be less than 25 characters long (Including spaces).\nOtherwise it won't display on Discord!"
                )
                return
            message = self.clean(Phrase)

            letter_dance = LetterDanceFunctions(message, "letterdance.gif")

            result = letter_dance.dance(2)
            with open(result, "rb") as result_file:
                await ctx.send(
                    file=discord.File(result_file, filename="letterdance.gif")
                )

    def clean(self, message):
        allowed_characters = set(" !$&0123456789@abcdefghijklmnopqrstuvwxyz?")
        filtered_string = "".join(
            char.lower() for char in message if char.lower() in allowed_characters
        )
        return filtered_string

    async def get_username(ctx, user: discord.User):
        username = user.name
        return username
