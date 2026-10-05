import asyncio
import logging
import aiohttp
import discord

from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.i18n import Translator, cog_i18n
from discord.ui import View, Button

log = logging.getLogger("red.lootandwaifus")
_ = Translator("LootAndWaifus", __file__)

ENDPOINTS = {
    "nikke": {
        "characters": "/nikke/characters.json"
    },
    "trickcal": {
        "characters": "/trickcal/characters.json",
        "artifacts": "/trickcal/artifacts.json",
        "runes": "/trickcal/runes.json"
    },
    "sxs": {
        "companions": "/swordxstaff/companions.json",
        "skills": "/swordxstaff/skills.json",
        "treasures": "/swordxstaff/treasures.json",
        "fantomons": "/swordxstaff/fantomons.json",
        "items": "/swordxstaff/items.json",
        "ingredients": "/swordxstaff/ingredients.json"
    },
    "mad": {
        "characters": "/mad/characters.json"
    }
}

class ResultView(View):
    def __init__(self, ctx, data, game, formatter):
        super().__init__(timeout=180.0)
        self.ctx = ctx
        self.data = data
        self.game = game
        self.formatter = formatter
        
        self.languages = {
            "🇺🇸": "en-US",
            "🇪🇸": "es-ES",
            "🇯🇵": "ja-JP",
            "🇨🇳": "zh-CN",
            "🇰🇷": "ko-KR"
        }
        
        for emoji, code in self.languages.items():
            btn = Button(emoji=emoji, style=discord.ButtonStyle.secondary, custom_id=code)
            btn.callback = self.make_callback(code)
            self.add_item(btn)

    def make_callback(self, code):
        async def callback(interaction: discord.Interaction):
            from redbot.core.i18n import set_contextual_locale
            try:
                set_contextual_locale(code)
            except ValueError:
                pass
            await interaction.response.defer()
            embed = await self.formatter(self.data, self.game, code)
            await interaction.message.edit(embed=embed, view=self)
        return callback

class DisambiguationView(View):
    def __init__(self, ctx, results, game, formatter):
        super().__init__(timeout=60.0)
        self.ctx = ctx
        self.results = results
        self.game = game
        self.formatter = formatter
        
        # Max buttons we can safely add is 25 (5 rows of 5)
        for i, res in enumerate(results[:25]):
            btn = Button(label=str(i + 1), style=discord.ButtonStyle.primary)
            btn.callback = self.make_callback(res)
            self.add_item(btn)

    def make_callback(self, res):
        async def callback(interaction: discord.Interaction):
            # Set the contextual locale for translation in views
            from redbot.core.i18n import set_contextual_locales_from_guild, set_contextual_locale
            
            # Use user preference if set, otherwise guild
            user_lang = await self.ctx.cog.config.user(interaction.user).lang()
            if user_lang:
                try:
                    set_contextual_locale(user_lang)
                except ValueError:
                    await set_contextual_locales_from_guild(self.ctx.bot, interaction.guild)
            else:
                await set_contextual_locales_from_guild(self.ctx.bot, interaction.guild)
            
            if interaction.user.id != self.ctx.author.id:
                return await interaction.response.send_message(_("This isn't your command."), ephemeral=True)
                
            await interaction.response.defer()
            result_view = ResultView(self.ctx, res, self.game, self.formatter)
            embed = await self.formatter(res, self.game, user_lang)
            await interaction.message.edit(embed=embed, view=result_view)
        return callback

