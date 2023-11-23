from .functions import LetterDance
import discord
from redbot.core import Config, commands
from PIL import Image
import imageio


class LetterCog(commands.Cog):
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
        Creates a letterdance gif
        """
        # discord.utils.escape_mentions on phrase

        if Phrase is None:
            await ctx.send("Please provide a valid phrase.")
            return
        if len(Phrase) > 40:
            await ctx.send("Phrase must be less than 40 characters long.")
            return
        message = self.clean(Phrase)

        letter_dance = LetterDance(message, "letterdance.gif")

        result = letter_dance.dance(2)
        with open(result, "rb") as result_file:
            await ctx.send(file=discord.File(result_file, filename="letterdance.gif"))

    def clean(self, message):
        allowed_characters = set(" !$&0123456789@abcdefghijklmnopqrstuvwxyz?")
        filtered_string = "".join(
            char.lower() for char in message if char.lower() in allowed_characters
        )
        return filtered_string

    async def get_username(ctx, user: discord.User):
        username = user.name
        return username
