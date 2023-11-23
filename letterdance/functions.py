"""
Letter Dance
by https://github.com/ntoskrn/letterdance
"""

from PIL import Image
import imageio
import os
from redbot.core.data_manager import bundled_data_path
import tempfile

class LetterDance:
    """
    Class to create a dance animation by combining letter GIFs horizontally.
    """

    def __init__(self, letters, output):
        """
        Initialize LetterDance object.

        Args:
            letters (str): String containing letters to be animated.
            output (str): Output filename for the dance animation.
        """

        self.letters = list(letters)
        self.output = output

    def get_frame_count(self, filename):
        """
        Get the number of frames in a GIF file.

        Args:
            filename (str): Path to the GIF file.

        Returns:
            int: Number of frames in the GIF.
        """

        return Image.open(filename).n_frames

    def get_duration_in_milliseconds(self, filename):
        """
        Get the duration of each frame in a GIF file in milliseconds.

        Args:
            filename (str): Path to the GIF file.

        Returns:
            int: Duration of each frame in milliseconds.
        """

        return Image.open(filename).info["duration"]

    def get_dimensions(self, filename):
        """
        Get the dimensions (width, height) of an image file.

        Args:
            filename (str): Path to the image file.

        Returns:
            tuple: Width and height of the image.
        """

        return Image.open(filename).size

    def dance(self, scale_factor=1):
        """
        Create the dance animation by combining letter GIFs horizontally.

        Args:
            scale_factor (int): Scaling factor for the letters. Default is 1 (no scaling).
        """

        combined_width = 0
        max_width = 0
        max_height = 0
        max_duration = 0
        max_frame_count = 0

        for letter in self.letters:
            if letter == " ":
                continue
            syspath = f"{bundled_data_path(self)}"
            # Replace "?" with "qm" in the file path
            letter = letter.replace("?", "qm")
            path = os.path.join(syspath, letter + ".gif")

            frame_count = self.get_frame_count(path)
            duration = self.get_duration_in_milliseconds(path)
            width, height = self.get_dimensions(path)

            if scale_factor > 1:
                width *= scale_factor
                height *= scale_factor

            combined_width += width
            max_width = max(max_width, width)
            max_height = max(max_height, height)
            max_duration = max(max_duration, duration)
            max_frame_count = max(max_frame_count, frame_count)

        combined_width = int(combined_width)
        max_height = int(max_height)
        max_width = int(max_width)

        combined_width += "".join(self.letters).count(" ") * max_width

        print("Max Width: " + str(max_width))
        print("Max Height: " + str(max_height))
        print("Max Duration: " + str(max_duration))
        print("Max Frame Count: " + str(max_frame_count))

        print("\n--RENDERING--\n")

        frames = []

        for i in range(max_frame_count):
            frame_buffer = Image.new("RGBA", (combined_width, max_height))
            x_offset = 0
            print("Frame: " + str(i) + "/" + str(max_frame_count))

            for letter in self.letters:
                try:
                    if letter == " ":
                        x_offset += max_width
                        continue
                    if letter == "?":
                       letter = "qm"


                    syspath = f"{bundled_data_path(self)}"      
                    gif = imageio.get_reader(os.path.join(syspath, letter + ".gif"))
                    frame = gif.get_data(i)

                    frame_width, frame_height = frame.shape[1], frame.shape[0]
                    frame_image = Image.fromarray(frame).convert("RGBA")

                    if scale_factor > 1:
                        frame_image = frame_image.resize(
                            (frame_width * scale_factor, frame_height * scale_factor)
                        )

                    frame_buffer.paste(
                        frame_image,
                        (x_offset, int((max_height - frame_image.height) / 2)),
                    )

                    x_offset += frame_image.width

                except (IndexError, EOFError):
                    print("Error: " + letter + ".gif")
                    pass

            frames.append(frame_buffer.copy())

        # Use a temporary file to store the frames
        with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as temp_file:
            frames[1].save(
                temp_file.name,
                save_all=True,
                append_images=frames[1:],
                duration=max_duration,
                loop=0,
                disposal=2
            )

        return temp_file.name  