@cog_i18n(_)
class LootAndWaifus(commands.Cog):
    """Fetch info from lootandwaifus.com API."""

    __author__ = "Glas"
    __version__ = "1.0.0"

    def __init__(self, bot: Red):
        super().__init__()
        self.bot: Red = bot
        self.config = Config.get_conf(self, 117, force_registration=True)
        self.config.register_user(lang=None)
        self.config.register_global(translation_cache={})
        self.session = aiohttp.ClientSession()
        self.base_url = "https://lootandwaifus.com/api"
        # Nested dict for cache structure
        self.cache = { "nikke": {}, "trickcal": {}, "sxs": {}, "mad": {} }
        self.translation_cache = {}

    async def cog_load(self) -> None:
        self.translation_cache = await self.config.translation_cache()
        asyncio.create_task(self.refresh_cache())

    async def cog_unload(self) -> None:
        await self.session.close()

    async def refresh_cache(self):
        log.info("Fetching data from Loot & Waifus API...")
        for game, categories in ENDPOINTS.items():
            for category, path in categories.items():
                try:
                    async with self.session.get(f"{self.base_url}{path}") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            self.cache[game][category] = data
                        else:
                            log.error(f"Failed to fetch {path} - status {resp.status}")
                except Exception as e:
                    log.error(f"Error fetching {path}: {e}")
        log.info("Finished fetching data from Loot & Waifus API.")

    def format_help_for_context(self, ctx: commands.Context):
        helpcmd = super().format_help_for_context(ctx)
        txt = _("Version: {version}\nAuthor: {author}").format(version=self.__version__, author=self.__author__)
        return f"{helpcmd}\n\n{txt}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int):
        return

    async def translate_text(self, text: str, target_lang: str) -> str:
        if not text or not isinstance(text, str):
            return text
            
        if not target_lang or target_lang.startswith("en"):
            return text
            
        lang_map = {"es-ES": "es", "ja-JP": "ja", "zh-CN": "zh-CN", "zh-TW": "zh-TW", "ko-KR": "ko"}
        tl = lang_map.get(target_lang)
        if not tl:
            if "-" in target_lang and target_lang not in ["zh-CN", "zh-TW"]:
                tl = target_lang.split("-")[0]
            else:
                tl = target_lang
            
        # Initialize cache if needed
        if target_lang not in self.translation_cache:
            self.translation_cache[target_lang] = {}
            
        if text in self.translation_cache[target_lang]:
            return self.translation_cache[target_lang][text]
            
        url = "https://clients5.google.com/translate_a/t"
        params = {
            "client": "dict-chrome-ex",
            "sl": "auto",
            "tl": tl,
            "q": text
        }
        
        if not hasattr(self, "_translate_lock"):
            self._translate_lock = asyncio.Semaphore(5)
            
        try:
            async with self._translate_lock:
                async with self.session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        translated = data[0][0] if data and isinstance(data, list) and isinstance(data[0], list) and data[0] else text
                        self.translation_cache[target_lang][text] = translated
                        # Schedule a save without blocking
                        asyncio.create_task(self.config.translation_cache.set(self.translation_cache))
                        return translated
                    else:
                        return text
        except Exception as e:
            log.error(f"Translation error: {e}")
            return text

    async def generate_embed(self, data: dict, game_name: str, target_lang: str = None) -> discord.Embed:
        # Determine language for translation
        if not target_lang:
            from redbot.core.i18n import get_locale
            target_lang = get_locale()

        name = data.get("name", _("Unknown"))
        name = await self.translate_text(name, target_lang)
        
        embed = discord.Embed(title=name, color=discord.Color.red())
        
        # Look for an icon
        icon = data.get("icon")
        if icon and (icon.endswith(".png") or icon.endswith(".webp") or icon.endswith(".jpg")):
            # It's a path
            embed.set_thumbnail(url=f"https://lootandwaifus.com/{icon}")
            
        # Collect all texts to translate
        translation_tasks = {}
        for key, value in data.items():
            if key in ["id", "name", "icon", "skill_description", "kr_name", "unique_effect", "basic_stats", "ranks", "skills", "yearning", "profile", "ability_tree_id", "nodes"]:
                continue
            if isinstance(value, list) and all(isinstance(v, str) for v in value):
                translation_tasks[key] = asyncio.create_task(self.translate_text(", ".join(value), target_lang))
            elif isinstance(value, str):
                translation_tasks[key] = asyncio.create_task(self.translate_text(value, target_lang))

        # Await simple translations
        translated_vals = {}
        for k, task in translation_tasks.items():
            translated_vals[k] = await task

        # Iterate over keys to dynamically build the embed
        for key, value in data.items():
            if key in ["id", "name", "icon", "skill_description", "kr_name", "unique_effect", "basic_stats", "ranks", "skills", "yearning", "profile", "ability_tree_id", "nodes"]:
                continue
            
            # Formatting lists
            if isinstance(value, list) or isinstance(value, str):
                if key in translated_vals:
                    val_str = translated_vals[key]
                    if len(val_str) > 1024:
                        val_str = val_str[:1021] + "..."
                    embed.add_field(name=_(key.replace("_", " ").title()), value=val_str, inline=True)
            elif isinstance(value, int) or isinstance(value, float):
                val_str = str(value)
                embed.add_field(name=_(key.replace("_", " ").title()), value=val_str, inline=True)
                
        # Handling special structured data:
        # skill_description
        skills = data.get("skill_description")
        if skills and isinstance(skills, list):
            for skill in skills:
                if isinstance(skill, list) and len(skill) >= 2:
                    name_str = f"{skill[0]} - {skill[1]}" if len(skill) >= 2 else skill[0]
                    name_str = await self.translate_text(name_str, target_lang)
                    val_str = skill[2] if len(skill) >= 3 else _("No description")
                    val_str = await self.translate_text(val_str, target_lang)
                    if len(val_str) > 1024:
                        val_str = val_str[:1021] + "..."
                    embed.add_field(name=name_str, value=val_str, inline=False)

        # yearning
        yearnings = data.get("yearning")
        if yearnings and isinstance(yearnings, list):
            for yearning in yearnings:
                if isinstance(yearning, list) and len(yearning) >= 2:
                    name_str = f"{yearning[0]} - {yearning[1]}" if len(yearning) >= 2 else yearning[0]
                    name_str = await self.translate_text(name_str, target_lang)
                    val_str = yearning[2] if len(yearning) >= 3 else _("No description")
                    val_str = await self.translate_text(val_str, target_lang)
                    if len(val_str) > 1024:
                        val_str = val_str[:1021] + "..."
                    embed.add_field(name=name_str, value=val_str, inline=False)
                    
        # basic_stats
        basic_stats = data.get("basic_stats")
        if basic_stats and isinstance(basic_stats, dict):
            stats_str = ""
            for k, v in basic_stats.items():
                k_trans = await self.translate_text(k, target_lang)
                if isinstance(v, list):
                    stats_str += f"**{k_trans}**: {', '.join(str(x) for x in v)}\n"
                else:
                    v_trans = await self.translate_text(str(v), target_lang)
                    stats_str += f"**{k_trans}**: {v_trans}\n"
            if stats_str:
                if len(stats_str) > 1024:
                    stats_str = stats_str[:1021] + "..."
                embed.add_field(name=_("Basic Stats"), value=stats_str, inline=False)
                
        # unique_effect
        unique = data.get("unique_effect")
        if unique and isinstance(unique, dict):
            eff_str = ""
            for k, v in unique.items():
                k_trans = await self.translate_text(k.title(), target_lang)
                v_trans = await self.translate_text(str(v), target_lang)
                eff_str += f"**{k_trans}**: {v_trans}\n"
            if eff_str:
                if len(eff_str) > 1024:
                    eff_str = eff_str[:1021] + "..."
                embed.add_field(name=_("Unique Effect"), value=eff_str, inline=False)
                
        # sxs skills
        sxs_skills = data.get("skills")
        if sxs_skills and isinstance(sxs_skills, list) and len(sxs_skills) > 0 and isinstance(sxs_skills[0], dict):
            for skill in sxs_skills:
                skill_name = await self.translate_text(skill.get("name", "Unknown"), target_lang)
                skill_type = await self.translate_text(skill.get("type", "Skill"), target_lang)
                skill_desc = await self.translate_text(skill.get("description", ""), target_lang)
                if skill_desc:
                    if len(skill_desc) > 1024:
                        skill_desc = skill_desc[:1021] + "..."
                    embed.add_field(name=f"{skill_type} - {skill_name}", value=skill_desc, inline=False)

        # mad profile
        profile = data.get("profile")
        if profile and isinstance(profile, dict):
            bio = profile.get("bio")
            if bio:
                bio_trans = await self.translate_text(bio, target_lang)
                if len(bio_trans) > 1024:
                    bio_trans = bio_trans[:1021] + "..."
                embed.add_field(name=_("Bio"), value=bio_trans, inline=False)
            prof_str = ""
            for k, v in profile.items():
                if k == "bio":
                    continue
                k_trans = await self.translate_text(k.title(), target_lang)
                v_trans = await self.translate_text(str(v), target_lang)
                prof_str += f"**{k_trans}**: {v_trans}\n"
            if prof_str:
                embed.add_field(name=_("Profile Info"), value=prof_str, inline=False)
                
        embed.set_footer(text=f"Loot & Waifus - {game_name.title()}")
        return embed

    async def search_and_respond(self, ctx, game: str, query: str):
        # Enforce user preference if it exists
        from redbot.core.i18n import set_contextual_locale
        user_lang = await self.config.user(ctx.author).lang()
        if user_lang:
            try:
                set_contextual_locale(user_lang)
            except ValueError:
                pass
                
        if not self.cache.get(game):
            await ctx.send(_("Data is still loading or failed to load. Try again in a moment."))
            return

        results = []
        for category, items in self.cache[game].items():
            if not isinstance(items, list):
                continue
            for item in items:
                name = item.get("name", "")
                if query.lower() in str(name).lower():
                    results.append(item)
                    
        if not results:
            await ctx.send(_("No results found for '{query}'.").format(query=query))
            return
            
        if len(results) == 1:
            res = results[0]
            embed = await self.generate_embed(res, game)
            result_view = ResultView(ctx, res, game, self.generate_embed)
            await ctx.send(embed=embed, view=result_view)
        else:
            embed = discord.Embed(
                title=_("Multiple results found"), 
                description=_("Please select one of the following:\n\n"), 
                color=discord.Color.red()
            )
            for i, res in enumerate(results[:25]):
                embed.description += f"**{i+1}.** {res.get('name', _('Unknown'))}\n"
            
            if len(results) > 25:
                embed.description += _("\n*Showing first 25 results. Please be more specific.*")
                
            view = DisambiguationView(ctx, results, game, self.generate_embed)
            await ctx.send(embed=embed, view=view)

    @commands.command(name="lwlang")
    async def cmd_lwlang(self, ctx, lang_code: str = None):
        """Set your preferred language for LootAndWaifus (e.g. es-ES, en-US, ja-JP)."""
        if not lang_code:
            await self.config.user(ctx.author).lang.set(None)
            await ctx.send(_("Language preference cleared."))
        else:
            await self.config.user(ctx.author).lang.set(lang_code)
            await ctx.send(_("Language preference set to {lang_code}.").format(lang_code=lang_code))

    @commands.is_owner()
    @commands.command(name="lwrefresh")
    async def cmd_lwrefresh(self, ctx):
        """Force refresh the API cache."""
        await ctx.send(_("Refreshing API cache..."))
        await self.refresh_cache()
        await ctx.send(_("Cache refreshed successfully!"))

    @commands.command(name="lwtest")
    async def cmd_lwtest(self, ctx):
        await ctx.send(_("Basic Stats"))

    @commands.command(name="nikke")
    async def cmd_nikke(self, ctx, *, query: str):
        """Search for NIKKE characters."""
        await self.search_and_respond(ctx, "nikke", query)
        
    @commands.command(name="trickcal")
    async def cmd_trickcal(self, ctx, *, query: str):
        """Search for Trickcal characters, artifacts, and runes."""
        await self.search_and_respond(ctx, "trickcal", query)
        
    @commands.command(name="sxs")
    async def cmd_sxs(self, ctx, *, query: str):
        """Search for Sword x Staff data."""
        await self.search_and_respond(ctx, "sxs", query)
        
    @commands.command(name="mad")
    async def cmd_mad(self, ctx, *, query: str):
        """Search for MAD characters."""
        await self.search_and_respond(ctx, "mad", query)
