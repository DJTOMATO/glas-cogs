import aiohttp
import discord
import json
import random
import logging
import datetime
import io
import re
import base64
import asyncio
from io import BytesIO
from urllib.parse import quote
from typing import Union, List, Optional, Dict, Any
from .constants import (
    DEFAULT_NEGATIVE_PROMPT, 
    DEFAULT_WIDTH, DEFAULT_HEIGHT, MIN_PIXELS, KLEIN_LARGE_WIDTH, KLEIN_LARGE_HEIGHT
)
from .utils import create_typing_and_send, create_image_embed, create_button_view, process_image

try:
    from gradio_client import Client
except ImportError:
    Client = None

async def send_generic_api_error(ctx_or_send, model: str, status: int, body: str = ""):
    """Sends a formatted embed for generic API errors."""
    error_titles = {
        500: "Internal Server Error",
        502: "Bad Gateway / Generator Offline",
        503: "Service Unavailable",
        504: "Gateway Timeout",
        400: "Bad Request / Invalid Parameters",
        429: "Too Many Requests / Rate Limited"
    }
    
    title = error_titles.get(status, f"API Error {status}")
    description = f"The API returned an error while processing your request for `{model}`."
    
    if body:
        try:
            data = json.loads(body)
            if "error" in data and isinstance(data["error"], dict):
                msg = data["error"].get("message")
            else:
                msg = data.get("message")
            if msg:
                description += f"\n\n**Message:**\n```\n{msg}\n```"
        except:
            if len(body) < 500:
                description += f"\n\n**Message:**\n```\n{body}\n```"

    embed = discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=discord.Color.red()
    )
    
    if callable(ctx_or_send):
        await ctx_or_send(embed=embed)
    else:
        await ctx_or_send.send(embed=embed)

async def fetch_jankrouter_models() -> List[Dict[str, Any]]:
    """Fetch the Jankrouter /v1/models list."""
    url = "https://jankrouter.waifly.com/v1/models"
    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("data", [])
    except Exception as e:
        pass
    return []

