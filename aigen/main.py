import asyncio
import logging
from gradio_client import Client
import io, base64
from redbot.core import Config, commands
from redbot.core.bot import Red
import discord  # Added for File sending
import aiohttp
from discord import File
from io import BytesIO
from urllib.parse import quote

log = logging.getLogger("red.glas-cogs-aigen")


class AiGen(commands.Cog):
    """A cog for generating images using various AI models."""

    __author__ = "[Glas](https://github.com/djtomato/glas-cogs)"
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

    async def _pollinations_generate(
        self, ctx: commands.Context, model: str, prompt: str
    ):
        pollinations_keys = await self.bot.get_shared_api_tokens("pollinations")
        token = pollinations_keys.get("token")
        if not token:
            await ctx.send(
                "Pollinations API token not set. Use `[p]set api pollinations token,<token>` (bot owner only)."
            )
            return
        params = {
            "width": 1024,
            "height": 1024,
            "seed": 43,
            "model": model,
            "nologo": "True",
            "private": "True",
            "enhance": "True",  # Enhance the image quality
        }
        encoded_prompt = quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        headers = {"Authorization": f"Bearer {token}"}
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as resp:
                    if resp.status != 200:
                        await ctx.send(f"Failed to fetch image: {resp.status}")
                        return
                    data = await resp.read()
                    file = BytesIO(data)
                    file.seek(0)
                    await ctx.send(file=File(file, filename="generated.png"))

    @commands.command(name="pflux")
    async def pflux(self, ctx: commands.Context, *, prompt: str):
        """Image Generation via Pollinations AI (flux model)."""
        await self._pollinations_generate(ctx, "flux", prompt)

    @commands.command(name="pkontext")
    async def pkontext(self, ctx: commands.Context, *, prompt: str):
        """Image Generation via Pollinations AI (kontext model)."""
        await self._pollinations_generate(ctx, "kontext", prompt)

    @commands.command(name="pturbo")
    async def pturbo(self, ctx: commands.Context, *, prompt: str):
        """Image Generation via Pollinations AI (turbo model)."""
        await self._pollinations_generate(ctx, "turbo", prompt)

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
