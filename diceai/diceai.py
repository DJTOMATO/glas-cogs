import perchance as pc
import discord
from redbot.core import commands, app_commands, Config
from redbot.core.bot import Red
from redbot.core.data_manager import bundled_data_path
from typing import List, Optional
from datetime import datetime
import asyncio
from PIL import Image
import io
import argparse
from .styles import styles, shapes
import aiohttp

class NoExitParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


class PerChance(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot

    def parse_arguments(self, argument: str) -> dict:
        """Parse arguments for the perchance command."""
        argument = argument.replace("—", "--")

        parser = NoExitParser(add_help=False)
        parser.add_argument("prompt", type=str, nargs="*")
        parser.add_argument(
            "--negative", "--negative-prompt", type=str, default="", nargs="*"
        )
        parser.add_argument("--cfg-scale", type=float, default=7.0)
        parser.add_argument("--seed", type=int, default=-1)
        parser.add_argument(
            "--shape",
            type=str,
            choices=["portrait", "square", "landscape"],
            default="square",
        )
        parser.add_argument(
            "--style", type=str, choices=list(styles.keys()), default=None
        )

        try:
            values = vars(parser.parse_args(argument.split(" ")))

        except Exception:
            raise ValueError("Invalid arguments")

        if not values["prompt"]:
            raise ValueError("Prompt is required")

        values["prompt"] = " ".join(values["prompt"])
        values["negative"] = " ".join(values["negative"])

        if not 1 <= values["cfg_scale"] <= 30:
            raise ValueError("CFG scale must be between 1 and 30")

        return values

    # Create choices from styles
    style_choices = [app_commands.Choice(name=key, value=key) for key in styles.keys()]

    @app_commands.command(name="perchance")
    @app_commands.describe(
        prompt="The description of the image you want to generate",
        negative="Things you do NOT want to see in the image",
        seed="Seed for image generation to get reproducible results",
        shape="Shape of the image. Can be 'portrait', 'square', or 'landscape'",
        cfg_scale="Guidance scale for prompt accuracy, between 1 and 30",
        style="Style of the image",
    )
    async def perchance(
        self,
        interaction: discord.Interaction,
        prompt: str,
        negative: Optional[str],
        style: Optional[str],
        shape: Optional[str] = "square",
        seed: Optional[int] = -1,
        cfg_scale: Optional[float] = 7.0,
    ):
        """
        Generate an AI-generated image using a text prompt.

        Arguments:
        - <prompt>: The description of the image you want to generate.
        - --negative or --negative-prompt <negative_prompt>: Things you do NOT want to see in the image (optional).
        - --seed <seed>: Seed for image generation to get reproducible results (optional, default is -1 for random).
        - --shape <shape>: Shape of the image. Can be 'portrait', 'square', or 'landscape' (optional, default is 'square').
        - --cfg-scale <scale>: Guidance scale for prompt accuracy, between 1 and 30 (optional, default is 7.0).
        - --style <style>: Style of the image.
        """
         
        await visit_and_close_url("https://perchance.org/ai-text-to-image-generator")
        parsed_args = {
            "prompt": prompt,
            "negative": negative,
            "cfg_scale": cfg_scale,
            "seed": seed,
            "shape": shape,
            "style": style,
        }
        eprompt = parsed_args["prompt"]
        prompt = parsed_args["prompt"]
        enegative_prompt = parsed_args["negative"]
        negative_prompt = parsed_args["negative"]
        seed = parsed_args["seed"]
        shape = parsed_args["shape"]
        guidance_scale = parsed_args["cfg_scale"]
        style = parsed_args["style"]
        # print("test.", enegative_prompt)
        if style in styles:
            style_info = styles[style]
            prompt = style_info["prompt"].replace("[input.description]", prompt)
            negative_prompt = style_info["negative"].replace(
                "[input.negative]", negative_prompt or ""
            )

        # description = (
        #     f"{interaction.user.mention} your image is ready!\n\nPrompt: {eprompt}"
        # )
        description = f"Prompt: {eprompt}"
        if style:
            description += f"\nStyle: {style}"
        if enegative_prompt:
            description += f"\nNegative Prompt: {enegative_prompt}"

        if seed != -1:
            description += f"\nSeed: {seed}"
        if shape:
            description += f"\nShape: {shape}"
        if guidance_scale != 7.0:
            description += f"\nGuidance Scale: {guidance_scale}"

        await interaction.response.defer(thinking=True)

        async with interaction.channel.typing():
            retries = 5
            delay = 3
            for attempt in range(retries):
                try:
                    gen = pc.ImageGenerator()
                    async with await gen.image(
                        prompt,
                        negative_prompt=negative_prompt,
                        seed=seed,
                        shape=shape,
                        guidance_scale=guidance_scale,
                    ) as result:
                        binary = await result.download()

                        # Debug step: Check if binary data is valid
                        if binary is None:
                            raise ValueError("Received empty binary data")

                        try:
                            image = Image.open(binary)
                        except Exception as e:
                            await interaction.followup.send(f"Error opening image: {e}")
                            return

                        image_buffer = io.BytesIO()
                        image.save(image_buffer, format="PNG")
                        image_buffer.seek(0)  # Rewind the buffer to the beginning
                        em = discord.Embed(description=description)
                        em.color = discord.Color(8599000)
                        em.timestamp = datetime.now()
                        file = discord.File(fp=image_buffer, filename="image.png")
                        em.set_image(url="attachment://image.png")


                        await interaction.followup.send(
                            content=f"{interaction.user.mention}, here is your generated image!",
                            file=file,
                            embed=em,
                        )
                        return

                except pc.errors.ConnectionError as e:
                    if attempt < retries - 1:
                        await asyncio.sleep(delay)  # Wait before retrying
                        delay *= 2  # Exponential backoff
                    else:
                        await interaction.followup.send(
                            f"Perchance API overloaded. Please try again in a few minutes.\n{e}"
                        )

                except ValueError as e:
                    await interaction.followup.send(f"ValueError: {e}")
                    return

                except Exception as e:
                    await interaction.followup.send(
                        f"An unexpected error occurred. Please try again later.\n{e}"
                    )
                    return

    @perchance.autocomplete("style")
    async def character_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        if not current:
            results = styles.keys()
        else:
            results = [
                ch for ch in styles.keys() if ch.lower().startswith(current.lower())
            ]
            results += [ch for ch in styles.keys() if current.lower() in ch[1:].lower()]

        return [app_commands.Choice(name=ch, value=ch) for ch in results][:25]

    @perchance.autocomplete("shape")
    async def shape_autocomplete(self, interaction: discord.Interaction, current: str):
        if not current:
            results = shapes
        else:
            results = [ch for ch in shapes if ch.lower().startswith(current.lower())]
            results += [ch for ch in shapes if current.lower() in ch[1:].lower()]

        return [app_commands.Choice(name=ch, value=ch) for ch in results][:25]

async def visit_and_close_url(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            await response.text()  # Wait for the page to load