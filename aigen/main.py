import asyncio
import logging
import discord
import io
import re
import uuid
import json
import aiohttp
import base64
from io import BytesIO
from typing import Optional, Union, List
from redbot.core import Config, commands, checks
from redbot.core.bot import Red
from urllib.parse import quote, urlencode
from discord import app_commands

from .utils import safe_field, process_image
from .parsers import PromptParser, ImageExtractor
from .ai_logic import (
    pollinations_image_generate, 
    pollinations_text_generate, 
    get_pollen_info,
    pollinations_audio_generate,
    hf_image_generate,
    get_time_until_refill
)
from .constants import (
    FLUX_DEFAULT_WIDTH, 
    FLUX_DEFAULT_HEIGHT,
    LINKEDIN_PROMPT_1,
    LINKEDIN_PROMPT_2
)

log = logging.getLogger("red.glas-cogs-aigen")

class AiGen(commands.Cog):
    """A cog for generating images, text and audio using various AI models via Pollinations.ai."""

    __author__ = "[Glas](https://github.com/djtomato/glas-cogs)"
    __version__ = "1.0.1"

    def __init__(self, bot: Red):
        super().__init__()
        self.bot: Red = bot
        self.config = Config.get_conf(self, 117, force_registration=True)
        self.config.register_global(referrer="none")
        self.log = logging.getLogger("glas.glas-cogs.aigen")
        default_guild = {"external_upload_enabled": False}
        self.config.register_guild(**default_guild)

    async def cog_load(self) -> None:
        asyncio.create_task(self.initialize())

    async def initialize(self) -> None:
        await self.bot.wait_until_red_ready()

    # --- Groups ---

    @commands.group()
    async def aigen(self, ctx: commands.Context):
        """AI generation commands and settings."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @aigen.group()
    async def text(self, ctx: commands.Context):
        """Text AI commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @aigen.group(invoke_without_command=True)
    async def aisettings(self, ctx: commands.Context):
        """Settings commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    # --- Helper Methods ---

    async def handle_image_generation(self, ctx, model, prompt, default_width=1024, default_height=1024, extract_images=False, 
                                     negative_prompt=None, width=None, height=None, seed=None, images=None):
        """Unified handler for image generation commands."""
        if not images and extract_images:
            images, prompt = await ImageExtractor.extract_images(ctx, prompt or "")
        
        params = PromptParser.parse_image_params(prompt or "", default_width, default_height)
        
        # Override with explicit params if provided (slash command)
        final_prompt = params["prompt"]
        final_neg = negative_prompt or params["negative_prompt"]
        final_width = width or params["width"]
        final_height = height or params["height"]
        final_seed = seed or params["seed"]
        
        await pollinations_image_generate(
            self, ctx, model, final_prompt, 
            seed=final_seed, 
            width=final_width, 
            height=final_height, 
            images=images,
            negative_prompt=final_neg
        )

    async def handle_text_generation(self, ctx, model, query, system_prompt=None, custom_title=None, custom_footer=None, image_urls=None, temperature=1.0, max_tokens=4096):
        """Unified handler for text generation commands."""
        await pollinations_text_generate(
            self, ctx, model, query, 
            system_prompt=system_prompt, 
            custom_title=custom_title, 
            custom_footer=custom_footer,
            image_urls=image_urls,
            temperature=temperature,
            max_tokens=max_tokens
        )

    async def handle_audio_generation(self, ctx, model, prompt, duration=None):
        """Unified handler for audio generation commands."""
        parsed_prompt, parsed_duration = self.parse_prompt_and_duration(prompt, 30)
        final_duration = duration or parsed_duration
        
        if final_duration < 3 or final_duration > 300:
            return await ctx.send("❌ Duration must be between 3 and 300 seconds.")
        await pollinations_audio_generate(self, ctx, model, parsed_prompt, final_duration)

    async def handle_video_generation(self, ctx, model, prompt, filename, image_url=None, duration=None):
        """Unified handler for video generation commands."""
        poll_keys = await self.bot.get_shared_api_tokens("pollinations")
        token = poll_keys.get("token") or poll_keys.get("api_key") or poll_keys.get("key")
        if not token: return await ctx.send("❌ Missing API token.")

        images = [image_url] if image_url else []
        if not images:
            images, prompt = await ImageExtractor.extract_images(ctx, prompt or "")
        
        prompt, parsed_duration = self.parse_prompt_and_duration(prompt, 5)
        final_duration = duration or parsed_duration

        async with ctx.typing():
            try:
                result, full_url = await self._pollinations_request(
                    prompt=prompt, model=model, token=token, 
                    duration=final_duration, image=images[0] if images else None
                )
                if isinstance(result, bytes):
                    await ctx.send(file=discord.File(io.BytesIO(result), filename))
                else:
                    await ctx.send(f"✨ Video ready: [View Video]({full_url})")
            except Exception as e:
                await ctx.send(f"❌ Error: {e}")

    async def _pollinations_request(self, *, prompt: str, model: str, token: str, **kwargs):
        """Helper for generic Pollinations GET requests (used by video commands)."""
        encoded_prompt = quote(prompt, safe="")
        base_url = f"https://gen.pollinations.ai/image/{encoded_prompt}"
        
        params = {"model": model, "key": token, "prompt": prompt}
        params.update({k: v for k, v in kwargs.items() if v is not None})

        headers = {
            "Authorization": f"Bearer {token}",
            "Referer": "https://pollinations.ai/",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params, headers=headers) as resp:
                full_url = str(resp.url)
                if "application/json" in resp.headers.get("Content-Type", ""):
                    data = await resp.json()
                else:
                    data = await resp.read()
        return data, full_url

    def parse_prompt_and_duration(self, prompt: str, default_duration: int):
        duration = default_duration
        match = re.search(r"--duration\s+(\d+)", prompt)
        if match:
            duration = int(match.group(1))
            prompt = re.sub(r"--duration\s+\d+", "", prompt).strip()
        return prompt, duration

    # --- Settings Commands ---

    @aisettings.command(name="externalupload")
    @commands.admin_or_permissions(manage_guild=True)
    async def externalupload(self, ctx, toggle: bool):
        """Enable or disable external uploads like Chibisafe for this server."""
        if not ctx.guild:
            return await ctx.send("❌ This command can only be used in a server.")
        await self.config.guild(ctx.guild).external_upload_enabled.set(toggle)
        await ctx.send(f"External uploads are now **{'enabled' if toggle else 'disabled'}**.")

    @aisettings.command()
    @commands.is_owner()
    async def referrer(self, ctx: commands.Context, *, new_referrer: str):
        """Set the global referrer used in Pollinations API requests."""
        await self.config.referrer.set(new_referrer)
        await ctx.send(f"✅ Referrer has been set to: `{new_referrer}`")

    @commands.hybrid_command(name="pollen")
    async def pollen(self, ctx: commands.Context):
        """Show current Pollen balance, recent usage, and refill timer."""
        async with ctx.typing():
            info = await get_pollen_info(self)
            if "error" in info:
                return await ctx.send(f"❌ Error: {info['error']}")

            balance = info.get("balance")
        if balance is not None:
            try:
                balance_display = f"{float(balance):.4f} Pollen"
            except (ValueError, TypeError):
                balance_display = f"{balance} Pollen"
        else:
            balance_display = "Unknown"
        
        refill_in = get_time_until_refill()
        description = f"**Current Balance:** {balance_display}\n**Next Refill In:** {refill_in}\n*Refills occur automatically every hour at :00.*"
        if "balance_error" in info:
            description += f"\n\n⚠️ **Balance Error:** {info['balance_error']}"

        embed = discord.Embed(
            title="🐝 Pollen Account Info",
            description=description,
            color=discord.Color.gold()
        )

        usage = info.get("usage", [])
        if usage:
            usage_text = ""
            for item in usage:
                model = item.get("model", "unknown")
                cost = item.get("cost_usd", 0)
                time = item.get("timestamp", "").replace("T", " ").split(".")[0]
                usage_text += f"• `{model}`: ${cost:.4f} ({time})\n"
            embed.add_field(name="Recent Usage", value=usage_text, inline=False)
        elif "usage_error" in info:
            embed.add_field(name="Recent Usage", value=f"⚠️ **Usage Error:** {info['usage_error']}", inline=False)
        else:
            embed.add_field(name="Recent Usage", value="No recent usage found.", inline=False)

        await ctx.send(embed=embed)

    # --- Slash Commands (Hybrid) ---

    @commands.hybrid_command(name="image")
    @app_commands.describe(
        model="The AI model to use",
        prompt="What you want to generate",
        negative_prompt="What you want to avoid",
        width="Image width (default 1024)",
        height="Height of the image (default 1024)",
        seed="Random seed for reproducibility",
        image="Reference image for img2img (attachment)"
    )
    @app_commands.choices(model=[
        app_commands.Choice(name="Flux (High Quality)", value="flux"),
        app_commands.Choice(name="Flux 2 Dev", value="flux-2-dev"),
        app_commands.Choice(name="Turbo (Fast)", value="turbo"),
        app_commands.Choice(name="Z-Image", value="zimage"),
        app_commands.Choice(name="Imagen-4", value="imagen-4"),
        app_commands.Choice(name="Grok Imagine", value="grok-imagine"),
        app_commands.Choice(name="Klein", value="klein"),
        app_commands.Choice(name="Klein Large", value="klein-large"),
        app_commands.Choice(name="Wan Image", value="wan-image"),
        app_commands.Choice(name="Qwen Image", value="qwen-image"),
        app_commands.Choice(name="GPT Image 2", value="gpt-image-2"),
    ])
    async def image_slash(self, ctx: commands.Context, model: str, prompt: str, 
                          negative_prompt: str = None, width: int = None, 
                          height: int = None, seed: int = None, 
                          image: discord.Attachment = None):
        """Generate an image using various AI models."""
        images = [image.url] if image else None
        await self.handle_image_generation(
            ctx, model, prompt, 
            negative_prompt=negative_prompt, 
            width=width, height=height, 
            seed=seed, images=images
        )

    @commands.hybrid_command(name="text")
    @app_commands.describe(
        model="The AI model to use",
        query="Your question or prompt",
        image="Optional image to analyze (multimodal)",
        temperature="Creativity level (0.0 to 2.0)",
        max_tokens="Maximum tokens in response"
    )
    @app_commands.choices(model=[
        app_commands.Choice(name="OpenAI (GPT-4o)", value="openai"),
        app_commands.Choice(name="Claude 3.5 Sonnet", value="claude-fast"),
        app_commands.Choice(name="Gemini 2.0 Flash", value="gemini"),
        app_commands.Choice(name="Grok 2", value="grok"),
        app_commands.Choice(name="DeepSeek V3", value="deepseek"),
        app_commands.Choice(name="OpenAI Reasoning (o1)", value="openai-reasoning"),
        app_commands.Choice(name="Qwen Coder", value="qwen-coder"),
        app_commands.Choice(name="Mistral Fast", value="mistral-fast"),
        app_commands.Choice(name="Perplexity Fast", value="perplexity-fast"),
        app_commands.Choice(name="Kimi K2.5", value="kimi"),
        app_commands.Choice(name="MiniMax M2.1", value="minimax"),
        app_commands.Choice(name="GLM-4", value="glm"),
    ])
    async def text_slash(self, ctx: commands.Context, model: str, query: str, 
                         image: discord.Attachment = None,
                         temperature: float = 1.0,
                         max_tokens: int = 4096):
        """Query AI text models."""
        image_urls = [image.url] if image else None
        await self.handle_text_generation(
            ctx, model, query, 
            image_urls=image_urls,
            temperature=temperature,
            max_tokens=max_tokens
        )

    @commands.hybrid_command(name="video")
    @app_commands.describe(
        model="The video generation model",
        prompt="Describe the video",
        duration="Video length in seconds (default 5)",
        image="Starting image for the video (attachment)"
    )
    @app_commands.choices(model=[
        app_commands.Choice(name="Nova Reel", value="nova-reel"),
        app_commands.Choice(name="LTX-2", value="ltx-2"),
        app_commands.Choice(name="Wan Video", value="wan"),
        app_commands.Choice(name="SeeDance", value="seedance"),
    ])
    async def video_slash(self, ctx: commands.Context, model: str, prompt: str, duration: int = 5, image: discord.Attachment = None):
        """Generate a short video from text or image."""
        image_url = image.url if image else None
        await self.handle_video_generation(ctx, model, prompt, f"{model}.mp4", image_url=image_url, duration=duration)

    @commands.hybrid_command(name="audio")
    @app_commands.describe(
        model="The audio model",
        prompt="Text to turn into audio/music",
        duration="Duration in seconds (default 30)"
    )
    @app_commands.choices(model=[
        app_commands.Choice(name="Qwen TTS", value="qwen3"),
        app_commands.Choice(name="ElevenMusic", value="elevenmusic"),
    ])
    async def audio_slash(self, ctx: commands.Context, model: str, prompt: str, duration: int = 30):
        """Generate audio or music from text."""
        await self.handle_audio_generation(ctx, model, prompt, duration=duration)

    # --- Shortcut Commands (Prefix only) ---

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def flux(self, ctx: commands.Context, *, prompt: str):
        """Generate an image using Flux."""
        await self.handle_image_generation(ctx, "flux", prompt, FLUX_DEFAULT_WIDTH, FLUX_DEFAULT_HEIGHT)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def flux2(self, ctx: commands.Context, *, prompt: str = None):
        """Generate an image using Flux-2-Dev with image-to-image support."""
        await self.handle_image_generation(ctx, "flux-2-dev", prompt, FLUX_DEFAULT_WIDTH, FLUX_DEFAULT_HEIGHT, extract_images=True)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def turbo(self, ctx: commands.Context, *, prompt: str):
        """Generate an image via turbo model."""
        await self.handle_image_generation(ctx, "turbo", prompt)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def zimage(self, ctx: commands.Context, *, prompt: str):
        """Generate an image via Z-Image model."""
        await self.handle_image_generation(ctx, "zimage", prompt)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def imagen(self, ctx: commands.Context, *, prompt: str):
        """Generate an image via Imagen-4 model."""
        await self.handle_image_generation(ctx, "imagen-4", prompt)

    @commands.command(name="gimagine")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def grokimagine(self, ctx: commands.Context, *, prompt: str):
        """Generate an image via Grok-Imagine model."""
        await self.handle_image_generation(ctx, "grok-imagine", prompt)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def img2img(self, ctx: commands.Context, *, prompt: str = None):
        """Generate an image using Flux based on other images."""
        await self.handle_image_generation(ctx, "flux", prompt, extract_images=True)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def klein(self, ctx: commands.Context, *, prompt: str = None):
        """Generate an image via Klein model."""
        await self.handle_image_generation(ctx, "klein", prompt, extract_images=True)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def kleinpro(self, ctx: commands.Context, *, prompt: str = None):
        """Generate an image via Klein-Large model."""
        await self.handle_image_generation(ctx, "klein-large", prompt, 2048, 2048, extract_images=True)

    @commands.command(name="wanimage")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def wanimage(self, ctx: commands.Context, *, prompt: str = None):
        """Generate an Image via wan-image model."""
        await self.handle_image_generation(ctx, "wan-image", prompt, 1024, 1536, extract_images=True)

    @commands.command(name="qwenimage")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def qwenimage(self, ctx: commands.Context, *, prompt: str = None):
        """Generate an Image via qwen-image model."""
        await self.handle_image_generation(ctx, "qwen-image", prompt, 1024, 1536, extract_images=True)

    @commands.command(name="gptimage")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def gptimage(self, ctx: commands.Context, *, prompt: str = None):
        """Generate an Image via gpt-image-2 model."""
        await self.handle_image_generation(ctx, "gpt-image-2", prompt, 1024, 1536, extract_images=True)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def hidream(self, ctx: commands.Context, *, prompt: str):
        """Generate an Image via HiDream endpoint."""
        endpoint = "https://huggingface.co/spaces/HiDream-ai/HiDream-I1-Dev/"
        await hf_image_generate(self, ctx, prompt, endpoint, api_name_override="/generate_with_status")

    # --- Special Commands ---

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def linkedin(self, ctx: commands.Context, *, query: str = None):
        """Transform text into LinkedIn-style post (v1)."""
        author = ctx.author
        await self.handle_text_generation(
            ctx, "gemini-fast", query, 
            system_prompt=LINKEDIN_PROMPT_1,
            custom_title=f"What {author} actually wanted to say:",
            custom_footer="lol, lmao even"
        )

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def linkedin2(self, ctx: commands.Context, *, query: str = None):
        """Transform text into LinkedIn-style post (v2)."""
        author = ctx.author
        await self.handle_text_generation(
            ctx, "openai", query, 
            system_prompt=LINKEDIN_PROMPT_2,
            custom_title=f"What {author} actually wanted to say:",
            custom_footer="lol, lmao even"
        )

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def analyze(self, ctx: commands.Context, *, arg: str = None):
        """Analyze an image using AI."""
        images, prompt = await ImageExtractor.extract_images(ctx, arg or "")
        if not images:
            return await ctx.send("❌ No image found to analyze.")
        
        query = prompt or "Describe this image in detail."
        await self.handle_text_generation(ctx, "claude-fast", query, image_urls=images)

    # --- Video Shortcuts ---

    @commands.command(name="nova_reel")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def nova_prefix(self, ctx, *, prompt: str = None):
        """Generate video via Nova-Reel."""
        await self.handle_video_generation(ctx, "nova-reel", prompt, "nova.mp4")

    @commands.command(name="ltx_video")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def ltx_prefix(self, ctx, *, prompt: str = None):
        """Generate video via LTX-2."""
        await self.handle_video_generation(ctx, "ltx-2", prompt, "ltx.mp4")

    # --- Audio Shortcuts ---

    @commands.command(name="qwentts_audio")
    @commands.cooldown(3, 5, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def qwentts_prefix(self, ctx: commands.Context, *, prompt: str):
        """Generate audio via qwen3 model."""
        await self.handle_audio_generation(ctx, "qwen3", prompt)
