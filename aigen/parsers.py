import re
import random
import discord
from typing import List, Tuple, Optional, Dict, Any
from .constants import DEFAULT_NEGATIVE_PROMPT

class PromptParser:
    @staticmethod
    def parse_image_params(prompt: str, default_width: int = 1024, default_height: int = 1024) -> Dict[str, Any]:
        """
        Parses image generation parameters from a prompt string.
        Extracts: --negative, --width, --height, --seed and positional seed.
        """
        params = {
            "prompt": prompt,
            "negative_prompt": DEFAULT_NEGATIVE_PROMPT,
            "width": default_width,
            "height": default_height,
            "seed": None
        }

        # Parse negative prompt
        negative_match = re.search(r"--negative\s+([^\n]+)", params["prompt"], re.IGNORECASE)
        if negative_match:
            params["negative_prompt"] = negative_match.group(1).strip()
            params["prompt"] = re.sub(r"--negative\s+[^\n]+", "", params["prompt"], flags=re.IGNORECASE).strip()

        # Parse height
        height_match = re.search(r"--height\s+(\d+)", params["prompt"], re.IGNORECASE)
        if height_match:
            params["height"] = int(height_match.group(1))
            params["prompt"] = re.sub(r"--height\s+\d+", "", params["prompt"], flags=re.IGNORECASE).strip()

        # Parse width
        width_match = re.search(r"--width\s+(\d+)", params["prompt"], re.IGNORECASE)
        if width_match:
            params["width"] = int(width_match.group(1))
            params["prompt"] = re.sub(r"--width\s+\d+", "", params["prompt"], flags=re.IGNORECASE).strip()

        # Parse --seed
        seed_match = re.search(r"--seed\s+(\d+)", params["prompt"], re.IGNORECASE)
        if seed_match:
            params["seed"] = int(seed_match.group(1))
            params["prompt"] = re.sub(r"--seed\s+\d+", "", params["prompt"], flags=re.IGNORECASE).strip()
        else:
            # Fallback to positional seed at the end of prompt
            words = params["prompt"].split()
            if words and words[-1].isdigit():
                params["seed"] = int(words[-1])
                params["prompt"] = " ".join(words[:-1])

        if params["seed"] is None:
            params["seed"] = random.randint(0, 1000000)

        return params

class ImageExtractor:
    @staticmethod
    async def extract_images(ctx: Any, prompt: str = "") -> Tuple[List[str], str]:
        """
        Extracts image URLs from attachments, replies, and URLs in the prompt.
        """
        images = []
        cleaned_prompt = prompt

        # 1. Check attachments in current message
        if hasattr(ctx, 'message') and ctx.message.attachments:
            images.extend([a.url for a in ctx.message.attachments if a.content_type and a.content_type.startswith("image/")])

        # 2. Check referenced message (reply)
        if hasattr(ctx, 'message') and ctx.message.reference:
            try:
                # Handle both Context and Interaction if needed, but Context has message.reference
                referenced = ctx.message.reference.resolved
                if not referenced and hasattr(ctx.channel, 'fetch_message'):
                    referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                
                if referenced:
                    if referenced.attachments:
                        images.extend([a.url for a in referenced.attachments if a.content_type and a.content_type.startswith("image/")])
                    if referenced.embeds:
                        for embed in referenced.embeds:
                            if embed.image and embed.image.url:
                                images.append(embed.image.url)
            except Exception:
                pass

        # 3. Check for explicit image URLs in prompt (image1=URL, etc.)
        for i in range(1, 4):
            match = re.search(rf"image{i}=(\S+)", cleaned_prompt)
            if match:
                images.append(match.group(1))
                cleaned_prompt = cleaned_prompt.replace(match.group(0), "").strip()

        # 4. Check for general URLs in prompt if we don't have enough images
        if len(images) < 3:
            urls = re.findall(r"(https?://\S+)", cleaned_prompt)
            for url in urls:
                if len(images) >= 3:
                    break
                if url not in images:
                    images.append(url)
                    # We might not want to remove these from prompt as they might be part of the prompt
                    # but usually in img2img they are just the image source.

        return images[:3], cleaned_prompt
