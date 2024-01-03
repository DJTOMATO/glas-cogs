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
import textwrap


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


def convert_to_discord_file(image):
    with io.BytesIO() as file_content:
        image.save(file_content, format="PNG")
        file_content.seek(0)
        return discord.File(file_content, filename="image.png")


def convert_to_image(canvas):
    # If canvas is already an Image object, return it
    if isinstance(canvas, Image.Image):
        return canvas

    # Otherwise, handle the conversion logic here
    # For example, open the canvas as an image
    return Image.open(canvas)


async def background_randomizer(self, ctx, type):
    path = f"{bundled_data_path(self)}/backgrounds/{type}"
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    random_file = random.choice(files)
    final_path = f"{bundled_data_path(self)}/backgrounds/{type}/{random_file}"
    return final_path


async def character_randomizer(self, ctx, type):
    type = str(type)
    path = f"{bundled_data_path(self)}/sprites/{type}"
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    random_file = random.choice(files)
    final_path = f"{bundled_data_path(self)}/sprites/{type}/{random_file}"

    try:
        # Load the image using PIL
        character_image = Image.open(final_path).convert("RGBA")

        # Check if the image has transparency
        if "A" not in character_image.getbands():
            # If the image does not have an alpha channel, create one
            alpha_image = Image.new("L", character_image.size, 255)
            character_image.putalpha(alpha_image)

    except Exception as e:
        # Log the error details
        self.log.error("An error occurred while processing the image:")
        self.log.error(str(e))
        character_image = None

    return final_path, character_image


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
    parameters = {
        key: parameters.get(key, default_value)
        for key, default_value in default_values.items()
    }

    # BG
    if parameters["bg"] is None:
        parameters["bg"] = "mainbuilding"

    final_path = await background_randomizer(self, ctx, parameters["bg"])

    # Load the background image directly as the canvas
    # Create a new transparent canvas
    canvas = Image.new("RGBA", (640, 480), (0, 0, 0, 255))

    # Load the background image
    self.log.info("Selected Background Image Path: %s", final_path)
    background = Image.open(final_path).convert("RGBA")
    self.log.info("Selected Background Image Size: %s", background.size)
    self.log.error("Background Size:: %s", background.size)
    self.log.error("Canvas Size:: %s", canvas.size)
    # Paste the background onto the canvas
    canvas.paste(background, (0, 0), background)
    self.log.info("Canvas Size after Loading Background: %s", canvas.size)
    meta_image = Image.open(
        f"{bundled_data_path(self)}/metaworld/hana1.webp"
    )  # Replace with the correct image path

    imageContainer = []
    for position in ["left", "right", "center", "metaleft", "metaright", "metacenter"]:
        if parameters[position]:
            image_path, character = await character_randomizer(
                self, ctx, CHARACTER_CHOICES[parameters[position]]
            )
            imageContainer.append((position, character))

    world = "meta"

    for position, character in imageContainer:
        if character.mode != "RGBA":
            character = character.convert("RGBA")

        if world == "meta":
            meta_position = position
            if meta_position == "left":
                # Use direct paste without alpha_composite
                canvas.paste(
                    character,
                    (int(canvas.width * -0.25), int(canvas.width * -0.05)),
                    character,
                )
            elif meta_position == "right":
                canvas.paste(
                    character,
                    (int(canvas.width * 0.41), int(canvas.width * -0.05)),
                    character,
                )
            elif meta_position == "center":
                canvas.paste(
                    character,
                    (int(canvas.width * 0.15), int(canvas.width * -0.05)),
                    character,
                )
        else:
            # Non-meta world
            if position == "left":
                canvas.paste(
                    character,
                    (
                        int(canvas.width * -0.13),
                        int(canvas.width * -0.05),
                    ),
                    character,
                )
            elif position == "right":
                canvas.paste(
                    character,
                    (
                        int(canvas.width * 0.41),
                        int(canvas.width * -0.05),
                    ),
                    character,
                )
            elif position == "center":
                canvas.paste(
                    character,
                    (
                        int(canvas.width * 0.15),
                        int(canvas.width * -0.05),
                    ),
                    character,
                )
    text_color = parameters.get("color1", "#000000")

    brightness = 0.55
    enhancer = ImageEnhance.Brightness(canvas)
    canvas = enhancer.enhance(brightness)
    canvas = canvas.filter(ImageFilter.BLUR)  # Assuming you want to remove the filter
    draw = ImageDraw.Draw(canvas)

    font_size = max(int((8 * 100) / canvas.height), 30)
    font_path = f"{bundled_data_path(self)}/fonts/sazanami-gothic.ttf"
    font = ImageFont.truetype(font_path, size=font_size)
    max_text_width = canvas.width - 2 * (canvas.width * 0.065)
    text_color = parameters.get("color1", "#000000")
    text_size = draw.textsize(parameters["text1"], font)

    # Adjusted text position (start from top-left corner)
    text_position = (
        canvas.width * 0.065,
        canvas.height * 0.055,
    )
    max_width = canvas.width * 0.9
    wrapped_text = textwrap.fill(parameters["text1"], width=20)
    wrapped_lines = wrapped_text.splitlines()
    # Draw multiline text
    current_y = text_position[1]

    shadow_offset = (2, 2)
    for line in wrapped_lines:
        line_width, line_height = draw.textsize(line, font=font)

        # Draw text shadow
        draw.text(
            (
                (canvas.width - line_width) / 2 + shadow_offset[0],
                current_y + shadow_offset[1],
            ),
            line,
            font=font,
            fill="#000000",  # Shadow color
            align="center",  # Center align the shadow
        )

        # Draw actual text
        draw.text(
            ((canvas.width - line_width) / 2, current_y),
            line,
            font=font,
            fill=text_color,
            align="center",  # Center align the text
        )
        current_y += line_height
        # Convert the canvas to an Image object
        image = convert_to_image(canvas)

    return image


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
