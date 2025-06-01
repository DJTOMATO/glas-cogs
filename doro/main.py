import asyncio
import logging
from collections import Counter
from io import BytesIO

import discord
from PIL import Image, ImageDraw
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.data_manager import bundled_data_path

log = logging.getLogger("red.glas-cogs-Doro")


class Doro(commands.Cog):
    """Description"""

    __author__ = "[Glas](https://github.com/dj_tomato/glas-cogs)"
    __version__ = "0.0.1"

    def __init__(self, bot: Red):
        super().__init__()
        self.bot: Red = bot
        self.config = Config.get_conf(self, 117, force_registration=True)

    def format_help_for_context(self, ctx: commands.Context):
        helpcmd = super().format_help_for_context(ctx)
        txt = "Version: {}\nAuthor: {}".format(self.__version__, self.__author__)
        return f"{helpcmd}\n\n{txt}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int):
        # Requester can be "discord_deleted_user", "owner", "user", or "user_strict"
        return

    async def red_get_data_for_user(self, *, requester: str, user_id: int):
        # Requester can be "discord_deleted_user", "owner", "user", or "user_strict"
        return

    async def cog_load(self) -> None:
        asyncio.create_task(self.initialize())

    async def cog_unload(self) -> None:
        pass

    async def initialize(self) -> None:
        await self.bot.wait_until_red_ready()

    async def get_avatar(self, member: discord.abc.User):
        """Fetch and return the avatar of a member as a BytesIO object."""

        avatar = BytesIO()
        display_avatar: discord.Asset = member.display_avatar.replace(
            size=512, static_format="png"
        )
        await display_avatar.save(avatar, seek_begin=True)
        return avatar

    async def process_avatar(
        self, ctx: commands.Context, target: discord.Member = None
    ):
        """Process the avatar of the user or a target."""
        async with ctx.typing():
            target = target or ctx.author

            # Fetch the avatar image using get_avatar
            avatar_data = await self.get_avatar(target)

            # Open the avatar image
            avatar_image = Image.open(avatar_data).convert("RGBA")

            # Resize the image to reduce the number of unique colors
            resized_image = avatar_image.resize((50, 50))

            # Group similar colors to avoid dominance of shades of the same color
            def group_similar_colors(pixels, tolerance=60):
                """Group similar colors based on a tolerance."""
                grouped_colors = {}
                for color in pixels:
                    for grouped_color in grouped_colors:
                        if all(
                            abs(c1 - c2) <= tolerance
                            for c1, c2 in zip(color[:3], grouped_color)
                        ):
                            grouped_colors[grouped_color] += 1
                            break
                    else:
                        grouped_colors[color[:3]] = 1
                return grouped_colors

            # Extract all pixels and count their occurrences
            pixels = list(resized_image.getdata())
            grouped_color_counts = group_similar_colors(pixels)

            # Get the seven most common colors, excluding black-like and white-like colors
            def is_valid_color(color):
                """Check if a color is neither black-like nor white-like."""
                color_sum = sum(color)
                return (
                    20 < color_sum < 745
                )  # Exclude black-like (<=20) and white-like (>=745)

            most_common_colors = [
                color
                for color, _ in Counter(grouped_color_counts).most_common(7)
                if is_valid_color(color)  # Exclude black-like and white-like colors
            ]
            while len(most_common_colors) < 7:
                most_common_colors.append((255, 255, 255))  # Use white as fallback

            # Reorder colors: red, blue, yellow, green, purple, orange, cyan
            reordered_colors = most_common_colors[:7]

            # Load the base image
            base_image_path = bundled_data_path(self) / f"images/base.png"
            base_image = Image.open(base_image_path).convert("RGBA")

            base_pixels = base_image.load()

            def is_color_close(color1, color2, tolerance=50):
                """Check if two colors are close within a given tolerance."""
                return all(abs(c1 - c2) <= tolerance for c1, c2 in zip(color1, color2))

            # Replace pixels with a tolerance for color matching
            for y in range(base_image.height):
                for x in range(base_image.width):
                    current_pixel = base_pixels[x, y][:3]  # Ignore alpha channel
                    if is_color_close(current_pixel, (255, 0, 0)):  # Red
                        base_pixels[x, y] = reordered_colors[0] + (255,)
                    elif is_color_close(current_pixel, (0, 0, 255)):  # Blue
                        base_pixels[x, y] = reordered_colors[1] + (255,)
                    elif is_color_close(current_pixel, (255, 255, 0)):  # Yellow
                        base_pixels[x, y] = reordered_colors[2] + (255,)
                    elif is_color_close(current_pixel, (0, 255, 0)):  # Green
                        base_pixels[x, y] = reordered_colors[3] + (255,)
                    elif is_color_close(current_pixel, (128, 0, 128)):  # Purple
                        base_pixels[x, y] = reordered_colors[4] + (255,)
                    elif is_color_close(current_pixel, (255, 165, 0)):  # Orange
                        base_pixels[x, y] = reordered_colors[5] + (255,)
                    elif is_color_close(current_pixel, (0, 255, 255)):  # Cyan
                        base_pixels[x, y] = reordered_colors[6] + (255,)

            # Save the modified image to a BytesIO object
            output_buffer = BytesIO()
            base_image.save(output_buffer, format="PNG")
            output_buffer.seek(0)
            if not ctx.channel.permissions_for(ctx.me).attach_files:
                await ctx.send(
                    "I don't have permission to attach files in this channel."
                )
                return
            # Send the modified image in the channel
            file = discord.File(output_buffer, filename="processed_avatar.png")
            await ctx.send(file=file)

    @commands.command()
    async def doro(self, ctx: commands.Context, target: discord.Member = None):
        """Dorify an user.

        Creates a Doro-style image for the user or a specified target based on it's profile picture colors.
        """
        async with ctx.typing():
            await self.process_avatar(ctx, target)
