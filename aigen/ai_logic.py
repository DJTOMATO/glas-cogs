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
    IMAGE_API_URL, TEXT_API_URL, AUDIO_API_URL, DEFAULT_NEGATIVE_PROMPT, 
    DEFAULT_WIDTH, DEFAULT_HEIGHT, MIN_PIXELS, KLEIN_LARGE_WIDTH, KLEIN_LARGE_HEIGHT,
    ACCOUNT_BALANCE_URL, ACCOUNT_USAGE_URL
)
from .utils import create_typing_and_send, create_image_embed, create_button_view, process_image

try:
    from gradio_client import Client
except ImportError:
    Client = None

def get_time_until_refill() -> str:
    """Calculates time remaining until the next hour."""
    now = datetime.datetime.utcnow()
    next_hour = (now + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    remaining = next_hour - now
    minutes, seconds = divmod(int(remaining.total_seconds()), 60)
    return f"{minutes}m {seconds}s"

async def send_insufficient_pollen_error(ctx_or_send, model: str, error_data: dict):
    """Sends a formatted embed for insufficient pollen balance."""
    message = error_data.get("error", {}).get("message", "Insufficient balance.")
    
    # Extract cost and balance from message like:
    # "This model costs ~0.1340 pollen per request, but your available balance is 0.0000."
    cost_match = re.search(r"costs ~?(\d+\.\d+)", message)
    balance_match = re.search(r"balance is (\d+\.\d+)", message)
    
    cost = cost_match.group(1) if cost_match else "N/A"
    current_balance = balance_match.group(1) if balance_match else "0.0000"
    
    refill_in = get_time_until_refill()
    
    embed = discord.Embed(
        title="⚠️ Insufficient Pollen",
        description=(
            f"You don't have enough pollen to use the `{model}` model right now.\n\n"
            f"**Your Balance:** {current_balance} Pollen\n"
            f"**Model Cost:** ~{cost} Pollen\n"
            f"**Next Refill In:** {refill_in}\n\n"
            "*Refills occur automatically every hour at :00.*"
        ),
        color=discord.Color.orange()
    )
    
    if callable(ctx_or_send):
        await ctx_or_send(embed=embed)
    else:
        await ctx_or_send.send(embed=embed)

async def send_generic_api_error(ctx_or_send, model: str, status: int, body: str = ""):
    """Sends a formatted embed for generic API errors (500, 502, 503, etc)."""
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
    
    if status == 502 or status == 503:
        description += "\n\n**Possible Reason:** The specific model generator is likely offline or restarting. Please try again in a few minutes or use a different model."
    elif status == 504:
        description += "\n\n**Possible Reason:** The request took too long to process. Try a shorter prompt or smaller dimensions."
    elif status == 429:
        description += "\n\n**Possible Reason:** You are sending requests too fast. Slow down and try again later."
    
    if body:
        # Try to parse json error message
        try:
            data = json.loads(body)
            if "error" in data and isinstance(data["error"], dict):
                msg = data["error"].get("message")
            else:
                msg = data.get("message")
            if msg:
                description += f"\n\n**Message:**\n```\n{msg}\n```"
        except:
            if len(body) < 500: # Don't dump huge HTML pages
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

async def get_detailed_pollen_footer(cog) -> str:
    """Creates a detailed footer string with balance, last cost, and refill time."""
    info = await get_pollen_info(cog)
    parts = []
    
    balance = info.get("balance")
    if balance is not None:
        try: parts.append(f"Balance: {float(balance):.4f}")
        except: parts.append(f"Balance: {balance}")
    
    cost = info.get("latest_cost")
    if cost is not None:
        try: parts.append(f"Cost: ${float(cost):.4f}")
        except: pass
        
    parts.append(f"Refill in: {get_time_until_refill()}")
    
    return " • ".join(parts)

async def get_pollen_info(cog) -> Dict[str, Any]:
    """Fetches pollen balance and recent usage info."""
    poll_keys = await cog.bot.get_shared_api_tokens("pollinations")
    # Try multiple common keys for the token
    token = poll_keys.get("token") or poll_keys.get("api_key") or poll_keys.get("key")
    
    if not token:
        cog.log.error("Pollen Info: Missing Pollinations API token in shared tokens.")
        return {"error": "Missing Pollinations API token. Use `[p]set api pollinations token,YOUR_KEY`"}

    headers = {"Authorization": f"Bearer {token}"}
    info = {}
    
    try:
        async with aiohttp.ClientSession() as session:
            # Get Balance
            async with session.get(ACCOUNT_BALANCE_URL, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    info["balance"] = data.get("balance")
                else:
                    body = await resp.text()
                    cog.log.error(f"Pollen Balance Error: {resp.status} - {body}")
                    info["balance_error"] = f"HTTP {resp.status}"

            # Get Usage (Recent)
            async with session.get(ACCOUNT_USAGE_URL, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    usage_list = data.get("usage", [])
                    info["usage"] = usage_list[:5] # Keep last 5
                    if usage_list:
                        info["latest_cost"] = usage_list[0].get("cost_usd")
                else:
                    body = await resp.text()
                    cog.log.error(f"Pollen Usage Error: {resp.status} - {body}")
                    info["usage_error"] = f"HTTP {resp.status}"
    except Exception as e:
        cog.log.error(f"Pollen Info Exception: {e}", exc_info=True)
        info["error"] = str(e)

    return info

async def pollinations_image_generate(
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
    """Handles image generation via Pollinations.ai"""
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

    pollinations_keys = await cog.bot.get_shared_api_tokens("pollinations")
    token = pollinations_keys.get("token") or pollinations_keys.get("api_key") or pollinations_keys.get("key")
    if not token:
        await send_func("Pollinations API token not set.")
        return

    # Scaling logic
    if width and height and width * height < MIN_PIXELS:
        scale = (MIN_PIXELS / (width * height)) ** 0.5
        width, height = int(width * scale), int(height * scale)

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

    encoded_prompt = quote(prompt, safe="")
    url = IMAGE_API_URL.format(prompt=encoded_prompt)
    headers = {"Authorization": f"Bearer {token}"}

    async with typing_cm:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        
                        embed = await create_image_embed(
                            title=f"AI Image - {model}",
                            prompt=prompt,
                            author=author,
                            params=params,
                            images=images
                        )
                        
                        # Add detailed balance info to footer
                        pollen_footer = await get_detailed_pollen_footer(cog)
                        readable_date = datetime.datetime.utcnow().strftime('%b %d, %Y, %I:%M %p')
                        
                        embed.set_footer(
                            text=f"Generated by {author} • {readable_date} • Powered by Pollinations.ai • {pollen_footer}"
                        )

                        async def regenerate_callback(interaction: discord.Interaction):
                            if interaction.user != author:
                                await interaction.response.send_message("You cannot use this button.", ephemeral=True)
                                return
                            await pollinations_image_generate(cog, interaction, model, prompt, random.randint(0, 1000000), width, height, images, negative_prompt)

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
                    elif response.status == 402:
                        try:
                            error_data = await response.json()
                        except Exception:
                            error_data = {"error": {"message": await response.text()}}
                        await send_insufficient_pollen_error(send_func, model, error_data)
                    else:
                        body = await response.text()
                        await send_generic_api_error(send_func, model, response.status, body)
        except Exception as e:
            cog.log.error(f"Image generation error: {e}", exc_info=True)
            await send_func(f"An error occurred: {e}")

async def pollinations_text_generate(
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
    """Handles text generation via Pollinations.ai"""
    referrer = await cog.config.referrer()
    if not referrer or referrer.lower() == "none":
        await ctx.send("⚠️ Pollinations referrer not set. Use `[p]settings referrer <your_referrer>`.")
        return

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
    
    poll_keys = await cog.bot.get_shared_api_tokens("pollinations")
    poll_token = poll_keys.get("token") or poll_keys.get("api_key") or poll_keys.get("key")

    if not poll_token:
        await ctx.send("❌ Missing Pollinations API token. Use `[p]set api pollinations token,<value>`")
        return

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": 1,
        "max_tokens": max_tokens,
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

    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(TEXT_API_URL, json=payload, headers=headers) as resp:
                    if resp.status == 402:
                        try:
                            error_data = await resp.json()
                        except Exception:
                            error_data = {"error": {"message": await resp.text()}}
                        await send_insufficient_pollen_error(ctx, model, error_data)
                        return
                    
                    if resp.status != 200:
                        body = await resp.text()
                        await send_generic_api_error(ctx, model, resp.status, body)
                        return
                    
                    data = await resp.json()
                    result = data["choices"][0]["message"]["content"]
                    
                    # Add detailed balance footer
                    pollen_footer_raw = await get_detailed_pollen_footer(cog)
                    balance_footer = f"\n\n*{pollen_footer_raw}*"

                    if custom_title or custom_footer:
                        # Use embeds if custom formatting is requested (like linkedin)
                        for i in range(0, len(result), 2000):
                            embed = discord.Embed(
                                title=custom_title or "AI Response",
                                description=result[i : i + 2000],
                                color=discord.Color.blue(),
                            )
                            if i + 2000 >= len(result):
                                embed.set_footer(text=(custom_footer or "Powered by Pollinations.ai") + " • " + pollen_footer_raw)
                            await ctx.send(embed=embed)
                    else:
                        if len(result) + len(balance_footer) > 2000:
                            fp = BytesIO((result + balance_footer).encode())
                            await ctx.send(file=discord.File(fp, filename="response.txt"))
                        else:
                            await ctx.send(result + balance_footer)
        except Exception as e:
            cog.log.error(f"Text generation error: {e}", exc_info=True)
            await ctx.send(f"❌ An unexpected error occurred: {type(e).__name__}")

async def pollinations_audio_generate(
    cog,
    ctx: discord.ext.commands.Context,
    model: str,
    prompt: str,
    duration: int = 30,
):
    """Handles audio generation via Pollinations.ai"""
    poll_keys = await cog.bot.get_shared_api_tokens("pollinations")
    token = poll_keys.get("token") or poll_keys.get("api_key") or poll_keys.get("key")
    if not token:
        await ctx.send("❌ Missing Pollinations API token.")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "input": prompt,
        "duration": duration,
        "instrumental": False,
    }

    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(AUDIO_API_URL, headers=headers, json=data) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        filename = prompt[:30].replace(' ', '_').replace(',', '').replace('.', '') + ".mp3"
                        if not filename: filename = "audio.mp3"
                        await ctx.send(file=discord.File(BytesIO(audio_data), filename=filename))
                    elif response.status == 402:
                        try:
                            error_data = await response.json()
                        except Exception:
                            error_data = {"error": {"message": await response.text()}}
                        await send_insufficient_pollen_error(ctx, model, error_data)
                    else:
                        body = await response.text()
                        await send_generic_api_error(ctx, model, response.status, body)
        except Exception as e:
            cog.log.error(f"Audio generation error: {e}", exc_info=True)
            await ctx.send(f"❌ An error occurred: {e}")

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
            # We'd need to fetch param names but let's simplify for brevity as in original
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
