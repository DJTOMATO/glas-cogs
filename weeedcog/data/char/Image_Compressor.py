import os
from PIL import Image

MAX_SIZE = (500, 500)  # Max width and height
QUALITY = 85
SUPPORTED_EXTS = (".jpg", ".jpeg", ".png", ".webp")


def compress_and_resize(image_path):
    try:
        with Image.open(image_path) as img:
            original_size = os.path.getsize(image_path)
            original_dims = img.size
            initial_img_mode = img.mode

            # Resize while maintaining aspect ratio
            img.thumbnail(MAX_SIZE)

            # Determine output format and prepare save options
            file_ext = os.path.splitext(image_path)[1].lower()
            save_options = {}

            if file_ext in (".jpg", ".jpeg"):
                # JPEGs do not support transparency.
                # Convert to RGB if the image has an alpha channel or is paletted.
                if img.mode in (
                    "RGBA",
                    "LA",
                    "P",
                ):  # LA is Luminance with Alpha, P is Paletted
                    img = img.convert("RGB")
                save_options["quality"] = QUALITY
                save_options["optimize"] = True
            elif file_ext == ".png":
                # PNGs support transparency; preserve it.
                # Pillow's save for PNG handles RGBA and P with transparency correctly.
                save_options["optimize"] = True
            elif file_ext == ".webp":
                # WebP supports transparency; preserve it.
                # Pillow's save for WebP handles RGBA and P with transparency correctly.
                save_options["quality"] = QUALITY

            # Save (overwrite) with appropriate options
            img.save(image_path, **save_options)

            new_size = os.path.getsize(image_path)
            print(
                f"✅ {os.path.basename(image_path)}: {original_dims} ({initial_img_mode}) → {img.size} ({img.mode}), {original_size//1024}KB → {new_size//1024}KB"
            )
    except Exception as e:
        print(f"❌ Error processing {image_path}: {e}")


def main():
    for filename in os.listdir("."):
        if filename.lower().endswith(SUPPORTED_EXTS):
            compress_and_resize(filename)


if __name__ == "__main__":
    main()
