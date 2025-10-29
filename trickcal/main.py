from redbot.core import commands
import discord
from pathlib import Path
from PIL import Image
import random
import json
import io
from redbot.core.data_manager import bundled_data_path


class Trickcal(commands.Cog):
    """Generate random Trick avatars"""

    def __init__(self, bot):
        self.bot = bot
        self.design_folder = Path(self.bundled_data_path()) / "design"
        self.coord_file = Path(self.bundled_data_path()) / "data.json"
        self.coordinates = self.load_coordinates()

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

    def generate_random_selection(self, available_assets):
        selections = []
        for layer_id in range(1, 8):
            if available_assets[layer_id]:
                selections.append(random.choice(available_assets[layer_id]))
            else:
                selections.append(0)
        return selections

    def create_avatar(self, layer_selections):
        canvas = Image.new("RGBA", (265, 265), (0, 0, 0, 0))
        layer_order = [6, 1, 5, 2, 3, 4, 7]
        for layer_idx in layer_order:
            asset_num = layer_selections[layer_idx - 1]
            if asset_num == 0:
                continue
            asset_path = self.design_folder / str(layer_idx) / f"{asset_num}.png"
            if not asset_path.exists():
                continue
            coords = self.get_coordinates(layer_idx, asset_num)
            if coords is None:
                continue
            if layer_idx == 7:
                coords["left"] += random.randint(-5, 5)
                coords["top"] += random.randint(20, 30)
            try:
                asset_img = Image.open(asset_path).convert("RGBA")
                asset_img = asset_img.resize(
                    (coords["width"], coords["height"]), Image.LANCZOS
                )
                canvas.paste(asset_img, (coords["left"], coords["top"]), asset_img)
            except Exception:
                continue
        return canvas

    def create_avatar_grid(self, grid_size):
        available_assets = self.get_available_assets()
        # Make grid_size x grid_size avatars
        cell = 265
        grid_px = cell * grid_size
        grid_image = Image.new("RGBA", (grid_px, grid_px), (0, 0, 0, 0))
        for y in range(grid_size):
            for x in range(grid_size):
                selections = self.generate_random_selection(available_assets)
                avatar_img = self.create_avatar(selections)
                grid_image.paste(avatar_img, (x * cell, y * cell), avatar_img)
        return grid_image

    async def send_avatar_embed(self, ctx, grid_size=1):
        if grid_size < 1 or grid_size > 8:  # You can set a cap
            await ctx.send("Grid size must be between 1 and 8.")
            return
        avatar_img = self.create_avatar_grid(grid_size)
        with io.BytesIO() as image_binary:
            avatar_img.save(image_binary, "PNG")
            image_binary.seek(0)
            file = discord.File(fp=image_binary, filename="trick_avatar.png")
            embed = discord.Embed(
                title=f"✨ Here's your Cheek! {grid_size}x{grid_size}",
                color=discord.Color.random(),
            )
            embed.set_image(url="attachment://trick_avatar.png")
            embed.set_footer(text="Play Trickcal!")
            await ctx.send(embed=embed, file=file)

    @commands.hybrid_command(
        name="trick",
        description="Generate Trick avatars in a grid (e.g., !trick 3=3x3 grid)",
    )
    async def trick(self, ctx, grid_size: int = 1):
        """Generate a grid of random Trick avatars. Example: !trick 4 (4x4 grid)"""
        async with ctx.typing():
            await self.send_avatar_embed(ctx, grid_size=grid_size)