async def jankrouter_image_generate(
    cog,
    ctx: Union[discord.ext.commands.Context, discord.Interaction],
    model: str,
    prompt: str,
    seed: Optional[int] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    images: Optional[List[str]] = None,
    negative_prompt: Optional[str] = None,
):
    """Handles image generation via Jankrouter"""
    from .views import EditModal

    if negative_prompt is None:
        negative_prompt = DEFAULT_NEGATIVE_PROMPT
    
    if not width and not height:
        width, height = DEFAULT_WIDTH, DEFAULT_HEIGHT
    
    if model == "klein-large":
        width, height = KLEIN_LARGE_WIDTH, KLEIN_LARGE_HEIGHT

    if seed is None:
        seed = random.randint(0, 1000000)

    typing_cm, send_func = await create_typing_and_send(ctx)
    author = ctx.author if isinstance(ctx, discord.ext.commands.Context) else ctx.user

    # Scaling logic
    if width and height and width * height < MIN_PIXELS:
        scale = (MIN_PIXELS / (width * height)) ** 0.5
        width, height = int(width * scale), int(height * scale)

    async with typing_cm:
        try:
            jankrouter_url = "https://jankrouter.waifly.com/v1/images/generations"
            jankrouter_payload = {
                "model": model,
                "prompt": prompt,
                "size": f"{width}x{height}"
            }
            
            if images and len(images) > 0:
                jankrouter_url = "https://jankrouter.waifly.com/v1/images/edits"
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(images[0]) as resp:
                            if resp.status == 200:
                                img_bytes = await resp.read()
                                jankrouter_payload["image"] = base64.b64encode(img_bytes).decode('utf-8')
                except Exception as e:
                    cog.log.warning(f"Jankrouter image fetch failed: {e}")
                    
            max_retries = 3

                    
            for attempt in range(1, max_retries + 1):

                    
                connector = aiohttp.TCPConnector(ssl=False)

                    
                async with aiohttp.ClientSession(connector=connector) as session:

                    
                    async with session.post(jankrouter_url, json=jankrouter_payload, headers={"Content-Type": "application/json"}) as resp:

                    
                        if resp.status == 200:

                    
                            data = await resp.json()

                    
                            if "data" in data and len(data["data"]) > 0 and "b64_json" in data["data"][0]:

                    
                                b64_data = data["data"][0]["b64_json"]

                    
                                image_data = base64.b64decode(b64_data)

                    
                                break

                    
                            else:

                    
                                if attempt == max_retries:

                    
                                    await send_func("? Jankrouter returned an invalid response format.")

                    
                                    return

                    
                                await asyncio.sleep(2)

                    
                        else:

                    
                            if attempt < max_retries and resp.status in (500, 502, 503, 504):

                    
                                await asyncio.sleep(2)

                    
                                continue

                    
                            body = await resp.text()

                    
                            await send_generic_api_error(send_func, model, resp.status, body)

                    
                            return

            embed = await create_image_embed(
                title=f"AI Image - {model}",
                prompt=prompt,
                author=author,
                params={"width": width, "height": height, "seed": seed, "negative_prompt": negative_prompt},
                images=images
            )
            
            readable_date = datetime.datetime.utcnow().strftime('%b %d, %Y, %I:%M %p')
            embed.set_footer(text=f"Generated by {author} • {readable_date} • Powered by Jankrouter (waifly.com)")

            async def regenerate_callback(interaction: discord.Interaction):
                if interaction.user != author:
                    await interaction.response.send_message("You cannot use this button.", ephemeral=True)
                    return
                await jankrouter_image_generate(cog, interaction, model, prompt, random.randint(0, 1000000), width, height, images, negative_prompt)

            async def edit_callback(interaction: discord.Interaction):
                if interaction.user != author:
                    await interaction.response.send_message("You cannot use this button.", ephemeral=True)
                    return
                modal = EditModal(cog, interaction, model, prompt, seed, width, height, ",".join(images) if images else None)
                await interaction.response.send_modal(modal)

            async def delete_callback(interaction: discord.Interaction):
                if interaction.user != author:
                    await interaction.response.send_message("You cannot use this button.", ephemeral=True)
                    return
                await interaction.message.delete()

            view = await create_button_view(regenerate_callback, edit_callback, delete_callback)
            
            file = discord.File(BytesIO(image_data), filename="generated.png")
            await send_func(embed=embed, file=file, view=view)
        except Exception as e:
            cog.log.error(f"Image generation error: {e}", exc_info=True)
            await send_func(f"An error occurred: {e}")

async def jankrouter_text_generate(
    cog,
    ctx: discord.ext.commands.Context,
    model: str,
    query: Optional[str] = None,
    system_prompt: Optional[str] = None,
    custom_title: Optional[str] = None,
    custom_footer: Optional[str] = None,
    image_urls: Optional[List[str]] = None,
    temperature: float = 1.0,
    max_tokens: int = 4096,
):
    """Handles text generation via Jankrouter"""
    if not query and ctx.message and ctx.message.attachments:
        query = "Describe this image"
    if not query:
        await ctx.send("❌ Please provide a prompt or attach an image.")
        return

    if image_urls is None:
        image_urls = []
        if ctx.message:
            image_urls = [att.url for att in ctx.message.attachments if att.content_type and att.content_type.startswith("image/")]
    
    content_parts = [{"type": "text", "text": query}]
    for url in image_urls:
        content_parts.append({"type": "image_url", "image_url": {"url": url}})

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": content_parts})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": 1,
        "max_tokens": max_tokens,
        "stream": False,
    }

    headers = {
        "Content-Type": "application/json"
    }

    async with ctx.typing():
        try:
            url = "https://jankrouter.waifly.com/v1/chat/completions"

            max_retries = 3

            for attempt in range(1, max_retries + 1):

                connector = aiohttp.TCPConnector(ssl=False)

                async with aiohttp.ClientSession(connector=connector) as session:

                    async with session.post(url, json=payload, headers=headers) as resp:

                        if resp.status == 200:

                            data = await resp.json()

                            result = data["choices"][0]["message"]["content"]

                            break

                        else:

                            if attempt < max_retries and resp.status in (500, 502, 503, 504):

                                await asyncio.sleep(2)

                                continue

                            body = await resp.text()

                            await send_generic_api_error(ctx, model, resp.status, body)

                            return

                    if custom_title or custom_footer:
                        for i in range(0, len(result), 2000):
                            embed = discord.Embed(
                                title=custom_title or "AI Response",
                                description=result[i : i + 2000],
                                color=discord.Color.blue(),
                            )
                            if i + 2000 >= len(result):
                                embed.set_footer(text=(custom_footer or "Powered by Jankrouter (waifly.com)"))
                            await ctx.send(embed=embed)
                    else:
                        if len(result) > 2000:
                            fp = BytesIO(result.encode())
                            await ctx.send(file=discord.File(fp, filename="response.txt"))
                        else:
                            await ctx.send(result)
        except Exception as e:
            cog.log.error(f"Text generation error: {e}", exc_info=True)
            await ctx.send(f"❌ An unexpected error occurred: {type(e).__name__}")

