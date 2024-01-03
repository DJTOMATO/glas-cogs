import discord
from rapidfuzz import process
from redbot.core import commands
from redbot.core.commands import BadArgument, MemberConverter
from unidecode import unidecode
from redbot.core.data_manager import bundled_data_path
import regex as re
from PIL import Image, ImageFilter, ImageDraw, ImageFont
import io, os, random, re
from redbot.core.app_commands import Choice
import logging


COLOR_CHOICES = {
    "red": "#ff0000",
    "blue": "#5decff",
    "golden": "#ffcc00",
    "white": "#ffffff",
}

LOCATION_CHOICES = {
    "airport": "Airport",
    "aquarium": "Aquarium",
    "chapel": "Chapel",
    "city": "City",
    "forest": "Forest",
    "garden": "Garden",
    "guesthouse": "Guesthouse",
    "kawhouse": "Kawhouse",
    "kumhouse": "Kumhouse",
    "mainbuilding": "Main Building",
    "nanclinic": "Nan Clinic",
    "restaurant": "Restaurant",
    "rosehouse": "Rosehouse",
    "school": "School",
    "secrethouse": "Secret House",
    "ship": "Ship",
    "subway": "Subway",
}

CHARACTER_CHOICES = {
    "Ange Ushiromiya": "ange",
    "Battler Ushiromiya": "battler",
    "Beatrice": "beatrice",
    "Bernkastel": "bernkastel",
    "Chiester 4101": "chiester41",
    "Chiester 45": "chiester45",
    "Dlanor A. Knox": "dlanor",
    "Erika Furudo": "erika",
    "Eva Ushiromiya": "eva",
    "Eva-Beatrice": "evatrice",
    "Gaap": "gaap",
    "Genji Ronoue": "genji",
    "Gohda": "gohda",
    "Jessica Ushiromiya": "jessica",
    "Kinzo Ushiromiya": "kinzo",
    "Kumasawa": "kumasawa",
    "Kyrie Ushiromiya": "kyrie",
    "Lambda Delta": "lambda",
    "Maria Ushiromiya": "maria",
    "Terumasa Nanjo": "nanjo",
    "Natsuhi Ushiromiya": "natsuhi",
    "Rosa Ushiromiya": "rosa",
    "Rudolf Ushiromiya": "rudolf",
    "Shannon": "shannon",
    "Virgilia": "virgilia",
    "Satan": "satan",
    "Beelzebub": "beelze",
    "Kanon": "kanon",
    "Sakutaro": "sakutaro",
    "Willard H. Wright": "will",
    "Zepar": "zepar",
    "Claire Vauxof Bernardus": "claire",
    "Cornelia": "cornelia",
    "Leviathan": "levia",
    "Belphegor": "belphe",
    "Amakusa": "amakusa",
    "Chiester 00": "chiester00",
    "Asmodeus": "asmo",
    "Featherine Augustus Aurora": "featherine",
    "Furfur": "furfur",
    "Lion Ushiromiya": "lion",
    "Gertrude": "gertrude",
    "Hideyoshi Ushiromiya": "hideyoshi",
    "Lucifer": "luci",
    "Mammon": "mammon",
    "Ronove": "ronove",
    "Krauss Ushiromiya": "krauss",
}


def convert_to_discord_file(image_data):
    """Convert image data to a Discord File."""
    # Replace the following lines with your actual conversion logic
    with io.BytesIO(image_data) as file_content:
        file_content.seek(0)
        discord_file = discord.File(file_content, filename="image.png")

    return discord_file


async def background_randomizer(self, ctx, type):
    path = f"{bundled_data_path(self)}/assets/backgrounds/{type}"
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    random_file = random.choice(files)
    final_path = f"{bundled_data_path(self)}/assets/backgrounds/{type}/{random_file}"
    return final_path


async def character_randomizer(self, ctx, type):
    path = f"{bundled_data_path(self)}/assets/sprites/{type}"
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    random_file = random.choice(files)
    final_path = f"{bundled_data_path(self)}/assets/sprites/{type}/{random_file}"
    return final_path


