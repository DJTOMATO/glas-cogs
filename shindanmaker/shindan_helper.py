from bs4 import BeautifulSoup
import cloudscraper


def get_shindan_title(shindan_id: int) -> str:
    """
    Extract the Shindan title from the page using cloudscraper.
    Returns the title string or raises ValueError if not found.
    """
    scraper = cloudscraper.create_scraper()
    url = f"https://en.shindanmaker.com/{shindan_id}"
    res = scraper.get(url)
    if not res.ok:
        raise ValueError(f"Failed to fetch Shindan page: {res.status_code}")

    soup = BeautifulSoup(res.text, "lxml")
    title_tag = soup.find("h1", {"id": "shindanTitle"})
    if title_tag and title_tag.get_text(strip=True):
        return title_tag.get_text(strip=True)

    # fallback: sometimes the title is in the <a> inside the h1
    link_tag = soup.select_one("h1#shindanTitle a")
    if link_tag and link_tag.get_text(strip=True):
        return link_tag.get_text(strip=True)

    raise ValueError("Shindan title not found")


# FUCK TURNSTILE I HATE YOU

# async def get_shindan_chart_image(shindan_url: str, log) -> bytes | None:
#     """
#     Fetch the ShindanMaker chart as PNG bytes.
#     Returns None if the chart cannot be rendered.
#     Logs detailed debug info using `log`.
#     """
#     log.warning(f"[DEBUG] Starting chart fetch for URL: {shindan_url}")

#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=True)
#         page = await browser.new_page()
#         log.warning("[DEBUG] Opening page in Playwright")

#         try:
#             response = await page.goto(shindan_url)
#             log.warning(
#                 f"[DEBUG] Page loaded, status: {response.status if response else 'no response'}"
#             )
#             html_snippet = await page.content()
#             log.warning(f"[DEBUG] Page snippet (first 500 chars): {html_snippet}")

#             # Wait for the canvas container
#             try:
#                 await page.wait_for_selector("p.canvas_block", timeout=10000)
#                 log.warning("[DEBUG] Canvas block found")
#             except:
#                 log.warning("[DEBUG] Canvas block NOT found")

#             # Try to get the canvas
#             canvas = await page.query_selector("canvas.chartjs-render-monitor")
#             if canvas:
#                 log.warning("[DEBUG] Canvas found, taking screenshot")
#                 image_data = await canvas.screenshot()
#                 await browser.close()
#                 log.warning("[DEBUG] Chart image successfully retrieved from canvas")
#                 return image_data

#             # Fallback: screenshot the full result div
#             log.warning("[DEBUG] Canvas not found, trying #shindanResult fallback")
#             result_div = await page.query_selector("#shindanResult")
#             if result_div:
#                 log.warning("[DEBUG] #shindanResult found, taking screenshot")
#                 image_data = await result_div.screenshot()
#                 await browser.close()
#                 log.warning(
#                     "[DEBUG] Chart image successfully retrieved from #shindanResult"
#                 )
#                 return image_data

#             log.warning("[DEBUG] No canvas or result div found, cannot retrieve chart")
#             await browser.close()
#             return None

#         except Exception as e:
#             log.warning(f"[DEBUG] Exception during chart fetch: {e}")
#             await browser.close()
#             return None
