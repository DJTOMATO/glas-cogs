import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
import logging
import discord
from PIL import Image, ImageDraw, ImageFont

# from redbot.core.data_manager import bundled_data_path


class WebScraper:
    def __init__(self):
        self.base_url = "https://gg.deals/games/?title="
        self.log = logging.getLogger("glas.glas-cogs.ggdeals-scraper")
        self.session = aiohttp.ClientSession()  # Initialize session

    async def close_session(self):
        """Closes the aiohttp session."""
        if not self.session.closed:
            await self.session.close()

    def cog_unload(self):
        """
        Closes the HTTP session.
        """
        self.bot.loop.create_task(self.session.close())

    async def scrape(self, ctx, gamename):
        async with self.session.get(
            f"{self.base_url}{gamename.replace(' ', '+')}"
        ) as response:
            if response.status == 200:
                text = await response.text()
                soup = BeautifulSoup(text, "lxml")

                # Find the first div with the specified CSS selector
                target_div = soup.select_one(
                    ".list-items div.hoverable-box:nth-child(1)"
                )
                gameinfoside = soup.select_one("#game-info-side")
                await self.session.close()
                # If the div is found, you can extract its text or other information
                if target_div:
                    # Extract and clean up the text content of the specific div
                    div_text = target_div.get_text(separator="\n").strip()

                    # Process the text to format as "Key: Value" pairs
                    formatted_data = self.format_data(div_text)

                    # Include additional information
                    formatted_data["Icon"] = self.extract_icon(target_div)
                    formatted_data["Game Image (URL)"] = self.extract_game_image_url(
                        target_div
                    )
                    formatted_data["Game name"] = self.extract_game_name(target_div)
                    # title = soup.select_one(".active span[itemprop='name']")
                    # self.log.warning("Title new" + str(formatted_data["Game name"]))
                    # Extract "Compare Prices" URL

                    compare_prices_url = self.extract_compare_prices_url(target_div)
                    compare_prices_url = compare_prices_url.replace("%7D", "}")

                    formatted_data["Compare Prices URL"] = compare_prices_url

                    # Scrape further details from the "Compare Prices URL"
                    all_deals_details = await self.scrape_compare_prices_url(
                        compare_prices_url
                    )

                    scraped_game_info = await self.scrape_game_info(compare_prices_url)

                    if scraped_game_info is None:
                        # If scraped_game_info is None, raise a custom exception
                        raise ValueError("No information available for this game.")

                    # Try to extract Steam App ID from the soup
                    steam_app_id = self.extract_steam_app_id(gameinfoside)
                    # self.log.warning(
                    #    "Steam App ID after extract_steam_app_id: " + str(steam_app_id)
                    # )
                    if steam_app_id is None:
                        # If steam_app_id is None, raise a custom exception
                        self.log.warning("No Steam App ID found.")
                    return (
                        formatted_data,
                        all_deals_details,
                        scraped_game_info,
                        steam_app_id,
                    )
                else:
                    a = "nnothing lol"

            else:
                await self.session.close()
                self.log.warning(
                    f"Failed to fetch content. Status code: {response.status} - Report to Dev"
                )

    # THIS FUNCTION HANGS THE BOT, maybe too many async calls needs further research
    async def follow_redirects(self, url):
        async with aiohttp.ClientSession() as session:
            while True:
                async with session.get(url, allow_redirects=False) as response:
                    # Check if the response is a redirect
                    if response.status in {301, 302, 303, 307, 308}:
                        # Get the next URL from the 'Location' header
                        await session.close()
                        url = response.headers["Location"]
                    else:
                        await session.close()
                        # If it's not a redirect, this is the final URL
                        return url

    def format_data(self, raw_text):
        # Split the text into lines and format as "Key: Value" pairs
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        formatted_data = {}

        current_key = None
        for line in lines:
            # Check if the line ends with a colon to determine the key
            if line.endswith(":"):
                current_key = line[:-1].strip()  # Remove the trailing colon
            elif current_key is not None:
                # If there is a current key, use the line as the corresponding value
                formatted_data[current_key] = line.strip()
                current_key = None

        return formatted_data

    def extract_icon(self, target_div):
        # Find any element with a class containing "platform" and "windows"
        windows_icon = target_div.select_one("[class*=platform][class*=windows]")

        if windows_icon:
            return "Windows"
        # Add more conditions for other platforms if needed

        # Find any element with a class containing "platform" and "linux"
        linux_icon = target_div.select_one("[class*=platform][class*=linux]")
        if linux_icon:
            return "Linux"

        # Add more conditions for other platforms if needed

        # If no specific platform icon is found, you can return a default value or None
        return "Unknown Platform"

    def extract_game_image_url(self, target_div):
        # Extract the game image URL using the provided CSS selector
        # with open(f"{bundled_data_path(self)}/target_div.txt", "w") as f:
        #     f.write(str(target_div))
        # game_image_div = target_div.select_one(
        #     "div:nth-child(3) > a:nth-child(1) > picture:nth-child(1) > img:nth-child(3)"
        # )

        # Find all image elements
        image_elements = target_div.find_all("img")

        for img in image_elements:
            srcset = img.get("srcset", "")
            if "498xr286.jpg" in srcset:
                urls = srcset.split(",")
                for url in urls:
                    if "498xr286.jpg" in url:
                        first_image_url = url.strip().split()[0]
                        break
                if first_image_url:
                    break

        # self.log.warning("first image: " + str(first_image_url))
        # if game_image_div:
        #     game_image_url = game_image_div.get("src", "")
        return first_image_url

    def extract_game_name(self, target_div):
        # Extract the game name using the provided CSS selector
        game_name_link = target_div.find("a", class_="title-inner")
        if game_name_link:
            game_name = game_name_link.get_text().strip()
            return game_name

    def extract_compare_prices_url(self, target_div):
        # Extract the "Compare Prices" URL using the updated CSS selector
        compare_prices_link = target_div.select_one(
            "a.action-ext.action-desktop-btn.single-label"
        )
        if compare_prices_link:
            # Get the 'href' attribute value
            compare_prices_url = compare_prices_link.get("href", "")
            # Join the URL with the base URL if it is a relative URL
            if not compare_prices_url.startswith("http"):
                compare_prices_url = f"https://gg.deals{compare_prices_url}"
            return compare_prices_url
        else:
            self.log.warning(
                "Compare Prices URL not found in the specified CSS selector - Report to Dev"
            )
            return None

    async def scrape_compare_prices_url(self, compare_prices_url):
        async with aiohttp.ClientSession() as session:
            async with session.get(compare_prices_url) as response:
                if response.status == 200:
                    soup = BeautifulSoup(await response.text(), "lxml")

                    # Extract details from each deal on the new page
                    deals = soup.select("div.similar-deals-container")

                    # List to store deal details
                    all_deal_details = []

                    for deal in deals:
                        deal_details = await self.extract_deal_details(deal)

                        all_deal_details.append(deal_details)

                    await session.close()
                    return all_deal_details
                else:
                    self.log.warning(
                        f"Failed to fetch content from {compare_prices_url}. Status code: {response.status} - Report to dev"
                    )
                    await session.close()
                    return None

    async def scrape_game_info(self, ctx, compare_prices_url):
        scrapped_game_info = {}
        async with aiohttp.ClientSession() as session:
            async with session.get(compare_prices_url) as response:
                if response.status == 200:
                    text = await response.text()
                    soup = BeautifulSoup(text, "lxml")

                    game_info_widget = soup.select_one("#game-info-side")
                    release_date = (
                        game_info_widget.find("h4", string="Release date")
                        .find_next("p", class_="game-info-details-content")
                        .text.strip()
                    )
                    scrapped_game_info["playable_on"] = (
                        game_info_widget.find("div", string="Playable On")
                        .find_next("div")
                        .text.strip()
                    )
                    scrapped_game_info["developer_publisher"] = (
                        game_info_widget.find("div", string="Developer / Publisher")
                        .find_next("div")
                        .text.strip()
                    )
                    scrapped_game_info["reviews"] = (
                        game_info_widget.find("div", string="Reviews")
                        .find_next("div")
                        .text.strip()
                    )
                    scrapped_game_info["genres"] = (
                        game_info_widget.find("div", string="Genres")
                        .find_next("div")
                        .text.strip()
                    )
                    scrapped_game_info["tags"] = (
                        game_info_widget.find("div", string="Tags")
                        .find_next("div")
                        .text.strip()
                    )
                    scrapped_game_info["features"] = (
                        game_info_widget.find("div", string="Features")
                        .find_next("div")
                        .text.strip()
                    )
                    scrapped_game_info["game_description"] = (
                        game_info_widget.find("div", class_="widget-heading")
                        .find_next("p")
                        .text.strip()
                        .split("\n\n")[0]
                    )

                    # Extract related links
                    swiper_slide_divs = soup.find_all("div", class_="swiper-slide")

                    related_links = []
                    for swiper_slide in swiper_slide_divs:
                        image_link = swiper_slide.find("a", class_="preview-link").get(
                            "href"
                        )
                        related_links.append(image_link)

                    scrapped_game_info["related_links"] = related_links
                    await session.close()
                    return scrapped_game_info
                else:
                    await session.close()
                    self.log.warning(
                        f"Failed to fetch content. Status code: {response.status} -Report to dev"
                    )

                    return {}

    def extract_additional_details(self, soup):
        # Example: Extracting additional details from the new URL
        additional_details = {}

        # Add code to extract additional details based on the HTML structure
        # For example:
        additional_details["Some Key"] = (
            soup.select_one(".some-class").get_text().strip()
        )

        return additional_details

    async def extract_deal_details(self, deal):
        # Extract details from each deal
        deal_details = {}

        # Shop Logo
        shop_logo_element = deal.select_one(".shop-image img")
        shop_logo = shop_logo_element.get("src", "") if shop_logo_element else ""
        deal_details["Shop Logo"] = shop_logo

        # Map shop logos to shop names
        shop_mapping = {
            "https://img.gg.deals/55/68/f5ab472cbb0587c9f5e1b66561498e6927d8.svg": "Steam",
            "https://img.gg.deals/d4/ba/1ec9eea47fc611633851b219023831083e95_90xt35_Q100.png": "GAMIVO*",
            "https://img.gg.deals/0f/81/dbacbd83d51f37dfac47c0954be70d3385a9.svg": "Instant Gaming*",
            "https://img.gg.deals/7f/fc/0519b5d0810864027e297a768faa8e922506_90xt35_Q100.png": "ENEBA*",
            "https://img.gg.deals/4f/38/62a96b564da05d1db8e3591c8548455ebda6.svg": "Humble Bundle Store",
            "https://img.gg.deals/77/95/1e2444e51329516a30a1e16a3d61215ba670.svg": "NewEgg",
            "https://img.gg.deals/07/28/3c6eeb2a7c86c6441a89898217781e7df6ff.svg": "G2Play*",
            "https://img.gg.deals/09/32/6dbacb7190441b0cfe2374ac0a5790c0a1c7_90xt35_Q100.png": "Kinguin*",
            "https://img.gg.deals/a6/6a/566b5bb65f82b5677344417533c427680077_90xt35_Q100.png": "Kinguin*",
            "https://img.gg.deals/fd/44/cb16f247f9085d1a3d30329b1aa7999a14f9.svg": "K4G*",
            "https://img.gg.deals/93/90/d19b88367ee8d52977848ab54abf081ba573.svg": "K4G*",
            "https://img.gg.deals/84/97/41332eaef689576ca0f10b3f53c51aa24976.svg": "GOG*",
            "https://img.gg.deals/4e/04/9be7ab9c9eaa79a94ad8bc17bb17e45b84a7.svg": "GOG*",
            "https://img.gg.deals/ff/c2/132a6bbe5f1eac950a87d0fab24bb9341b67_90xt35_Q100.png": "GameBillet",
            "https://img.gg.deals/d9/f7/1c0556dd97fdc3eca891cf716432e68603ff_90xt35_Q100.png": "GameBillet",
            "https://img.gg.deals/d3/7b/6fd0e7fe8270ecd25ca5498179924d83a8a8.svg": "Game",
            "https://img.gg.deals/bb/a5/bb03c33f3538ad4be392296c6ce53f9beea9.svg": "Game",
            "https://img.gg.deals/60/de/c317e405fa36be3886dd098963324b1c7ac1_90xt35_Q100.png": "CDKeys*",
            "https://img.gg.deals/a4/ef/40f22b8023f160e7877a635e2eda6bcaa9eb_90xt35_Q100.png": "CDKeys*",
            "https://img.gg.deals/ff/2c/10a66019fc4202d191bbbb6515d6c7e62fb2.svg": "IndieGala",
            "https://img.gg.deals/4e/fe/cb6d51cda8be396256202fa80a6d1bc26ba4.svg": "IndieGala",
            "https://img.gg.deals/18/93/128a5dc7abdb6ca529957c94d56f02f53331.svg": "Fanatical",
            "https://img.gg.deals/6e/67/057fb90629fd628003980b92477276c4594f.svg": "G2A*",
            "https://img.gg.deals/9a/b7/887418f9bc8725e5a60d3edeb2f2d023ea3d.svg": "G2A*",
            "https://img.gg.deals/55/a0/2b6ea3d1302b0db179964a9b68fd11c81c31.svg": "Microsoft Store",
            "https://img.gg.deals/a6/4f/c0e24320970b5b0563d67784f43a182a9250.svg": "Microsoft Store",
            "https://img.gg.deals/f7/46/a2bfac8854ad9e116643458b5e0d7504c2ce_90xt35_Q100.png": "MTCGAME*",
            "https://img.gg.deals/08/b1/8609adc12910b43ef07b3f2563205a3191ef_90xt35_Q100.png": "MTCGAME*",
            "https://img.gg.deals/59/af/a6775f91e45dc89393a411cb9af173c5a175.svg": "Driffle*",
            "https://img.gg.deals/58/3d/191405fb7798cb3520e0e8f7dcf96ad6e1fd.svg": "Driffle*",
            "https://img.gg.deals/b9/4f/d6049f39b978a6b14ea09731c2704fb7aa8e.svg": "GameSeal*",
            "https://img.gg.deals/e9/be/7f3f4f266ebbcac23cc2b06ec50116a618ec.svg": "GameSeal*",
            "https://img.gg.deals/d7/f7/ef59006a3db0dc177f8c99a49838b3540841_90xt35_Q100.png": "Minecraft Store",
            "https://img.gg.deals/b7/a8/1bdf3de51f6ddcd197d7c52c7097b2941e1b.svg": "GamesPlanet **UK**",
            "https://img.gg.deals/c0/8e/03c6c3a3f46d79a3ff340af4523a7c857478.svg": "GamesPlanet **UK**",
            "https://img.gg.deals/bf/6e/abca8bb55ba442f27c9e5aadb85c2ce78c14_90xt35_Q100.png": "JoyBuggy",
            "https://img.gg.deals/37/6e/466703e3769c79252b9a140a6df34d712f54_90xt35_Q100.png": "JoyBuggy",
            "https://img.gg.deals/17/c1/09fd29fa9a61da4bfa1dc42f1813f99b1915_90xt35_Q100.png": "HRK",
            "https://img.gg.deals/17/c1/09fd29fa9a61da4bfa1dc42f1813f99b1915_90xt35_Q100.png": "HRK",
            "https://img.gg.deals/6d/38/363da1aa77190a475d9871d0d1bdaa68d5d0.svg": "DLGAMER",
            "https://img.gg.deals/06/46/9941ae8cf02a6bca9b720185e4e1fd4713db.svg": "DLGAMER",
            "https://img.gg.deals/63/06/c2664d916ee13c4aee10e0659238f5898eaf_90xt35_Q100.png": "WinGameStore",
            "https://img.gg.deals/7e/c6/69f2e354883c0ce9703081ae16e5c624a411_90xt35_Q100.png": "WinGameStore",
            "https://img.gg.deals/31/f0/f443dc6e18c2a93ba59fb9a42cbb9eba41e3_90xt35_Q100.png": "Epic Store",
            "https://img.gg.deals/31/f0/f443dc6e18c2a93ba59fb9a42cbb9eba41e3_90xt35_Q100.png": "Epic Store",
            "https://img.gg.deals/fe/08/de2c02530fb90ebba80e45fbe39cc02c3324_90xt35_Q100.png": "YUPLAY*",
            "https://img.gg.deals/86/56/0acb7fb648728c5a5ad370db7c26714b5cb9.svg": "GamesPlanet US",
            "https://img.gg.deals/0a/8c/cbd93a75cce4d35d2e91fca073f2353fa9bd.svg": "GamesPlanet US",
            "https://img.gg.deals/53/0e/fbc31eb9b0fa0d8d7cc4534d559fd48977a3_90xt35_Q100.png": "Nuveem",
            "https://img.gg.deals/f7/50/92c4f611a78f7070912a754a000195c2e26a.svg": "GameSeal*",
            "https://img.gg.deals/fc/4d/0098e85b68abbb6831511036a67b21e2d804_90xt35_Q100.png": "AllYouPlay*",
            "https://img.gg.deals/2f/49/5511e9bfeb8d186e64437ab6e1f07f032d6a_90xt35_Q100.png": "Etail Market (US)*",
            "https://img.gg.deals/e9/f9/74e5cfd0af1b5fd339d9cff33b3d6f76837c_90xt35_Q100.png": "Etail Market (EU)*",
            "https://img.gg.deals/b5/bf/f6a2641666e4fd0055e7d7fb2bcb20beb455_90xt35_Q100.png": "GamersGate",
            "https://img.gg.deals/32/d0/acd6afa24776b1eb578e4d22d24cf24669b4.svg": "Newegg",
            "https://img.gg.deals/43/5d/048b3ab04326f931059e735b45ee3760da96_90xt35_Q100.png": "PremiumCDKeys",
            "https://img.gg.deals/c9/cc/51fd616765c46c619e9f65b57987731739b9_90xt35_Q100.png": "PremiumCDKeys",
            "https://img.gg.deals/ba/f8/ac55a33003c12dea18e851a90ce12a1b7bf9.svg": "GreenManGaming",
            "https://img.gg.deals/3f/c7/232386017599a08e6395944ce80062b4ff99.svg": "GreenManGaming",
            "https://img.gg.deals/dc/1f/8af436d14c21df1a992a88e431e28fb83f23_90xt35_Q100.png": "GamerThor",
            "https://img.gg.deals/b3/03/a60a38b007532b8a52cdfe3913df944ce11e_90xt35_Q100.png": "GamerThor",
            "https://img.gg.deals/cd/b7/4774ca8e256b0d11114ea982389eaf4649a5_90xt35_Q100.png": "KeyCense",
            "https://img.gg.deals/a2/a6/07b915b57163f742620b85079adfec60502b_90xt35_Q100.png": "DifMark",
            "https://img.gg.deals/8a/0a/c2b880ca4d909e70b0e6affc703fdbbf6888_90xt35_Q100.png": "DifMark",
        }

        # Get the shop name based on the logo
        shop_name = shop_mapping.get(shop_logo, "Unknown Shop - Report it to Dev")

        # Update the deal details with the shop name
        deal_details["Shop Name"] = shop_name
        # Title
        # print(deal)
        title_element = deal.select_one(
            ".breadcrumbs-list > li:nth-child(4) > a:nth-child(1) > span:nth-child(1)"
        )
        # self.log.warning(f"title_element: {title_element}")

        title = title_element.get_text().strip() if title_element else ""
        deal_details["Title"] = title

        # Platform
        platform_element = deal.select_one(".platforms-tag.tag-icon.tag span.value")
        platform_icon = platform_element.find("svg")
        platform_icon_url = (
            platform_icon.find("use").get("xlink:href", "") if platform_icon else ""
        )
        # Define the list of possible icon names
        possible_icon_names = [
            "svg-icon-alert-fill",
            "svg-icon-alert",
            "svg-icon-arrow-top-right",
            "svg-icon-arrow-top",
            "svg-icon-arrow-up",
            "svg-icon-bundles",
            "svg-icon-clock",
            "svg-icon-connection-humble-bundle",
            "svg-icon-contact-balloons",
            "svg-icon-currency",
            "svg-icon-disqus-grey",
            "svg-icon-disqus",
            "svg-icon-dlc",
            "svg-icon-drm-battle-net",
            "svg-icon-drm-drm-free",
            "svg-icon-drm-ea",
            "svg-icon-drm-epic-games",
            "svg-icon-drm-gog",
            "svg-icon-drm-itch-io",
            "svg-icon-drm-microsoft-store",
            "svg-icon-drm-nintendo",
            "svg-icon-drm-other",
            "svg-icon-drm-prime-gaming",
            "svg-icon-drm-psn",
            "svg-icon-drm-rockstar",
            "svg-icon-drm-steam",
            "svg-icon-drm-ubisoft-connect",
            "svg-icon-filter-funnel",
            "svg-icon-full-arrow-left",
            "svg-icon-full-arrow-right",
            "svg-icon-game-price-chart",
            "svg-icon-icon-18",
            "svg-icon-icon-checkbox-tick",
            "svg-icon-icon-clear-input",
            "svg-icon-icon-copy",
            "svg-icon-icon-discord",
            "svg-icon-icon-dollar-green",
            "svg-icon-icon-edit",
            "svg-icon-icon-error",
            "svg-icon-icon-facebook",
            "svg-icon-icon-fire",
            "svg-icon-icon-gear",
            "svg-icon-icon-ghost",
            "svg-icon-icon-grid",
            "svg-icon-icon-heart-red",
            "svg-icon-icon-import-from-wishlist",
            "svg-icon-icon-info",
            "svg-icon-icon-link-solid",
            "svg-icon-icon-list-with-sidebar",
            "svg-icon-icon-list",
            "svg-icon-icon-manage",
            "svg-icon-icon-metacritic-logo",
            "svg-icon-icon-options-plus",
            "svg-icon-icon-pause-fill",
            "svg-icon-icon-pin",
            "svg-icon-icon-play-fill",
            "svg-icon-icon-pricetag-blue",
            "svg-icon-icon-profile-circle",
            "svg-icon-icon-reddit",
            "svg-icon-icon-save",
            "svg-icon-icon-settings-sliders",
            "svg-icon-icon-tags",
            "svg-icon-icon-tick-active",
            "svg-icon-icon-trash",
            "svg-icon-icon-trophy",
            "svg-icon-icon-twitter",
            "svg-icon-icon-x-circle",
            "svg-icon-icon-x",
            "svg-icon-ignore",
            "svg-icon-includes",
            "svg-icon-info_circle",
            "svg-icon-key",
            "svg-icon-login-dude",
            "svg-icon-menu-cards",
            "svg-icon-menu-coins",
            "svg-icon-menu-games",
            "svg-icon-menu-people",
            "svg-icon-menu-ranks",
            "svg-icon-menu-slides",
            "svg-icon-menu-subs",
            "svg-icon-menu-vouchers",
            "svg-icon-owned-fill",
            "svg-icon-owned",
            "svg-icon-platform-android",
            "svg-icon-platform-geforce-now",
            "svg-icon-platform-ios",
            "svg-icon-platform-linux",
            "svg-icon-platform-mac",
            "svg-icon-platform-nintendo-switch",
            "svg-icon-platform-pc",
            "svg-icon-platform-ps",
            "svg-icon-platform-steam-deck-playable",
            "svg-icon-platform-steam-deck-unsupported",
            "svg-icon-platform-steam-deck-verified",
            "svg-icon-platform-steam-deck",
            "svg-icon-platform-vr-required",
            "svg-icon-platform-vr-supported",
            "svg-icon-platform-windows",
            "svg-icon-platform-xbox-one",
            "svg-icon-platform-xbox-series",
            "svg-icon-platform-xbox",
            "svg-icon-series",
            "svg-icon-shield",
            "svg-icon-social-facebook",
            "svg-icon-social-reddit",
            "svg-icon-social-rss",
            "svg-icon-social-twitter",
            "svg-icon-subscriptions",
            "svg-icon-text-plus",
            "svg-icon-wishlist-fill",
            "svg-icon-wishlist",
            "svg-icon-zoom",
        ]

        # Extract the icon name from the URL
        icon_name_match = re.search(r'#([^"]+)$', platform_icon_url)
        icon_name = icon_name_match.group(1) if icon_name_match else ""

        # Filter the icon name to get the platform name
        filtered_platform = next(
            (name for name in possible_icon_names if name in icon_name), icon_name
        )

        # If there's a match, extract the platform name
        platform_name_match = re.search(r"platform-(\w+)", filtered_platform)
        platform_name = (
            platform_name_match.group(1).capitalize() if platform_name_match else ""
        )

        deal_details["Platform"] = platform_name

        # Deal Date
        deal_date_element = deal.select_one(".time-icon-tag span.value time")
        # self.log.warning(f"deal: {deal}")
        # self.log.warning(f"deal_date_element: {deal_date_element}")
        import datetime

        if deal_date_element:
            deal_date_raw = deal_date_element.get(
                "datetime", deal_date_element.get_text()
            ).strip()
            try:
                deal_date_dt = datetime.datetime.fromisoformat(
                    deal_date_raw.replace("Z", "+00:00")
                )
                unix_ts = int(deal_date_dt.timestamp())
                deal_date = f"<t:{unix_ts}:R>"
            except Exception as e:
                self.log.warning(f"Failed to parse deal date: {deal_date_raw} ({e})")
                deal_date = deal_date_raw
        else:
            deal_date = ""
        deal_details["Deal Date"] = deal_date

        # DRM Icon
        drm_icon_element = deal.select_one(".tag-drm svg")
        drm_icon = (
            drm_icon_element.get("data-original-title", "").replace("DRM: ", "")
            if drm_icon_element
            else ""
        )

        # Define the list of possible DRM icon names
        possible_drm_icon_names = [
            "svg-icon-drm-steam",
            "svg-icon-drm-origin",
            "svg-icon-drm-uplay",
            "svg-icon-drm-gog",
            "svg-icon-drm-epic-games",
            "svg-icon-drm-battle-net",
            "svg-icon-drm-microsoft-store",
            "svg-icon-drm-playstation",
            "svg-icon-drm-xbox",
            "svg-icon-drm-nintendo",
            "svg-icon-drm-rockstar",
            "svg-icon-drm-ubisoft-connect",
        ]

        # Get the DRM icon URL
        drm_icon_url = "/images/svgs/icons.svg?v=a2de01c3#svg-icon-drm-steam"  # Replace with the actual URL

        # Extract the icon name from the URL
        drm_icon_name_match = re.search(r'#([^"]+)$', drm_icon_url)
        drm_icon_name = drm_icon_name_match.group(1) if drm_icon_name_match else ""

        # Filter the DRM icon name to get the DRM platform
        filtered_drm_icon = next(
            (name for name in possible_drm_icon_names if name in drm_icon_name),
            drm_icon_name,
        )

        # If there's a match, extract the DRM platform
        drm_platform_match = re.search(r"drm-(\w+)", filtered_drm_icon)
        drm_platform = (
            drm_platform_match.group(1).capitalize() if drm_platform_match else ""
        )

        deal_details["DRM"] = drm_platform

        # Price
        price_element = deal.select_one(".price-wrapper .price")
        # self.log.warning(f"price_element: {price_element}")
        price = price_element.get_text().strip() if price_element else ""
        deal_details["Price"] = price

        # Coupon Code and Percentage
        coupon_element = deal.select_one(".code")
        coupon_code = None
        percentage = None
        if coupon_element:
            coupon_text = coupon_element.get_text().strip()
            percentage_match = re.search(r"(-?\d+)%", coupon_text)

            coupon_code = coupon_text
            percentage = int(percentage_match.group(1)) if percentage_match else None
        else:
            coupon_code = None
            percentage = None

        deal_details["Coupon Code"] = coupon_code
        deal_details["Coupon Percentage"] = percentage

        # Best Deal
        best_deal_element = deal.select_one(".best.label")
        best_deal = best_deal_element.get_text().strip() if best_deal_element else None

        deal_details["Best Deal"] = best_deal if best_deal is not None else ""

        # Shop URL

        shop_url_element = deal.select_one(".shop-link")
        shop_url = shop_url_element.get("href", "") if shop_url_element else ""

        # Prepend the base URL if shop_url starts with a slash
        if shop_url.startswith("/"):
            base_url = "https://deals.gg"
            shop_url = f"{base_url}{shop_url}"
        # THE FUNCTION BELOW HANGS THE BOT, maybe too many async calls needs further research
        # shop_url2 = await self.follow_redirects(shop_url)
        # self.log.warning(f"shop_url2: {shop_url2}")
        deal_details["Shop URL"] = shop_url

        return deal_details

    async def extract_platform(self, target_div):
        # Extract the platform based on the presence of the .platform-link-icon element
        platform_element = target_div.select_one(".platform-link-icon")

        if platform_element:
            # Get the text content of the nested span element
            platform_text = platform_element.find("span").get_text(strip=True)
            return platform_text
        else:
            self.log.warning(
                f"Platform information not found in the specified CSS selector. - Report to dev"
            )

            return None

    async def scrape_game_info(self, compare_prices_url):
        async with aiohttp.ClientSession() as session:
            async with session.get(compare_prices_url) as response:
                if response.status == 200:
                    soup = BeautifulSoup(await response.text(), "lxml")
        reviews = None
        features = None
        game_info_widget = soup.select_one("#game-info-side")
        # self.log.warning(f"game_info_widget: {game_info_widget}")

        # release_date = (
        #     game_info_widget.find("h4", string="Release date")
        #     .find_next("p", class_="game-info-details-content")
        #     .text.strip()
        # )

        if game_info_widget:
            release_date_span = game_info_widget.find("span", string="Release date")

            if release_date_span:
                release_date_p = release_date_span.find_next_sibling(
                    "p", class_="game-info-details-content"
                )

                if release_date_p:
                    release_date = release_date_p.text.strip()
                else:
                    release_date = "Release date not found"
            else:
                release_date = "Release date span not found"
        else:
            release_date = "Game info widget not found"

        playable_on_section = game_info_widget.find("h4", string="Playable on")
        if playable_on_section:
            playable_on = []
            platform_icons = playable_on_section.find_next(
                "div", class_="platform-link-icons-wrapper"
            ).find_all("a", class_="platform-icon")

            for platform in platform_icons:
                platform_title = (
                    platform.find("use").get("xlink:href").split("-")[-1].capitalize()
                )

                if "Unsupported" in platform_title:
                    platform_title = "Steam Deck Unsupported"

                playable_on.append(platform_title)
        else:
            playable_on = []
        # dev
        developer_publisher = "None"

        # Find all <span> elements with class 'game-info-inner-heading'
        span_elements = soup.find_all("span", class_="game-info-inner-heading")

        # Iterate through each span element to find the one with 'Developer / Publisher'
        for span in span_elements:
            if span.text.strip() == "Developer / Publisher":
                # Navigate to the parent <div> with class 'game-info-details-section-developer'
                parent_div = span.parent

                if parent_div:
                    # Find all <a> tags with class 'grey-light-link' within the parent <div>
                    developer_publisher_links = parent_div.find_all(
                        "a", class_="grey-light-link"
                    )

                    # Extract developer and publisher names if links are found
                    if developer_publisher_links:
                        developer_names = [
                            link.text.strip() for link in developer_publisher_links
                        ]
                        developer_publisher = " / ".join(developer_names)

                break  # Exit the loop once we've found and extracted the information

        # self.log.warning(f"Developer / Publisher: {developer_publisher}")

        # DEV
        # Reviews Section Parsing
        reviews_element = game_info_widget.find(
            "span", class_="game-info-details-section game-info-details-section-reviews"
        )
        reviews = None  # Initialize reviews to avoid UnboundLocalError
        reviews_element = game_info_widget.select_one(
            "div.game-info-score-section.game-info-steam-score-section span.reviews-label"
        )
        reviews = None  # Initialize reviews to avoid UnboundLocalError
        if reviews_element:
            reviews = reviews_element.get_text(strip=True)
        else:
            self.log.warning("Reviews label not found in Steam score section.")

        game_info_genres = soup.select_one("#game-info-genres")

        if game_info_genres:
            genres = [
                genre.text.strip()
                for genre in game_info_genres.find_all("a", class_="badge-wrapper")
            ]
        else:
            genres = "Genres container not found."

        game_info_tags = soup.select_one(".game-info-content")
        # TAGS

        if game_info_tags:
            tags_section = game_info_tags.find("span", string="Tags")
            if tags_section:
                tags_div = tags_section.find_next(
                    "div",
                    class_="d-flex tags-list badges-container tags-list-dotdotdot",
                )
                if tags_div:
                    tags = [
                        tag.text.strip()
                        for tag in tags_div.find_all("a", class_="badge-wrapper")[:3]
                    ]
                else:
                    tags = []  # Return an empty list when the tags div is not found
            else:
                tags = []  # Return an empty list when tags section header is not found
        else:
            tags = []  # Return an empty list when game_info_tags is not found

        # TAGS

        game_info_features = soup.select_one("#game-info-features")

        if game_info_features:
            features_section = game_info_features.find("h4", string="Features")
            if features_section:
                features = [
                    feature.text.strip()
                    for feature in features_section.find_next(
                        "div",
                        class_="d-flex tags-list badges-container tags-list-dotdotdot",
                    ).find_all("a", class_="badge-wrapper")[:3]
                ]
        else:
            self.log.warning("Game info features not found.")
            features = []  # Return an empty list when features are not present

        # test
        # game_info_features = soup.select_one("#game-info-features")
        # features_section = game_info_features.find("h4", string="Features")

        # if features_section:
        #     features = [
        #         feature.text.strip()
        #         for feature in features_section.find_next(
        #             "div",
        #             class_="d-flex tags-list badges-container tags-list-dotdotdot",
        #         ).find_all("a", class_="badge-wrapper")[:3]
        #     ]
        # else:
        #     features = []

        game_info_links = soup.select_one(
            ".game-info-box .game-connected-list.type-links"
        )
        if game_info_links:
            related_links = [
                {
                    "url": entry.find("a", class_="game-info-entry-link").get("href"),
                    "text": entry.find("a", class_="game-info-entry-link").text.strip(),
                }
                for entry in game_info_links.find_all(
                    "li", class_="game-connected-single"
                )
            ]
        else:
            related_links = []

        game_description_element = soup.select_one(".game-description.description-text")

        if game_description_element:
            game_description_text = game_description_element.text.strip()
        else:
            game_description_text = "Description not available"

        extracted_info = {
            "release_date": release_date,
            "playable_on": playable_on,
            "developer_publisher": developer_publisher,
            "reviews": reviews,
            "genres": genres,
            "tags": tags,
            "features": features,
            "related_links": related_links,
            "game_description": game_description_text,
        }
        await session.close()
        return extracted_info

    def extract_steam_app_id(self, soup):
        """
        Extract the Steam App ID from the soup if present in the Steam score section.
        Returns the app id as int, or None if not found.
        Adds debug logging for troubleshooting.
        """
        # self.log.warning("Extracting Steam App ID from soup.")
        # Find all score sections
        score_sections = soup.select(
            "div.game-info-details-section.game-info-score-section"
        )
        for section in score_sections:
            heading = section.find("span", class_="game-info-inner-heading")
            if heading and heading.get_text(strip=True).startswith("Steam"):
                link = section.select_one("a.score-grade")
                if link and link.has_attr("href"):
                    href = link["href"]
                    # self.log.warning(f"Found Steam link: {href}")
                    match = re.search(r"/app/(\d+)/", href)  # <-- FIX: single backslash
                    if match:
                        app_id = int(match.group(1))
                        # self.log.warning(f"Extracted Steam App ID: {app_id}")
                        return app_id
                    else:
                        pass
                        # self.log.warning("No App ID found in Steam link.")
                else:
                    # self.log.warning("No valid href found in score-grade link.")
                    pass
        # self.log.warning("Steam score link not found in soup.")
        return None

    async def make_embed(
        self, ctx, formatted_data, all_deals_details, scraped_game_info
    ):
        # obtain all columns from formatted_data
        columns = list(formatted_data.keys())
        embed = discord.Embed(
            title=f"{formatted_data.get('Game name')}",
        )

        # ['Release Date', 'Genres', 'Official Stores',
        #  'Keyshops', 'Icon', 'Game Image (URL)', 'Game name', 'Compare Prices URL']
        # self.log.warning(f"columns: {columns}")
        for column_name in columns:
            # Skip certain columns that are not to be added as fields
            if column_name not in [
                "Game Image (URL)",
                "Compare Prices URL",
                "Game name",
                "Icon",
                "Keyshops",
                "Official Stores",
                "From",
            ]:
                # Get the value from formatted_data or set to "N/A" if not present
                column_value = formatted_data.get(column_name, "N/A")
                # Add field to the embed
                embed.add_field(name=column_name, value=column_value, inline=True)

        embed.set_image(url=formatted_data["Game Image (URL)"])
        columns = list(formatted_data.keys())
        # ['release_date', 'playable_on', 'developer_publisher', 'reviews', 'genres', 'tags', 'features', 'related_links', 'game_description']
        max_length = 1024  # Maximum length for a field in Discord embed
        a = scraped_game_info.get("tags")
        developer_publisher = scraped_game_info.get("developer_publisher", "")

        first_publisher = developer_publisher.split(" / ")[
            0
        ]  # Get the first part before " / "
        # self.log.warning(f"first_publisher: {first_publisher}")
        if first_publisher and first_publisher != "None":
            embed.add_field(name="Dev/Pub", value=first_publisher, inline=True)
        # self.log.warning(a)
        if a and a != "":
            embed.add_field(
                name="Tags",
                value=" - ".join([f"{tag}" for tag in scraped_game_info.get("tags")]),
                inline=True,
            )
        features = scraped_game_info.get("features")
        if features:
            embed.add_field(
                name="Features",
                value=" - ".join([f"{feature}" for feature in features]),
                inline=True,
            )

        b = scraped_game_info.get("reviews")
        if b and b != "None":
            embed.add_field(
                name="Reviews",
                value=f"{scraped_game_info.get('reviews')}",
                inline=True,
            )
        description = (
            # f"\n__Keyshops__: {formatted_data.get('Keyshops')} - __Official Stores__: {formatted_data.get('Official Stores')}\n\n"
            f"\nOnly four storefronts & Keyshops will be displayed.\n[Press here for the full list]({formatted_data.get('Compare Prices URL')})\n"
        )
        # await ctx.send(f"{scraped_game_info.get('game_description')}")
        first_paragraph = scraped_game_info.get("game_description").split("\n")[0]

        # await ctx.send(f"{first_paragraph}")
        # Build the final description
        filled_description = f"{first_paragraph}\n {description}"
        # trim filled_descipriton to 1024
        filled_description = filled_description[:1500]

        embed.add_field(name="Description", value=filled_description, inline=False)

        # Filter out "~" and "$" from prices for sorting
        pricing_details_filtered = [
            {
                "Shop Name": details["Shop Name"],
                "Price": (
                    0
                    if details["Price"].lower() == "free"
                    else float(
                        details["Price"]
                        .replace("~", "")
                        .replace("$", "")
                        .replace("¥", "")
                        .replace("€", "")
                        .replace("£", "")
                        .replace("CHF", "")
                        .replace("CA$", "")
                        .replace("A$", "")
                        .replace("AU$", "")
                        .replace("元", "")
                        .replace("₹", "")
                        .replace("₩", "")
                        .replace("R$", "")
                        .replace("₽", "")
                        .replace(",", ".")  # Replace commas with dots
                        .rsplit(".", 1)[0]  # Replace only the last dot
                        if details["Price"]
                        else "0"
                    )
                ),
                "Formatted Price": details["Price"],
                "Deal Date": details["Deal Date"],
                "Shop URL": details["Shop URL"],
                "Best Deal": details["Best Deal"],
                "Coupon Code": details["Coupon Code"],
            }
            for details in all_deals_details
        ]

        # Sort the pricing details by price and then by deal date
        sorted_details = sorted(
            pricing_details_filtered, key=lambda x: (x["Price"], x["Deal Date"])
        )

        warning = (
            "\\* means Keyshop, beware there may be risks type ``{prefix}risks`` for details."
        ).format(prefix=ctx.clean_prefix)
        # Check if the list is not empty

        embed2 = discord.Embed(
            title="No Pricing Details",
            description="No pricing information available.",
        )
        embed2.set_footer(
            icon_url="https://bae.lena.moe/l9q3mnnat3i3.gif",
            text="Powered by deals.gg",
        )

        if all_deals_details:
            # Initialize description with an empty string
            description = ""

            # Iterate over the list of dictionaries
            best_deal_value = None
            coupon_lines = []

            for index, details in enumerate(sorted_details):
                shop_name = details["Shop Name"]
                shop_url = details["Shop URL"]
                formatted_price = details["Formatted Price"]
                deal_date = details["Deal Date"]
                coupon_code = str(details.get("Coupon Code", ""))

                # Check if this is the first item in the sorted_details list
                if index == 0:
                    coupon_details = f"* [{shop_name}]({shop_url}) {formatted_price} - {deal_date} - **BEST DEAL**"
                else:
                    if coupon_code == "None" or coupon_code == "":
                        coupon_details = f"* [{shop_name}]({shop_url}) {formatted_price} - {deal_date}"
                    else:
                        coupon_details = f"* [{shop_name}]({shop_url}) {formatted_price} - {deal_date} - Coupon: {coupon_code}"

                coupon_lines.append(coupon_details)

            # Create the embed with the concatenated description
            embed2 = discord.Embed(
                title=f"Pricing Details", description="\n".join(coupon_lines)
            )
            embed2.set_footer(
                icon_url="https://bae.lena.moe/l9q3mnnat3i3.gif",
                text=f"Powered by gg.deals",
            )
            embed2.add_field(name="Disclaimer", value=warning, inline=False)

        # Return the embeds
        return embed, embed2


