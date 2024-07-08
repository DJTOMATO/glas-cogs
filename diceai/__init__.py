from .diceai import PerChance
from .diceai import styles, shapes
__red_end_user_data_statement__ = (
    "This cog does not persistently store data or metadata about users."
)


async def setup(bot):
    await bot.add_cog(PerChance(bot))

async def cog_load(self):
    tree = self.bot.tree
    tree.add_command(self.perchance)

async def cog_unload(self):
    tree = self.bot.tree
    tree.remove_command(self.perchance.name)