async def generate(self, ctx, **kwargs):
    self.log.warning(f"args: {kwargs}")
    # BG
    final_path = background_randomizer(kwargs=type)

    canvas = Image.new("RGB", (640, 480), "white")
    ctx = ImageDraw.Draw(canvas)
    ctx.rectangle([(0, 0), (canvas.width, canvas.height)], fill="white")
    # FONT
    font = ImageFont.truetype(
        f"{bundled_data_path(self)}/assets/fonts/sazanami-gothic.ttf", size=12
    )

    try:
        font.load()
        # No direct equivalent for document.fonts.add(loaded_face) in Python Imaging Library
    except Exception as error:
        print(error)

    brightness = 0.55
    ctx.filter(ImageFilter.Brightness(brightness))
    # Abre BG
    bgImage = Image.open(f"{final_path}")  # Replace with the correct image path
    if bgImage:
        ctx.draw_image(bgImage, (0, 0, canvas.width, canvas.height))
    meta = False

    meta_image = Image.open(
        f"{bundled_data_path(self)}/assets/metaworld/hana1.webp"
    )  # Replace with the correct image path

    if left:
        left = character_randomizer(left)

    imageContainer = Image.open(
        "imageContainer.jpg"
    )  # Replace with the correct image path

    for child in imageContainer:
        if child.dataset["show"] == "true":
            world = child.dataset.get("world", "normal")

            if world == "meta":
                ctx.draw_image(meta_image, (0, 0, canvas.width, canvas.height))
                ctx.filter(ImageFilter.Brightness(brightness))
                position = child.dataset.get("position", "center")

                if position == "left":
                    ctx.draw_image(
                        child,
                        (
                            canvas.width * -0.25,
                            canvas.width * -0.05,
                            canvas.width * 0.75,
                            canvas.width * 0.6,
                        ),
                    )
                elif position == "right":
                    ctx.draw_image(
                        child,
                        (
                            canvas.width * 0.41,
                            canvas.width * -0.05,
                            canvas.width * 0.75,
                            canvas.width * 0.6,
                        ),
                    )
                elif position == "center":
                    ctx.draw_image(
                        child,
                        (
                            canvas.width * 0.15,
                            canvas.width * -0.05,
                            canvas.width * 0.75,
                            canvas.width * 0.6,
                        ),
                    )
            else:
                if meta:
                    ctx.filter(ImageFilter.Brightness(0.3))

                position = child.dataset.get("position", "left")

                if position == "left":
                    ctx.draw_image(
                        child,
                        (
                            canvas.width * -0.13,
                            canvas.width * -0.05,
                            canvas.width * 0.75,
                            canvas.width * 0.6,
                        ),
                    )
                elif position == "right":
                    ctx.draw_image(
                        child,
                        (
                            canvas.width * 0.41,
                            canvas.width * -0.05,
                            canvas.width * 0.75,
                            canvas.width * 0.6,
                        ),
                    )
                elif position == "center":
                    ctx.draw_image(
                        child,
                        (
                            canvas.width * 0.15,
                            canvas.width * -0.05,
                            canvas.width * 0.75,
                            canvas.width * 0.6,
                        ),
                    )

    ctx.global_alpha = 1
    ctx.filter(ImageFilter.BLUR)  # Assuming you want to remove the filter

    # Set font size to be responsive with window
    font_size = (8 * 100) / canvas.height
    ctx.font = f"{font_size}vh SazanamiGothic"

    text_x = canvas.width * 0.065
    text_y = canvas.width * 0.055
    max_text_width = canvas.width - canvas.width * 0.065 * 2
    line_height = canvas.width * 0.034
    text = text
    ctx.textShadow = (2, 2, "#000000")
    wrap_text(ctx, text, text_x, text_y, max_text_width, line_height)


def wrap_text(ctx, text, x, y, max_width, line_height):
    color_codes = {
        "red": "#ff0000",
        "blue": "#5decff",
        "golden": "#ffcc00",
    }

    regex = re.compile(r"\[(\w+)\](.*?)\[\/\w+\]|([^\[\n]+)|(\n)")
    matches = regex.findall(text)

    current_x = x
    current_y = y

    for match in matches:
        color, content, plain_text, new_line = match

        if new_line:
            current_y += line_height
            current_x = x
        elif color:
            text_color = color_codes.get(color, "white")
            words = content.split(" ")
            line = ""

            for word in words:
                test_line = line + word + " "
                metrics = ctx.textsize(test_line)
                test_width = metrics[0]

                if current_x + test_width > x + max_width:
                    ctx.text((current_x, current_y), line, fill=text_color)
                    current_y += line_height
                    line = word + " "
                    current_x = x
                else:
                    line = test_line

            ctx.text((current_x, current_y), line, fill=text_color)
            line_metrics = ctx.textsize(line)
            current_x += line_metrics[0] - ctx.textsize(" ")[0]
        elif plain_text:
            words = plain_text.split(" ")
            line = ""

            for word in words:
                test_line = line + word + " "
                metrics = ctx.textsize(test_line)
                test_width = metrics[0]

                if current_x + test_width > x + max_width:
                    ctx.text((current_x, current_y), line, fill="white")
                    current_y += line_height
                    line = word + " "
                    current_x = x
                else:
                    line = test_line

            ctx.text((current_x, current_y), line, fill="white")
            line_metrics = ctx.textsize(line)
            current_x += line_metrics[0] - ctx.textsize(" ")[0]


# Assuming the ctx object is from the Python Imaging Library (Pillow) and has a method 'text'.
# If you're using a different library, adapt the text rendering accordingly.


CHOICE_DESC = {
    "left": "Left character",
    "center": "Center character",
    "right": "Right character.",
    "text1": "Top text.",
    "text2": "Center text (optional).",
    "color1": "The truth level.",
    "color2": "Truth Level.",
    "metaleft": "Meta Character",
    "metaright": "Meta Character",
    "metacenter": "Meta Character",
}

CHOICES = {
    # "left": [
    #     Choice(name=title, value=value) for value, title in CHARACTER_CHOICES.items()
    # ],
    # "center": [
    #     Choice(name=title, value=value) for value, title in CHARACTER_CHOICES.items()
    # ],
    # "right": [
    #     Choice(name=title, value=value) for value, title in CHARACTER_CHOICES.items()
    # ],
    "color1": [
        Choice(name=value, value=title) for value, title in COLOR_CHOICES.items()
    ],
    "color2": [
        Choice(name=value, value=title) for value, title in COLOR_CHOICES.items()
    ],
    "bg": [
        Choice(name=title, value=value) for value, title in LOCATION_CHOICES.items()
    ],
    # "metaleft": [
    #     Choice(name=title, value=value) for value, title in CHARACTER_CHOICES.items()
    # ],
    # "metaright": [
    #     Choice(name=title, value=value) for value, title in CHARACTER_CHOICES.items()
    # ],
    # "metacenter": [
    #     Choice(name=title, value=value) for value, title in CHARACTER_CHOICES.items()
    # ],
}
