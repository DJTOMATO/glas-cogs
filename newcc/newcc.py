from typing import Iterable, List, Tuple
from redbot.core.utils.chat_formatting import escape, pagify, box
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu
from redbot.core import commands
import discord

# Create global array
results = []


def PATCHED_prepare_command_list(
    ctx: commands.Context, command_list: Iterable[Tuple[str, dict]]
) -> List[Tuple[str, str]]:

    for command, body in command_list:

        responses = body["response"]
        if isinstance(responses, list):
            result = ", ".join(responses)
        elif isinstance(responses, str):
            result = responses
        else:
            continue
        if len(result) > 297:
            result = result[:297] + "\u200c"
            result = result.replace("\n", " ")
            result = escape(result, formatting=True, mass_mentions=True)
        results.append((f"{ctx.clean_prefix}{command}", f""))

    return results


class NewCC(commands.Cog):
    """Custom commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def list(self, ctx):
        """Returns cc list in a fancier way"""
        embed = discord.Embed(
            title="Command list",
            description="Here are the image macros available",
            type="rich",
            color=3066993,
        )
        print(
            "Total commands available:  {len(results)}"
        )  # In my instance I have 276 values, why does it only prints the first 25?
        # for each in results:
        #    embed.add_field(name=each[0], value="\u200c", inline=True)

        image_list = results
        if image_list == []:
            await ctx.send(_("I do not have any images saved!"))
            return
        post_list = [image_list[i : i + 25] for i in range(0, len(image_list), 25)]
        images = []
        for post in post_list:
            em = discord.Embed(timestamp=ctx.message.created_at)
            for image in post:
                em.add_field(name=image[0], value="\u200c")
            em.set_footer(
                text=("Page ") + "{}/{}".format(post_list.index(post) + 1, len(post_list))
            )
            images.append(em)
            em.title = "Command list"
            em.color = 3066993
            em.description = "Here are the image macros available"
        await menu(ctx, images, DEFAULT_CONTROLS)


#        await ctx.send(embed=embed)