async def get_ggdeals_api_prices_by_steamid(bot, steam_app_ids, region=None):
    """
    Fetch price data from gg.deals API by Steam App ID(s) using Red shared API tokens.
    Returns a dict of {appid: price_data or None}.
    """
    api_tokens = await bot.get_shared_api_tokens("ggdeals")
    api_key = api_tokens.get("api_key")
    if not api_key:
        return {
            "error": "The gg.deals API key has not been set. Please set it with `[p]set api ggdeals api_key,<your_key>`\n If you need it, obtain it from https://gg.deals/settings/."
        }
    steamapi = await bot.get_shared_api_tokens("steam")
    api_key_steam = steamapi.get("api_key")
    if not api_key_steam:
        return {
            "error": "The Steam API key has not been set. Please set it with `[p]set api steam api_key,<your_key>`\n If you need it, obtain it from https://steamcommunity.com/dev/apikey."
        }

    ids = ",".join(str(i) for i in steam_app_ids)
    url = f"https://api.gg.deals/v1/prices/by-steam-app-id/?ids={ids}&key={api_key}"
    if region:
        url += f"&region={region}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 429:
                    data = await resp.json()
                    return {
                        "error": f"Rate limit exceeded: {data.get('data', {}).get('message', 'Too Many Requests')}."
                    }
                if resp.status != 200:
                    return {"error": f"API error: {resp.status} {resp.reason}"}
                # Always return a dict, even if data is missing
                try:
                    data = await resp.json()
                except Exception as e:
                    return {"error": f"Failed to parse JSON: {e}"}
                if not isinstance(data, dict):
                    return {"error": "API did not return a dict response."}
                return data
        except Exception as e:
            return {"error": f"API request failed: {e}"}


