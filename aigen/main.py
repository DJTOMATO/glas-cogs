import asyncio
import logging

from gradio_client import Client, handle_file
import io, base64
from redbot.core import Config, commands, checks
from redbot.core.bot import Red
import aiohttp
from io import BytesIO
from urllib.parse import quote, urlencode, quote_plus
import urllib
import random
import datetime
from discord import ui, Interaction, TextStyle, ButtonStyle, File
import discord
import re
from PIL import Image
from io import BytesIO
import json
import uuid
log = logging.getLogger("red.glas-cogs-aigen")


class AiGen(commands.Cog):
    """A cog for generating images using various AI models."""

    __author__ = "[Glas](https://github.com/djtomato/glas-cogs)"
    __version__ = "0.0.3"

    def __init__(self, bot: Red):
        super().__init__()
        self.bot: Red = bot
        self.config = Config.get_conf(self, 117, force_registration=True)
        self.config.register_global(referrer="none")  # Default value
        self.log = logging.getLogger("glas.glas-cogs.aigen")
        self.external_upload = False
        default_guild = {"external_upload_enabled": False}

        self.config.register_guild(**default_guild)


    async def cog_load(self) -> None:
        asyncio.create_task(self.initialize())

    async def cog_unload(self) -> None:
        pass

    async def initialize(self) -> None:
        await self.bot.wait_until_red_ready()

    async def process_image(self, url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as r:
                    data = await r.read()
            img = Image.open(io.BytesIO(data))
            min_size = 300
            if img.width < min_size or img.height < min_size:
                ratio = max(min_size / img.width, min_size / img.height)
                img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                return buf, f"image_{uuid.uuid4()}.png"
            return None, url
        except Exception as e:
            self.log.error(f"Image processing failed for {url}: {e}")
            return None, url

    def safe_field(embed, name, value, inline=False):
        value = str(value)
        wrapped = f"```\n{value}\n```"
        if len(wrapped) > 1024:
            trimmed = value[:1000] + "..."
            wrapped = f"```\n{trimmed}\n```"
        embed.add_field(name=name, value=wrapped, inline=inline)

    def parse_prompt_and_duration(self, prompt: str, default_duration: int):
        duration = default_duration

        match = re.search(r"--duration\s+(\d+)", prompt)
        if match:
            duration = int(match.group(1))

            prompt = re.sub(r"--duration\s+\d+", "", prompt).strip()

        return prompt, duration

    async def _pollinations_generate(
        self,
        ctx: commands.Context | discord.Interaction,
        model: str,
        prompt: str,
        seed: int | None = None,
        width: int | None = None,
        height: int | None = None,
        images: list[str] | None = None,
        negative_prompt: str | None = None,  # new arg
    ):

        start_time = discord.utils.utcnow()
        if negative_prompt is None:
            negative_prompt = "worst quality, blurry"  # fallback default
        if not width and not height and model != "nanobanana-pro":
            width = 1024
            height = 1024
        if width and height and model != "nanobanana-pro":
            try:
                width = int(width)
                height = int(height)
            except ValueError:
                # fallback if input is not a number
                width = 1024
                height = 1024

        if seed is None:
            seed = random.randint(0, 1000000)
        if isinstance(ctx, commands.Context):
            typing_cm = ctx.typing()
            author_name = f"{ctx.author.name}#{ctx.author.discriminator}"

            async def send_func(*args, **kwargs):
                try:
                    await ctx.send(*args, **kwargs)
                except Exception as e:
                    try:

                        await ctx.send(f"Something went wrong, please try again. {e}")
                    except Exception:
                        pass

        elif isinstance(ctx, discord.Interaction):
            typing_cm = ctx.channel.typing()
            author_name = f"{ctx.user.name}#{ctx.user.discriminator}"

            async def send_func(*args, **kwargs):
                try:
                    if not ctx.response.is_done():
                        await ctx.response.send_message(*args, **kwargs)
                    else:
                        await ctx.followup.send(*args, **kwargs)
                except Exception:

                    try:
                        if not ctx.response.is_done():
                            await ctx.response.send_message(
                                "Something went wrong, please try again.",
                                ephemeral=True,
                            )
                        else:
                            await ctx.followup.send(
                                "Something went wrong, please try again.",
                                ephemeral=True,
                            )
                    except Exception:
                        pass

        else:
            raise TypeError("ctx must be Context or Interaction")

        pollinations_keys = await self.bot.get_shared_api_tokens("pollinations")
        token = pollinations_keys.get("token")
        if not token:
            await send_func("Pollinations API token not set.")
            return

        min_pixels = 921600
        if width and height and model != "nanobanana-pro":
            if width * height < min_pixels:
                scale = (min_pixels / (width * height)) ** 0.5
                width = int(width * scale)
                height = int(height * scale)

        if model == "nanobanana-pro" and not width and not height:
            width = 3840
            height = 2160
        params = {
            "model": model,
            "width": width,
            "height": height,
            "seed": seed,
            "nologo": "true",
            "private": "false",
            "nofeed": "false",
            "safe": "false",
            "quality": "high",
            "enhance": "true",
            "guidance_scale": 1,
            "negative_prompt": negative_prompt,
            "transparent": "false",
        }
        if images:
            params["image"] = ",".join(images)

        none_params = [k for k, v in params.items() if v is None]
        if none_params:
            pass

        params = {k: v for k, v in params.items() if v is not None}

        if images:
            params["image"] = ",".join(images)
        encoded_prompt = quote(prompt, safe="")
        url = f"https://gen.pollinations.ai/api/generate/image/{encoded_prompt}"
        if model == "nanobanana-pro":
            payload = {
                "model": model,
                "width": width,
                "height": height,
                "seed": seed,
                "enhance": True,
                "private": True,
                "nologo": True,
                "quality": "high",
                "negative_prompt": "worst quality, blurry",
                "prompt": prompt,
            }
        else:
            payload = {
                "model": model,
                "width": width,
                "height": height,
                "seed": seed,
                "enhance": True,
                "private": True,
                "nologo": True,
                "quality": "high",
                "negative_prompt": "worst quality, blurry",
                "prompt": prompt,
            }
        if images:
            payload["image"] = ",".join(images)

        headers = {"Authorization": f"Bearer {token}"}
        real_height = height
        real_width = width

        async with typing_cm:
            async with aiohttp.ClientSession() as session:

                async with session.get(url, params=params, headers=headers) as resp:

                    if resp.status != 200:
                        response_body = await resp.read()
                        response_text = response_body.decode(errors="replace")  # always safe
                        headers_text = json.dumps(dict(resp.headers), indent=2)

                        try:
                            response_json = json.loads(response_body)
                            # Drill down into nested error message if present
                            if "error" in response_json and isinstance(response_json["error"], dict):
                                error_message = response_json["error"].get("message", response_text)
                            else:
                                error_message = response_json.get("message", response_text)
                        except Exception:
                            error_message = response_text  # fallback if JSON parsing fails

                        # Include status code, headers, and body
                        error = discord.Embed(
                            title="⚠️ Oops! I couldn't generate your image",
                            # description=(
                            #     f"**HTTP Status:** {resp.status}\n"
                            #     f"**Response Headers:**\n```\n{headers_text}\n```\n"
                            #     f"**Response Body:**\n```\n{error_message}\n```"
                            # ),
                            description=(
                                "Something went wrong while talking to the image service.\n\n"
                                "**Error message:**\n"
                                f"```\n{error_message}\n```"
                                "**Possible reasons:**\n"
                                "• One of the image links might be invalid or expired.\n"
                                "• The image might be private or not accessible.\n"
                                "• The generation service might be having temporary issues.\n\n"
                                "Please try again with different images or later."
                            ),
                            color=discord.Color.orange(),
                        )
                        await send_func(embed=error)
                        return

                    data = await resp.read()
                    image_bytes = await resp.read()

                    # Para PIL dimensions
                    with Image.open(BytesIO(image_bytes)) as img_for_pil:
                        real_width, real_height = img_for_pil.size

                    # Elimina params width/height para embed (opcional)
                    for key in ["width", "height"]:
                        if key in params:
                            del params[key]

        # Upload to chibisafe
        chibisafe_tokens = await self.bot.get_shared_api_tokens("chibisafe")
        upload_url = chibisafe_tokens.get("upload_url")
        api_key = chibisafe_tokens.get("x_api_key")
        external_upload = await self.config.guild(ctx.guild).external_upload_enabled() if ctx.guild else False
        if external_upload:
            if not upload_url or not api_key:
                await send_func("External upload is enabled, but Chibisafe upload URL or API key is missing. Please set them first using `[p]set api chibisafe upload_url,<url> x_api_key,<key>`",
                "Please set them first."
                )
            else:        
                headers = {"x-api-key": api_key}
                data_form = aiohttp.FormData()
                chibisafe_buffer = BytesIO(image_bytes)
                chibisafe_buffer.seek(0)
                data_form.add_field(
                    "file[]",
                    chibisafe_buffer,
                    filename="generated.png",
                    content_type="image/png",
                )

                async with aiohttp.ClientSession() as session:
                    async with session.post(upload_url, data=data_form, headers=headers) as resp:
                        if resp.status == 200:
                            resp_json = await resp.json()
                            uploaded_url = resp_json.get("url")
                            thumb_url = resp_json.get("thumb")  # optional thumbnail if your API returns it
                        else:
                            uploaded_url = None
                            thumb_url = None

        time_taken = (discord.utils.utcnow() - start_time).total_seconds()
        embed = discord.Embed(title="🖼️ Image Generated Successfully")
        embed.set_image(url="attachment://generated.png")
        embed.add_field(name="Width", value=f"```{real_width}```", inline=True)
        embed.add_field(name="Height", value=f"```{real_height}```", inline=True)
        MAX_FIELD_LEN = 1024
        for k, v in params.items():
            if v is None:
                await ctx.send(f"⚠️ Param {k} is None")
        for key, value in params.items():
            if key.lower() not in [
                "private",
                "nologo",
                "referrer",
                "enhance",
                "image",
                "quality",
            ]:

                # Ensure value fits inside Discord's 1024-char limit (account for formatting)
                val_str = str(value)
                if len(val_str) > MAX_FIELD_LEN - 7:  # account for ```\n and \n```
                    val_str = val_str[: MAX_FIELD_LEN - 30] + "..."
                embed.add_field(name=key, value=f"```\n{val_str}\n```", inline=True)

        embed.add_field(name="Time Taken", value=f"```{time_taken:.2f} seconds```")
        if len(prompt) > 1000:
            prompt = prompt[:800]
        prompt = re.sub(r"^\d{3,4}x\d{3,4}\s+", "", prompt)
        embed.add_field(name="Prompt", value=f"```\n{prompt}\n```", inline=False)
        embed.set_footer(
            text=f"Generated by {author_name} • {datetime.datetime.utcnow().strftime('%m/%d/%Y %I:%M %p')} • Powered by Pollinations.ai - Images may be resized due to Discord Constraints"
        )

        if images:
            ref_value = "\n".join(
                [f"[Image {i+1}]({img})" for i, img in enumerate(images)]
            )

            # Hard limit = 1024
            if len(ref_value) > 1024:
                # Keep it readable, but trimmed
                ref_value = ref_value[:1000] + "..."

            embed.add_field(
                name="Reference Images",
                value=ref_value,
                inline=False,
            )

        view = discord.ui.View()
        regenerate_button = discord.ui.Button(
            label="Regenerate", style=discord.ButtonStyle.green
        )
        edit_button = discord.ui.Button(label="Edit", style=discord.ButtonStyle.blurple)
        delete_button = discord.ui.Button(label="Delete", style=discord.ButtonStyle.red)

        async def regenerate_callback(interaction: discord.Interaction):
            await interaction.response.defer()
            await self._pollinations_generate(
                interaction,
                model,
                prompt,
                seed=random.randint(0, 1000000),
                width=width,
                height=height,
                images=images,
            )

        async def edit_callback(interaction: discord.Interaction):
            current_seed = seed
            current_prompt = prompt
            current_width = width
            current_height = height
            current_images = images
            await interaction.response.send_modal(
                EditModal(
                    cog=self,
                    interaction=interaction,
                    model=model,
                    prompt=current_prompt,
                    seed=current_seed,
                    width=current_width,
                    height=current_height,
                    images=current_images,
                )
            )

        async def delete_callback(interaction: discord.Interaction):
            await interaction.message.delete()

        regenerate_button.callback = regenerate_callback
        edit_button.callback = edit_callback
        delete_button.callback = delete_callback

        view.add_item(regenerate_button)
        view.add_item(edit_button)
        view.add_item(delete_button)
        if external_upload: 
            if uploaded_url:
                embed.add_field(name="Shared Link (4K Download)", value=f"[View Image]({uploaded_url})", inline=False)

        # Nuevo buffer para Discord
        discord_buffer = BytesIO(image_bytes)
        discord_buffer.seek(0)
        await send_func(
            file=File(discord_buffer, filename="generated.png"),
            embed=embed,
            view=view
        )
        if external_upload: 
            if uploaded_url:
                await ctx.send(f"High Quality Image uploaded to: {uploaded_url}")

    async def callback(self, interaction: discord.Interaction):
        new_prompt = self.children[0].value
        await self._pollinations_generate(interaction, model, new_prompt)

        ## TEST

    async def _run_pollinations_text(
        self,
        ctx: commands.Context,
        model: str,
        query: str = None,
    ):
        referrer = await self.config.referrer()
        if not referrer or referrer.lower() == "none":
            await ctx.send(
                "⚠️ Pollinations referrer not set.\n"
                "Use `[p]referrer <your_referrer>` (bot owner only).\n"
                "Get it from: <https://auth.pollinations.ai/>"
            )
            return

        # Prompt fallback
        if not query and ctx.message.attachments:
            query = "Describe this image"
        if not query and not ctx.message.attachments:
            await ctx.send("❌ Please provide a prompt or attach an image.")
            return

        # Collect image URLs
        image_urls = []
        for att in ctx.message.attachments:
            if att.content_type and att.content_type.startswith("image/"):
                image_urls.append(att.url)

        # Build messages (OpenAI‑compatible multimodal format)
        content_parts = [{"type": "text", "text": query}]
        for url in image_urls:
            content_parts.append({"type": "image_url", "image_url": {"url": url}})

        messages = [{"role": "user", "content": content_parts}]

        # Pollinations token
        poll_keys = await self.bot.get_shared_api_tokens("pollinations")
        poll_token = poll_keys.get("token") if poll_keys else None

        if not poll_token:
            await ctx.send(
                "❌ Missing Pollinations API token. "
                "Use `[p]set api pollinations token,<value>`"
            )
            return

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 1,
            "top_p": 1,
            "max_tokens": 4096,
            "seed": 0,
            "referrer": referrer,
            "isPrivate": bool(poll_token),
            "stream": False,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {poll_token}",
            "referer": referrer,
        }
        API_URL = "https://gen.pollinations.ai/api/generate/v1/chat/completions"
        async with ctx.typing():
            try:
                async with aiohttp.ClientSession() as session:

                    async with session.post(API_URL, json=payload, headers=headers) as resp:
                        text = await resp.text()

                        if resp.status != 200:
                            if resp.status == 500 and model == "grok":
                                await ctx.send("❌ The Grok model is currently unavailable due to server issues. Please try again later.")
                            else:
                                await ctx.send(
                                    f"❌ **API Error:** HTTP {resp.status}\n"
                                    f"``````"
                                )
                            return

                        try:
                            data = json.loads(text)
                            result = data["choices"][0]["message"]["content"]
                        except Exception:
                            result = text  # fallback

                        for i in range(0, len(result), 2000):
                            chunk = result[i : i + 2000]
                            await ctx.send(chunk)

            except aiohttp.ClientError as e:
                await ctx.send(f"❌ **Request Failed:** `{e}`")
            except Exception as e:
                await ctx.send(f"⚠️ **Unexpected Error:** `{type(e).__name__}: {e}`")

    @commands.command(name="externalupload")
    @commands.admin_or_permissions(manage_guild=True)
    async def externalupload(self, ctx, toggle: bool):
        """Enable or disable external uploads like Chibisafe for this server."""
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server, not in DMs.")
            return
        await self.config.guild(ctx.guild).external_upload_enabled.set(toggle)
        status = "enabled" if toggle else "disabled"
        await ctx.send(f"External uploads are now **{status}** for this server.")

    @commands.command(name="flux")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def flux(self, ctx: commands.Context, *, prompt: str):
        """Generate an image using the Flux model.

        Parameters
        ----------
        ctx : commands.Context
            The command context containing message and author information.
        prompt : str
            The text prompt describing the image to generate.
            Supports optional seed at the end (e.g., "a cat 12345").
            Supports negative prompt via --negative flag (e.g., "a cat --negative blurry").

        Returns
        -------
        None
            Sends the generated image to the channel with metadata embed.

        Notes
        -----
        - Cooldown: 1 use per 60 seconds per guild.
        - Requires bot permission to attach files.
        - Seed is optional; if not provided, a random seed is used.
        - Negative prompt defaults to "worst quality, blurry" if not specified.
        - Output includes regenerate, edit, and delete buttons.
        - Powered by Pollinations.ai API.
        """
        words = prompt.split()
        seed = None

        # Parse negative prompt if present in format --negative <text>
        negative_prompt = "worst quality, blurry"  # default negative prompt
        negative_match = re.search(r"--negative\s+([^\n]+)", prompt, re.IGNORECASE)
        if negative_match:
            negative_prompt = negative_match.group(1).strip()
            # Remove the --negative part from the prompt
            prompt = re.sub(r"--negative\s+[^\n]+", "", prompt, flags=re.IGNORECASE).strip()

        if words and words[-1].isdigit():
            seed = int(words[-1])
            words = words[:-1]
            prompt = " ".join(words)
        else:
            seed = random.randint(0, 1000000)

        await self._pollinations_generate(ctx, "flux", prompt, seed, negative_prompt=negative_prompt)

    @commands.command(name="kontext")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def kontext(self, ctx: commands.Context, *, prompt: str):
        """Image Gen via kontext model."""

        # Parse negative prompt if present in format --negative <text>
        negative_prompt = "worst quality, blurry"  # default negative prompt
        negative_match = re.search(r"--negative\s+([^\n]+)", prompt, re.IGNORECASE)
        if negative_match:
            negative_prompt = negative_match.group(1).strip()
            # Remove the --negative part from the prompt
            prompt = re.sub(
                r"--negative\s+[^\n]+", "", prompt, flags=re.IGNORECASE
            ).strip()

        words = prompt.split()
        seed = None

        if words and words[-1].isdigit():
            seed = int(words[-1])
            words = words[:-1]
            prompt = " ".join(words)
        else:
            seed = random.randint(0, 1000000)

        await self._pollinations_generate(ctx, "kontext", prompt, seed, negative_prompt=negative_prompt)

    @commands.command(name="seedream")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def seedream(self, ctx: commands.Context, *, prompt: str = None):
        """Image Gen via seedream model.
        Can be used with text prompt only or with image attachments.
        Image size can be changed via command arguments; default 1700x1200.
        Ex: !seedream a cat
        Ex: !seedream 1024x768 a cat
        Ex: !seedream 1024 768 a cat"""
        # Parse negative prompt if present in format --negative <text>
        negative_prompt = "worst quality, blurry"  # default negative prompt
        negative_match = re.search(r"--negative\s+([^\n]+)", prompt, re.IGNORECASE)
        if negative_match:
            negative_prompt = negative_match.group(1).strip()
            # Remove the --negative part from the prompt
            prompt = re.sub(
                r"--negative\s+[^\n]+", "", prompt, flags=re.IGNORECASE
            ).strip()

        images = []

        if prompt and ctx.message.mentions:
            for user in ctx.message.mentions:
                if hasattr(user, "display_avatar"):
                    images.append(user.display_avatar.with_format("png").with_size(1024).url)
                else:
                    images.append(user.avatar_url)

        if ctx.message.attachments:
            images.extend([a.url for a in ctx.message.attachments])

        if ctx.message.reference:
            try:
                referenced = await ctx.channel.fetch_message(
                    ctx.message.reference.message_id
                )
                if referenced.attachments:
                    images.extend([a.url for a in referenced.attachments])
                elif referenced.embeds:
                    for embed in referenced.embeds:
                        if embed.image and embed.image.url:
                            images.append(embed.image.url)
            except Exception:
                pass

        if not prompt and not images:
            await ctx.send("❌ Please provide a prompt and/or attach an image.")
            return

        # Default resolution values
        width = 1700
        height = 1200

        if prompt:
            parts = prompt.split(maxsplit=2)
            if parts:
                # Try parsing the first part as WxH format
                if "x" in parts[0]:
                    try:
                        width_str, height_str = parts[0].lower().split("x")
                        width = int(width_str)
                        height = int(height_str)
                        prompt = parts[1] if len(parts) > 1 else ""
                        # If there is more after the second part, append it
                        if len(parts) > 2:
                            prompt += " " + parts[2]
                    except ValueError:
                        width = 1700
                        height = 1200
                        prompt = prompt
                # Otherwise try parsing first two parts as integers
                elif len(parts) >= 2:
                    try:
                        width = int(parts[0])
                        height = int(parts[1])
                        prompt = parts[2] if len(parts) > 2 else ""
                    except ValueError:
                        width = 1700
                        height = 1200
                        prompt = prompt

        # Handle seed extraction from prompt
        seed = random.randint(0, 1000000)
        if prompt:
            words = prompt.split()
            if words and words[-1].isdigit():
                seed = int(words[-1])
                prompt = " ".join(words[:-1])

        # Replace certain gif URLs with pngs for compatibility
        images = [
            (
                img.replace(".gif", ".png")
                if img.endswith(".gif") and "discordapp.com/avatars/" in img
                else img
            )
            for img in images
        ]

        # Remove duplicate images
        seen = set()
        images = [x for x in images if not (x in seen or seen.add(x))]

        await self._pollinations_generate(
            ctx,
            "seedream",
            prompt or "",
            seed=seed,
            images=images if images else None,
            width=width,
            height=height,
            negative_prompt=negative_prompt,
        )


    @commands.command(name="turbo")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def turbo(self, ctx: commands.Context, *, prompt: str):
        """Image Gen via turbo model."""

        # Parse negative prompt if present in format --negative <text>
        negative_prompt = "worst quality, blurry"  # default negative prompt
        negative_match = re.search(r"--negative\s+([^\n]+)", prompt, re.IGNORECASE)
        if negative_match:
            negative_prompt = negative_match.group(1).strip()
            # Remove the --negative part from the prompt
            prompt = re.sub(
                r"--negative\s+[^\n]+", "", prompt, flags=re.IGNORECASE
            ).strip()

        words = prompt.split()
        seed = None

        if words and words[-1].isdigit():
            seed = int(words[-1])

            words = words[:-1]
            prompt = " ".join(words)
        else:
            seed = random.randint(0, 1000000)

        await self._pollinations_generate(ctx, "turbo", prompt, seed, negative_prompt=negative_prompt)

    @commands.command()
    @commands.is_owner()
    async def referrer(self, ctx: commands.Context, *, new_referrer: str):
        """Set the global referrer used in Pollinations API requests."""
        await self.config.referrer.set(new_referrer)
        await ctx.send(f"✅ Referrer has been set to: `{new_referrer}`")

    async def _generate_hf_image(
        self, ctx, prompt, endpoint, model=None, api_name_override=None
    ):
        """Helper to generate an image from a Hugging Face gradio space endpoint."""

        api_key = (await self.bot.get_shared_api_tokens("huggingface")).get("api_key")
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

        def extract_hf_space(endpoint):

            m = re.match(r"https?://huggingface.co/spaces/([^/]+)/([^/?#]+)", endpoint)
            if m:
                return f"{m.group(1)}/{m.group(2)}"
            m = re.match(r"https?://huggingface.co/([^/]+)/([^/?#]+)", endpoint)
            if m:
                return f"{m.group(1)}/{m.group(2)}"
            m = re.match(r"https?://([a-z0-9\-]+)\.hf\.space", endpoint)
            if m:
                sub = m.group(1)
                parts = sub.split("-", 1)
                if len(parts) == 2:
                    org, space = parts
                    return f"{org}/{space.replace('-', ' ').title().replace(' ', '-')}"
                return sub
            raise ValueError(
                f"Cannot extract Hugging Face space from endpoint: {endpoint}"
            )

        space = extract_hf_space(endpoint)
        client = Client(space, hf_token=api_key if api_key else None)
        api_name = api_name_override if api_name_override else "/generate_image"
        try:
            api_info = client.view_api(return_format="dict")
            # await ctx.send(api_info)
            if (
                api_info
                and "named_endpoints" in api_info
                and api_name in api_info["named_endpoints"]
            ):
                params = api_info["named_endpoints"][api_name].get("parameters", [])
                param_names = [
                    p.get("parameter_name") or p.get("name")
                    for p in params
                    if p.get("parameter_name") or p.get("name")
                ]
            else:
                param_names = []
        except Exception:
            param_names = []
        predict_kwargs = {"api_name": api_name}
        if "prompt" in param_names:
            predict_kwargs["prompt"] = prompt
        elif "prompt_text" in param_names:
            predict_kwargs["prompt_text"] = prompt
        else:
            predict_kwargs["prompt"] = prompt
        if model and "model" in param_names:
            predict_kwargs["model"] = model
        try:
            result = await asyncio.get_running_loop().run_in_executor(
                None, lambda: client.predict(**predict_kwargs)
            )
        except Exception as e:
            await ctx.send(f"Error: {e}")
            return

        image_bytes = None
        if isinstance(result, dict):
            if result.get("url"):
                url = result["url"]
                if url.startswith("data:image"):
                    b64data = url.split(",", 1)[-1]
                    image_bytes = io.BytesIO(base64.b64decode(b64data))
                else:
                    import aiohttp

                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as resp:
                            image_bytes = io.BytesIO(await resp.read())
            elif result.get("path"):
                with open(result["path"], "rb") as f:
                    image_bytes = io.BytesIO(f.read())
        elif isinstance(result, str):
            if result.startswith("data:image"):
                b64data = result.split(",", 1)[-1]
                image_bytes = io.BytesIO(base64.b64decode(b64data))
            elif result.startswith("http://") or result.startswith("https://"):
                import aiohttp

                async with aiohttp.ClientSession() as session:
                    async with session.get(result) as resp:
                        image_bytes = io.BytesIO(await resp.read())
            else:
                with open(result, "rb") as f:
                    image_bytes = io.BytesIO(f.read())
        elif isinstance(result, tuple):
            image_result = result[0]
            if isinstance(image_result, str):
                if image_result.startswith("data:image"):
                    b64data = image_result.split(",", 1)[-1]
                    image_bytes = io.BytesIO(base64.b64decode(b64data))
                elif image_result.startswith("http://") or image_result.startswith(
                    "https://"
                ):
                    import aiohttp

                    async with aiohttp.ClientSession() as session:
                        async with session.get(image_result) as resp:
                            image_bytes = io.BytesIO(await resp.read())
                else:
                    with open(image_result, "rb") as f:
                        image_bytes = io.BytesIO(f.read())
        if image_bytes:
            image_bytes.seek(0)
            file = discord.File(image_bytes, filename="image.png")
            await ctx.send(file=file)
        else:
            await ctx.send("No image returned.")

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def hidream(self, ctx: commands.Context, *, prompt: str):
        """Image Gen via HiDream endpoint."""
        endpoint = "https://huggingface.co/spaces/HiDream-ai/HiDream-I1-Dev/"
        async with ctx.typing():
            await self._generate_hf_image(
                ctx, prompt, endpoint, api_name_override="/generate_with_status"
            )

    # @commands.command()
    # async def flux(self, ctx: commands.Context, *, prompt: str):
    #     """Image Gen via Fake-FLUX-Pro-Unlimited endpoint."""
    #     endpoint = "https://huggingface.co/spaces/llamameta/Fake-FLUX-Pro-Unlimited/"
    #     async with ctx.typing():
    #         await self._generate_hf_image(ctx, prompt, endpoint, model="flux")

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def lumina(self, ctx: commands.Context, *, prompt: str):
        """Image Gen via NetaLumina."""
        endpoint = "https://huggingface.co/spaces/neta-art/NetaLumina_T2I_Playground/"
        async with ctx.typing():
            await self._generate_hf_image(ctx, prompt, endpoint)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def analyze(self, ctx: commands.Context, *, arg: str = None):
        """Analyze an image: provide an attachment, URL, or mention a user (for avatar)."""
        image_url = None
        if ctx.message.attachments:
            image_url = ctx.message.attachments[0].url
        elif ctx.message.reference:
            # The command is replying to another message
            try:
                referenced = await ctx.channel.fetch_message(
                    ctx.message.reference.message_id
                )
                if referenced.attachments:
                    image_url = referenced.attachments[0].url
                elif referenced.embeds:
                    for embed in referenced.embeds:
                        if embed.image and embed.image.url:
                            image_url = embed.image.url
                            break
            except Exception:
                pass
        elif arg and ctx.message.mentions:
            user = ctx.message.mentions[0]
            image_url = (
                user.display_avatar.url
                if hasattr(user, "display_avatar")
                else user.avatar_url
            )
        elif arg and (arg.startswith("http://") or arg.startswith("https://")):
            image_url = arg.strip()
        elif arg and arg.strip().isdigit():
            user_id = int(arg.strip())
            user = ctx.guild.get_member(user_id) if ctx.guild else None
            if not user:
                try:
                    user = await self.bot.fetch_user(user_id)
                except Exception:
                    user = None
            if user:
                image_url = (
                    user.display_avatar.url
                    if hasattr(user, "display_avatar")
                    else user.avatar_url
                )
            else:
                await ctx.send("Could not find user with that ID.")
                return
        else:
            await ctx.send(
                "Please provide an image attachment, a direct image URL, or mention a user."
            )
            return

        question = "What's in this image?"
        url = "https://text.pollinations.ai/openai"
        headers = {"Content-Type": "application/json"}
        pollinations_keys = await self.bot.get_shared_api_tokens("pollinations")
        poll_token = pollinations_keys.get("token") if pollinations_keys else None
        if poll_token:
            headers["Authorization"] = f"Bearer {poll_token}"
        payload = {
            "model": "openai-large",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            "max_tokens": 500,
        }

        async with ctx.typing():
            api_result = None
            error = None
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status != 200:
                        error = f"Error: {resp.status}"
                    else:
                        try:
                            api_result = await resp.json()
                        except Exception as e:
                            error = f"Received unexpected response:\n{str(e)}"
            try:
                a = 1  # await ctx.send(image_url)
            except Exception:
                pass
            if error:
                await ctx.send(error)
            elif api_result:
                try:
                    text = api_result["choices"][0]["message"]["content"]
                    await ctx.send(f"\U0001f5bc Image Analysis:\n{text}")
                except Exception:
                    await ctx.send("Received unexpected response:\n" + str(api_result))

    @commands.command(name="img2img")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def img2img(self, ctx: commands.Context, *, text: str = None):
        """
        Multi-Image-to-Image Gen via gptimage model.
        Detects images from attachments, reply, mention, ID, or URL.
        Supports up to 3 images.
        Usage examples:
        !img2img put them together (with 2+ attachments)
        !img2img image1=https://example.com/1.png image2=https://example.com/2.png combine them
        !img2img add a background here @username
        !img2img enhance this 123456789012345678
        !img2img (reply to an image) stylize this
        """
        images = []
        prompt = text or ""

        for i in range(1, 4):
            match = re.search(rf"image{i}=(\S+)", prompt)
            if match:
                images.append(match.group(1))
                prompt = prompt.replace(match.group(0), "").strip()

        if ctx.message.reference and len(images) < 3:
            replied = ctx.message.reference.resolved
            if not replied:
                try:
                    replied = await ctx.channel.fetch_message(
                        ctx.message.reference.message_id
                    )
                except Exception:
                    replied = None
            if replied:
                if replied.attachments:
                    images.extend(
                        [a.url for a in replied.attachments[: 3 - len(images)]]
                    )
                elif replied.embeds:
                    for embed in replied.embeds:
                        if embed.image and embed.image.url:
                            images.append(embed.image.url)
                            if len(images) >= 3:
                                break

        if ctx.message.attachments and len(images) < 3:
            images.extend([a.url for a in ctx.message.attachments[: 3 - len(images)]])

        if len(images) < 3:
            urls = re.findall(r"(https?://\S+)", prompt)
            for url in urls:
                if len(images) >= 3:
                    break
                images.append(url)
                prompt = prompt.replace(url, "").strip()

        for mention in ctx.message.mentions:
            if len(images) >= 3:
                break
            images.append(mention.display_avatar.url)
            prompt = prompt.replace(mention.mention, "").strip()

        if len(images) < 3:
            id_matches = re.findall(r"\b\d{17,20}\b", prompt)
            for mid in id_matches:
                if len(images) >= 3:
                    break
                user = ctx.guild.get_member(int(mid)) if ctx.guild else None
                if not user:
                    try:
                        user = await self.bot.fetch_user(int(mid))
                    except Exception:
                        user = None
                if user:
                    images.append(user.display_avatar.url)
                    prompt = prompt.replace(mid, "").strip()

        if not images:
            await ctx.send(
                "❌ Please provide 1–3 images (attachment, URL, mention, ID, or reply)."
            )
            return

        if not prompt:
            await ctx.send("❌ Please provide a prompt after the image(s).")
            return

        pollinations_keys = await self.bot.get_shared_api_tokens("pollinations")
        token = pollinations_keys.get("token") if pollinations_keys else None

        encoded_prompt = quote(prompt)
        encoded_images = [quote(url) for url in images]
        images_param = ",".join(encoded_images)

        seed = random.randint(0, 1000000)
        query_params = {
            "width": 512,
            "height": 512,
            "seed": seed,
            "model": "kontext",
            "referrer": await self.config.referrer(),
            "nologo": "True",
            "private": "True",
            "nofeed": "True",
            "enhance": "True",
        }

        base_url = f"https://gen.pollinations.ai/api/generate/image/{encoded_prompt}"
        query_str = urlencode(query_params)
        full_url = f"{base_url}?{query_str}&image={images_param}"

        headers = {"Authorization": f"Bearer {token}"} if token else {}

        if isinstance(ctx, commands.Context):
            typing_cm = ctx.typing()
            send_func = ctx.send
            author_name = f"{ctx.author.name}#{ctx.author.discriminator}"
        elif isinstance(ctx, discord.Interaction):
            typing_cm = ctx.channel.typing()
            send_func = lambda *args, **kwargs: (
                ctx.response.send_message(*args, **kwargs)
                if not ctx.response.is_done()
                else ctx.followup.send(*args, **kwargs)
            )
            author_name = f"{ctx.user.name}#{ctx.user.discriminator}"
        else:
            raise TypeError("ctx must be Context or Interaction")

        async with typing_cm:
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                async with aiohttp.ClientSession() as session:
                    async with session.get(full_url, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.read()
                            file = BytesIO(data)
                            file.seek(0)
                            break
                        elif attempt == max_retries:
                            error = discord.Embed(
                                title="⚠️ Oops! I couldn't generate your image",
                                description=(
                                    "Something went wrong while talking to the image service.\n\n"
                                    "**Possible reasons:**\n"
                                    "• One of the image links might be invalid or expired.\n"
                                    "• The image might be private or not accessible.\n"
                                    "• The generation service might be having temporary issues.\n\n"
                                    "Please try again with different images or later."
                                ),
                                color=discord.Color.orange(),
                            )
                            # error.add_field(
                            #     name="Technical details",
                            #     value=f"HTTP Status: `{resp.status}`\n```\n{full_url}\n```",
                            #     inline=False,
                            # )
                            await send_func(embed=error)
                            return
                        # else: retry

        embed = discord.Embed(title="🖼️ Image Generated Successfully")
        embed.set_image(url="attachment://img2img.png")
        for key, value in query_params.items():
            if key.lower() not in [
                "private",
                "nologo",
                "referrer",
                "enhance",
                "nofeed",
                "quality",
            ]:
                embed.add_field(name=key, value=f"```\n{value}\n```", inline=True)

        if len(prompt) > 1024:
            prompt = prompt[:1024]

        prompt_value = f"```\n{prompt}\n```"
        if len(prompt_value) > 1024:
            trimmed = prompt[: 1024 - 10] + "..."
            prompt_value = f"```\n{trimmed}\n```"

        embed.add_field(name="Prompt", value=prompt_value, inline=False)
        ref_value = "\n".join([f"[Image {i+1}]({img})" for i, img in enumerate(images)])
        if len(ref_value) > 1024:
            ref_value = ref_value[:1000] + "..."

        embed.add_field(name="Reference Images", value=ref_value, inline=False)
        # embed.add_field(
        #     name="Images",
        #     value=" • ".join([f"[Image{i+1}]({url})" for i, url in enumerate(images)]),
        #     inline=False,
        # )
        author = ctx.author if hasattr(ctx, "author") else ctx.user
        embed.set_footer(
            text=f"Generated by {author} • {datetime.datetime.utcnow().strftime('%m/%d/%Y %I:%M %p')} • Powered by Pollinations.ai"
        )

        view = discord.ui.View()
        regenerate_button = discord.ui.Button(
            label="Regenerate", style=discord.ButtonStyle.green
        )
        edit_button = discord.ui.Button(label="Edit", style=discord.ButtonStyle.blurple)
        delete_button = discord.ui.Button(label="Delete", style=discord.ButtonStyle.red)

        async def regenerate_callback(interaction: discord.Interaction):
            await interaction.response.defer()
            img_args = " ".join([f"image{i+1}={url}" for i, url in enumerate(images)])
            await self.img2img(interaction, text=f"{img_args} {prompt}")

        async def edit_callback(interaction: discord.Interaction):
            await interaction.response.send_modal(
                EditModal(
                    cog=self,
                    interaction=interaction,
                    model="kontext",
                    prompt=prompt,
                    seed=seed,
                    image_url=(
                        ",".join(images) if images else None
                    ),  # Pass comma-delimited
                )
            )

        async def delete_callback(interaction: discord.Interaction):
            await interaction.message.delete()

        regenerate_button.callback = regenerate_callback
        edit_button.callback = edit_callback
        delete_button.callback = delete_callback

        view.add_item(regenerate_button)
        view.add_item(edit_button)
        view.add_item(delete_button)

        await send_func(file=File(file, filename="img2img.png"), embed=embed, view=view)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def evil(self, ctx: commands.Context, *, query: str):
        """Query with `evil`.
        """
        ref = await self.config.referrer()
        if ref == "none":
            await ctx.send(
                "Pollinations referrer not set. Use `[p]referrer <your_referrer>` (bot owner only).\nObtain your referrer from https://auth.pollinations.ai/"
            )
            return
        base_url = "https://text.pollinations.ai/"

        encoded_query = urllib.parse.quote(query)

        headers = {}
        params = {"model": "evil", "referrer": await self.config.referrer()}

        pollinations_keys = await self.bot.get_shared_api_tokens("pollinations")
        poll_token = pollinations_keys.get("token") if pollinations_keys else None

        if poll_token:
            headers["Authorization"] = f"Bearer {poll_token}"
            params["private"] = "true"

        async with ctx.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{base_url}{encoded_query}", headers=headers, params=params
                    ) as resp:
                        body = await resp.text()

                        if resp.status == 200:
                            await ctx.send(f"{body[:2000]}")
                        else:
                            await ctx.send(
                                f"❌ **API Error:** Received HTTP {resp.status} status.\n"
                                f"```\n{body[:1000]}\n```"
                            )
            except aiohttp.ClientError as e:

                await ctx.send(
                    f"❌ **Request Failed:** An error occurred while contacting the API.\n`{e}`"
                )

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def geminisearch(self, ctx: commands.Context, *, query: str):
        """
        Query the GeminiSearch model at Pollinations with a search prompt.
        """
        ref = await self.config.referrer()
        if ref == "none":
            await ctx.send(
                "Pollinations referrer not set. Use `[p]referrer <your_referrer>` (bot owner only).\nObtain your referrer from https://auth.pollinations.ai/"
            )
            return
        base_url = "https://text.pollinations.ai/"
        encoded_query = urllib.parse.quote(query)
        headers = {}
        params = {"model": "gemini-search", "referrer": await self.config.referrer()}

        MODEL_INFO = {
            "name": "gemini-search",
            "description": "Gemini Search",
            "provider": "azure",
            "tier": "anonymous",
            "community": False,
            "aliases": ["gemini-search"],
            "input_modalities": ["text", "image"],
            "output_modalities": ["text"],
            "tools": True,
            "vision": True,
            "audio": False,
        }
        pollinations_keys = await self.bot.get_shared_api_tokens("pollinations")
        poll_token = pollinations_keys.get("token") if pollinations_keys else None

        if poll_token:
            headers["Authorization"] = f"Bearer {poll_token}"
            # Add 'private=true' for authenticated requests
            params["private"] = "true"

        async with ctx.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{base_url}{encoded_query}", headers=headers, params=params
                    ) as resp:
                        body = await resp.text()
                        if resp.status == 200:
                            for i in range(0, len(body), 2000):
                                embed = discord.Embed(
                                    title="📡 Gemini Search Response",
                                    description=body[i : i + 2000],
                                    color=discord.Color.blue(),
                                )
                                embed.set_footer(
                                    text=f"Model: {MODEL_INFO['name']} | Provider: {MODEL_INFO['provider']} | Powered by pollinations.ai"
                                )
                                await ctx.send(embed=embed)
                        else:

                            await ctx.send(
                                f"❌ **API Error:** Received HTTP {resp.status} status.\n"
                                f"```\n{body[:1000]}\n```"
                            )
            except aiohttp.ClientError as e:

                await ctx.send(
                    f"❌ **Request Failed:** An error occurred while contacting the API.\n`{e}`"
                )

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def gemini3(self, ctx: commands.Context, *, query: str = None):
        """
        Query via Gemini3
        """

        MODEL = "gemini-large"  # Pollinations new API model name

        referrer = await self.config.referrer()
        if not referrer or referrer.lower() == "none":
            await ctx.send(
                "⚠️ Pollinations referrer not set.\n"
                "Use `[p]referrer <your_referrer>` (bot owner only).\n"
                "Get it from: <https://auth.pollinations.ai/>"
            )
            return

        # Prompt fallback
        if not query and ctx.message.attachments:
            query = "Describe this image"
        if not query and not ctx.message.attachments:
            await ctx.send("❌ Please provide a prompt or attach an image.")
            return

        # Collect image URLs
        image_urls = []
        for att in ctx.message.attachments:
            if att.content_type and att.content_type.startswith("image/"):
                image_urls.append(att.url)

        # Build messages
        content_parts = [{"type": "text", "text": query}]
        for url in image_urls:
            content_parts.append({"type": "image_url", "image_url": {"url": url}})

        messages = [{"role": "user", "content": content_parts}]

        # Pollinations token
        poll_keys = await self.bot.get_shared_api_tokens("pollinations")
        poll_token = poll_keys.get("token") if poll_keys else None

        if not poll_token:
            await ctx.send(
                "❌ Missing Pollinations API token. Use `[p]set api pollinations token,<value>`"
            )
            return

        payload = {
            "model": MODEL,
            "messages": messages,
            "temperature": 1,
            "top_p": 1,
            "max_tokens": 4096,
            "seed": 0,

            # Pollinations custom fields
            "referrer": referrer,
            "isPrivate": bool(poll_token),

            # streaming disabled
            "stream": False
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {poll_token}",
            "referer": referrer,
        }

        url = "https://gen.pollinations.ai/api/generate/v1/chat/completions"

        async with ctx.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, headers=headers) as resp:
                        text = await resp.text()

                        if resp.status != 200:
                            await ctx.send(
                                f"❌ **API Error:** HTTP {resp.status}\n"
                                f"```\n{text[:1000]}\n```"
                            )
                            return

                        # Parse response
                        try:
                            data = json.loads(text)
                            result = data["choices"][0]["message"]["content"]
                        except Exception:
                            result = text  # fallback

                        # Send in 2000-char chunks
                        for i in range(0, len(result), 2000):
                            embed = discord.Embed(
                                title="🤖 Pollinations Response",
                                description=result[i : i + 2000],
                                color=discord.Color.blue(),
                            )
                            embed.set_footer(text=f"Model: {MODEL} | pollinations.ai")
                            await ctx.send(embed=embed)

            except aiohttp.ClientError as e:
                await ctx.send(f"❌ **Request Failed:** `{e}`")
            except Exception as e:
                await ctx.send(f"⚠️ **Unexpected Error:** `{type(e).__name__}: {e}`")

    @commands.command(name="gptimage")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def gptimage(self, ctx: commands.Context, *, prompt: str = None):
        """
        Image Gen via gptimage model.
        Max size is 1024x1024
        Usage:
          [p]gptimage <prompt> [attach image(s), reply, mention, ID, or URL(s)]
          [p]gptimage <prompt> (text-only prompt is supported)
          Multiple images supported (comma-separated).
        """

        # Parse negative prompt if present in format --negative <text>
        negative_prompt = "worst quality, blurry"  # default negative prompt
        negative_match = re.search(r"--negative\s+([^\n]+)", prompt, re.IGNORECASE)
        if negative_match:
            negative_prompt = negative_match.group(1).strip()
            # Remove the --negative part from the prompt
            prompt = re.sub(r"--negative\s+[^\n]+", "", prompt, flags=re.IGNORECASE).strip()
        images = []
        if ctx.message.attachments:
            images.extend([a.url for a in ctx.message.attachments])
        if ctx.message.reference:
            try:
                referenced = await ctx.channel.fetch_message(
                    ctx.message.reference.message_id
                )
                if referenced.attachments:
                    images.extend([a.url for a in referenced.attachments])
                elif referenced.embeds:
                    for embed in referenced.embeds:
                        if embed.image and embed.image.url:
                            images.append(embed.image.url)
            except Exception:
                pass
        if prompt and ctx.message.mentions:
            for user in ctx.message.mentions:
                if hasattr(user, "display_avatar"):
                    images.append(user.display_avatar.with_format("png").with_size(1024).url)
                else:
                    images.append(user.avatar_url)
                prompt = prompt.replace(user.mention, "").strip()
        if prompt:
            url_matches = re.findall(r"(https?://\S+)", prompt)
            for url in url_matches:
                images.append(url)
                prompt = prompt.replace(url, "").strip()
        if prompt:
            id_matches = re.findall(r"\b\d{17,20}\b", prompt)
            for mid in id_matches:
                user = ctx.guild.get_member(int(mid)) if ctx.guild else None
                if not user:
                    try:
                        user = await self.bot.fetch_user(int(mid))
                    except Exception:
                        user = None
                if user:
                    if hasattr(user, "display_avatar"):
                        images.append(user.display_avatar.with_format("png").with_size(1024).url)
                    else:
                        images.append(user.avatar_url)
                    prompt = prompt.replace(mid, "").strip()
        images = [
            (
                img.replace(".gif", ".png")
                if img.endswith(".gif") and "discordapp.com/avatars/" in img
                else img
            )
            for img in images
        ]
        seen = set()
        images = [x for x in images if not (x in seen or seen.add(x))]

        if not prompt:
            await ctx.send("❌ Please provide a prompt.")
            return
        width = 1024
        height = 1536
        seed = random.randint(0, 1000000)
        await self._pollinations_generate(
            ctx,
            "gptimage",
            prompt or "",
            seed=seed,
            width=width,
            height=height,
            images=images if images else None,
            negative_prompt=negative_prompt,
        )

    @commands.command(name="nanobanana")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def nanobanana(self, ctx: commands.Context, *, prompt: str = None):
        """
        Image Gen via nanobanana pro model.
        Max size is 2048x2048
        Usage:
          [p]nanobanana <prompt> [attach image(s), reply, mention, ID, or URL(s)]
          [p]nanobanana <prompt> (text-only prompt is supported)
          Multiple images supported (comma-separated).
        """
        # Parse negative prompt if present in format --negative <text>
        negative_prompt = "worst quality, blurry"  # default negative prompt
        negative_match = re.search(r"--negative\s+([^\n]+)", prompt, re.IGNORECASE)
        if negative_match:
            negative_prompt = negative_match.group(1).strip()
            # Remove the --negative part from the prompt
            prompt = re.sub(
                r"--negative\s+[^\n]+", "", prompt, flags=re.IGNORECASE
            ).strip()

        # Parse height if present in format --height <number>
        height = 3072  # default height
        height_match = re.search(r"--height\s+(\d+)", prompt, re.IGNORECASE)
        if height_match:
            height = int(height_match.group(1))
            prompt = re.sub(r"--height\s+\d+", "", prompt, flags=re.IGNORECASE).strip()
        # Parse width if present in format --width <number>
        width = 5504  # default width
        width_match = re.search(r"--width\s+(\d+)", prompt, re.IGNORECASE)
        if width_match:
            width = int(width_match.group(1))
            prompt = re.sub(r"--width\s+\d+", "", prompt, flags=re.IGNORECASE).strip()

        # --- Parse --seed ---
        seed_match = re.search(r"--seed\s+(\d+)", prompt, re.IGNORECASE)
        if seed_match:
            seed = int(seed_match.group(1))
            prompt = re.sub(r"--seed\s+\d+", "", prompt, flags=re.IGNORECASE).strip()
        images = []
        if ctx.message.attachments:
            images.extend([a.url for a in ctx.message.attachments])
        if ctx.message.reference:
            try:
                referenced = await ctx.channel.fetch_message(
                    ctx.message.reference.message_id
                )
                if referenced.attachments:
                    images.extend([a.url for a in referenced.attachments])
                elif referenced.embeds:
                    for embed in referenced.embeds:
                        if embed.image and embed.image.url:
                            images.append(embed.image.url)
            except Exception:
                pass
        if prompt and ctx.message.mentions:
            for user in ctx.message.mentions:
                if hasattr(user, "display_avatar"):
                    images.append(
                        user.display_avatar.with_format("png").with_size(1024).url
                    )
                    # images.append(user.display_avatar.with_format("png").with_size(1024).url)
                else:
                    images.append(user.avatar_url)
                prompt = prompt.replace(user.mention, "").strip()
        if prompt:
            url_matches = re.findall(r"(https?://\S+)", prompt)
            for url in url_matches:
                images.append(url)
                prompt = prompt.replace(url, "").strip()
        if prompt:
            id_matches = re.findall(r"\b\d{17,20}\b", prompt)
            for mid in id_matches:
                user = ctx.guild.get_member(int(mid)) if ctx.guild else None
                if not user:
                    try:
                        user = await self.bot.fetch_user(int(mid))
                    except Exception:
                        user = None
                if user:
                    if hasattr(user, "display_avatar"):
                        # avatar_url = user.display_avatar.with_format("png").with_size(1024).url
                        images.append(user.display_avatar.with_format("png").with_size(1024).url)
                    else:

                        images.append(user.avatar_url)
                    prompt = prompt.replace(mid, "").strip()
        images = [
            (
                img.replace(".gif", ".png")
                if img.endswith(".gif") and "discordapp.com/avatars/" in img
                else img
            )
            for img in images
        ]
        seen = set()
        images = [x for x in images if not (x in seen or seen.add(x))]

        if not prompt:
            await ctx.send("❌ Please provide a prompt.")
            return

        seed = None
        if not seed:
            seed = random.randint(0, 1000000)
        await self._pollinations_generate(
            ctx,
            "nanobanana",
            prompt or "",
            seed=seed,
            images=images if images else None,
            negative_prompt=negative_prompt,
            height=height,
            width=width,
        )

    async def _pollinations_request(
        self,
        *,
        prompt: str,
        model: str,
        token: str,
        images=None,
        duration=None,
        audio=False,
        aspect_ratio=None,
        resolution=None,
        negative_prompt=None,
        seed=None,
    ):
        """
        Handles Pollinations GET requests for all models, capturing all parameters for debugging.
        Supports Wan 2.6 video generation with proper parameter handling.
        """
        encoded_prompt = urllib.parse.quote(prompt, safe="")
        base_url = f"https://gen.pollinations.ai/api/generate/image/{encoded_prompt}"
        params = {
            k: v
            for k, v in {
                "model": model,
                "duration": duration,
                "audio": "true" if audio else None,
                "aspectRatio": aspect_ratio,
                "resolution": resolution,
                "negative_prompt": negative_prompt,
                "seed": seed,
            }.items()
            if v is not None
        }

        if images:
            params["image"] = images[0]  

        headers = {
            "Authorization": f"Bearer {token}",
            "Referer": "https://pollinations.ai/",
            "Origin": "https://pollinations.ai",
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params, headers=headers) as resp:
                full_url = str(resp.url)

                content_type = resp.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    data = await resp.json()
                else:
                    data = await resp.read()

        return data, full_url

    @commands.command(name="seedance")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.has_permissions(attach_files=True)
    async def seedance(self, ctx, *, prompt: str = None):
        if not prompt and not ctx.message.attachments and not ctx.message.reference:
            return await ctx.send("❌ Provide a prompt and/or images.")

        poll_keys = await self.bot.get_shared_api_tokens("pollinations")
        token = poll_keys.get("token") if poll_keys else None
        if not token:
            return await ctx.send("Missing Pollinations API token.")
        processed_images = []
        temp_msgs = []

        if prompt:
            # Extract URLs from the prompt
            url_regex = r"https?://\S+\.(?:png|jpg|jpeg|webp)"
            found_urls = re.findall(url_regex, prompt)
            for url in found_urls:
                buf, result = await self.process_image(url)
                if buf:
                    msg = await ctx.channel.send(
                        content="Processing Image... Please wait",
                        file=discord.File(buf, filename=result),
                    )
                    temp_msgs.append(msg)
                    processed_images.append(msg.attachments[0].url)
                else:
                    processed_images.append(result)
            # Remove URLs from prompt so Pollinations doesn't try to read them as text
            for url in found_urls:
                prompt = prompt.replace(url, "").strip()
        # a
        for a in ctx.message.attachments:
            buf, result = await self.process_image(a.url.rstrip("&"))
            if buf:
                msg = await ctx.channel.send(content="Processing Image... Please wait",file=discord.File(buf, filename=result))
                temp_msgs.append(msg)
                processed_images.append(msg.attachments[0].url)
            else:
                processed_images.append(result)

        if ctx.message.reference:
            try:
                ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                for a in ref.attachments:
                    buf, result = await self.process_image(a.url)
                    if buf:
                        msg = await ctx.channel.send(content="Processing Image... Please wait",file=discord.File(buf, filename=result))
                        temp_msgs.append(msg)
                        processed_images.append(msg.attachments[0].url)
                    else:
                        processed_images.append(result)
                for embed in ref.embeds:
                    if embed.image and embed.image.url:
                        buf, result = await self.process_image(embed.image.url)
                        if buf:
                            msg = await ctx.channel.send(content="Processing Image... Please wait",file=discord.File(buf, filename=result))
                            temp_msgs.append(msg)
                            processed_images.append(msg.attachments[0].url)
                        else:
                            processed_images.append(result)
            except Exception as e:
                self.log.error(f"Failed fetching referenced message: {e}")

        if prompt and ctx.message.mentions:
            for user in ctx.message.mentions:
                avatar_url = user.display_avatar.with_format("png").with_size(1024).url
                buf, result = await self.process_image(avatar_url)
                if buf:
                    msg = await ctx.channel.send(content="Processing Image... Please wait",file=discord.File(buf, filename=result))
                    temp_msgs.append(msg)
                    processed_images.append(msg.attachments[0].url)
                else:
                    processed_images.append(result)
                prompt = prompt.replace(user.mention, "").strip()

        images = list(dict.fromkeys(processed_images))[:1] if processed_images else []
        prompt, duration = self.parse_prompt_and_duration(prompt or "", default_duration=8)
        async with ctx.typing():
            result, full_url = await self._pollinations_request(
                prompt=prompt or "",
                model="seedance",
                token=token,
                images=images if images else None,
                duration=duration,
                aspect_ratio="16:9",
            )
            if isinstance(result, bytes):
                # normal case: we got video bytes
                try:
                    await ctx.send(
                        file=discord.File(io.BytesIO(result), "seedance.mp4")
                    )
                except discord.HTTPException:
                    await ctx.send(
                        f"🎬 Your Seedance video is ready: [Here]({full_url})"
                    )
            elif isinstance(result, dict) and result.get("error"):
                # API returned an error, e.g., no credits
                embed = discord.Embed(
                    title="⚠️ Oops! Seedance Generation Failed",
                    description=(
                        "Something went wrong while generating your Seedance video.\n\n"
                        "**Error message:**\n"
                        f"```\n{result['error']['message']}\n```"
                        "**Possible reasons:**\n"
                        "• The generation service might be temporarily down.\n"
                        "• Your prompt might be invalid or too long.\n"
                        "• You might have run out of credits/pollen balance.\n\n"
                        "Please try again later or adjust your prompt."
                    ),
                    color=discord.Color.orange(),
                )
                await ctx.send(embed=embed)
            else:
                # fallback
                await ctx.send(f"🎬 Your Seedance video is ready: [Here]({full_url})")

            for m in temp_msgs:
                try:
                    await m.delete()
                except:
                    pass

    @commands.command(name="seedancepro")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.has_permissions(attach_files=True)
    async def seedancepro(self, ctx, *, prompt: str = None):
        if not prompt and not ctx.message.attachments and not ctx.message.reference:
            return await ctx.send("❌ Provide a prompt and/or images.")

        poll_keys = await self.bot.get_shared_api_tokens("pollinations")
        token = poll_keys.get("token") if poll_keys else None
        if not token:
            return await ctx.send("Missing Pollinations API token.")
        processed_images = []
        temp_msgs = []

        if prompt:
            # Extract URLs from the prompt
            url_regex = r"https?://\S+\.(?:png|jpg|jpeg|webp)"
            found_urls = re.findall(url_regex, prompt)
            for url in found_urls:
                buf, result = await self.process_image(url)
                if buf:
                    msg = await ctx.channel.send(
                        content="Processing Image... Please wait",
                        file=discord.File(buf, filename=result),
                    )
                    temp_msgs.append(msg)
                    processed_images.append(msg.attachments[0].url)
                else:
                    processed_images.append(result)
            # Remove URLs from prompt so Pollinations doesn't try to read them as text
            for url in found_urls:
                prompt = prompt.replace(url, "").strip()
        # a
        for a in ctx.message.attachments:
            buf, result = await self.process_image(a.url.rstrip("&"))
            if buf:
                msg = await ctx.channel.send(content="Processing Image... Please wait",file=discord.File(buf, filename=result))
                temp_msgs.append(msg)
                processed_images.append(msg.attachments[0].url)
            else:
                processed_images.append(result)

        if ctx.message.reference:
            try:
                ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                for a in ref.attachments:
                    buf, result = await self.process_image(a.url)
                    if buf:
                        msg = await ctx.channel.send(content="Processing Image... Please wait",file=discord.File(buf, filename=result))
                        temp_msgs.append(msg)
                        processed_images.append(msg.attachments[0].url)
                    else:
                        processed_images.append(result)
                for embed in ref.embeds:
                    if embed.image and embed.image.url:
                        buf, result = await self.process_image(embed.image.url)
                        if buf:
                            msg = await ctx.channel.send(content="Processing Image... Please wait",file=discord.File(buf, filename=result))
                            temp_msgs.append(msg)
                            processed_images.append(msg.attachments[0].url)
                        else:
                            processed_images.append(result)
            except Exception as e:
                self.log.error(f"Failed fetching referenced message: {e}")

        if prompt and ctx.message.mentions:
            for user in ctx.message.mentions:
                avatar_url = user.display_avatar.with_format("png").with_size(1024).url
                buf, result = await self.process_image(avatar_url)
                if buf:
                    msg = await ctx.channel.send(content="Processing Image... Please wait",file=discord.File(buf, filename=result))
                    temp_msgs.append(msg)
                    processed_images.append(msg.attachments[0].url)
                else:
                    processed_images.append(result)
                prompt = prompt.replace(user.mention, "").strip()

        images = list(dict.fromkeys(processed_images))[:1] if processed_images else []
        prompt, duration = self.parse_prompt_and_duration(prompt or "", default_duration=8)
        async with ctx.typing():
            result, full_url = await self._pollinations_request(
                prompt=prompt or "",
                model="seedance-pro",
                token=token,
                images=images if images else None,
                duration=duration,
                aspect_ratio="16:9",
            )
            if isinstance(result, bytes):
                # normal case: we got video bytes
                try:
                    await ctx.send(
                        file=discord.File(io.BytesIO(result), "seedancePro.mp4")
                    )
                except discord.HTTPException:
                    await ctx.send(
                        f"🎬 Your Seedance video is ready: [Here]({full_url})"
                    )
            elif isinstance(result, dict) and result.get("error"):
                # API returned an error, e.g., no credits
                embed = discord.Embed(
                    title="⚠️ Oops! Seedance Pro Generation Failed",
                    description=(
                        "Something went wrong while generating your Seedance video.\n\n"
                        "**Error message:**\n"
                        f"```\n{result['error']['message']}\n```"
                        "**Possible reasons:**\n"
                        "• The generation service might be temporarily down.\n"
                        "• Your prompt might be invalid or too long.\n"
                        "• You might have run out of credits/pollen balance.\n\n"
                        "Please try again later or adjust your prompt."
                    ),
                    color=discord.Color.orange(),
                )
                await ctx.send(embed=embed)
            else:
                # fallback
                await ctx.send(f"🎬 Your Seedance Pro video is ready: [Here]({full_url})")

            for m in temp_msgs:
                try:
                    await m.delete()
                except:
                    pass     



    @commands.command(name="wan")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.has_permissions(attach_files=True)
    async def wan(self, ctx, *, prompt: str = None):
        """Generate videos using Alibaba Wan 2.6 model.
        
        Supports text-to-video and image-to-video generation.
        
        Usage:
        !wan a girl dancing in a field
        !wan --resolution 720p --aspect_ratio 9:16 a vertical video of someone singing
        
        Parameters in prompt:
        --resolution: 720p or 1080p (default: 1080p)
        --aspect_ratio: 16:9 or 9:16 (default: 16:9)
        --negative_prompt: things to avoid in the video
        
        Image-to-video: attach an image and provide a prompt.
        Duration: automatically optimized (2-15 seconds).
        """
        if not prompt and not ctx.message.attachments and not ctx.message.reference:
            return await ctx.send("❌ Please provide a prompt and/or images.")

        poll_keys = await self.bot.get_shared_api_tokens("pollinations")
        token = poll_keys.get("token") if poll_keys else None
        if not token:
            return await ctx.send("❌ Missing Pollinations API token.")
        
        processed_images = []
        temp_msgs = []

        # Parse resolution from prompt
        resolution = "1080p"  # default
        resolution_match = re.search(r"--resolution\s+(720p|1080p)", prompt or "", re.IGNORECASE)
        if resolution_match:
            resolution = resolution_match.group(1).lower()
            prompt = re.sub(r"--resolution\s+(?:720p|1080p)", "", prompt or "", flags=re.IGNORECASE).strip()
        
        # Parse aspect ratio from prompt
        aspect_ratio = "16:9"  # default
        aspect_match = re.search(r"--aspect_ratio\s+(16:9|9:16)", prompt or "", re.IGNORECASE)
        if aspect_match:
            aspect_ratio = aspect_match.group(1)
            prompt = re.sub(r"--aspect_ratio\s+(?:16:9|9:16)", "", prompt or "", flags=re.IGNORECASE).strip()
        
        # Parse negative prompt
        negative_prompt = None
        neg_match = re.search(r"--negative_prompt\s+([^\-]+?)(?=--|$)", prompt or "", re.IGNORECASE)
        if neg_match:
            negative_prompt = neg_match.group(1).strip()
            prompt = re.sub(r"--negative_prompt\s+[^\-]+?(?=--|$)", "", prompt or "", flags=re.IGNORECASE).strip()
        
        # Parse seed from prompt
        seed = None
        seed_match = re.search(r"--seed\s+(\d+)", prompt or "", re.IGNORECASE)
        if seed_match:
            seed = int(seed_match.group(1))
            prompt = re.sub(r"--seed\s+\d+", "", prompt or "", flags=re.IGNORECASE).strip()
        else:
            seed = random.randint(0, 1000000)

        if prompt:
            # Extract URLs from the prompt
            url_regex = r"https?://\S+\.(?:png|jpg|jpeg|webp)"
            found_urls = re.findall(url_regex, prompt)
            for url in found_urls:
                buf, result = await self.process_image(url)
                if buf:
                    msg = await ctx.channel.send(
                        content="🔄 Processing image...",
                        file=discord.File(buf, filename=result),
                    )
                    temp_msgs.append(msg)
                    processed_images.append(msg.attachments[0].url)
                else:
                    processed_images.append(result)
            # Remove URLs from prompt
            for url in found_urls:
                prompt = prompt.replace(url, "").strip()
        
        # Process attachments
        for a in ctx.message.attachments:
            buf, result = await self.process_image(a.url.rstrip("&"))
            if buf:
                msg = await ctx.channel.send(content="🔄 Processing image...", file=discord.File(buf, filename=result))
                temp_msgs.append(msg)
                processed_images.append(msg.attachments[0].url)
            else:
                processed_images.append(result)

        # Process referenced message
        if ctx.message.reference:
            try:
                ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                for a in ref.attachments:
                    buf, result = await self.process_image(a.url)
                    if buf:
                        msg = await ctx.channel.send(content="🔄 Processing image...", file=discord.File(buf, filename=result))
                        temp_msgs.append(msg)
                        processed_images.append(msg.attachments[0].url)
                    else:
                        processed_images.append(result)
                for embed in ref.embeds:
                    if embed.image and embed.image.url:
                        buf, result = await self.process_image(embed.image.url)
                        if buf:
                            msg = await ctx.channel.send(content="🔄 Processing image...", file=discord.File(buf, filename=result))
                            temp_msgs.append(msg)
                            processed_images.append(msg.attachments[0].url)
                        else:
                            processed_images.append(result)
            except Exception as e:
                self.log.error(f"Failed fetching referenced message: {e}")

        # Process mentions
        if prompt and ctx.message.mentions:
            for user in ctx.message.mentions:
                avatar_url = user.display_avatar.with_format("png").with_size(1024).url
                buf, result = await self.process_image(avatar_url)
                if buf:
                    msg = await ctx.channel.send(content="🔄 Processing image...", file=discord.File(buf, filename=result))
                    temp_msgs.append(msg)
                    processed_images.append(msg.attachments[0].url)
                else:
                    processed_images.append(result)
                prompt = prompt.replace(user.mention, "").strip()

        # Get first image if available (Wan 2.6 supports image-to-video)
        images = list(dict.fromkeys(processed_images))[:1] if processed_images else []
        
        # Parse duration from prompt (Wan 2.6: 2-15 seconds, Pollinations optimizes automatically)
        prompt, duration = self.parse_prompt_and_duration(prompt or "", default_duration=5)
        
        async with ctx.typing():
            try:
                result, full_url = await self._pollinations_request(
                    prompt=prompt or "",
                    model="wan",
                    token=token,
                    images=images if images else None,
                    duration=duration,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    negative_prompt=negative_prompt,
                    seed=seed,
                )
                if isinstance(result, bytes):
                    # Got video bytes - try to send as file
                    try:
                        await ctx.send(
                            content="✨ Your Wan 2.6 video is ready!",
                            file=discord.File(io.BytesIO(result), "wan.mp4")
                        )
                    except discord.HTTPException:
                        # File too large, send link instead
                        await ctx.send(
                            f"✨ Your Wan 2.6 video is ready! [View Video]({full_url})"
                        )
                elif isinstance(result, dict) and result.get("error"):
                    # API returned an error
                    embed = discord.Embed(
                        title="⚠️ Wan 2.6 Generation Failed",
                        description=(
                            "Something went wrong while generating your video.\n\n"
                            "**Error message:**\n"
                            f"```\n{result['error'].get('message', 'Unknown error')}\n```\n"
                            "**Possible reasons:**\n"
                            "• The generation service might be temporarily down.\n"
                            "• Your prompt might be invalid or too long.\n"
                            "• You might have run out of credits/pollen balance.\n\n"
                            "Please try again later or adjust your prompt."
                        ),
                        color=discord.Color.orange(),
                    )
                    await ctx.send(embed=embed)
                else:
                    # Unexpected response format
                    await ctx.send(f"✨ Your Wan 2.6 video is ready! [View Video]({full_url})")
            except asyncio.TimeoutError:
                await ctx.send("⏱️ Request timed out. The video generation is taking longer than expected. Please try again later.")
            except Exception as e:
                self.log.error(f"Wan 2.6 generation error: {e}", exc_info=True)
                await ctx.send(f"❌ An unexpected error occurred: {type(e).__name__}")
            finally:
                # Clean up temporary messages
                for m in temp_msgs:
                    try:
                        await m.delete()
                    except:
                        pass     


    @commands.command()
    @commands.cooldown(3, 5, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def openai(self, ctx: commands.Context, *, query: str = None):
        """Query with `openai`."""
        await self._run_pollinations_text(ctx, "openai", query)

    @commands.command()
    @commands.cooldown(3, 5, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def openaifast(self, ctx: commands.Context, *, query: str = None):
        """Query with `openai-fast`."""
        await self._run_pollinations_text(ctx, "openai-fast", query)

    @commands.command()
    @commands.cooldown(3, 5, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def openailarge(self, ctx: commands.Context, *, query: str = None):
        """Query with `openai-large`."""
        await self._run_pollinations_text(ctx, "openai-large", query)

    @commands.command()
    @commands.cooldown(3, 5, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def qwencoder(self, ctx: commands.Context, *, query: str = None):
        """Query with `qwen-coder`."""
        await self._run_pollinations_text(ctx, "qwen-coder", query)

    @commands.command()
    @commands.cooldown(3, 5, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def mistral(self, ctx: commands.Context, *, query: str = None):
        """Query with `mistral`."""
        await self._run_pollinations_text(ctx, "mistral", query)

    @commands.command()
    @commands.cooldown(3, 5, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def mistralfast(self, ctx: commands.Context, *, query: str = None):
        """Query with `mistral-fast`."""
        await self._run_pollinations_text(ctx, "mistral-fast", query)

    @commands.command()
    @commands.cooldown(3, 5, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def deepseek(self, ctx: commands.Context, *, query: str = None):
        """Query with `deepseek`."""
        await self._run_pollinations_text(ctx, "deepseek", query)

    @commands.command()
    @commands.cooldown(3, 5, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def grok(self, ctx: commands.Context, *, query: str = None):
        """Query with `grok`."""
        await self._run_pollinations_text(ctx, "grok", query)

    @commands.command()
    @commands.cooldown(3, 5, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def claude(self, ctx: commands.Context, *, query: str = None):
        """Query with `claude`."""
        await self._run_pollinations_text(ctx, "claude", query)


    @commands.command()
    @commands.cooldown(3, 5, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def openaireasoning(self, ctx: commands.Context, *, query: str = None):
        """Query with `openai-reasoning`."""
        await self._run_pollinations_text(ctx, "openai-reasoning", query)

    @commands.command()
    @commands.cooldown(3, 5, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def gemini(self, ctx: commands.Context, *, query: str = None):
        """Query with `gemini`."""
        await self._run_pollinations_text(ctx, "gemini", query)

    @commands.command()
    @commands.cooldown(3, 5, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def geminisearch(self, ctx: commands.Context, *, query: str = None):
        """Query with `gemini-search`."""
        await self._run_pollinations_text(ctx, "gemini-search", query)

    @commands.command()
    @commands.cooldown(3, 5, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def midijourney(self, ctx: commands.Context, *, query: str = None):
        """Query with `midijourney`."""
        await self._run_pollinations_text(ctx, "midijourney", query)

    @commands.command()
    @commands.cooldown(3, 5, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def chickytutor(self, ctx: commands.Context, *, query: str = None):
        """Query with `chickytutor`."""
        await self._run_pollinations_text(ctx, "chickytutor", query)

    @commands.command()
    @commands.cooldown(3, 5, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def perplexityfast(self, ctx: commands.Context, *, query: str = None):
        """Query with `perplexity-fast`."""
        await self._run_pollinations_text(ctx, "perplexity-fast", query)

    @commands.command()
    @commands.cooldown(3, 5, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def perplexityreasoning(self, ctx: commands.Context, *, query: str = None):
        """Query with `perplexity-reasoning`."""
        await self._run_pollinations_text(ctx, "perplexity-reasoning", query)

    @commands.command()
    @commands.cooldown(3, 5, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def kimik2thinking(self, ctx: commands.Context, *, query: str = None):
        """Query with `kimi-k2-thinking`."""
        await self._run_pollinations_text(ctx, "kimi-k2-thinking", query)

    @commands.command(name="klein")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def klein(self, ctx: commands.Context, *, prompt: str = None):
        """
        Image Gen via klein pro model.
        Max size is 2048x2048
        Usage:
          [p]klein <prompt> [attach image(s), reply, mention, ID, or URL(s)]
          [p]klein <prompt> (text-only prompt is supported)
          Multiple images supported (comma-separated).
        """
        # Parse negative prompt if present in format --negative <text>
        negative_prompt = "worst quality, blurry"  # default negative prompt
        negative_match = re.search(r"--negative\s+([^\n]+)", prompt, re.IGNORECASE)
        if negative_match:
            negative_prompt = negative_match.group(1).strip()
            # Remove the --negative part from the prompt
            prompt = re.sub(
                r"--negative\s+[^\n]+", "", prompt, flags=re.IGNORECASE
            ).strip()

        # Parse height if present in format --height <number>
        height = 3072  # default height
        height_match = re.search(r"--height\s+(\d+)", prompt, re.IGNORECASE)
        if height_match:
            height = int(height_match.group(1))
            prompt = re.sub(r"--height\s+\d+", "", prompt, flags=re.IGNORECASE).strip()
        # Parse width if present in format --width <number>
        width = 5504  # default width
        width_match = re.search(r"--width\s+(\d+)", prompt, re.IGNORECASE)
        if width_match:
            width = int(width_match.group(1))
            prompt = re.sub(r"--width\s+\d+", "", prompt, flags=re.IGNORECASE).strip()

        # --- Parse --seed ---
        seed_match = re.search(r"--seed\s+(\d+)", prompt, re.IGNORECASE)
        if seed_match:
            seed = int(seed_match.group(1))
            prompt = re.sub(r"--seed\s+\d+", "", prompt, flags=re.IGNORECASE).strip()
        images = []
        if ctx.message.attachments:
            images.extend([a.url for a in ctx.message.attachments])
        if ctx.message.reference:
            try:
                referenced = await ctx.channel.fetch_message(
                    ctx.message.reference.message_id
                )
                if referenced.attachments:
                    images.extend([a.url for a in referenced.attachments])
                elif referenced.embeds:
                    for embed in referenced.embeds:
                        if embed.image and embed.image.url:
                            images.append(embed.image.url)
            except Exception:
                pass
        if prompt and ctx.message.mentions:
            for user in ctx.message.mentions:
                if hasattr(user, "display_avatar"):
                    images.append(
                        user.display_avatar.with_format("png").with_size(1024).url
                    )
                    # images.append(user.display_avatar.with_format("png").with_size(1024).url)
                else:
                    images.append(user.avatar_url)
                prompt = prompt.replace(user.mention, "").strip()
        if prompt:
            url_matches = re.findall(r"(https?://\S+)", prompt)
            for url in url_matches:
                images.append(url)
                prompt = prompt.replace(url, "").strip()
        if prompt:
            id_matches = re.findall(r"\b\d{17,20}\b", prompt)
            for mid in id_matches:
                user = ctx.guild.get_member(int(mid)) if ctx.guild else None
                if not user:
                    try:
                        user = await self.bot.fetch_user(int(mid))
                    except Exception:
                        user = None
                if user:
                    if hasattr(user, "display_avatar"):
                        # avatar_url = user.display_avatar.with_format("png").with_size(1024).url
                        images.append(user.display_avatar.with_format("png").with_size(1024).url)
                    else:

                        images.append(user.avatar_url)
                    prompt = prompt.replace(mid, "").strip()
        images = [
            (
                img.replace(".gif", ".png")
                if img.endswith(".gif") and "discordapp.com/avatars/" in img
                else img
            )
            for img in images
        ]
        seen = set()
        images = [x for x in images if not (x in seen or seen.add(x))]

        if not prompt:
            await ctx.send("❌ Please provide a prompt.")
            return

        seed = None
        if not seed:
            seed = random.randint(0, 1000000)
        await self._pollinations_generate(
            ctx,
            "klein",
            prompt or "",
            seed=seed,
            images=images if images else None,
            negative_prompt=negative_prompt,
            height=height,
            width=width,
        )

    @commands.command(name="kleinpro")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def kleinpro(self, ctx: commands.Context, *, prompt: str = None):
        """
        Image Gen via klein pro model.
        Max size is 2048x2048
        Usage:
          [p]kleinpro <prompt> [attach image(s), reply, mention, ID, or URL(s)]
          [p]kleinpro <prompt> (text-only prompt is supported)
          Multiple images supported (comma-separated).
        """
        # Parse negative prompt if present in format --negative <text>
        negative_prompt = "worst quality, blurry"  # default negative prompt
        negative_match = re.search(r"--negative\s+([^\n]+)", prompt, re.IGNORECASE)
        if negative_match:
            negative_prompt = negative_match.group(1).strip()
            # Remove the --negative part from the prompt
            prompt = re.sub(
                r"--negative\s+[^\n]+", "", prompt, flags=re.IGNORECASE
            ).strip()

        # Parse height if present in format --height <number>
        height = 3072  # default height
        height_match = re.search(r"--height\s+(\d+)", prompt, re.IGNORECASE)
        if height_match:
            height = int(height_match.group(1))
            prompt = re.sub(r"--height\s+\d+", "", prompt, flags=re.IGNORECASE).strip()
        # Parse width if present in format --width <number>
        width = 5504  # default width
        width_match = re.search(r"--width\s+(\d+)", prompt, re.IGNORECASE)
        if width_match:
            width = int(width_match.group(1))
            prompt = re.sub(r"--width\s+\d+", "", prompt, flags=re.IGNORECASE).strip()

        # --- Parse --seed ---
        seed_match = re.search(r"--seed\s+(\d+)", prompt, re.IGNORECASE)
        if seed_match:
            seed = int(seed_match.group(1))
            prompt = re.sub(r"--seed\s+\d+", "", prompt, flags=re.IGNORECASE).strip()
        images = []
        if ctx.message.attachments:
            images.extend([a.url for a in ctx.message.attachments])
        if ctx.message.reference:
            try:
                referenced = await ctx.channel.fetch_message(
                    ctx.message.reference.message_id
                )
                if referenced.attachments:
                    images.extend([a.url for a in referenced.attachments])
                elif referenced.embeds:
                    for embed in referenced.embeds:
                        if embed.image and embed.image.url:
                            images.append(embed.image.url)
            except Exception:
                pass
        if prompt and ctx.message.mentions:
            for user in ctx.message.mentions:
                if hasattr(user, "display_avatar"):
                    images.append(
                        user.display_avatar.with_format("png").with_size(1024).url
                    )
                    # images.append(user.display_avatar.with_format("png").with_size(1024).url)
                else:
                    images.append(user.avatar_url)
                prompt = prompt.replace(user.mention, "").strip()
        if prompt:
            url_matches = re.findall(r"(https?://\S+)", prompt)
            for url in url_matches:
                images.append(url)
                prompt = prompt.replace(url, "").strip()
        if prompt:
            id_matches = re.findall(r"\b\d{17,20}\b", prompt)
            for mid in id_matches:
                user = ctx.guild.get_member(int(mid)) if ctx.guild else None
                if not user:
                    try:
                        user = await self.bot.fetch_user(int(mid))
                    except Exception:
                        user = None
                if user:
                    if hasattr(user, "display_avatar"):
                        # avatar_url = user.display_avatar.with_format("png").with_size(1024).url
                        images.append(user.display_avatar.with_format("png").with_size(1024).url)
                    else:

                        images.append(user.avatar_url)
                    prompt = prompt.replace(mid, "").strip()
        images = [
            (
                img.replace(".gif", ".png")
                if img.endswith(".gif") and "discordapp.com/avatars/" in img
                else img
            )
            for img in images
        ]
        seen = set()
        images = [x for x in images if not (x in seen or seen.add(x))]

        if not prompt:
            await ctx.send("❌ Please provide a prompt.")
            return

        seed = None
        if not seed:
            seed = random.randint(0, 1000000)
        await self._pollinations_generate(
            ctx,
            "klein-large",
            prompt or "",
            seed=seed,
            images=images if images else None,
            negative_prompt=negative_prompt,
            height=height,
            width=width,
        )


    @commands.command(name="gemini25pro")
    @commands.cooldown(3, 5, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def gemini25pro(self, ctx: commands.Context, *, query: str = None):
        """Query with Google's latest Gemini 2.5 Pro model for advanced text generation.
        
        Parameters
        ----------
        ctx : commands.Context
            The command context.
        query : str, optional
            The text query or prompt.
        
        Notes
        -----
        - Cooldown: 3 uses per 5 seconds per guild.
        - Powered by Google Gemini 2.5 Pro via Pollinations.ai API.
        """
        await self._run_pollinations_text(ctx, "gemini-2.5-pro", query)

    @commands.command(name="nomnom")
    @commands.cooldown(3, 5, commands.BucketType.guild)
    @checks.bot_has_permissions(attach_files=True)
    async def nomnom(self, ctx: commands.Context, *, query: str = None):
        """Query with NomNom (alias: gemini-scrape) for web research, scraping, and crawling.
        
        Parameters
        ----------
        ctx : commands.Context
            The command context.
        query : str, optional
            The search query or URL to scrape/crawl.
        
        Notes
        -----
        - Cooldown: 3 uses per 5 seconds per guild.
        - Excellent for web research and scraping tasks.
        - Powered by Pollinations.ai API.
        """
        await self._run_pollinations_text(ctx, "nomnom", query)


class EditModal(ui.Modal):

    def __init__(
        self,
        cog,
        interaction: Interaction,
        model: str,
        prompt: str,
        seed: int,
        width: int = None,
        height: int = None,
        images: str = None,
    ):

        super().__init__(title="Edit Prompt & Seed")
        self.cog = cog
        self.interaction = interaction
        self.model = model
        self.seed = seed
        self.images = images
        self.width_input = width
        self.width = width
        self.height_input = height
        self.height = height
        self.prompt = prompt
        self.prompt_input = ui.TextInput(
            label="Prompt",
            placeholder="Enter a new prompt",
            style=discord.TextStyle.paragraph,
            default=prompt,
        )
        self.add_item(self.prompt_input)

        self.width_input = ui.TextInput(
            label="Width (optional)",
            placeholder="Enter a width or leave empty",
            style=discord.TextStyle.short,
            default=str(width) if width is not None else "",  # Fixed
        )
        self.add_item(self.width_input)

        self.height_input = ui.TextInput(
            label="Height (optional)",
            placeholder="Enter a height or leave empty",
            style=discord.TextStyle.short,
            default=str(height) if height is not None else "",  # Fixed
        )
        self.add_item(self.height_input)

        self.seed_input = ui.TextInput(
            label="Seed (optional)",
            placeholder="Enter a numeric seed or leave empty",
            style=discord.TextStyle.short,
            default=str(seed),
            required=False,
        )
        self.add_item(self.seed_input)

    async def on_submit(self, interaction: Interaction):
        new_prompt = self.prompt_input.value
        new_seed = self.seed
        new_width = self.width_input.value.strip() or None
        new_height = self.height_input.value.strip() or None
        new_images = self.images

        try:
            new_width = int(new_width) if new_width and new_width != "None" else None
            new_height = (
                int(new_height) if new_height and new_height != "None" else None
            )
        except ValueError:
            new_width = None
            new_height = None

        if self.seed_input.value.strip():
            try:
                new_seed = int(self.seed_input.value.strip())
            except ValueError:
                await interaction.response.send_message(
                    "Seed must be an integer. Using previous seed.", ephemeral=True
                )
                return
        # await interaction.response.send_message(
        #     f"Sending request to pollinations with values {{model: {self.model}, prompt: {new_prompt}, seed: {new_seed}, width: {new_width}, height: {new_height}, images: {new_images}}}",
        #     ephemeral=False,
        # )
        if not interaction.response.is_done():
            await interaction.response.defer()

        try:
            if self.model == "kontext" and self.image_url:
                await self.cog.img2img(
                    interaction, text=f"{new_prompt} {self.image_url}"
                )
            else:
                await self.cog._pollinations_generate(
                    interaction,
                    self.model,
                    new_prompt,
                    seed=new_seed,
                    width=new_width,
                    height=new_height,
                    images=new_images,
                )
        except Exception as e:
            self.cog.log.error(f"[EditModal Error] {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Something went wrong, try again.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "Something went wrong, try again.", ephemeral=True
                )
