#!/usr/bin/env python
import argparse
import os
import pathlib
import sys

from PIL import Image, ImageFont, ImageDraw, ImageFilter
from colorama import Fore, Style, init
from yaspin import yaspin

from exif import generate_exif_dict
# spinner = Halo(text='Processing', spinner='dots', color='cyan')
from utils import dotdict, DictX

parser = argparse.ArgumentParser()

parser.add_argument('image_paths', type=pathlib.Path, nargs='?', help='Path to image or folder')
parser.add_argument('-f', '--font', type=pathlib.Path, help='Path to OTF / TTF font', default="./fonts/SF-Pro-Display-Medium.otf")

args = parser.parse_args()
print(args)

'''
    global
    spaces in px
'''
SPACE_FROM_BOTTOM = 60
SPACE_FROM_LEFT = 80
SPACE_BETWEEN_BOXES = 40
INCLUDED_EXTENSIONS = ['jpg', 'jpeg', 'png']

'''
    BOX
'''
# Degree of transparency, 0-100%
BOX_TRANSPARENCY = 15
BOX_PADDING = dotdict({"top": 20, "right": 50, "bottom": 35, "left": 50})

BOX_OPACITY = int(255 * (BOX_TRANSPARENCY / 100))

'''
    Text
'''
# FONT_SIZE = 125
# as percent
FONT_SIZE = 2.3
FONT_ITALIC = ImageFont.truetype("./fonts/SF-Pro-Display-LightItalic.otf", 125)
TEXT_TRANSPARENCY = 100

TEXT_OPACITY = int(255 * (BOX_TRANSPARENCY / 100))

EXIF_TAGS_TO_PRINT = {
    "Model": "Model",
    "Lens": "LensModel",
    "Aperture": "ApertureValue",
    "FocalLength": "FocalLength",
    "Exposure": "ExposureTime",
    "ISO": "ISOSpeedRatings",
}

init()

spinner = yaspin(text="Processing images", color="cyan")


class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


# save image with high quality and same ICC Profile
def _save_image(img):
    filepath = os.path.dirname(img.filename)
    filename = os.path.basename(img.filename)
    new_path = os.path.join(filepath, 'EXIF')
    if not os.path.exists(new_path):
        os.makedirs(new_path)

    fullpath = os.path.join(filepath, 'EXIF', filename)
    img.save(fullpath, quality=100, subsampling=0, format='JPEG', icc_profile=img.info.get('icc_profile', ''))
    # spinner.write(' ✔ Saved %s to %s' % (img.filename, fullpath))


def draw_image(img, exif_info, count, current):
    # spinner.text(f"Processing images {count}/{current}")
    font_size = round(img.height * FONT_SIZE / 100)
    font = ImageFont.truetype(str(args.font), font_size)
    text_size_space = font.getsize(' ')

    image_for_blur = img

    rectangle_y = image_for_blur.height - SPACE_FROM_BOTTOM

    box_padding_percent = dotdict(
        {
            "top": int(font_size * 16 / 100),
            "right": int(font_size * 40 / 100),
            "bottom": int(font_size * 28 / 100),
            "left": int(font_size * 40 / 100)
        }
    )

    mask = Image.new('L', image_for_blur.size, 0)
    draw_blurred = ImageDraw.Draw(mask)
    for name, value in reversed(exif_info.items()):
        if name == 'Exposure':
            value = "%ss" % str(value)
        elif name == 'Aperture':
            value = 'f%s' % str(value)
        else:
            value = str(value)

        name = "%s:" % str(name)

        text_size_description = font.getsize(name)
        text_size_value = font.getsize(value)
        rectangle_height = text_size_description[1] + box_padding_percent.top + box_padding_percent.bottom
        rectangle_width = text_size_description[0] + text_size_value[0] + text_size_space[0] + box_padding_percent.left + box_padding_percent.right
        rectangle_y = rectangle_y - rectangle_height
        rectangle_x = 0 + SPACE_FROM_LEFT
        # rectangle_x = int(img.width / 2)

        rectangle_position = [
            rectangle_x,
            rectangle_y,
            rectangle_x + rectangle_width,
            rectangle_y + rectangle_height,
        ]

        # draw.rectangle(rectangle_position, fill=(255, 255, 255, BOX_OPACITY))

        draw_blurred.rounded_rectangle(rectangle_position, fill=255, radius=7)
        rectangle_y = rectangle_y - SPACE_BETWEEN_BOXES

    blurred_img = image_for_blur.filter(ImageFilter.GaussianBlur(30))
    img.paste(blurred_img, mask=mask)

    draw_text = ImageDraw.Draw(img, "RGBA")
    rectangle_y = img.height - SPACE_FROM_BOTTOM
    for name, value in reversed(exif_info.items()):
        if name == 'Exposure':
            value = "%ss" % str(value)
        elif name == 'Aperture':
            value = 'f%s' % str(value)
        else:
            value = str(value)

        name = "%s:" % str(name)

        text_size_description = font.getsize(name)
        text_size_value = font.getsize(value)
        rectangle_height = text_size_description[1] + box_padding_percent.top + box_padding_percent.bottom
        rectangle_width = text_size_description[0] + text_size_value[0] + text_size_space[0] + box_padding_percent.left + box_padding_percent.right
        rectangle_y = rectangle_y - rectangle_height
        rectangle_x = 0 + SPACE_FROM_LEFT
        # rectangle_x = int(img.width / 2)

        rectangle_position = [
            rectangle_x,
            rectangle_y,
            rectangle_x + rectangle_width,
            rectangle_y + rectangle_height,
        ]

        # draw.rectangle(rectangle_position, fill=(255, 255, 255, BOX_OPACITY))

        draw_text.rounded_rectangle(rectangle_position, fill=(255, 255, 255, BOX_OPACITY), radius=7)
        #

        # # drop shadow
        # blurred = Image.new('RGBA', img.size)
        # draw_blurred = ImageDraw.Draw(blurred)
        # draw_blurred.text(xy=(rectangle_x + BOX_PADDING.left + 3, rectangle_y + BOX_PADDING.top + 3), text=name, fill=(0, 0, 0, 100), font=font)
        # blurred = blurred.filter(ImageFilter.BoxBlur(3))
        #
        # # Paste soft text onto background
        # img.paste(blurred, blurred)

        # icon = Image.open('./icons/aperture.png')
        # icon.convert('RGBA')
        #
        # icon.thumbnail((font_size, font_size), Image.ANTIALIAS)
        #
        # img.paste(icon, (rectangle_x + BOX_PADDING.left, rectangle_y + BOX_PADDING.top), icon)
        draw_text.text((rectangle_x + box_padding_percent.left, rectangle_y + box_padding_percent.top), name, (255, 255, 255, 255), font=font)

        draw_text.text(
            (rectangle_x + box_padding_percent.left + text_size_description[0] + text_size_space[0], rectangle_y + box_padding_percent.top),
            str(value),
            (255, 255, 255, 255),
            font=font
        )
        rectangle_y = rectangle_y - SPACE_BETWEEN_BOXES

    _save_image(img)


