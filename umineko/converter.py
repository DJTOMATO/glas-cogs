import os
from PIL import Image

def convert_to_webp(input_path, output_path):
    try:
        img = Image.open(input_path)
        img.save(output_path, 'webp')
        return True
    except Exception as e:
        print(f"Error converting {input_path}: {e}")
        return False

def convert_directory(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith('.png'):
                png_path = os.path.join(dirpath, filename)
                webp_filename = os.path.splitext(filename)[0] + '.webp'
                webp_path = os.path.join(dirpath, webp_filename)

                if convert_to_webp(png_path, webp_path):
                    os.remove(png_path)
                    print(f"Converted and removed: {png_path}")
                else:
                    print(f"Failed to convert: {png_path}")

if __name__ == "__main__":
    input_directory = "assets"  # Replace with the path to your directory
    convert_directory(input_directory)