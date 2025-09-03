import asyncio
import logging
from unittest import result
from gradio_client import Client, handle_file
import io, base64
from redbot.core import Config, commands
from redbot.core.bot import Red
import discord  # Added for File sending
import aiohttp
from discord import File
from io import BytesIO
from urllib.parse import quote, urlencode
import urllib
import random
import datetime
from discord import ui, Interaction, TextStyle, ButtonStyle
import json

log = logging.getLogger("red.glas-cogs-aigen")


class AiGen(commands.Cog):
    """A cog for generating images using various AI models."""

    __author__ = "[Glas](https://github.com/djtomato/glas-cogs)"
    __version__ = "0.0.1"

    def __init__(self, bot: Red):
        super().__init__()
        self.bot: Red = bot
        self.config = Config.get_conf(self, 117, force_registration=True)
        self.config.register_global(referrer="none")  # Default value
        self.log = logging.getLogger("glas.glas-cogs.aigen")

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

    async def _pollinations_generate(
        self,
        ctx: commands.Context | discord.Interaction,
        model: str,
        prompt: str,
        seed: int | None = None,  # New seed parameter
    ):
        start_time = discord.utils.utcnow()

        if seed is None:
            seed = random.randint(0, 1000000)

        # Determine send function and typing context
        if isinstance(ctx, commands.Context):
            typing_cm = ctx.typing()
            author_name = f"{ctx.author.name}#{ctx.author.discriminator}"

            async def send_func(*args, **kwargs):
                try:
                    await ctx.send(*args, **kwargs)
                except Exception:
                    # fallback if something goes wrong
                    try:
                        await ctx.send("Something went wrong, please try again.")
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
                    # Fallback ephemeral message
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
        # Call Pollinations API
        pollinations_keys = await self.bot.get_shared_api_tokens("pollinations")
        token = pollinations_keys.get("token")
        if not token:
            await send_func("Pollinations API token not set.")
            return

        params = {
            "width": 1024,
            "height": 1024,
            "seed": seed,
            "model": model,
            "nologo": "True",
            "private": "True",
            "enhance": "True",
        }
        encoded_prompt = quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        headers = {"Authorization": f"Bearer {token}"}

        async with typing_cm:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as resp:
                    if resp.status != 200:
                        await send_func(
                            f"Failed to fetch image: {resp.status} \n{await resp.text()}"
                        )
                        return
                    data = await resp.read()
                    file = BytesIO(data)
                    file.seek(0)

        time_taken = (discord.utils.utcnow() - start_time).total_seconds()
        embed = discord.Embed(title="🖼️ Image Generated Successfully")
        embed.set_image(url="attachment://generated.png")
        for key, value in params.items():
            if key.lower() not in ["private", "nologo", "referrer", "enhance"]:
                embed.add_field(name=key, value=f"```\n{value}\n```", inline=True)

        embed.add_field(name="Time Taken", value=f"```{time_taken:.2f} seconds```")
        embed.add_field(name="Prompt", value=f"```\n{prompt}\n```", inline=False)
        embed.set_footer(
            text=f"Generated by {author_name} • {datetime.datetime.utcnow().strftime('%m/%d/%Y %I:%M %p')} • Powered by Pollinations.ai"
        )

        view = discord.ui.View()
        regenerate_button = discord.ui.Button(
            label="Regenerate", style=discord.ButtonStyle.green
        )
        edit_button = discord.ui.Button(label="Edit", style=discord.ButtonStyle.blurple)
        delete_button = discord.ui.Button(label="Delete", style=discord.ButtonStyle.red)

        async def regenerate_callback(interaction: discord.Interaction):
            await interaction.response.defer()
            await self._pollinations_generate(interaction, model, prompt)

        async def edit_callback(interaction: discord.Interaction):
            current_seed = seed  # pass the current seed here
            current_prompt = prompt
            await interaction.response.send_modal(
                EditModal(
                    cog=self,
                    interaction=interaction,
                    model=model,
                    prompt=current_prompt,
                    seed=current_seed,
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

        await send_func(
            file=File(file, filename="generated.png"), embed=embed, view=view
        )

    async def callback(self, interaction: discord.Interaction):
        # Get the new prompt
        new_prompt = self.children[0].value
        # Regenerate the image with the new prompt
        await self._pollinations_generate(interaction, model, new_prompt)

    @commands.command(name="pflux")
    async def pflux(self, ctx: commands.Context, *, prompt: str):
        """Image Generation via Pollinations AI (flux model)."""
        words = prompt.split()
        seed = None

        # Check if the last word is numeric
        if words and words[-1].isdigit():
            seed = int(words[-1])
            # Remove the seed from the prompt
            words = words[:-1]
            prompt = " ".join(words)
        else:
            # Generate a random seed
            seed = random.randint(0, 1000000)

        await self._pollinations_generate(ctx, "flux", prompt, seed)

    @commands.command(name="pkontext")
    async def pkontext(self, ctx: commands.Context, *, prompt: str):
        """Image Generation via Pollinations AI (kontext model)."""
        words = prompt.split()
        seed = None

        # Check if the last word is numeric
        if words and words[-1].isdigit():
            seed = int(words[-1])
            # Remove the seed from the prompt
            words = words[:-1]
            prompt = " ".join(words)
        else:
            # Generate a random seed
            seed = random.randint(0, 1000000)

        await self._pollinations_generate(ctx, "kontext", prompt, seed)

    @commands.command(name="pturbo")
    async def pturbo(self, ctx: commands.Context, *, prompt: str):
        """Image Generation via Pollinations AI (turbo model)."""
        words = prompt.split()
        seed = None

        # Check if the last word is numeric
        if words and words[-1].isdigit():
            seed = int(words[-1])
            # Remove the seed from the prompt
            words = words[:-1]
            prompt = " ".join(words)
        else:
            # Generate a random seed
            seed = random.randint(0, 1000000)

        await self._pollinations_generate(ctx, "turbo", prompt, seed)

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

        # Extract org/space from endpoint
        def extract_hf_space(endpoint):
            import re

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
        # Try to get API info and parameter names
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
        # Handle result (url, base64, file, etc)
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
    async def hidream(self, ctx: commands.Context, *, prompt: str):
        """Image Generation using HiDream endpoint."""
        endpoint = "https://huggingface.co/spaces/HiDream-ai/HiDream-I1-Dev/"
        async with ctx.typing():
            await self._generate_hf_image(
                ctx, prompt, endpoint, api_name_override="/generate_with_status"
            )

    @commands.command()
    async def flux(self, ctx: commands.Context, *, prompt: str):
        """Image Generation using Fake-FLUX-Pro-Unlimited endpoint."""
        endpoint = "https://huggingface.co/spaces/llamameta/Fake-FLUX-Pro-Unlimited/"
        async with ctx.typing():
            await self._generate_hf_image(ctx, prompt, endpoint, model="flux")

    @commands.command()
    async def lumina(self, ctx: commands.Context, *, prompt: str):
        """Image Generation using NetaLumina_T2I_Playground endpoint."""
        endpoint = "https://huggingface.co/spaces/neta-art/NetaLumina_T2I_Playground/"
        async with ctx.typing():
            await self._generate_hf_image(ctx, prompt, endpoint)

    @commands.command()
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
            "model": "openai",
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
    async def img2img(self, ctx: commands.Context, *, text: str = None):
        """
        Multi-Image-to-Image generation via Pollinations AI (kontext model).
        Detects images from attachments, reply, mention, ID, or URL.
        Supports up to 3 images.
        Usage examples:
        !img2img put them together (with 2+ attachments)
        !img2img image1=https://example.com/1.png image2=https://example.com/2.png combine them
        !img2img add a background here @username
        !img2img enhance this 123456789012345678
        !img2img (reply to an image) stylize this
        """
        import re

        images = []
        prompt = text or ""

        # 1. Explicit image1=, image2=, image3= in text
        for i in range(1, 4):
            match = re.search(rf"image{i}=(\S+)", prompt)
            if match:
                images.append(match.group(1))
                prompt = prompt.replace(match.group(0), "").strip()

        # 2. Replied-to message
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

        # 3. Attachments in current message
        if ctx.message.attachments and len(images) < 3:
            images.extend([a.url for a in ctx.message.attachments[: 3 - len(images)]])

        # 4. Direct URLs inside message
        if len(images) < 3:
            urls = re.findall(r"(https?://\S+)", prompt)
            for url in urls:
                if len(images) >= 3:
                    break
                images.append(url)
                prompt = prompt.replace(url, "").strip()

        # 5. Mentioned users
        for mention in ctx.message.mentions:
            if len(images) >= 3:
                break
            images.append(mention.display_avatar.url)
            prompt = prompt.replace(mention.mention, "").strip()

        # 6. Numeric IDs
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

        # Error if no image found
        if not images:
            await ctx.send(
                "❌ Please provide 1–3 images (attachment, URL, mention, ID, or reply)."
            )
            return

        # Error if no prompt
        if not prompt:
            await ctx.send("❌ Please provide a prompt after the image(s).")
            return

        # Encode prompt + images
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
            "enhance": "True",
        }

        # Build URL with comma-delimited image list
        base_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        query_str = urlencode(query_params)
        full_url = f"{base_url}?{query_str}&image={images_param}"

        headers = {"Authorization": f"Bearer {token}"} if token else {}

        # Handle Context vs Interaction
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
                            error.add_field(
                                name="Technical details",
                                value=f"HTTP Status: `{resp.status}`\n```\n{full_url}\n```",
                                inline=False,
                            )
                            await send_func(embed=error)
                            return
                        # else: retry

        # Embed
        embed = discord.Embed(title="🖼️ Image Generated Successfully")
        embed.set_image(url="attachment://img2img.png")
        for key, value in query_params.items():
            if key.lower() not in ["private", "nologo", "referrer", "enhance"]:
                embed.add_field(name=key, value=f"```\n{value}\n```", inline=True)

        embed.add_field(name="Prompt", value=f"```\n{prompt}\n```", inline=False)
        embed.add_field(
            name="Images",
            value=" • ".join([f"[Image{i+1}]({url})" for i, url in enumerate(images)]),
            inline=False,
        )
        author = ctx.author if hasattr(ctx, "author") else ctx.user
        embed.set_footer(
            text=f"Generated by {author} • {datetime.datetime.utcnow().strftime('%m/%d/%Y %I:%M %p')} • Powered by Pollinations.ai"
        )

        # Buttons
        view = discord.ui.View()
        regenerate_button = discord.ui.Button(
            label="Regenerate", style=discord.ButtonStyle.green
        )
        edit_button = discord.ui.Button(label="Edit", style=discord.ButtonStyle.blurple)
        delete_button = discord.ui.Button(label="Delete", style=discord.ButtonStyle.red)

        async def regenerate_callback(interaction: discord.Interaction):
            await interaction.response.defer()
            # Pass same images again with prompt
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
                    image_url=",".join(images),  # Pass comma-delimited
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
    async def elixposearch(self, ctx: commands.Context, *, query: str):
        """
        Query the Elixposearch model at Pollinations with a text prompt.
        """
        ref = await self.config.referrer()
        if ref == "none":
            await ctx.send(
                "Pollinations referrer not set. Use `[p]referrer <your_referrer>` (bot owner only).\nObtain your referrer from https://auth.pollinations.ai/"
            )
            return
        # Base URL without parameters
        base_url = "https://text.pollinations.ai/"

        # URL-encode the user's query
        encoded_query = urllib.parse.quote(query)

        # Prepare headers and parameters
        headers = {}
        params = {"model": "elixposearch", "referrer": await self.config.referrer()}

        # Fetch API token and add it to headers if it exists
        pollinations_keys = await self.bot.get_shared_api_tokens("pollinations")
        poll_token = pollinations_keys.get("token") if pollinations_keys else None

        if poll_token:
            headers["Authorization"] = f"Bearer {poll_token}"
            # Add 'private=true' for authenticated requests
            params["private"] = "true"

        async with ctx.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    # Make the request using the base URL, encoded prompt, headers, and params
                    async with session.get(
                        f"{base_url}{encoded_query}", headers=headers, params=params
                    ) as resp:
                        body = await resp.text()

                        # Check for a successful response (HTTP 200)
                        if resp.status == 200:
                            # Use a consistent and clean output format
                            await ctx.send(f"{body[:2000]}")
                        else:
                            # Handle HTTP errors with a clear message
                            await ctx.send(
                                f"❌ **API Error:** Received HTTP {resp.status} status.\n"
                                f"```\n{body[:1000]}\n```"
                            )
            except aiohttp.ClientError as e:
                # Handle client-side request errors
                await ctx.send(
                    f"❌ **Request Failed:** An error occurred while contacting the API.\n`{e}`"
                )

    # This would be inside your Cog class
    @commands.command()
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
        # Base URL without parameters
        base_url = "https://text.pollinations.ai/"

        # URL-encode the user's query
        encoded_query = urllib.parse.quote(query)

        # Prepare headers and parameters
        headers = {}
        params = {"model": "geminisearch", "referrer": await self.config.referrer()}

        # Fetch API token and add it to headers if it exists
        pollinations_keys = await self.bot.get_shared_api_tokens("pollinations")
        poll_token = pollinations_keys.get("token") if pollinations_keys else None

        if poll_token:
            headers["Authorization"] = f"Bearer {poll_token}"
            # Add 'private=true' for authenticated requests
            params["private"] = "true"

        async with ctx.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    # Make the request using the base URL, encoded prompt, headers, and params
                    async with session.get(
                        f"{base_url}{encoded_query}", headers=headers, params=params
                    ) as resp:
                        body = await resp.text()

                        # Check for a successful response (HTTP 200)
                        if resp.status == 200:
                            # Use a consistent and clean output format
                            await ctx.send(f"{body[:2000]}")
                        else:
                            # Handle HTTP errors with a clear message
                            await ctx.send(
                                f"❌ **API Error:** Received HTTP {resp.status} status.\n"
                                f"```\n{body[:1000]}\n```"
                            )
            except aiohttp.ClientError as e:
                # Handle client-side request errors
                await ctx.send(
                    f"❌ **Request Failed:** An error occurred while contacting the API.\n`{e}`"
                )

    @commands.command()
    async def gpt5(self, ctx: commands.Context, *, query: str = None):
        """
        Query the GPT-5 Nano model at Pollinations with optional image input.
        Usage:
          [p]gpt5 <prompt> [attach image]
        Examples:
          [p]gpt5 Tell me a joke
          [p]gpt5 Describe this in detail (attach an image)
          [p]gpt5 (just attach an image)
        """
        MODEL_INFO = {
            "name": "gpt-5-nano",
            "description": "OpenAI GPT-5 Nano",
            "provider": "azure",
            "tier": "anonymous",
            "community": False,
            "aliases": ["gpt-5-nano"],
            "input_modalities": ["text", "image"],
            "output_modalities": ["text"],
            "tools": True,
            "vision": True,
            "audio": False,
        }

        # Referrer check
        referrer = await self.config.referrer()
        if not referrer or referrer.lower() == "none":
            await ctx.send(
                "⚠️ Pollinations referrer not set.\n"
                "Use `[p]referrer <your_referrer>` (bot owner only).\n"
                "Obtain your referrer from: <https://auth.pollinations.ai/>"
            )
            return

        # Default prompt if only image is given
        if not query and ctx.message.attachments:
            query = "Describe this image"
        if not query and not ctx.message.attachments:
            await ctx.send("❌ Please provide a prompt or attach an image.")
            return

        # Collect image URLs
        image_urls = []
        if ctx.message.attachments and "image" in MODEL_INFO["input_modalities"]:
            for attachment in ctx.message.attachments:
                if attachment.content_type and attachment.content_type.startswith(
                    "image/"
                ):
                    image_urls.append(attachment.url)

        # Prepare headers & params
        headers = {"Content-Type": "application/json"}
        params = {"model": MODEL_INFO["name"], "referrer": referrer}

        # Auth
        pollinations_keys = await self.bot.get_shared_api_tokens("pollinations")
        poll_token = pollinations_keys.get("token") if pollinations_keys else None
        if poll_token:
            headers["Authorization"] = f"Bearer {poll_token}"
            params["private"] = "true"

        # Build messages array in OpenAI-style format
        content_parts = [{"type": "text", "text": query}]
        for url in image_urls:
            content_parts.append({"type": "image_url", "image_url": {"url": url}})

        payload = {"messages": [{"role": "user", "content": content_parts}]}

        async with ctx.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://text.pollinations.ai/",
                        headers=headers,
                        params=params,
                        json=payload,
                    ) as resp:
                        text = await resp.text()

                        if resp.status == 200:
                            for i in range(0, len(text), 2000):
                                embed = discord.Embed(
                                    title="📡 GPT-5 Nano Response",
                                    description=text[i : i + 2000],
                                    color=discord.Color.blue(),
                                )
                                embed.set_footer(
                                    text=f"Model: {MODEL_INFO['name']} | Provider: {MODEL_INFO['provider']} | Powered by pollinations.ai"
                                )
                                await ctx.send(embed=embed)
                        else:
                            await ctx.send(
                                f"❌ **API Error:** HTTP {resp.status}\n"
                                f"```\n{text[:1000]}\n```"
                            )
            except aiohttp.ClientError as e:
                await ctx.send(f"❌ **Request Failed:** `{e}`")
            except Exception as e:
                await ctx.send(f"⚠️ **Unexpected Error:** `{type(e).__name__}: {e}`")


class EditModal(ui.Modal):
    def __init__(
        self,
        cog,
        interaction: Interaction,
        model: str,
        prompt: str,
        seed: int,
        image_url: str = None,
    ):
        super().__init__(title="Edit Prompt & Seed")
        self.cog = cog
        self.interaction = interaction
        self.model = model
        self.seed = seed
        self.image_url = image_url

        self.prompt_input = ui.TextInput(
            label="Prompt",
            placeholder="Enter a new prompt",
            style=discord.TextStyle.paragraph,
            default=prompt,
        )
        self.add_item(self.prompt_input)

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
        if self.seed_input.value.strip():
            try:
                new_seed = int(self.seed_input.value.strip())
            except ValueError:
                await interaction.response.send_message(
                    "Seed must be an integer. Using previous seed.", ephemeral=True
                )
                return

        if not interaction.response.is_done():
            await interaction.response.defer()

        try:
            # For img2img, pass image_url as part of the text argument
            if self.model == "kontext" and self.image_url:
                # Compose text as "prompt image_url"
                await self.cog.img2img(
                    interaction, text=f"{new_prompt} {self.image_url}"
                )
            else:
                await self.cog._pollinations_generate(
                    interaction, self.model, new_prompt, seed=new_seed
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
