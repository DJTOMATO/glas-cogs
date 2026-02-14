import asyncio
import typing
import discord
import aiohttp
import io
from redbot.core import commands
from howlongtobeatpy import HowLongToBeat
from fuzzywuzzy import fuzz


class HowLongToBeatCog(commands.Cog):
    """
    A cog made to search info on HowLongToBeat.com
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.__version__ = "1.0.0"
        self.hltb = HowLongToBeat(
            0.0
        )  # Similarity threshold up to 0.7, 0.0 will return all games.

    @commands.bot_has_permissions(attach_files=True, embed_links=True)
    @commands.command(name="howlongtobeat", aliases=["hltb"])
    async def HowLongToBeat(self, ctx: commands.Context, *, game_name: str):
        """Search how long a games takes to be beaten.

        Searches for the game name provided and returns the estimated time to beat it.
        """


        processed_game_name = game_name.strip()
        if not processed_game_name:
            await ctx.send_help(ctx.command)
            return

        async with ctx.typing():
            try:
                results = await self.hltb.async_search(
                    processed_game_name, similarity_case_sensitive=False
                )  # Case insensitive search

                if results is None or len(results) == 0:
                    await ctx.send(
                        f"No results found for '{processed_game_name}'. Please try a different game name."
                    )
                    return

                # For fuzzy matching, use a casefolded version of the input for consistent comparison
                processed_game_name_folded = processed_game_name.casefold()
                for result in results:
                    result.similarity = fuzz.ratio(
                        processed_game_name_folded, result.game_name.casefold()
                    )

                results = sorted(
                    results, key=lambda entry: entry.similarity, reverse=True
                )

                if not results:
                    await ctx.send(
                        f"No close matches found for '{processed_game_name}'. Please try a different game name."
                    )
                    return

                if len(results) > 1:
                    query_str = "Multiple results found, choose a number:\n" + "\n".join(
                        f"{i}. {result.game_name} (Similarity: {result.similarity:.2f})"
                        for i, result in enumerate(results[:5], 1)
                    )
                    await ctx.send(query_str)

                    def check(m):
                        return (
                            m.author.id == ctx.author.id
                            and m.channel.id == ctx.channel.id
                            and m.content.isdigit()
                            and 0 < int(m.content) <= min(len(results), 5)
                        )

                    try:
                        msg = await self.bot.wait_for(
                            "message", check=check, timeout=30
                        )
                        best_match = results[int(msg.content) - 1]
                    except asyncio.TimeoutError:
                        await ctx.send(
                            "You took too long to respond. Please try again."
                        )
                        return
                else:
                    best_match = results[0]

                embed = discord.Embed(
                    title=best_match.game_name,
                    url=f"https://howlongtobeat.com/game/{best_match.game_id}",
                    description=f"**Main Story:** {best_match.main_story} hours\n"
                    f"**Main + Extra:** {best_match.main_extra} hours\n"
                    f"**Completionist:** {best_match.completionist} hours\n",
                    color=discord.Color.green(),
                )
                embed.set_thumbnail(
                    url=self.bot.user.avatar.url if self.bot.user.avatar else None
                )
                embed.add_field(
                    name="Review Score",
                    value=(
                        f"{best_match.review_score}/100"
                        if hasattr(best_match, "review_score")
                        else "N/A"
                    ),
                    inline=True,
                )
                embed.add_field(
                    name="Platforms",
                    value=(
                        ", ".join(best_match.profile_platforms)
                        if hasattr(best_match, "profile_platforms")
                        else "N/A"
                    ),
                    inline=True,
                )
                embed.add_field(
                    name="Release Date",
                    value=(
                        best_match.release_world
                        if hasattr(best_match, "release_world")
                        else "N/A"
                    ),
                    inline=True,
                )

                if hasattr(best_match, "game_image_url") and best_match.game_image_url:
                    embed.set_image(url=best_match.game_image_url)

                await ctx.send(embed=embed)
            except asyncio.TimeoutError:
                await ctx.send("The request timed out. Please try again later.")
            except Exception as e:
                await ctx.send(f"An unexpected error occurred: {e}")

    async def red_delete_data_for_user(self, *, requester, user_id: int):
        pass