async def jankrouter_audio_generate(
    cog,
    ctx: discord.ext.commands.Context,
    model: str,
    prompt: str,
    duration: int = 30,
):
    """Audio is currently unsupported on Jankrouter."""
    await ctx.send("❌ Audio generation is not currently supported on Jankrouter.")

async def hf_image_generate(
    cog, ctx, prompt, endpoint, model=None, api_name_override=None
):
    """Helper to generate an image from a Hugging Face gradio space endpoint."""
    if Client is None:
        return await ctx.send("❌ `gradio_client` is not installed.")

    api_key = (await cog.bot.get_shared_api_tokens("huggingface")).get("api_key")

    def extract_hf_space(endpoint):
        m = re.match(r"https?://huggingface.co/spaces/([^/]+)/([^/?#]+)", endpoint)
        if m: return f"{m.group(1)}/{m.group(2)}"
        m = re.match(r"https?://huggingface.co/([^/]+)/([^/?#]+)", endpoint)
        if m: return f"{m.group(1)}/{m.group(2)}"
        m = re.match(r"https?://([a-z0-9\-]+)\.hf\.space", endpoint)
        if m:
            sub = m.group(1)
            parts = sub.split("-", 1)
            if len(parts) == 2:
                org, space = parts
                return f"{org}/{space.replace('-', ' ').title().replace(' ', '-')}"
            return sub
        raise ValueError(f"Cannot extract Hugging Face space from endpoint: {endpoint}")

    async with ctx.typing():
        try:
            space = extract_hf_space(endpoint)
            client = await asyncio.get_running_loop().run_in_executor(
                None, lambda: Client(space, hf_token=api_key)
            )
            api_name = api_name_override or "/generate_image"
            
            # Predict
            predict_kwargs = {"api_name": api_name}
            predict_kwargs["prompt"] = prompt
            if model: predict_kwargs["model"] = model
            
            result = await asyncio.get_running_loop().run_in_executor(
                None, lambda: client.predict(**predict_kwargs)
            )
            
            image_bytes = None
            if isinstance(result, dict):
                if result.get("url"):
                    url = result["url"]
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as resp:
                            image_bytes = BytesIO(await resp.read())
                elif result.get("path"):
                    with open(result["path"], "rb") as f:
                        image_bytes = BytesIO(f.read())
            elif isinstance(result, str):
                if result.startswith("http"):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(result) as resp:
                            image_bytes = BytesIO(await resp.read())
                else:
                    with open(result, "rb") as f:
                        image_bytes = BytesIO(f.read())
            
            if image_bytes:
                image_bytes.seek(0)
                await ctx.send(file=discord.File(image_bytes, filename="image.png"))
            else:
                await ctx.send("❌ No image returned.")
        except Exception as e:
            cog.log.error(f"HF Generation error: {e}", exc_info=True)
            await ctx.send(f"❌ Error: {e}")