async def get_steam_app_id_from_name(bot, game_name):
    """
    Try to get the Steam App ID for a given game name using the Steam Storefront search API (undocumented, but used by the Steam website).
    Returns the appid as int, or None if not found.
    This is more accurate for user queries than local fuzzy matching.
    """
    import aiohttp
    import urllib.parse

    query = urllib.parse.quote(game_name)
    url = f"https://store.steampowered.com/api/storesearch/?term={query}&l=en&cc=US"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            items = data.get("items", [])
            if not items:
                return None
            # Return the first result's appid
            return items[0].get("id")


async def get_steam_game_details(appid):
    """
    Fetch game details (image, description, genres, reviews, release date) from the Steam API.
    Returns a dict with the relevant info or None if not found.
    """
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=en"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            if not data or not data.get(str(appid), {}).get("success"):
                return None
            game_data = data[str(appid)]["data"]
            return {
                "image": game_data.get("header_image"),
                "description": game_data.get("short_description"),
                "genres": [g["description"] for g in game_data.get("genres", [])],
                "release_date": game_data.get("release_date", {}).get("date"),
                "reviews": game_data.get("recommendations", {}).get("total"),
                "name": game_data.get("name"),
            }


async def get_ggdeals_bundles_by_steam_app_id(bot, steam_app_ids, region=None):
    """
    Fetch bundle data from gg.deals API by Steam App ID(s) using Red shared API tokens.
    Returns a dict of {appid: bundle_data or None}.
    """
    api_tokens = await bot.get_shared_api_tokens("ggdeals")
    api_key = api_tokens.get("api_key")
    if not api_key:
        return {
            "error": "The gg.deals API key has not been set. Please set it with `[p]set api ggdeals api_key,<your_key>`\n If you need it, obtain it from https://gg.deals/settings/."
        }
    ids = ",".join(str(i) for i in steam_app_ids)
    url = f"https://api.gg.deals/v1/bundles/by-steam-app-id/?ids={ids}&key={api_key}"
    if region:
        url += f"&region={region}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 429:
                    data = await resp.json()
                    return {
                        "error": f"Rate limit exceeded: {data.get('data', {}).get('message', 'Too Many Requests')}."
                    }
                if resp.status != 200:
                    return {"error": f"API error: {resp.status} {resp.reason}"}
                try:
                    data = await resp.json()
                except Exception as e:
                    return {"error": f"Failed to parse JSON: {e}"}
                if not isinstance(data, dict):
                    return {"error": "API did not return a dict response."}
                return data
        except Exception as e:
            return {"error": f"API request failed: {e}"}
