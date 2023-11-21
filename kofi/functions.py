import aiohttp, re
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen


async def scraper(url):
    # Send a GET request to the URL
    # Assuming you have the URL stored in a variable called 'url'
    # and that we need to use headers for aiohttp

    async with aiohttp.ClientSession() as session:
        headers = {"User-Agent": "Mozilla/5.0"}
        async with session.get(url, headers=headers) as response:
            webpage = await response.text()
            soup = BeautifulSoup(webpage, "html.parser")

    # Create a dictionary to store the scraped data
    scraped_data = {}

    # Ko-fi User
    ko_fi_user = soup.select_one(".kfds-font-size-22 > span")
    if ko_fi_user:
        scraped_data["Ko-fi User"] = ko_fi_user.get_text()

    # Goal Title
    goal_title = soup.select_one(".kfds-btm-mrgn-24 > .text-left")
    if goal_title:
        scraped_data["Goal Title"] = goal_title.get_text()

    # Current Percentage
    current_percentage = soup.select_one(".text-left > .kfds-font-bold")
    if current_percentage:
        scraped_data["Current Percentage"] = current_percentage.get_text()

    # Of Goal Total
    of_goal_total = soup.select_one(".goal-label")
    if of_goal_total:
        scraped_data["Of Goal Total"] = of_goal_total.get_text()

    # Goal Description
    goal_description = soup.select_one(".goal-description")
    if goal_description:
        scraped_data["Goal Description"] = goal_description.get_text()

    # About User
    about_user = soup.select_one(".kfds-btm-mrgn-8 > .kfds-c-para-control")
    if about_user:
        scraped_data["About User"] = about_user.get_text()

    # Ko-fi Received
    ko_fi_received = soup.select_one(".koficounter-value")
    if ko_fi_received:
        scraped_data["Ko-fi Received"] = ko_fi_received.get_text()

    # URL
    url = soup.select_one(".buy-header-link")
    if url:
        scraped_data["URL"] = url["href"]

    # Profile Image URL
    profile_image = soup.select_one("#profilePicture")
    if profile_image:
        scraped_data["Profile Image URL"] = profile_image["src"]
    # if empty replace by default https://ko-fi.com/img/anon2.png
    else:
        scraped_data["Profile Image URL"] = "https://ko-fi.com/img/anon2.png"
    # Cover Image URL
    # Find the div element with id="profile-header"
    profile_header_div = soup.find("div", id="profile-header")

    # Check if the element exists and has a style attribute
    if profile_header_div and "style" in profile_header_div.attrs:
        style_value = profile_header_div["style"]

        # Use regex to extract the background URL
        url_match = re.search(r"url\((.*?)\)", style_value)
        if url_match:
            background_url = url_match.group(1)
            # print(background_url)
            # Split the URL by the ".png" extension
            sanitized_url = background_url.split(".png")[0] + ".png"
            scraped_data["Profile Banner URL"] = sanitized_url
        else:
            print("Background URL not found")
    else:
        print("Element or style attribute not found")

        # Display the scraped data
        # for key, value in scraped_data.items():
        # print(f"{key}: {value}")

    return scraped_data
