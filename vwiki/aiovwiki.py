import aiohttp
from bs4 import BeautifulSoup, SoupStrainer
import re
from typing import Optional, TypeVar, Any, List, Dict
from urllib.parse import urljoin
import string
import logging

headers = {
    "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
}

AioVwikiT = TypeVar("AioVwikiT", bound="AioVwiki")


class AioVwiki:

    def __init__(self, session: Optional[aiohttp.ClientSession] = None) -> None:
        self.session = session
        self.image = ""
        self.name: Optional[str] = None
        self.log = logging.getLogger("glas.glas-cogs2.Vwiki")

    async def __aenter__(self: AioVwikiT) -> AioVwikiT:
        return self

    async def __aexit__(self, *excinfo: Any) -> None:
        await self.close()

    async def close(self) -> None:
        if self.session is not None:
            await self.session.close()

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None:
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def _fetch_page_soup(self, page_url: str) -> Optional[BeautifulSoup]:
        """Fetches a page and returns a BeautifulSoup object, or None on failure."""
        session = await self._get_session()
        try:
            async with session.get(page_url) as response:
                response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
                html_content = await response.read()  # Read as bytes
                # Let BeautifulSoup handle encoding detection from bytes
                # soup = BeautifulSoup(html_content, "lxml")
                soup = BeautifulSoup(html_content, "html.parser")  # Try html.parser
                return soup
        except aiohttp.ClientResponseError as e:
            self.log.warning(
                f"Failed to fetch {page_url}, status: {e.status}, message: {e.message}"
            )
            return None
        except aiohttp.ClientError as e:
            self.log.error(f"Client error fetching {page_url}: {e}")
            return None
        except Exception as e:
            self.log.error(f"Error parsing HTML from {page_url}: {e}")
            return None

    def _find_main_content_body(
        self, soup: Optional[BeautifulSoup]
    ) -> Optional[Any]:  # bs4.element.Tag
        """Finds the main content body (e.g., mw-parser-output) from a soup object."""
        if not soup:
            return None

        selectors = [
            "div.mw-parser-output",  # Common on Fandom
            ".mw-parser-output",  # General class
            "div.mw-content-ltr.mw-parser-output",  # More specific MediaWiki
        ]

        for selector in selectors:
            body_element = soup.select_one(selector)
            if body_element:
                self.log.debug(f"Found main content body using selector: '{selector}'")
                return body_element

        self.log.warning(
            "Could not find the main content body (e.g., .mw-parser-output) on the page."
        )
        return None

    def _update_page_image(
        self, soup: Optional[BeautifulSoup], body: Optional[Any]
    ) -> None:
        """Extracts the main page image and updates self.image."""
        page_image_url = "None"
        if body:  # Try finding in the parsed main content body first
            img_tag = body.find("img", class_="pi-image-thumbnail")
            if img_tag and img_tag.has_attr("src"):
                page_image_url = img_tag["src"]

        if (
            page_image_url == "None" and soup
        ):  # If not in body, or body was None, try infobox in full soup
            infobox = soup.find("aside", class_="portable-infobox")
            if infobox:
                img_tag_infobox = infobox.find("img", class_="pi-image-thumbnail")
                if img_tag_infobox and img_tag_infobox.has_attr("src"):
                    page_image_url = img_tag_infobox["src"]
            elif (
                page_image_url == "None"
            ):  # Fallback: any pi-image-thumbnail in the soup if not in infobox
                img_tag_soup = soup.find("img", class_="pi-image-thumbnail")
                if img_tag_soup and img_tag_soup.has_attr("src"):
                    page_image_url = img_tag_soup["src"]

        if page_image_url and page_image_url != "None":
            if page_image_url.startswith("//"):  # Handle protocol-relative URLs
                page_image_url = "https:" + page_image_url
        self.image = page_image_url if page_image_url else "None"

    @staticmethod
    def _clean_text(text: Optional[str]) -> str:
        if not text:
            return ""
        # Remove wiki citation marks like [1], [2], etc.
        cleaned_text = re.sub(r"\[\s*\d+\s*\]", "", text)
        # Further cleaning for multiple spaces that might result from separators
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
        return cleaned_text

    @staticmethod
    def _make_absolute_url(url: str, base_page_url: str) -> str:
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("/"):
            # Use the full page URL as base for resolving relative paths like /wiki/Something
            # This correctly forms https://virtualyoutuber.fandom.com/wiki/Something
            return urljoin(base_page_url, url)
        # If it's already a full URL (http, https), return as is.
        # Otherwise, it might be a relative path not starting with /
        # which is less common for primary links in infoboxes.
        # For safety, one could also join with the domain base if it's not absolute.
        if not (url.startswith("http:") or url.startswith("https:")):
            # Fallback for paths like 'path/to/file' relative to current page
            return urljoin(base_page_url, url)
        return url

    def _parse_infobox_details(
        self, soup: BeautifulSoup, page_url: str
    ) -> Dict[str, Any]:
        """Parses specific details from the infobox."""
        infobox = soup.find("aside", class_="portable-infobox")
        if not infobox:
            self.log.warning(
                f"Infobox ('aside.portable-infobox') not found on page {page_url} for {self.name}"
            )
            return {}

        self.log.debug(f"Infobox element found for {self.name} on {page_url}.")

        details: Dict[str, Any] = {}

        desired_data_sources = {
            "debut_date": "Debut Date",
            "channel": "Channel",
            "official_website": "Website",
            "gender": "Gender",
            "age": "Age",
            "birthday": "Birthday",
            "height": "Height",
            "weight": "Weight",
            "zodiac_sign": "Zodiac Sign",
            "fan_name": "Fan Name",
            "emoji": "Emoji",
        }

        # Original find_all method
        data_items_find_all = infobox.find_all(
            "div", class_="pi-item pi-data", attrs={"data-source": True}
        )
        self.log.debug(
            f"Using find_all: Found {len(data_items_find_all)} potential 'div.pi-item.pi-data[data-source]' items in infobox for {self.name}."
        )

        # Alternative: CSS selector
        # Selects div tags that have class 'pi-item', class 'pi-data', and a 'data-source' attribute.
        data_items_select = infobox.select("div.pi-item.pi-data[data-source]")
        self.log.debug(
            f"Using select (CSS): Found {len(data_items_select)} potential 'div.pi-item.pi-data[data-source]' items in infobox for {self.name}."
        )

        # Prefer CSS selector if it finds items and find_all doesn't,
        # or if it generally proves more reliable.
        data_items = data_items_select if data_items_select else data_items_find_all

        if not data_items:
            self.log.warning(
                f"Infobox found for {self.name}, but no 'div.pi-item.pi-data[data-source]' items were located within it on {page_url}."
                f" (Used find_all count: {len(data_items_find_all)}, CSS select count: {len(data_items_select)})."
                f" HTML of infobox (first 4000 chars): {str(infobox)[:4000]}"
            )  # Log the content of the infobox
            return {}

        self.log.debug(
            f"Found {len(data_items)} potential 'div.pi-item.pi-data[data-source]' items in infobox for {self.name}."
        )

        for i, item in enumerate(data_items):
            data_source_key = item.get("data-source")  # Use .get() for safety
            if not data_source_key:
                self.log.debug(
                    f"Infobox item {i} for {self.name} is missing 'data-source' attribute. Item: {str(item)[:100]}"
                )
                continue

            if data_source_key not in desired_data_sources:
                self.log.debug(
                    f"Skipping data_source '{data_source_key}' for {self.name} (item {i}) as it's not in desired_data_sources."
                )
                continue

            value_div = item.find("div", class_="pi-data-value")
            if not value_div:
                self.log.debug(
                    f"No 'div.pi-data-value' found for data_source '{data_source_key}' (item {i}) in infobox for {self.name}. Item: {str(item)[:100]}"
                )
                continue

            dict_key = desired_data_sources[data_source_key]
            extracted_value = None
            if data_source_key in ["channel", "official_website"]:
                links_data = []
                for link_tag in value_div.find_all("a", href=True):
                    href = link_tag["href"]
                    abs_url = self._make_absolute_url(href, base_page_url=page_url)
                    links_data.append(
                        {"text": self._clean_text(link_tag.get_text()), "url": abs_url}
                    )
                if links_data:
                    extracted_value = links_data
                elif value_div.get_text(
                    strip=True
                ):  # Fallback if no <a> tags but text exists
                    extracted_value = self._clean_text(
                        value_div.get_text(separator=" ", strip=True)
                    )
            else:
                raw_text = value_div.get_text(separator=" ", strip=True)
                extracted_value = self._clean_text(raw_text)

            if extracted_value is not None and (
                isinstance(extracted_value, str)
                and extracted_value.strip() != ""
                or isinstance(extracted_value, list)
                and extracted_value
            ):
                details[dict_key] = extracted_value
                self.log.debug(
                    f"Successfully parsed and added to infobox_details for {self.name}: '{dict_key}': '{str(extracted_value)[:100]}'"
                )
            else:
                self.log.debug(
                    f"Value for '{dict_key}' (data_source: '{data_source_key}') for {self.name} was empty or None after processing, not adding. Item: {str(item)[:100]}"
                )

        if not details:
            self.log.warning(
                f"Infobox parsed for {self.name} on {page_url}, but the resulting 'details' dictionary is empty. Check debug logs for reasons why items might have been skipped or yielded no data."
            )
        return details

    async def decompose_useless(self, body):
        infoboxes = body.find_all("aside", class_="portable-infobox")
        first_run = True
        for box in infoboxes:
            if first_run:
                exc = box.find("img", class_="pi-image-thumbnail")
                if exc is None:
                    box.decompose()
                    first_run = False
                    continue
                self.image = exc["src"]
                first_run = False
            box.decompose()

        toc = body.find("div", id="toc")
        if toc:
            toc.decompose()

        message_boxes = body.find_all("table", class_="messagebox")
        for box in message_boxes:
            box.decompose()

        captions = body.find_all("p", class_="caption")
        for caption in captions:
            caption.decompose()

        nav_boxes = body.find_all("table", class_="navbox")
        for box in nav_boxes:
            box.decompose()

        return body

    async def validity_check(
        self, vtuber: str, auto_correct: bool, session: aiohttp.ClientSession
    ):
        params = {
            "action": "query",
            "titles": vtuber,
            "format": "json",
            "formatversion": 2,
        }
        x = ""
        if auto_correct is False:
            req = await session.get(
                "https://virtualyoutuber.fandom.com/api.php", params=params
            )
            res = await req.json()
            try:
                fin = res["query"]["pages"][0]["missing"]
                if fin == True or fin == "":
                    return None
            except KeyError:
                x = string.capwords(vtuber).replace(" ", "_")
                pass
        else:
            res = await self.search(vtuber=vtuber)
            if res == []:
                return None
            if res[0].startswith("List") is False:
                x = string.capwords(res[0]).replace(" ", "_")
            else:
                return None
        return x

    async def search(self, vtuber: str, limit=10):
        session = await self._get_session()
        params = {
            "action": "query",
            "srsearch": vtuber,
            "srlimit": limit,
            "list": "search",
            "format": "json",
        }
        req = await session.get(
            f"https://virtualyoutuber.fandom.com/api.php", params=params
        )
        res = await req.json()
        fin = res["query"]["search"]
        result = list((object["title"] for object in fin))
        return result

    async def summary(self, vtuber: str, auto_correct: bool = True):
        session = await self._get_session()
        x = await self.validity_check(
            vtuber=vtuber, auto_correct=auto_correct, session=session
        )

        self.name = x
        if x is None:
            return "Make sure the names are correct, and use auto_correct if you haven't already"
        html_req = await session.get(f"https://virtualyoutuber.fandom.com/wiki/{x}")
        # html = await html_req.content.read()
        # html = html.decode("utf-8")
        # cls_output = SoupStrainer(class_="mw-parser-output")

        # soup = BeautifulSoup(html, "lxml")  # Try without parse_only first
        # body = soup.find(class_="mw-parser-output")

        # if body is None:
        #     # Fallback approach if the direct search fails
        #     body = soup.select_one(
        #         "div.mw-content-ltr.mw-parser-output"
        #     ) or soup.select_one("div.mw-parser-output")
        page_url = f"https://virtualyoutuber.fandom.com/wiki/{x}"
        soup = await self._fetch_page_soup(page_url)
        body = self._find_main_content_body(soup)
        self._update_page_image(
            soup, body
        )  # Updates self.image, handles None soup/body

        if body is None:
            return "Could not parse page content to find summary."

        # body = await self.decompose_useless(body)
        para = body.find_all("p", recursive=False, limit=3)
        if not para or len(para) < 2:  # Check if enough paragraphs are found
            self.log.warning(f"Not enough paragraphs found for summary on {self.name}")
            return "Summary not available or page structure is different."
        annoying_string = para[0].find("i")
        if annoying_string != None:
            para.pop(0)

        summary = para[1].text
        return summary.strip()

    async def personality(self, vtuber: str, auto_correct: bool = True):
        session = await self._get_session()  # Needed for validity_check
        page_name_slug = await self.validity_check(
            vtuber=vtuber, auto_correct=auto_correct, session=session
        )
        self.name = page_name_slug

        if page_name_slug is None:
            return f'No wiki results for Vtuber "{vtuber}"'

        page_url = f"https://virtualyoutuber.fandom.com/wiki/{page_name_slug}"
        soup = await self._fetch_page_soup(page_url)
        body = self._find_main_content_body(soup)
        self._update_page_image(soup, body)

        if body is None:
            self.log.warning(
                f"Could not find mw-parser-output for {vtuber} ({self.name}) in personality."
            )
            return "Could not parse page content to find personality."

        # body = await self.decompose_useless(body)
        person_tag = body.find("span", id="Personality")
        prsn = "None"
        if person_tag:
            p_person_tag = person_tag.parent
            ph = p_person_tag.find_next_sibling()
            prsn = ""
            while True:
                if (
                    not ph or ph.name != "p"
                ):  # Stop if not a <p> tag or no more siblings
                    break
                prsn = prsn + "\n" + ph.text
                ph = ph.find_next_sibling()
        return prsn.strip()

    async def quote(self, vtuber: str, auto_correct: bool = True) -> List[str]:
        session = await self._get_session()  # Needed for validity_check
        page_name_slug = await self.validity_check(
            vtuber=vtuber, auto_correct=auto_correct, session=session
        )
        self.name = page_name_slug

        if page_name_slug is None:
            # Return empty list, consistent with successful parse but no quotes found
            self.log.info(f'No wiki results for Vtuber "{vtuber}" for quote method.')
            return []

        page_url = f"https://virtualyoutuber.fandom.com/wiki/{page_name_slug}"
        soup = await self._fetch_page_soup(page_url)

        if soup is None:
            # _fetch_page_soup already logs
            return []  # Return empty list on fetch/parse failure

        body = self._find_main_content_body(soup)
        self._update_page_image(soup, body)  # Updates self.image

        if body is None:
            self.log.warning(
                f"Could not find mw-parser-output for {vtuber} ({self.name}) in quote method."
            )
            return []  # Return empty list if main content not found

        # body = await self.decompose_useless(body)
        qts_tag = body.find("span", id="Quotes")
        qts_list: List[str] = []

        if qts_tag:
            p_qts_tag = qts_tag.parent
            # Iterate through siblings to find <ul> or <p> tags containing quotes
            current_element = p_qts_tag.find_next_sibling()
            while current_element:
                if current_element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    # Stop if we hit another major section header
                    if current_element.find("span", class_="mw-headline"):
                        break

                if current_element.name == "ul":
                    for li in current_element.find_all("li", recursive=False):
                        text_content = li.get_text(strip=True)
                        if text_content:
                            real_t = re.sub(r"\[[0-9]+\]", "", text_content).strip()
                            if real_t:
                                qts_list.append(real_t)
                    # Assuming one main <ul> for quotes, break after processing it
                    break
                # Add handling for quotes in <p> tags if necessary, similar to personality
                current_element = current_element.find_next_sibling()

        if not qts_list:
            self.log.info(f"No quotes found for {vtuber} ({self.name}).")
            # The original code returned "None" string here. Returning an empty list is more consistent.
            # If the calling cog specifically expects the string "None", it should handle an empty list.
            # For now, let's stick to the original behavior if it's critical for the cog.
            # However, for type consistency, [] is better.
            # To match original behavior for "None" string:
            # return "None" # type: ignore
            # For now, let's return empty list for consistency.

        return qts_list

    async def history(self, vtuber: str, auto_correct: bool = True):
        session = await self._get_session()
        x = await self.validity_check(
            vtuber=vtuber, auto_correct=auto_correct, session=session
        )
        self.name = x
        if x is None:
            return f'No wiki results for Vtuber "{vtuber}"'

        page_url = f"https://virtualyoutuber.fandom.com/wiki/{x}"
        soup = await self._fetch_page_soup(page_url)
        body = self._find_main_content_body(soup)
        self._update_page_image(soup, body)

        if body is None:
            self.log.warning(
                f"Could not find mw-parser-output for {vtuber} ({self.name}) in history."
            )
            return {}  # Return empty dict if content not found

        # body = await self.decompose_useless(body)
        hs_tag = body.find("span", id="History")
        section = ""
        res = {}
        hs = "None"
        first_run = True
        if hs_tag != None:
            hs = ""
            p_hs_tag = hs_tag.parent
            next_node = p_hs_tag.find_next_sibling()
            # r_next_node = p_hs_tag.find_next_sibling()
            while True:
                if str(next_node).startswith("<h3>"):
                    if first_run is False:
                        res[section] = hs
                        hs = ""
                        section = next_node.text
                    else:
                        section = next_node.text
                if str(next_node).startswith("<h2>"):
                    if hs != "":
                        res[section] = hs
                    break

                if next_node.name == "p":
                    if next_node.text != "":
                        real_t = re.sub("\[[0-9]+\]", "", next_node.text)
                        hs = hs + "\n" + real_t
                        if first_run is True:
                            first_run = False
                next_node = next_node.find_next_sibling()
        return res

    async def trivia(self, vtuber: str, auto_correct: bool = True):
        session = await self._get_session()
        x = await self.validity_check(
            vtuber=vtuber, auto_correct=auto_correct, session=session
        )

        self.name = x
        if x is None:
            self.log.warning(
                f'No wiki results for Vtuber "{vtuber}" in validity_check for trivia.'
            )
            return []  # Return empty list as cog expects a list

        page_url = f"https://virtualyoutuber.fandom.com/wiki/{x}"
        soup = await self._fetch_page_soup(page_url)  # soup can be None
        body = self._find_main_content_body(soup)  # body can be None

        if body is None:
            self.log.warning(
                f"Could not find mw-parser-output for {vtuber} ({self.name}) in trivia."
            )
            return []

        # Update self.image (consistent image extraction logic)
        self._update_page_image(soup, body)

        trivia_heading_element = None
        # Strategy 1: Find <span> with id containing "Trivia" (case-insensitive) and get its parent heading
        trivia_span = body.find("span", id=re.compile(r"trivia", re.I))
        if trivia_span and "trivia" in trivia_span.get_text(strip=True).lower():
            parent_heading = trivia_span.find_parent(
                ["h1", "h2", "h3", "h4", "h5", "h6"]
            )
            if parent_heading:
                trivia_heading_element = parent_heading

        # Strategy 2: If not found, search for <h2>, <h3> etc. containing "Trivia" text via mw-headline span.
        if not trivia_heading_element:
            possible_headers = body.find_all(
                ["h2", "h3", "h4"]
            )  # Common levels for sections
            for header in possible_headers:
                headline_span = header.find("span", class_="mw-headline")
                if (
                    headline_span
                    and "trivia" in headline_span.get_text(strip=True).lower()
                ):
                    trivia_heading_element = header
                    break

        msc_items = []
        if trivia_heading_element:
            self.log.debug(
                f"Found trivia heading for {self.name}: {trivia_heading_element.name} with text '{trivia_heading_element.get_text(strip=True)}'"
            )
            try:
                trivia_level = int(trivia_heading_element.name[1])
            except (IndexError, ValueError, TypeError):
                self.log.warning(
                    f"Could not determine level for trivia_heading_element: {trivia_heading_element.name}. Defaulting to 2."
                )
                trivia_level = 2  # Default to h2 level for safety

            current_element = trivia_heading_element.find_next_sibling()
            while current_element:
                # Stop condition: if we encounter another heading of the same or higher level
                if current_element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    try:
                        current_level = int(current_element.name[1])
                        if current_level <= trivia_level:
                            # Check if it's a significant section header (often has mw-headline)
                            if current_element.find("span", class_="mw-headline"):
                                self.log.debug(
                                    f"Stopping trivia collection at new section for {self.name}: {current_element.name} '{current_element.get_text(strip=True)}'"
                                )
                                break
                    except (IndexError, ValueError, TypeError):
                        pass  # Not a standard h-tag name like h1-h6

                if current_element.name == "ul":
                    for li in current_element.find_all(
                        "li", recursive=False
                    ):  # direct children
                        text_content = li.get_text(separator=" ", strip=True)
                        if text_content:
                            cleaned_text = re.sub(r"\[\d+\]", "", text_content).strip()
                            if cleaned_text:
                                msc_items.append(cleaned_text)

                current_element = current_element.find_next_sibling()
        else:
            self.log.info(
                f"Trivia section/heading not found for {vtuber} ({self.name})."
            )

        return msc_items

    async def image_link(self, vtuber: str, auto_correct: bool = True):
        session = await self._get_session()
        x = await self.validity_check(
            vtuber=vtuber, auto_correct=auto_correct, session=session
        )
        # self.name is set by validity_check caller, or should be set here if x is used for name
        self.name = x
        if x is None:
            return f'No wiki results for Vtuber "{vtuber}"'

        page_url = f"https://virtualyoutuber.fandom.com/wiki/{x}"
        soup = await self._fetch_page_soup(page_url)
        body = self._find_main_content_body(soup)
        self._update_page_image(soup, body)  # This will set self.image

        # If body is None, _update_page_image would have tried to find image from soup.
        # self.image will be "None" if nothing found.

        return self.image

    def _parse_trivia_from_body(self, body: Optional[Any]) -> List[str]:
        """
        Parses trivia items from the provided body content.
        This is an adaptation of the core logic from the trivia() method.
        """
        if not body:
            return []

        trivia_heading_element = None
        # Strategy 1: Find <span> with id containing "Trivia" (case-insensitive) and get its parent heading
        # Ensure the span's text actually is "Trivia" to avoid partial matches in ID.
        trivia_span = body.find(
            "span",
            id=re.compile(r"trivia", re.I),
            string=re.compile(r"^\s*Trivia\s*$", re.I),
        )
        if trivia_span:
            parent_heading = trivia_span.find_parent(
                ["h1", "h2", "h3", "h4", "h5", "h6"]
            )
            if parent_heading:
                trivia_heading_element = parent_heading

        # Strategy 2: If not found, search for <h2>, <h3> etc. containing "Trivia" text via mw-headline span.
        if not trivia_heading_element:
            possible_headers = body.find_all(["h2", "h3", "h4"])
            for header in possible_headers:
                headline_span = header.find("span", class_="mw-headline")
                if (
                    headline_span
                    and "trivia" in headline_span.get_text(strip=True).lower()
                ):
                    trivia_heading_element = header
                    break

        msc_items = []
        if trivia_heading_element:
            self.log.debug(
                f"Found trivia heading for {self.name} in _parse_trivia_from_body: {trivia_heading_element.name} with text '{trivia_heading_element.get_text(strip=True)}'"
            )
            try:
                trivia_level = int(trivia_heading_element.name[1])
            except (IndexError, ValueError, TypeError):
                trivia_level = 2  # Default

            current_element = trivia_heading_element.find_next_sibling()
            while current_element:
                if current_element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    try:
                        current_level = int(current_element.name[1])
                        if current_level <= trivia_level and current_element.find(
                            "span", class_="mw-headline"
                        ):
                            break
                    except (IndexError, ValueError, TypeError):
                        pass

                if current_element.name == "ul":
                    for li in current_element.find_all("li", recursive=False):
                        text_content = li.get_text(separator=" ", strip=True)
                        cleaned_text = self._clean_text(text_content)
                        if cleaned_text:
                            msc_items.append(cleaned_text)
                current_element = current_element.find_next_sibling()
        return msc_items

    async def infobox_details(
        self, vtuber: str, auto_correct: bool = True
    ) -> Dict[str, Any]:
        """Fetches and parses infobox details for a vtuber."""
        session = await self._get_session()
        page_name_slug = await self.validity_check(
            vtuber=vtuber, auto_correct=auto_correct, session=session
        )
        self.name = page_name_slug

        if page_name_slug is None:
            self.log.info(f'No wiki results for Vtuber "{vtuber}" for infobox_details.')
            return {}

        page_url = f"https://virtualyoutuber.fandom.com/wiki/{page_name_slug}"
        soup = await self._fetch_page_soup(page_url)

        if soup is None:
            # _fetch_page_soup already logs
            return {}

        # Update main image as a side effect of fetching the page
        body_content_for_image_update = self._find_main_content_body(soup)
        self._update_page_image(soup, body_content_for_image_update)

        return self._parse_infobox_details(soup, page_url)

    async def all(self, vtuber: str, auto_correct: bool = True):
        session = await self._get_session()
        x = await self.validity_check(
            vtuber=vtuber, auto_correct=auto_correct, session=session
        )
        self.name = x
        if x is None:
            return f'No wiki results for Vtuber "{vtuber}"'

        page_url = f"https://virtualyoutuber.fandom.com/wiki/{x}"
        soup = await self._fetch_page_soup(page_url)
        body = self._find_main_content_body(soup)
        self._update_page_image(soup, body)  # Sets self.image

        if body is None:
            self.log.warning(
                f"Could not find mw-parser-output for {vtuber} ({self.name}) in all method."
            )
            # Return a partial result or an error message
            return f"Could not parse main content for {vtuber}. Image link might be available: {self.image}"

        # Parse infobox details using the fetched soup
        infobox_data = {}
        if soup:  # Ensure soup is not None before parsing infobox
            infobox_data = self._parse_infobox_details(soup, page_url)

        # body = await self.decompose_useless(body) # Ensure body is not None if uncommented
        para = body.find_all("p", recursive=False, limit=3)
        summary = "Not available"
        annoying_string = para[0].find("i") if para else None
        if annoying_string != None:
            para.pop(0)

        summary = (para[1].text).strip()

        person_tag = body.find("span", id="Personality")
        prsn = "None"
        if person_tag != None:
            p_person_tag = person_tag.parent
            ph = p_person_tag.find_next_sibling()
            prsn = ""
            while True:
                if str(ph)[:3] != "<p>":
                    break
                prsn = prsn + "\n" + ph.text
                ph = ph.find_next_sibling()

        hs_tag = body.find("span", id="History")
        section = ""
        res = {}
        hs = "None"
        first_run = True
        if hs_tag != None:
            hs = ""
            p_hs_tag = hs_tag.parent
            next_node = p_hs_tag.find_next_sibling()
            # r_next_node = p_hs_tag.find_next_sibling()
            while True:
                if str(next_node).startswith("<h3>"):
                    if first_run is False:
                        res[section] = hs
                        hs = ""
                        section = next_node.text
                    else:
                        section = next_node.text
                if str(next_node).startswith("<h2>"):
                    if hs != "":
                        res[section] = hs
                    break

                if next_node.name == "p":
                    if next_node.text != "":
                        real_t = re.sub("\[[0-9]+\]", "", next_node.text)
                        hs = hs + "\n" + real_t
                        if first_run is True:
                            first_run = False
                next_node = next_node.find_next_sibling()

        parsed_trivia_list = self._parse_trivia_from_body(body)

        def trim_20_words_until_period(text):
            words = text.split()
            if len(words) <= 10:
                return text

            # Join first 20 words
            partial = " ".join(words[:10])

            # Find where this substring ends in the original text
            index = text.find(partial)
            remaining = text[index + len(partial) :]

            # Search for the next period after the first 20 words
            match = re.search(r"\.", remaining)
            if match:
                end_index = index + len(partial) + match.end()
                return text[:end_index].strip()
            else:
                return partial.strip()

        raw_history = hs
        if isinstance(raw_history, list) and raw_history:
            history_text = raw_history[0]
        elif isinstance(raw_history, str):
            history_text = raw_history
        else:
            history_text = ""

        trivia = [
            trim_20_words_until_period(item)
            # Take up to the first 3 trivia items
            for item in parsed_trivia_list[:3]
        ]

        self.log.warning(infobox_data)

        return {
            "vtuber": self.name,
            "summary": trim_20_words_until_period(summary),
            "personality": trim_20_words_until_period(
                prsn.strip(),
            ),
            "history": trim_20_words_until_period(history_text).strip(),
            "trivia": trivia,
            "infobox_details": infobox_data,
            "image_link": self.image,
        }
