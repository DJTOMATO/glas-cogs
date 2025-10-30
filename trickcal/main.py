from redbot.core import commands
import discord
from pathlib import Path
from PIL import Image
import random
import json
import io
from redbot.core.data_manager import bundled_data_path
from discord import app_commands

class Trickcal(commands.Cog):
    """Generate random Trick avatars"""

    def __init__(self, bot):
        self.bot = bot
        self.design_folder = Path(self.bundled_data_path()) / "design"
        self.coord_file = Path(self.bundled_data_path()) / "data.json"
        self.coordinates = self.load_coordinates()

        self.character_heads = {
            "kommy": 1,
            "rin": 2,
            "butter": 3,
            "meluna": 4,
            "gabia": 5,
            "ui": 6,
            "tig": 7,
            "yumimi": 8,
            "diana": 9,
            "ashur": 20,
            "elena": 18,
            "posher": 11,
            "naia": 16,
            "levi": 12,
            "patula": 10,
            "mayo": 13,
            "marie": 14,
            "erpin": 21,
            "aya": 15,
            "rohne": 17,
            "goldy": 19,
        }

    def bundled_data_path(self):
        return Path(f"{bundled_data_path(self)}")

    def load_coordinates(self):
        if not self.coord_file.exists():
            raise FileNotFoundError(f"Coordinate file not found: {self.coord_file}")
        with open(self.coord_file, "r") as f:
            return json.load(f)

    def get_available_assets(self):
        available = {}
        for layer_id in range(1, 8):
            layer_folder = self.design_folder / str(layer_id)
            if layer_folder.exists():
                png_files = list(layer_folder.glob("*.png"))
                asset_numbers = []
                for png in png_files:
                    try:
                        num = int(png.stem)
                        asset_numbers.append(num)
                    except ValueError:
                        continue
                available[layer_id] = sorted(asset_numbers)
            else:
                available[layer_id] = []
        return available

    def get_coordinates(self, layer_id, asset_num):
        layer_key = str(layer_id)
        if layer_key not in self.coordinates:
            return None
        assets = self.coordinates[layer_key]
        if asset_num < 1 or asset_num > len(assets):
            return None
        idx = asset_num - 1
        if idx >= len(assets):
            return None
        return assets[idx]

    def generate_random_selection(self, available_assets, fixed_head=None):
        selections = []
        for layer_id in range(1, 8):
            if layer_id == 1 and fixed_head is not None:
                selections.append(fixed_head)
                continue
            if available_assets[layer_id]:
                selections.append(random.choice(available_assets[layer_id]))
            else:
                selections.append(0)
        return selections

    def create_avatar(self, layer_selections):
        canvas = Image.new("RGBA", (265, 265), (0, 0, 0, 0))
        layer_order = [6, 1, 5, 2, 3, 4, 7]

        exclusive_accessories = {76, 66, 57, 69, 65, 53, 47, 33, 32, 56, 27, 7, 1, 16}

        for layer_idx in layer_order:
            asset_num = layer_selections[layer_idx - 1]
            if layer_idx == 7 and random.random() < 0.50:  # 50% chance (adjust as desired)
                continue
            if asset_num == 0:
                continue

            if layer_idx == 5:
                accessory_choices = [asset_num]
                base_is_exclusive = asset_num in exclusive_accessories
                if not base_is_exclusive and random.random() < 0.1:
                    accessory_dir = self.design_folder / "5"
                    available = [
                        int(f.stem)
                        for f in accessory_dir.glob("*.png")
                        if f.stem.isdigit()
                    ]
                    available = [
                        x
                        for x in available
                        if x != asset_num and x not in exclusive_accessories
                    ]
                    if available:
                        extra_count = random.randint(1, 2)
                        extras = random.sample(
                            available, min(extra_count, len(available))
                        )
                        accessory_choices.extend(extras)

                for acc_num in accessory_choices:
                    self._paste_layer(canvas, layer_idx, acc_num)
                continue

            self._paste_layer(canvas, layer_idx, asset_num)

        return canvas

    def _paste_layer(self, canvas, layer_idx, asset_num):
        asset_path = self.design_folder / str(layer_idx) / f"{asset_num}.png"
        if not asset_path.exists():
            return
        coords = self.get_coordinates(layer_idx, asset_num)
        if coords is None:
            return
        if layer_idx == 7:
            coords["left"] += random.randint(-5, 5)
            coords["top"] += random.randint(2, 7)
        try:
            asset_img = Image.open(asset_path).convert("RGBA")
            asset_img = asset_img.resize(
                (coords["width"], coords["height"]), Image.LANCZOS
            )
            canvas.paste(asset_img, (coords["left"], coords["top"]), asset_img)
        except Exception:
            pass

    def create_avatar_grid(self, grid_size, fixed_head=None):
        available_assets = self.get_available_assets()
        cell = 265
        grid_px = cell * grid_size
        grid_image = Image.new("RGBA", (grid_px, grid_px), (0, 0, 0, 0))
        for y in range(grid_size):
            for x in range(grid_size):
                selections = self.generate_random_selection(
                    available_assets, fixed_head=fixed_head
                )
                avatar_img = self.create_avatar(selections)
                grid_image.paste(avatar_img, (x * cell, y * cell), avatar_img)
        return grid_image

    async def send_avatar_embed(self, ctx, grid_size=1, character_name=None):
        if grid_size < 1 or grid_size > 8:
            await ctx.send("Grid size must be between 1 and 8.")
            return

        fixed_head = None
        title = "✨ Here's your Cheek!"

        if character_name:
            char_key = character_name.lower()
            if char_key in self.character_heads:
                fixed_head = self.character_heads[char_key]
                title = f"✨ {character_name.capitalize()}'s Cheeks!"
            else:
                await ctx.send(f"Unknown character name: `{character_name}`")
                return

        avatar_img = self.create_avatar_grid(grid_size, fixed_head=fixed_head)
        with io.BytesIO() as image_binary:
            avatar_img.save(image_binary, "PNG")
            image_binary.seek(0)
            file = discord.File(fp=image_binary, filename="trick_avatar.png")
            embed = discord.Embed(color=discord.Color.random())
            if grid_size == 1:
                embed.title = (
                    f"✨ {character_name.capitalize()}'s Cheek!"
                    if character_name
                    else "✨ Here's your Cheek!"
                )
            else:
                embed.title = (
                    f"✨ {character_name.capitalize()}'s {grid_size}x{grid_size} Cheeks!"
                    if character_name
                    else f"✨ Here's your {grid_size}x{grid_size} Cheeks!"
                )
            embed.set_image(url="attachment://trick_avatar.png")
            embed.set_footer(text="Play Trickcal!")
            await ctx.send(embed=embed, file=file)

    async def character_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
      
        names = [name.capitalize() for name in self.character_heads.keys()]
        return [
            app_commands.Choice(name=n, value=n)
            for n in names
            if current.lower() in n.lower()
        ][
            :25
        ]  

    @commands.hybrid_command(
        name="trick",
        description="Generate Trick avatars in a grid (e.g., !trick 3 Mayo = 3x3 Mayo grid)",
    )
    @app_commands.autocomplete(character_name=character_autocomplete)
    async def trick(self, ctx, grid_size: int = 1, character_name: str = None):
        """Generate a grid of random Trick avatars.
        Example: !trick 4 or !trick 8 Mayo
        """
        async with ctx.typing():
            await self.send_avatar_embed(
                ctx, grid_size=grid_size, character_name=character_name
            )

    @commands.hybrid_command(
        name="trickchars", description="Show all available Trick characters."
    )
    async def trickchars(self, ctx):
        """List all available Trick characters."""
        char_list = ", ".join(name.capitalize() for name in self.character_heads.keys())
        embed = discord.Embed(
            title="🎨 Available Trick Characters",
            description=char_list,
            color=discord.Color.blurple(),
        )
        embed.set_footer(
            text="Use !trick <size> <name> to pick one! Example: !trick 4 Mayo"
        )
        await ctx.send(embed=embed)
