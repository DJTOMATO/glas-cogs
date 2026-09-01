import discord
from discord import ui, Interaction
import logging
from typing import Optional, Union

class EditModal(ui.Modal):
    def __init__(
        self,
        cog,
        interaction: Interaction,
        model: str,
        prompt: str,
        seed: int,
        width: Optional[int] = None,
        height: Optional[int] = None,
        images: Optional[str] = None,
    ):
        super().__init__(title="Edit Prompt & Seed")
        self.cog = cog
        self.interaction = interaction
        self.model = model
        self.seed = seed
        self.images = images
        self.width = width
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
            default=str(width) if width is not None else "",
        )
        self.add_item(self.width_input)

        self.height_input = ui.TextInput(
            label="Height (optional)",
            placeholder="Enter a height or leave empty",
            style=discord.TextStyle.short,
            default=str(height) if height is not None else "",
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
        new_width_val = self.width_input.value.strip() or None
        new_height_val = self.height_input.value.strip() or None
        new_images = self.images

        try:
            new_width = int(new_width_val) if new_width_val and new_width_val != "None" else None
            new_height = (
                int(new_height_val) if new_height_val and new_height_val != "None" else None
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

        if not interaction.response.is_done():
            await interaction.response.defer()

        try:
            # Note: self.cog refers to the AiGen cog instance
            # Use the unified image generation handler for all cases
            await self.cog.handle_image_generation(
                interaction,
                self.model,
                new_prompt,
                seed=new_seed,
                width=new_width,
                height=new_height,
                images=new_images.split(",") if new_images else None
            )
        except Exception as e:
            logging.getLogger("red.glas-cogs.aigen").error(f"[EditModal Error] {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Something went wrong, try again.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "Something went wrong, try again.", ephemeral=True
                )
