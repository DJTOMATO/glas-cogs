import discord
from redbot.core import commands
from discord import app_commands
from PIL import Image
import io
import aiohttp
import re
import asyncio
from typing import Optional
from functools import partial

class Gabib(commands.Cog):
    """Create a retro degraded image with noisy, glitchy, blocky artifacts."""

    def __init__(self, bot):
        self.bot = bot
        self._session = aiohttp.ClientSession()

    def cog_unload(self):
        # We create a task to close the session because cog_unload isn't async
        self.bot.loop.create_task(self._session.close())

    async def get_image_url(self, ctx, user: Optional[discord.Member]):
        """Helper to find an image URL from context, attachments, or user avatar."""
        # 1. User mentioned or passed as argument
        if user:
            return str(user.display_avatar.url)

        # 2. Attachment in current message
        if ctx.message.attachments:
            return ctx.message.attachments[0].url

        # 3. Message reference (replies)
        if ctx.message.reference and ctx.message.reference.resolved:
            msg = ctx.message.reference.resolved
            if isinstance(msg, discord.Message):
                if msg.attachments:
                    return msg.attachments[0].url
                # Look for URL in replied message content
                match = re.search(r'https?://\S+', msg.content)
                if match:
                    return match.group(0)

        # 4. URL in current message content
        match = re.search(r'https?://\S+', ctx.message.content)
        if match:
            return match.group(0)

        # 5. Fallback to author's avatar
        return str(ctx.author.display_avatar.url)

    def process_image(self, data, downscale, quality, loops):
        """Heavy lifting image processing in a separate thread."""
        with io.BytesIO(data) as input_buffer:
            img = Image.open(input_buffer)
            img.load()
            
            original_size = img.size
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Step 1: Downscale
            ratio = downscale / 100.0
            new_w = max(1, int(original_size[0] * ratio))
            new_h = max(1, int(original_size[1] * ratio))
            img = img.resize((new_w, new_h), resample=Image.LANCZOS)

            # Step 2: Recursive JPEG Compression
            for _ in range(loops):
                with io.BytesIO() as loop_buffer:
                    img.save(loop_buffer, format="JPEG", quality=quality)
                    loop_buffer.seek(0)
                    img = Image.open(loop_buffer)
                    img.load()

            # Step 3: Upscale back to original size
            # Using NEAREST to preserve the "gabigabi" blocky artifacts
            img = img.resize(original_size, resample=Image.NEAREST)

            # Final output
            output_buffer = io.BytesIO()
            img.save(output_buffer, format="JPEG", quality=85)
            output_buffer.seek(0)
            return output_buffer

    @commands.hybrid_command(name="gabib")
    @app_commands.describe(
        downscale="Percentage of original size (1-100, default: 25%)",
        quality="JPEG quality level (1-95, default: 5)",
        loops="Number of compression passes (1-50, default: 10)",
        user="Target user for their avatar"
    )
    async def gabib(
        self,
        ctx: commands.Context,
        downscale: Optional[int] = 25,
        quality: Optional[int] = 5,
        loops: Optional[int] = 10,
        user: Optional[discord.Member] = None
    ):
        """Create a retro "gabigabi" degraded image.

        Examples:
        [p]gabib
        [p]gabib 25 5 10
        [p]gabib 15 3 20
        """
        # Validate inputs
        if loops > 50:
            return await ctx.send("Error: Loops cannot be greater than 50.")
        if loops < 1:
            loops = 1
        if downscale < 1 or downscale > 100:
            return await ctx.send("Error: Downscale must be between 1 and 100.")
        if quality < 1 or quality > 95:
            return await ctx.send("Error: Quality must be between 1 and 95.")

        image_url = await self.get_image_url(ctx, user)

        # Detect if command was run without parameters (for UX requirement)
        params_provided = False
        if ctx.interaction:
            options = ctx.interaction.data.get('options', [])
            if any(opt['name'] in ('downscale', 'quality', 'loops') for opt in options):
                params_provided = True
        else:
            msg_args = ctx.message.content.split()[1:]
            # Filter out user mentions if they were provided as arguments
            filtered_args = [arg for arg in msg_args if not re.match(r'<@!?\d+>', arg)]
            for arg in filtered_args:
                if arg.isdigit():
                    params_provided = True
                    break

        async with ctx.typing():
            try:
                # Use headers to check file size before reading if possible
                async with self._session.get(image_url, timeout=10) as resp:
                    if resp.status != 200:
                        return await ctx.send(f"Error: Could not download image (HTTP {resp.status}).")
                    
                    if resp.content_length and resp.content_length > 10 * 1024 * 1024:
                        return await ctx.send("Error: Image file size exceeds 10MB limit.")
                    
                    data = await resp.read()
                    if len(data) > 10 * 1024 * 1024:
                        return await ctx.send("Error: Image file size exceeds 10MB limit.")

                # Processing in executor to avoid blocking the main event loop
                task = partial(self.process_image, data, downscale, quality, loops)
                output_buffer = await self.bot.loop.run_in_executor(None, task)
                
                discord_file = discord.File(fp=output_buffer, filename="gabib_output.jpg")
                
                # UX: If no parameters provided, show current stats
                if not params_provided:
                    await ctx.send(
                        f"Downscale: {downscale}%\nJPEG Quality: {quality}\nLoops: {loops}", 
                        file=discord_file
                    )
                else:
                    await ctx.send(file=discord_file)

            except aiohttp.ClientError:
                await ctx.send("Error: Failed to connect to image URL.")
            except Exception:
                # Catch-all for unexpected processing errors
                await ctx.send("Error: An unexpected processing error occurred.")
