#!/usr/bin/env python
import argparse
import os
import pathlib
import sys

from PIL import Image, ImageFont, ImageDraw, ImageFilter, ImageColor
from colorama import init
from halo import Halo

from exif import generate_exif_dict
from utils import dotdict, DictX

parser = argparse.ArgumentParser()

parser.add_argument('image_paths', type=pathlib.Path, nargs='?', help='Path to image or folder')
parser.add_argument('-f', dest='font', type=pathlib.Path, help='Path to OTF / TTF font', default="./fonts/SF-Pro-Display-Medium.otf",
                    metavar='./fonts/SF-Pro-Display-Medium.otf')
parser.add_argument('-t', dest='transparency', type=int, help='Background transparency 0-100', default="15", metavar='15')
parser.add_argument('-c', dest='color', type=str, help='Text color in HEX', default="#ffffff", metavar='"#ffffff"')
parser.add_argument('-b', dest='background', type=str, help='Box color in HEX', default="#000000", metavar='"#000000"')
parser.add_argument('-p', dest='position', help='Position of exif infos', default="left", choices=['left', 'center', 'right'], metavar='left')
parser.add_argument('-o', dest='output', type=pathlib.Path, help='Output folder', default=None, metavar='/Desktop/img')

args = parser.parse_args()

# Globals
SPACE_FROM_BOTTOM = 60
SPACE_FROM_LEFT = 80
SPACE_BETWEEN_BOXES = 40
INCLUDED_EXTENSIONS = ['jpg', 'jpeg', 'png']
POSITION = args.position
if not args.output:
    if os.path.isdir(args.image_paths):
        PATH = args.image_paths
    else:
        PATH = os.path.join(os.path.dirname(args.image_paths), 'output')
else:
    PATH = os.path.abspath(args.output)

# Box
BOX_TRANSPARENCY = args.transparency
BOX_PADDING = dotdict({"top": 20, "right": 50, "bottom": 35, "left": 50})
BOX_COLOR = ImageColor.getrgb(args.background)

BOX_OPACITY = int(255 * (BOX_TRANSPARENCY / 100))
BOX_RGBA = (BOX_COLOR + (BOX_OPACITY,))

# Text
FONT_SIZE = 2.3
TEXT_TRANSPARENCY = 100
TEXT_COLOR = ImageColor.getrgb(args.color)

TEXT_OPACITY = int(255 * (BOX_TRANSPARENCY / 100))
TEXT_RGBA = (TEXT_COLOR + (TEXT_OPACITY,))

EXIF_TAGS_TO_PRINT = {
    "Model": "Model",
    "Lens": "LensModel",
    "Aperture": "ApertureValue",
    "FocalLength": "FocalLength",
    "Exposure": "ExposureTime",
    "ISO": "ISOSpeedRatings",
}

init()

spinner = Halo(text='Loading..', spinner='bouncingBar', text_color='cyan')


# save image with high quality and same ICC Profile
def _save_image(img):
    basename = os.path.basename(img.filename)
    filename_parts = os.path.splitext(basename)
    filename = filename_parts[0] + '.exif' + filename_parts[1]
    if not os.path.exists(PATH):
        spinner.fail('Output path "%s" does not exist!' % PATH)

    fullpath = os.path.join(PATH, filename)

    img.save(fullpath, quality=100, subsampling=0, format='JPEG', icc_profile=img.info.get('icc_profile', ''))


def _draw_blurred_background(img, drawing_data):
    image = img
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)

    for item, data in drawing_data.items():
        draw.rounded_rectangle(data.rectangle.position, fill=255, radius=7)

    blurry_image = image.filter(ImageFilter.GaussianBlur(30))
    img.paste(blurry_image, mask=mask)


