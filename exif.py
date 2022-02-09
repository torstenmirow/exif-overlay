import datetime
from fractions import Fraction

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from utils import DictX


def generate_exif_dict(filepath):
    try:

        image = Image.open(filepath)

        exif_data_pil = image._getexif()

        available_tags = {**TAGS, **GPSTAGS}

        exif_data = {}

        if exif_data_pil is None:
            print('Sorry, image has no exif data.')
        else:
            for key, val in exif_data_pil.items():
                if key in available_tags:
                    if val == 'MakerNote' or val == 'UserComment' or val == 'FocalLengthIn35mmFilm':
                        continue
                    if len(str(val)) > 64:
                        val = str(val)[:65] + "..."

                    exif_data[available_tags[key]] = DictX({
                        "tag": key,
                        "raw": val,
                        "processed": val
                    })

        image.close()

        exif_data = _process_exif_dict(exif_data)

        return exif_data

    except IOError as ioe:

        raise


def _derationalize(rational):
    return rational.numerator / rational.denominator


def _process_exif_dict(exif_dict):
    date_format = "%Y:%m:%d %H:%M:%S"

    if exif_dict["DateTime"]["raw"] is not None:
        exif_dict["DateTime"]["processed"] = \
            datetime.datetime.strptime(exif_dict["DateTime"]["raw"], date_format)

    if exif_dict["DateTimeOriginal"]["raw"] is not None:
        exif_dict["DateTimeOriginal"]["processed"] = \
            datetime.datetime.strptime(exif_dict["DateTimeOriginal"]["raw"], date_format)

    if exif_dict["DateTimeDigitized"]["raw"] is not None:
        exif_dict["DateTimeDigitized"]["processed"] = \
            datetime.datetime.strptime(exif_dict["DateTimeDigitized"]["raw"], date_format)

    if exif_dict["FNumber"]["raw"] is not None:
        exif_dict["FNumber"]["processed"] = \
            _derationalize(exif_dict["FNumber"]["raw"])

    if exif_dict["FNumber"]["processed"] is not None:
        exif_dict["FNumber"]["processed"] = \
            "f{}".format(exif_dict["FNumber"]["processed"])

    if exif_dict["MaxApertureValue"]["raw"] is not None:
        exif_dict["MaxApertureValue"]["processed"] = \
            _derationalize(exif_dict["MaxApertureValue"]["raw"])

    if exif_dict["MaxApertureValue"]["processed"] is not None:
        exif_dict["MaxApertureValue"]["processed"] = \
            "f{:2.1f}".format(exif_dict["MaxApertureValue"]["processed"])

    if exif_dict["FocalLength"]["raw"] is not None:
        exif_dict["FocalLength"]["processed"] = \
            _derationalize(exif_dict["FocalLength"]["raw"])

    if exif_dict["FocalLength"]["processed"] is not None:
        exif_dict["FocalLength"]["processed"] = \
            "{}mm".format(exif_dict["FocalLength"]["processed"])

    if exif_dict["XResolution"]["raw"] is not None:
        exif_dict["XResolution"]["processed"] = \
            int(_derationalize(exif_dict["XResolution"]["raw"]))

    if exif_dict["YResolution"]["raw"] is not None:
        exif_dict["YResolution"]["processed"] = \
            int(_derationalize(exif_dict["YResolution"]["raw"]))

    if exif_dict["ExposureTime"]["raw"] is not None:
        exif_dict["ExposureTime"]["processed"] = \
            _derationalize(exif_dict["ExposureTime"]["raw"])

    if exif_dict["ExposureTime"]["processed"] is not None:
        exif_dict["ExposureTime"]["processed"] = \
            str(Fraction(exif_dict["ExposureTime"]["processed"]).limit_denominator(8000))

    if exif_dict["ExposureBiasValue"]["raw"] is not None:
        exif_dict["ExposureBiasValue"]["processed"] = \
            _derationalize(exif_dict["ExposureBiasValue"]["raw"])

    if exif_dict["ExposureBiasValue"]["processed"] is not None:
        exif_dict["ExposureBiasValue"]["processed"] = \
            "{} EV".format(exif_dict["ExposureBiasValue"]["processed"])

    return exif_dict
