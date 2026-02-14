from aiohttp import ClientSession
from bs4 import BeautifulSoup

# Cool Kids don't use request
import aiohttp

# Thanks Flame!
import discord
from redbot.core import commands
from redbot.core import commands, data_manager
from .functions import (
    search,
    import_json_file,
    callback,
    get_emoji_by_iurl,
    extract_label,
    on_error,
)
import logging
import re


# rrat
class YourView(discord.ui.View):
    def __init__(self):
        super().__init__()

    async def on_error(self, interaction, error, item):
        await interaction.channel.send(
            f"An error occurred during the interaction. Please try again later. \n Error: {error}\n Item: {item}"
        )


class HoloWiki(commands.Cog):
    """HoloWiki Commands

    Your friend wiki of your favourite Chuubas"""

    def __init__(self, bot):
        self.bot = bot
        self.json = str(data_manager.bundled_data_path(self) / f"data.json")
        self.chuubas = import_json_file(self, self.json)
        self.log = logging.getLogger("glas.glas-cogs.holowiki")

    async def parse(self, ctx, entry, url, iurl):

        async with ClientSession() as session:
            async with session.get(url) as response:
                response_text = await response.text()
                soup = BeautifulSoup(response_text, "html.parser")
        data = {}
        odd = 0
        paragraphs = soup.select("div.mw-parser-output > p")

        clean_paragraphs = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and not text.startswith("This article is"):
                clean_paragraphs.append(text)

        data["greet"] = clean_paragraphs[0] if len(clean_paragraphs) > 0 else "No greeting found."
        data["bio"] = clean_paragraphs[1] if len(clean_paragraphs) > 1 else ""

        for row in soup.select(
            "#mw-content-text > div.mw-parser-output > table.infobox tr"
        ):
            th_element = row.find("th")
            td_element = row.find("td")
            if th_element and td_element:
                key = th_element.text.strip()
                # await ctx.send(key)
                value_element = td_element.find("a")
                if value_element:
                    value = value_element["href"]
                    if key == "Member of":
                        value = value.replace("/wiki", "https://hololive.wiki/wiki")
                        value = f"[{value_element.text}]({value})"
                    elif key == "Fan Name":
                        value = td_element.text.strip().split("[")[0].strip()
                    elif key == "Emoji / Oshi Mark":
                        value = td_element.string
                    elif key == "Height":
                        if len(data) == 1:
                            value = next(iter(data.values()))
                        elif len(data) == 2:
                            values = list(data.values())
                            value = f"{values[0]}\n{values[1]}"
                        else:
                            value = ""
                    elif key == "Fans":
                        hashtag = td_element.find("a").text.strip()
                        value = f"[{hashtag}](https://twitter.com/hashtag/{hashtag})"
                    elif key in [
                        "YouTube",
                        "Website",
                        "Twitter",
                        "Marshmallow",
                        "Spotify",
                        "bilibili",
                        "Twitch",
                    ]:
                        value = f"[{key}]({value})"
                    elif key == "MMD":
                        hashtag = td_element.find("a").text.strip()
                        value = f"[{hashtag}](https://twitter.com/hashtag/{hashtag})"
                    elif key == "Stream Talk":
                        hashtag = td_element.find("a").text.strip()
                        value = f"[{hashtag}](https://twitter.com/hashtag/{hashtag})"
                    elif key == "Debut Date":
                        hashtag = td_element.find("a").text.strip()
                        value = hashtag.replace(" (", " (\n")
                    elif key == "Age":
                        td = td_element
                        if td is not None:
                            hashtag = td.text.strip().split("[")[0]

                        value = f"{hashtag}"
                    elif key == "Age" and "years old" not in td_element.text:
                        value = "Unknown"
                    elif key == "Birthday":
                        hashtag = td_element.text
                        value = re.sub(r"\[\d+\]", "", td_element.text)

                    elif key == "Twitter Spaces":
                        hashtag = td_element.find("a").text.strip()
                        value = f"[{hashtag}](https://twitter.com/hashtag/{hashtag})"
                    elif key in ["Fanart"]:
                        hashtag = td_element.find("a").text.strip()
                        value = f"[Fanart](https://twitter.com/hashtag/{hashtag})"
                    elif key in ["Fanart (NSFW)"]:
                        hashtag = td_element.find("a").text.strip()
                        value = (
                            f"[Fanart (NSFW)](https://twitter.com/hashtag/{hashtag})"
                        )
                    elif key == "English":
                        if "cite_note" in td_element.text:
                            td_element = soup.select_one(
                                "#mw-content-text > div.mw-parser-output > table.infobox > tbody > tr:nth-child(35) > td"
                            )
                            # await ctx.send(td_element)
                            value = td_element
                        else:
                            value = (
                                f"[{hashtag}](https://twitter.com/hashtag/{hashtag})"
                            )

                else:
                    value = td_element.text.strip()
                data[key] = value

        for key, value in data.items():
            if value:
                # await ctx.send(value)
                value = value.replace("/wiki", "https://hololive.wiki/wiki")

            element = soup.select_one(
                "#mw-content-text > div.mw-parser-output > table.infobox > tbody > tr:nth-child(1) > th"
            )
            # await ctx.send(element)
            style = element.get("style")
            style_properties = style.split(";")

            for property in style_properties:
                if "background-color" in property:
                    color = property.split(":")[1].strip()

        pree = ""
        try:
            pree = get_emoji_by_iurl(self, iurl)
        except:
            pree = ""
        if "English Name" in data:
            title = data["English Name"]
        elif "Japanese Name" in data:
            title = data["Japanese Name"]
        else:
            title = "Report to dev error"
        emb = discord.Embed(
            title=title + " " + pree,
            description=f"**{data['greet']}**\n\n{data['bio']}",
            url=entry["url"],
        )
        # if Japanese Name add otherwise don't
        if "Japanese Name" in data:
            emb.add_field(name="Japanese Name", value=data["Japanese Name"])

        if "Debut Date" in data:
            emb.add_field(name="Debut Date", value=data.get("Debut Date", "N/A"))
        if "Member of" in data:
            emb.add_field(name="Member of", value=data.get("Member of", "N/A"))
        if "Fan Name" in data:
            emb.add_field(name="Fan Name", value=data.get("Fan Name", "N/A"))
        if "Birthday Name" in data:
            emb.add_field(name="Birthday", value=data["Birthday"])
        if "Age" in data:
            emb.add_field(name="Age", value=data["Age"])
        else:
            emb.add_field(name="Age", value="Unknown")
        if "Height" in data:
            emb.add_field(name="Height", value=data.get("Height", "N/A"))
        if "English" in data:
            emb.add_field(name="Nicknames", value=data.get("English", "N/A"))
        values = []
        if "Twitter" in data:
            values.append(data["Twitter"])
        if "Spotify" in data:
            values.append(data["Spotify"])
        if "Fanart" in data:
            values.append(data["Fanart"])
        if "Website" in data:
            values.append(data["Website"])
        if "YouTube" in data:
            values.append(data["YouTube"])
        if "Twitch" in data:
            values.append(data["Twitch"])
        emb.add_field(name="Social Media", value=" - ".join(values))
        color = discord.Colour(int(color.strip("#"), 16))
        emb.colour = color
        images = []
        session.close()
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response_text = await response.text()
                soup = BeautifulSoup(response_text, "html.parser")
                for image in soup.find_all("img"):
                    if "_Portrait" in image["src"]:
                        i = "https:" + image["src"]
                        images.append(i)
                    elif "_3D" in image["src"]:
                        i = "https:" + image["src"]
                        images.append(i)
                    elif "_Signature" in image["src"]:
                        i = "https:" + image["src"]
                        images.append(i)
                    elif (
                        "_YouTube_Profile_Picture" in image["src"]
                        and "DOVA-SYNDROME" not in image["src"]
                    ):
                        i = "https:" + image["src"]
                        images.append(i)
                    elif (
                        "_Twitter_Profile_Picture" in image["src"]
                        and "DOVA-SYNDROME" not in image["src"]
                    ):
                        i = "https:" + image["src"]
                        images.append(i)
                    elif "Yagoo" in image["src"]:
                        i = "https:" + image["src"]
                        images.append(i)

        baseimage = images[0]
        if len(images) > 0:
            baseimage = images[0]
        else:
            # Handle the case when the images list is empty
            baseimage = "https://bae.lena.moe/H5qlcnEjgsma.png"
        pattern = r"\/(\d+)px"
        fixedimages = []

        for image_url in images:
            if image_url.endswith("Signature.png"):
                new_image_url = re.sub(pattern, r"/241px", image_url)
            else:
                new_image_url = re.sub(pattern, r"/500px", image_url)
            fixedimages.append(new_image_url)

        images = fixedimages
        emb.set_image(url=baseimage)
        emb.set_footer(
            text="Powered by hololive.wiki - Search with {prefix}holo <name>".format(
                prefix=ctx.clean_prefix
            ),
            icon_url="https://static.miraheze.org/hololivewiki/b/ba/HFW-Favicon.png",
        )
        view = YourView()
        style = discord.ButtonStyle.gray
        count = 0
        # if image none don't do below
        if len(images) == 0:
            for image in enumerate(images):
                style = discord.ButtonStyle.gray
                label = image[1]
                label = await extract_label(self, image[1])
                button = discord.ui.Button(
                    style=style,
                    label=label,
                    custom_id=f"image_button_{count}",
                )
                # Thanks Flame!
                button.callback = lambda i, u=image[1], e=emb: callback(self, i, u, e)
                count += 1
                view.add_item(button)
        session.close()

        await ctx.send(embed=emb, view=view)

    @commands.command(cooldown_after_parsing=True)
    @commands.bot_has_permissions(attach_files=True, embed_links=True)
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def holo(self, ctx, chuuba):
        """Search a VTuber"""


        async with ctx.typing():
            result = search(self.chuubas, chuuba)

            if len(result) > 1:
                names = [item["Name"] for item in result]
                resultlist = "- " + "\n- ".join(names)
                number = len(result)
                await ctx.send(
                    f"{number} __results found, try again with a more precise name__: \n {resultlist} \n\n **Remember you can see the whole list typing** ``{0}hololist``".format(ctx.prefix)
                )
            if len(result) == 0:
                await ctx.send("No results found, try again with a more precise name.")
            else:
                entry = result[0]

                iurl = entry["url"].replace("https://hololive.wiki/wiki/", "")

                url = entry["url"]
                await self.parse(ctx, entry, url, iurl)

    @commands.command()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    async def hololist(self, ctx):
        """Display a list of all Hololive members."""

        emb = discord.Embed()

        # Use already loaded data from self.chuubas
        sorted_chuubas = sorted(self.chuubas, key=lambda x: x["Category"])
        chuubas_by_category = {chuuba["Category"]: [] for chuuba in sorted_chuubas}

        for chuuba in sorted_chuubas:
            chuubas_by_category[chuuba["Category"]].append(chuuba)

        for category, chuubas in chuubas_by_category.items():
            names = [chuuba["Name"] for chuuba in chuubas]
            all_names = ", ".join(names)
            emb.add_field(name=category, value=all_names)

        emb.set_footer(
            text="Powered by hololive.wiki - Search with {}holo <query>".format(ctx.prefix),
            icon_url="https://static.miraheze.org/hololivewiki/b/ba/HFW-Favicon.png",
        )
        await ctx.send(embed=emb)