def _draw_text(img, drawing_data):
    draw = ImageDraw.Draw(img, "RGBA")
    for item, data in drawing_data.items():
        # draw.rectangle(rectangle_position, fill=(255, 255, 255, BOX_OPACITY))

        draw.rounded_rectangle(data.rectangle.position, fill=BOX_RGBA, radius=7)
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
        draw.text(data.text_description.position, data.text_description.text, TEXT_RGBA, font=data.text_description.font)

        draw.text(
            data.text_value.position,
            data.text_value.text,
            TEXT_RGBA,
            font=data.text_value.font
        )


def draw_image(img, exif_info):
    drawing_data = _generate_draw_data(img, exif_info)
    _draw_blurred_background(img, drawing_data)
    _draw_text(img, drawing_data)
    _save_image(img)


def _generate_draw_data(img, exif_info):
    font_size = round(img.height * FONT_SIZE / 100)
    space_left = round(img.height * (SPACE_FROM_LEFT / img.height * 100) / 100)
    space_between = round(img.height * (SPACE_BETWEEN_BOXES / img.height * 100) / 100)
    space_bottom = round(img.height * (SPACE_FROM_BOTTOM / img.height * 100) / 100)
    font = ImageFont.truetype(str(args.font), font_size)
    text_size_space = font.getsize(' ')
    rectangle_y = img.height - space_bottom
    box_padding_percent = dotdict(
        {
            "top": int(font_size * 16 / 100),
            "right": int(font_size * 40 / 100),
            "bottom": int(font_size * 28 / 100),
            "left": int(font_size * 40 / 100)
        }
    )
    draw_data = DictX({})
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
        rectangle_x = 0 + space_left

        rectangle_position = [
            rectangle_x,
            rectangle_y,
            rectangle_x + rectangle_width,
            rectangle_y + rectangle_height,
        ]

        draw_data[name] = DictX({
            "rectangle": DictX({
                "width": rectangle_width,
                "height": rectangle_height,
                "position": rectangle_position,
            }),
            "text_description": DictX({
                "width": text_size_description[0],
                "height": text_size_description[1],
                "position": (rectangle_x + box_padding_percent.left, rectangle_y + box_padding_percent.top),
                "text": str(name),
                "font": font
            }),
            "text_value": DictX({
                "width": text_size_value[0],
                "height": text_size_value[1],
                "position": (rectangle_x + box_padding_percent.left + text_size_description[0] + text_size_space[0], rectangle_y + box_padding_percent.top),
                "text": str(value),
                "font": font
            })
        })

        rectangle_y = rectangle_y - space_between

    return draw_data


def custom_exif(filepath):
    exif_data = generate_exif_dict(filepath, spinner)
    if exif_data is None:
        return

    exif_info = {}

    for name, value in EXIF_TAGS_TO_PRINT.items():
        if exif_data.get(value) is not None:
            exif_value = exif_data[value]['processed']
            if exif_value is not None:
                exif_info[name] = exif_data[value]['processed']

    if len(exif_info.values()) == 0:
        return None

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
        spinner.start('Parsing %i images' % number_of_operations)

        for img_path in image_list:
            fullpath = os.path.join(filepath, img_path)
            image = Image.open(fullpath)
            exif_info = custom_exif(fullpath)
            if exif_info is None:
                spinner.warn('%s contains no exif data' % image.filename)
                number_of_operations -= 1
                spinner.start('Parsing %i images' % number_of_operations)
                continue
            draw_image(image, exif_info)
        spinner.succeed("Saved %i images to %s." % (number_of_operations, args.output))

    elif os.path.isfile(filepath):
        spinner.start('Parsing 1 image')

        image = Image.open(filepath)
        exif_info = custom_exif(filepath)
        if exif_info is None:
            spinner.fail('%s contains no exif data' % image.filename)
            return
        draw_image(image, exif_info)
        spinner.succeed("Saved 1 image to %s." % args.output)

    else:
        spinner.warn("Unknown file.")


if __name__ == '__main__':
    spinner.start('Loading...')
    read_image()
    spinner.stop()