def _generate_draw_data(img, exif_info):
    font_size = round(img.height * FONT_SIZE / 100)
    font = ImageFont.truetype(str(args.font), font_size)
    text_size_space = font.getsize(' ')
    rectangle_y = img.height - SPACE_FROM_BOTTOM
    box_padding_percent = dotdict(
        {
            "top": int(font_size * 16 / 100),
            "right": int(font_size * 40 / 100),
            "bottom": int(font_size * 28 / 100),
            "left": int(font_size * 40 / 100)
        }
    )
    virtual_drawing = DictX({})
    for name, value in reversed(exif_info.items()):
        if name == 'Exposure':
            value = "%ss" % str(value)
        elif name == 'Aperture':
            value = 'f%s' % str(value)
        else:
            value = str(value)

        name = "%s:" % str(name)

        text_size_description = font.getsize(name)
        text_size_value = font.getsize(value)
        rectangle_height = text_size_description[1] + box_padding_percent.top + box_padding_percent.bottom
        rectangle_width = text_size_description[0] + text_size_value[0] + text_size_space[0] + box_padding_percent.left + box_padding_percent.right
        rectangle_y = rectangle_y - rectangle_height
        rectangle_x = 0 + SPACE_FROM_LEFT
        # rectangle_x = int(img.width / 2)

        rectangle_position = [
            rectangle_x,
            rectangle_y,
            rectangle_x + rectangle_width,
            rectangle_y + rectangle_height,
        ]

        virtual_drawing[name] = DictX({
            "rectangle": DictX({
                "width": rectangle_width,
                "height": rectangle_height,
                "position": rectangle_position
            }),
            "text_description": DictX({
                "width": text_size_description[0],
                "height": text_size_description[1],
                "position": (rectangle_x + box_padding_percent.left, rectangle_y + box_padding_percent.top),
                "text": str(name)
            }),
            "text_value": DictX({
                "width": text_size_value[0],
                "height": text_size_value[1],
                "position": (rectangle_x + box_padding_percent.left + text_size_description[0] + text_size_space[0], rectangle_y + box_padding_percent.top),
                "text": str(value)
            })
        })

        rectangle_y = rectangle_y - SPACE_BETWEEN_BOXES


def custom_exif(filepath):
    exif_data = generate_exif_dict(filepath)
    if exif_data is None:
        return

    exif_info = {}

    for name, value in EXIF_TAGS_TO_PRINT.items():
        exif_value = exif_data[value]['processed']
        if exif_value is not None:
            exif_info[name] = exif_data[value]['processed']

    return exif_info


def get_list_of_images(filepath):
    file_names = [
        fn for fn in os.listdir(filepath)
        if any(fn.endswith(ext) for ext in INCLUDED_EXTENSIONS)
    ]
    return file_names


def read_image():
    spinner.start()

    if len(sys.argv) <= 1:
        spinner.fail("Oops!  No image detected.  Try again...")
        return
    # filepath = sys.argv[1]
    filepath = args.image_paths
    if os.path.isdir(filepath):
        image_list = get_list_of_images(filepath)
        number_of_operations = len(image_list)
        print(''.join([
            Fore.YELLOW + "Parsing the following images from ",
            color.ITALIC + Fore.BLUE + "\'%s:\'\n" % filepath + color.END,
            *list(map(lambda x: color.ITALIC + Fore.RED + "  * %s\n" % x[1] + color.END, enumerate(image_list))),
            Style.RESET_ALL
        ]))

        for index, img_path in enumerate(image_list):
            fullpath = os.path.join(filepath, img_path)
            image = Image.open(fullpath)
            exif_info = custom_exif(fullpath)
            if exif_info is None:
                return
            draw_image(image, exif_info, len(image_list), index + 1)
        spinner.ok("✅ ")

    elif os.path.isfile(filepath):

        spinner.write(''.join([
            Fore.YELLOW + "Parsing image ",
            color.ITALIC + Fore.BLUE + "%s" % filepath + color.END,
            Fore.YELLOW + ".",
            Style.RESET_ALL
        ]))

        image = Image.open(filepath)
        exif_info = custom_exif(filepath)
        draw_image(image, exif_info, 1, 1)
        spinner.ok("✅ done")

    else:
        print("It is a special file (socket, FIFO, device file)")

    spinner.stop()


if __name__ == '__main__':
    read_image()
