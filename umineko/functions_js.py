import discord
from rapidfuzz import process
from redbot.core import commands
from redbot.core.commands import BadArgument, MemberConverter
from unidecode import unidecode
from redbot.core.data_manager import bundled_data_path
import regex as re
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageEnhance
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
    path = f"{bundled_data_path(self)}/backgrounds/{type}"
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    random_file = random.choice(files)
    final_path = f"{bundled_data_path(self)}/backgrounds/{type}/{random_file}"
    return final_path


async def character_randomizer(self, ctx, type):
    path = f"{bundled_data_path(self)}/sprites/{type}"
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    random_file = random.choice(files)
    final_path = f"{bundled_data_path(self)}/sprites/{type}/{random_file}"
    return final_path


async def generate(self, ctx, **parameters):
    # Create a dictionary with default values
    default_values = {
        "text1": "",
        "text2": "",
        "left": "",
        "center": "",
        "right": "",
        "metaleft": "",
        "metacenter": "",
        "metaright": "",
        "color1": "",
        "color2": "",
        "bg": "",
    }
    # Update the default values with the provided parameters
    parameters = {
        key: parameters.get(key, default_value)
        for key, default_value in default_values.items()
    }

    self.log.warning(
        f"args: {', '.join(f'{key}={value}' for key, value in parameters.items())}"
    )

    # BG
    final_path = await background_randomizer(self, ctx, parameters["bg"])

    canvas = Image.new("RGB", (640, 480), "white")
    draw = ImageDraw.Draw(canvas)

    # FONT
    font = ImageFont.truetype(
        f"{bundled_data_path(self)}/fonts/sazanami-gothic.ttf", size=12
    )

    brightness = 0.55
    enhancer = ImageEnhance.Brightness(canvas)
    canvas = enhancer.enhance(brightness)

    # Abre BG
    bgImage = Image.open(f"{final_path}")  # Replace with the correct image path
    if bgImage:
        canvas.paste(bgImage, (0, 0))

    meta_image = Image.open(
        f"{bundled_data_path(self)}/metaworld/hana1.webp"
    )  # Replace with the correct image path

    imageContainer = []
    for position in ["left", "right", "center", "metaleft", "metaright", "metacenter"]:
        if parameters[position]:
            character = await character_randomizer(self, ctx, parameters[position])
            imageContainer.append((position, character))

    for position, child in imageContainer:
        if child.dataset["show"] == "true":
            world = child.dataset.get("world", "normal")

            if world == "meta":
                canvas = canvas.filter(ImageFilter.Brightness(brightness))
                meta = True
                meta_position = child.dataset.get("position", "center")

                if meta_position == "left":
                    canvas.paste(
                        child,
                        (int(canvas.width * -0.25), int(canvas.width * -0.05)),
                        child,
                    )
                elif meta_position == "right":
                    canvas.paste(
                        child,
                        (int(canvas.width * 0.41), int(canvas.width * -0.05)),
                        child,
                    )
                elif meta_position == "center":
                    canvas.paste(
                        child,
                        (int(canvas.width * 0.15), int(canvas.width * -0.05)),
                        child,
                    )
            else:
                meta = False
                position = child.dataset.get("position", "left")

                if position == "left":
                    canvas.paste(
                        child,
                        (int(canvas.width * -0.13), int(canvas.width * -0.05)),
                        child,
                    )
                elif position == "right":
                    canvas.paste(
                        child,
                        (int(canvas.width * 0.41), int(canvas.width * -0.05)),
                        child,
                    )
                elif position == "center":
                    canvas.paste(
                        child,
                        (int(canvas.width * 0.15), int(canvas.width * -0.05)),
                        child,
                    )

    canvas = canvas.filter(ImageFilter.BLUR)  # Assuming you want to remove the filter

    # Set font size to be responsive with window
    font_size = (8 * 100) / canvas.height
    font = ImageFont.truetype(
        f"{bundled_data_path(self)}/fonts/sazanami-gothic.ttf", size=font_size
    )
    draw.text(
        (canvas.width * 0.065, canvas.width * 0.055), parameters["text1"], font=font
    )

    # You can continue to draw text and perform other operations with the canvas and draw objects

    # Convert the canvas to a Discord File
    image_file = convert_to_discord_file(canvas)
    return image_file


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
