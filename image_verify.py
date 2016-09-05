#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""Checks images for corruption in a given directory recursively.

Dependencies:

    sudo pip install Pillow OpenEXR

Usage:

    python image_verify.py /path/to/root/folder/with/images
        # ^^^^^^ will check all PNGs, JPGs and EXRs recursively in specified directory

"""


import sys
import argparse
import os
import logging
logging.basicConfig(
    # filename='image_verify.log',
    level=logging.INFO,
    format='%(asctime)20s %(msg_tag)16s  %(message)s'
)

openexr_enabled = False
try:
    import OpenEXR
    openexr_enabled = True
except:
    logging.warning('Can not import OpenEXR, EXR check disabled')
    pass

from multiprocessing import Pool, cpu_count
from collections import Counter

from PIL import Image

IMAGE_EXTS = ['png', 'jpg', 'jpeg', ]
if openexr_enabled:
    IMAGE_EXTS += ['exr', ]


stats_counter = Counter()


def process_image(image_path):
    try:
        statinfo = os.stat(image_path)
        if statinfo.st_size == 0:
            return

        # OpenEXR file check
        if image_path.lower().endswith('.exr') and openexr_enabled:
            if not OpenEXR.isOpenExrFile(image_path):
                logging.warning('%s: OpenEXR could not read file', image_path, extra={'msg_tag': "EXR_ERROR"})
                stats_counter["EXR_ERROR"] += 1
                return

        # PIL-supported file formats
        else:
            img = Image.open(image_path)
            try:
                _ = img.verify()
            except Exception as e:
                logging.warning(image_path)
                logging.warning('%s: %s', image_path, e, extra={'msg_tag': "PIL_ERROR"})
                stats_counter["PIL_ERROR"] += 1
                return

    except Exception as e:
        logging.warning(image_path)
        logging.error('%s: %s', image_path, e, extra={'msg_tag': "OTHER_ERROR"})
        stats_counter["OTHER_ERROR"] += 1
        return

    logging.info(image_path, extra={'msg_tag': 'OK'})
    stats_counter["OK"] += 1


def iterate_images(root_folder):
    for root, dirs, files in os.walk(root_folder):
        for file_name in files:
            if not any([file_name.lower().endswith('.' + ext) for ext in IMAGE_EXTS]):
                continue

            yield os.path.join(root, file_name)


def parse_args():
    """Parses command-line arguments.

    """
    parser = argparse.ArgumentParser(
        description=__doc__,
    )

    #   Add arguments below
    parser.add_argument('root_folder', help='Path to the root folder to check.')

    return parser.parse_args()


def main():
    args = parse_args()

    for image_path in iterate_images(args.root_folder):
        logging.info(image_path, extra={'msg_tag': 'OPEN_IMAGE'})
        # pool.apply_async(process_image, [image_path, ])
        process_image(image_path)

    print
    print "Stats:"
    for k, v in stats_counter.items():
        print "{}: {}".format(k, v)

    return 0


if __name__ == '__main__':
    sys.exit(main())
