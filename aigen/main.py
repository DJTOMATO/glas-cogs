import asyncio
import logging
import discord
import io
import re
import uuid
import json
import aiohttp
import base64
import datetime
from io import BytesIO
from typing import Optional, Union, List
from redbot.core import Config, commands, checks
from redbot.core.bot import Red
from urllib.parse import quote, urlencode
from discord import app_commands

from .utils import safe_field, process_image
from .parsers import PromptParser, ImageExtractor
from .ai_logic import (
    jankrouter_image_generate, 
    jankrouter_text_generate, 
    
    jankrouter_audio_generate,
    hf_image_generate,
    
    fetch_jankrouter_models,
)
from .constants import (
    FLUX_DEFAULT_WIDTH, 
    FLUX_DEFAULT_HEIGHT,
    LINKEDIN_PROMPT_1,
    LINKEDIN_PROMPT_2
)

log = logging.getLogger("red.glas-cogs-aigen")

class AiGen(commands.Cog):
    """A cog for generating images, text and audio using various AI models via Jankrouter."""

    __author__ = "[Glas](https://github.com/djtomato/glas-cogs)"
    __version__ = "1.0.1"

    def __init__(self, bot: Red):
        super().__init__()
        self.bot: Red = bot
        self.config = Config.get_conf(self, 117, force_registration=True)
        self.config.register_global(
            referrer="none",
            free_model_ids=[],
            free_models_last_refresh=None,
        )
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
        
        await jankrouter_image_generate(
            self, ctx, model, final_prompt, 
            seed=final_seed, 
            width=final_width, 
            height=final_height, 
            images=images,
            negative_prompt=final_neg
        )

    async def get_free_model_ids(self) -> List[str]:
        """Return cached Jankrouter model IDs, fetching once if cache is empty."""
        free_models = await self.config.free_model_ids()
        if free_models:
            return free_models

        return await self.refresh_free_model_cache()

    async def refresh_free_model_cache(self) -> List[str]:
        """Fetch models from Jankrouter and store them in the cog cache."""
        model_objects = await fetch_jankrouter_models()
        free_models = sorted(
            {m.get("id") for m in model_objects if m.get("id")}
        )
        await self.config.free_model_ids.set(free_models)
        await self.config.free_models_last_refresh.set(datetime.datetime.utcnow().isoformat() + "Z")
        return free_models


    async def handle_text_generation(self, ctx, model, query, system_prompt=None, custom_title=None, custom_footer=None, image_urls=None, temperature=1.0, max_tokens=4096):
        """Unified handler for text generation commands."""
        await jankrouter_text_generate(
            self, ctx, model, query, 
            system_prompt=system_prompt, 
            custom_title=custom_title, 
            custom_footer=custom_footer,
            image_urls=image_urls,
            temperature=temperature,
            max_tokens=max_tokens
        )

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
        """Set the global referrer used in Jankrouter API requests."""
        await self.config.referrer.set(new_referrer)
        await ctx.send(f"✅ Referrer has been set to: `{new_referrer}`")

    @aigen.command(name="models")
    async def list_models(self, ctx: commands.Context, category: Optional[str] = None):
        """List available Jankrouter models entries."""
        supported_categories = {"text", "image", "video", "audio"}
        if category:
            category = category.lower().strip()
            if category not in supported_categories:
                return await ctx.send("❌ Invalid category. Use `text`, `image`, `video`, or `audio`.")

        try:
            free_model_ids = await self.get_free_model_ids()
        except Exception as e:
            return await ctx.send(f"❌ Could not load cached model list: {e}")

        rows = {"text": [], "image": [], "video": [], "audio": []}

        for model_id in free_model_ids:
            categories = set()
            if any(token in model_id for token in ("video", "ltx", "nova-reel", "wan", "seedance")):
                categories.add("video")
            if any(token in model_id for token in ("image", "vision", "flux", "gptimage", "klein", "kontext", "nova-canvas", "zimage", "ideogram", "midijourney", "seedream", "stable-diffusion", "stable-horde")):
                categories.add("image")
            if any(token in model_id for token in ("audio", "tts", "eleven", "qwen-tts", "qwen3", "openai-audio", "stable-audio", "whisper", "polly", "midijourney")):
                categories.add("audio")
            if not categories:
                categories.add("text")

            for cat in categories:
                if cat in rows:
                    rows[cat].append(model_id)

        for cat in rows:
            rows[cat].sort()

        if category:
            selected = rows[category]
            if not selected:
                return await ctx.send(f"❌ No free {category} models found.")
            output = ", ".join(f"`{model_id}`" for model_id in selected)
            if len(output) > 1900:
                fp = BytesIO(output.encode())
                await ctx.send(file=discord.File(fp, filename=f"{category}_models.txt"))
            else:
                await ctx.send(f"**Jankrouter {category.capitalize()} Models**\n{output}")
            return

        def summarize_models(models_list: List[str], category_name: str, max_items: int = 8) -> str:
            if not models_list:
                return "None"
            if len(models_list) <= max_items:
                return ", ".join(f"`{model_id}`" for model_id in models_list)
            shown = models_list[:max_items]
            remaining = len(models_list) - max_items
            return ", ".join(f"`{model_id}`" for model_id in shown) + f" ... and {remaining} more. Use `aigen models {category_name}` for full list."

        last_refresh = await self.config.free_models_last_refresh()
        if last_refresh is None:
            footer = "No model cache found. Run `aigen refreshmodels` to populate it."
        else:
            footer = f"Cached on {last_refresh} UTC. Use `aigen refreshmodels` to refresh."

        embed = discord.Embed(
            title="Jankrouter Models (Free / non-paid-only)",
            color=discord.Color.blue(),
            description="Use `[p]aigen models text`, `[p]aigen models image`, `[p]aigen models video`, or `[p]aigen models audio` for a specific category."
        )
        for cat in ("text", "image", "video", "audio"):
            values = rows[cat]
            field_value = summarize_models(values, cat)
            embed.add_field(name=cat.capitalize(), value=field_value, inline=False)
        embed.set_footer(text=footer)
        await ctx.send(embed=embed)

    @aigen.command(name="refreshmodels")
    async def refresh_models(self, ctx: commands.Context):
        """Refresh the cached free Jankrouter model list."""
        async with ctx.typing():
            try:
                model_ids = await self.refresh_free_model_cache()
            except Exception as e:
                return await ctx.send(f"❌ Failed to refresh model cache: {e}")

        if not model_ids:
            return await ctx.send("⚠️ No free models were found in the Jankrouter model list.")

        await ctx.send(
            f"✅ Cached {len(model_ids)} free Jankrouter models. "
            f"Use `aigen models` to view them."
        )

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

    @commands.hybrid_group(name="text", fallback="ask", invoke_without_command=True)
    @app_commands.describe(
        model="The AI model to use",
        query="Your question or prompt",
        image="Optional image to analyze (multimodal)",
        temperature="Creativity level (0.0 to 2.0)",
        max_tokens="Maximum tokens in response"
    )
    async def text(self, ctx: commands.Context, model: str, *, query: str, 
                   image: Optional[discord.Attachment] = None,
                   temperature: float = 1.0,
                   max_tokens: int = 4096):
        """Query AI text models."""
        
        # 1. Normalize prefix inputs (e.g., handling lazy typing like '!text gemini hi')
        model_lower = model.lower().strip()
        if model_lower == "gemini":
            model = "gemini-fast"
        elif model_lower == "claude":
            model = "claude-fast"

        # 2. Automatically grab image attachments from regular prefix messages if available
        if ctx.interaction is None and not image and ctx.message.attachments:
            image = ctx.message.attachments[0]

        image_urls = [image.url] if image else None


        # 3. Pass ctx down to your backend handler
        await self.handle_text_generation(
            ctx, model, query, 
            image_urls=image_urls,
            temperature=temperature,
            max_tokens=max_tokens
        )

    @image_slash.autocomplete("model")
    async def image_model_autocomplete(self, interaction: discord.Interaction, current: str):
        free_models = await self.get_free_model_ids()
        matches = [m for m in free_models if current.lower() in m.lower()]
        return [app_commands.Choice(name=m, value=m) for m in matches[:25]]

    @text.autocomplete("model")
    async def text_model_autocomplete(self, interaction: discord.Interaction, current: str):
        free_models = await self.get_free_model_ids()
        matches = [m for m in free_models if current.lower() in m.lower()]
        return [app_commands.Choice(name=m, value=m) for m in matches[:25]]

    # --- Shortcut Commands (Prefix only) ---

    @commands.command(name="lucid", aliases=["lucid-origin"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def lucid(self, ctx: commands.Context, *, prompt: str = None):
        """Generate an image via lucid-origin model."""
        await self.handle_image_generation(ctx, "lucid-origin", prompt, 1024, 1024, extract_images=True)

    @commands.command(name="phoenix", aliases=["phoenix-1.0"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def phoenix(self, ctx: commands.Context, *, prompt: str = None):
        """Generate an image via phoenix-1.0 model."""
        await self.handle_image_generation(ctx, "phoenix-1.0", prompt, 1024, 1024, extract_images=True)

    @commands.command(name="sdxl", aliases=["sdxl-lightning"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def sdxl(self, ctx: commands.Context, *, prompt: str = None):
        """Generate an image via sdxl-lightning model."""
        await self.handle_image_generation(ctx, "sdxl-lightning", prompt, 1024, 1024, extract_images=True)

    @commands.command(name="schnell", aliases=["flux-1-schnell"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def schnell(self, ctx: commands.Context, *, prompt: str = None):
        """Generate an image via flux-1-schnell model."""
        await self.handle_image_generation(ctx, "flux-1-schnell", prompt, 1024, 1024, extract_images=True)

    @commands.command(name="klein4b", aliases=["flux-2-klein-4b"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def klein4b(self, ctx: commands.Context, *, prompt: str = None):
        """Generate an image via flux-2-klein-4b model."""
        await self.handle_image_generation(ctx, "flux-2-klein-4b", prompt, 1024, 1024, extract_images=True)

    @commands.command(name="klein9b", aliases=["flux-2-klein-9b"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def klein9b(self, ctx: commands.Context, *, prompt: str = None):
        """Generate an image via flux-2-klein-9b model."""
        await self.handle_image_generation(ctx, "flux-2-klein-9b", prompt, 1024, 1024, extract_images=True)

    # --- Special Commands ---

    # --- Video Shortcuts ---




    # --- Auto-generated Text Shortcuts ---

    @text.command(name="qwen3guard8b", aliases=["qwen3-guard-8b"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def qwen3guard8b(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using qwen3-guard-8b."""
        await self.handle_text_generation(ctx, "qwen3-guard-8b", prompt)

    @text.command(name="qwen3827b", aliases=["qwen3.8-27b"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def qwen3827b(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using qwen3.8-27b."""
        await self.handle_text_generation(ctx, "qwen3.8-27b", prompt)

    @text.command(name="qwen38flash", aliases=["qwen3.8-flash"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def qwen38flash(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using qwen3.8-flash."""
        await self.handle_text_generation(ctx, "qwen3.8-flash", prompt)

    @text.command(name="nemotron35lightning30b", aliases=["nemotron-3.5-lightning-30b"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def nemotron35lightning30b(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using nemotron-3.5-lightning-30b."""
        await self.handle_text_generation(ctx, "nemotron-3.5-lightning-30b", prompt)

    @text.command(name="northminicode", aliases=["north-mini-code"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def northminicode(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using north-mini-code."""
        await self.handle_text_generation(ctx, "north-mini-code", prompt)

    @text.command(name="glm46vflash", aliases=["glm-4.6v-flash"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def glm46vflash(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using glm-4.6v-flash."""
        await self.handle_text_generation(ctx, "glm-4.6v-flash", prompt)

    @text.command(name="glm52", aliases=["glm-5.2"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def glm52(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using glm-5.2."""
        await self.handle_text_generation(ctx, "glm-5.2", prompt)

    @text.command(name="glm53flash", aliases=["glm-5.3-flash"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def glm53flash(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using glm-5.3-flash."""
        await self.handle_text_generation(ctx, "glm-5.3-flash", prompt)

    @text.command(name="gpt56luna", aliases=["gpt-5.6-luna"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def gpt56luna(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using gpt-5.6-luna."""
        await self.handle_text_generation(ctx, "gpt-5.6-luna", prompt)

    @text.command(name="kimik27code", aliases=["kimi-k2.7-code"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def kimik27code(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using kimi-k2.7-code."""
        await self.handle_text_generation(ctx, "kimi-k2.7-code", prompt)

    @text.command(name="mimov25", aliases=["mimo-v2.5"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def mimov25(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using mimo-v2.5."""
        await self.handle_text_generation(ctx, "mimo-v2.5", prompt)

    @text.command(name="deepseekv4flash", aliases=["deepseek-v4-flash"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def deepseekv4flash(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using deepseek-v4-flash."""
        await self.handle_text_generation(ctx, "deepseek-v4-flash", prompt)

    @text.command(name="deepseekv4pro", aliases=["deepseek-v4-pro"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def deepseekv4pro(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using deepseek-v4-pro."""
        await self.handle_text_generation(ctx, "deepseek-v4-pro", prompt)

    @text.command(name="gemma426ba4b", aliases=["gemma-4-26b-a4b"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def gemma426ba4b(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using gemma-4-26b-a4b."""
        await self.handle_text_generation(ctx, "gemma-4-26b-a4b", prompt)

    @text.command(name="gemmadiffusion", aliases=["gemma-diffusion"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def gemmadiffusion(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using gemma-diffusion."""
        await self.handle_text_generation(ctx, "gemma-diffusion", prompt)

    @text.command(name="gemma431b", aliases=["gemma-4-31b"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def gemma431b(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using gemma-4-31b."""
        await self.handle_text_generation(ctx, "gemma-4-31b", prompt)

    @text.command(name="gemini25flashlite", aliases=["gemini-2.5-flash-lite"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def gemini25flashlite(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using gemini-2.5-flash-lite."""
        await self.handle_text_generation(ctx, "gemini-2.5-flash-lite", prompt)

    @text.command(name="gemini3flashpreview", aliases=["gemini-3-flash-preview"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def gemini3flashpreview(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using gemini-3-flash-preview."""
        await self.handle_text_generation(ctx, "gemini-3-flash-preview", prompt)

    @text.command(name="gemini31flashlite", aliases=["gemini-3.1-flash-lite"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def gemini31flashlite(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using gemini-3.1-flash-lite."""
        await self.handle_text_generation(ctx, "gemini-3.1-flash-lite", prompt)

    @text.command(name="gemini31propreview", aliases=["gemini-3.1-pro-preview"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def gemini31propreview(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using gemini-3.1-pro-preview."""
        await self.handle_text_generation(ctx, "gemini-3.1-pro-preview", prompt)

    @text.command(name="minimaxm3", aliases=["minimax-m3"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def minimaxm3(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using minimax-m3."""
        await self.handle_text_generation(ctx, "minimax-m3", prompt)

    @text.command(name="moondream31", aliases=["moondream-3.1"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def moondream31(self, ctx: commands.Context, *, prompt: str = None):
        """Generate text using moondream-3.1."""
        await self.handle_text_generation(ctx, "moondream-3.1", prompt)

    # --- Audio Shortcuts ---
