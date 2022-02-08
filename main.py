#!/usr/bin/env python
import os
import pprint

from PIL import Image, ImageFont, ImageDraw, ExifTags
import sys

from exif import generate_exif_dict

'''
    global
    spaces in px
'''
SPACE_FROM_BOTTOM = 40
SPACE_FROM_LEFT = 40

'''
    BOX
'''
# Degree of transparency, 0-100%
BOX_TRANSPARENCY = 10
BOX_PADDING = {"top": 50, "right": 80, "bottom": 50, "left": 80}

BOX_OPACITY = int(255 * (BOX_TRANSPARENCY / 100))

'''
    Text
'''
FONT_SIZE = 125
FONT = ImageFont.truetype("./fonts/SF-Pro-Display-Light.otf", FONT_SIZE)
FONT_ITALIC = ImageFont.truetype("./fonts/SF-Pro-Display-LightItalic.otf", FONT_SIZE)
TEXT_TRANSPARENCY = 100

TEXT_OPACITY = int(255 * (BOX_TRANSPARENCY / 100))


def draw_image(img, exif_info):
    draw = ImageDraw.Draw(img, "RGBA")
    space_between_paragraphs = (img.height / 100 * 2)
    initial_bottom_space = img.height - SPACE_FROM_BOTTOM
    width_of_space = FONT_ITALIC.getsize(' ')[1]

    bottom_space = initial_bottom_space

    for name, value in reversed(exif_info.items()):
        if name == 'Exposure':
            value = value + 's'
        elif name == 'Aperture':
            value = 'f' + str(value)

        text = '%s: %s' % (name, value)
        text_size = FONT.getsize(text)
        space_from_bottom = bottom_space - text_size[1]
        space_from_left = 0 + (img.width / 100 * 1)

        rectangle_position = [
            space_from_left,
            space_from_bottom + text_size[1] + BOX_PADDING['top'] + BOX_PADDING['bottom'] + space_between_paragraphs,
            space_from_left + text_size[0] + BOX_PADDING['left'] + BOX_PADDING['right'],
            space_from_bottom,
        ]

        draw.rectangle(rectangle_position, fill=(255, 255, 255, BOX_OPACITY))
        draw.text((space_from_left + BOX_PADDING['left'], space_from_bottom + BOX_PADDING['top']), name, (255, 255, 255), font=FONT)
        draw.text(
            (space_from_left + BOX_PADDING['left'] + text_size[0] + width_of_space, space_from_bottom + BOX_PADDING['top']),
            str(value),
            (255, 255, 255),
            font=FONT_ITALIC)

        bottom_space -= (text_size[1] + space_between_paragraphs)

    img.save("a_test.png")


def custom_exif(filepath):
    exif_data = generate_exif_dict(filepath)
    # pprint.pprint(exif_data)

    exif_info = {
        "Model": exif_data['Model']['processed'],
        "Lens": exif_data['LensModel']['processed'],
        "Aperture": exif_data['ApertureValue']['processed'],
        "FocalLength": exif_data['FocalLength']['processed'],
        "Exposure": exif_data['ExposureTime']['processed'],
        "ISO": exif_data['ISOSpeedRatings']['processed']
    }
    return exif_info


def read_image():
    filepath = sys.argv[1]
    fullpath = os.path.abspath(filepath)
    image = Image.open(filepath)
    exif_info = custom_exif(filepath)
    draw_image(image, exif_info)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    read_image()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
