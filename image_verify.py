#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""Checks images for corruption

"""


import sys
import argparse
import os
import logging
logging.basicConfig(
    # filename='image_verify.log',
    level=logging.WARN,
    format='%(asctime)s %(message)s'
)

openexr_enabled = False
try:
    import OpenEXR
    openexr_enabled = True
except:
    logging.warning('Can not import OpenEXR, EXR check disabled')
    pass

from multiprocessing import Pool, cpu_count

from PIL import Image

IMAGE_EXTS = ['png', 'jpg', 'jpeg', ]
if openexr_enabled:
    IMAGE_EXTS += ['exr', ]


def process_image(image_path):
    try:
        statinfo = os.stat(image_path)
        if statinfo.st_size == 0:
            return

        if image_path.lower().endswith('.exr'):
            if not OpenEXR.isOpenExrFile(image_path):
                logging.warning('%s: OpenEXR could not read file', image_path)
            return

        img = Image.open(image_path)
        try:
            _ = img.verify()
        except Exception as e:
            logging.warning(image_path)
            logging.warning('%s: %s', image_path, e)

    except Exception as e:
        logging.warning(image_path)
        logging.error('%s: %s', image_path, e)


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
        print "Processing: {0}".format(image_path)
        # pool.apply_async(process_image, [image_path, ])
        process_image(image_path)

    return 0


if __name__ == '__main__':
    sys.exit(main())
