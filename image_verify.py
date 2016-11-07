#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""Checks images for corruption in a given directory recursively.

"""


import sys
import argparse
import os
import logging

PEXPECT_AVAILABLE = False
try:
    import pexpect
    PEXPECT_AVAILABLE = True
except ImportError:
    pass

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


MASTERS_EXTS = ('mov', 'mp4', )


stats_counter = Counter()


class FileNotFoundEx(Exception):
    pass


def check_exr(path):
    if not OpenEXR.isOpenExrFile(path):
        logging.warning("EXR_ERROR %s : OpenEXR could not read file", path)
        return {'valid': False, 'message': 'OpenEXR could not read file'}
    return {'valid': True, 'message': 'ok'}


def check_pil(path):
    try:
        img = Image.open(path)
        _ = img.verify()
    except Exception as e:
        logging.warning('PIL_ERROR %s : %s', path, e)
        return {'valid': False, 'message': '{}'.format(e)}

    return {'valid': True, 'message': 'ok'}


def check_movie(path):
    def shellquote(s):
        return "'" + s.replace("'", "'\\''") + "'"

    cmd = 'ffmpeg -i {0} -f null -'.format(shellquote(path))
    thread = pexpect.spawn(cmd)

    patterns = thread.compile_pattern_list(
        [
            pexpect.EOF,
            ".*(damaged|error|invalid|Error|Invalid).*",
            ".*No such file or directory.*",
            '(.+)',
        ]
    )

    while True:
        i = thread.expect_list(patterns, timeout=None)
        if i == 0:
            # No errors, we're good
            return {'valid': True, 'message': 'ok'}
        elif i == 1:
            # FFMpeg found an error
            logging.warning('FFMPEG_ERROR %s : %s', path, 'ffmpeg error')
            return {'valid': False, 'message': 'ffmpeg error'}
        elif i == 2:
            # File not found
            raise FileNotFoundEx("{0}: file not found".format(path))
        elif i == 3:
            # File being processed, wait
            pass


def process_image(image_path):

    checks_map = [
        {
            'ext': ('exr', ),
            'func': check_exr,
            'counter': 'EXR_ERROR',
        },
        {
            'ext': ('png', 'jpg', 'jpeg', ),
            'func': check_pil,
            'counter': 'PIL_ERROR',
        },
        {
            'ext': ('mp4', 'mov', ),
            'func': check_movie,
            'counter': 'FFMPEG_ERROR',
        }
    ]

    try:

        statinfo = os.stat(image_path)
        if statinfo.st_size == 0:
            return

        for check in checks_map:
            for ext in check['ext']:
                if not image_path.lower().endswith('.{}'.format(ext)):
                    continue

                check_result = check['func'](image_path)
                if not check_result['valid']:
                    stats_counter[check['counter']] += 1
                    return

    except Exception as e:
        logging.error('OTHER_ERROR %s: %s', image_path, e)
        stats_counter["OTHER_ERROR"] += 1
        return

    logging.info("OK %s", image_path)
    stats_counter["OK"] += 1


def iterate_files(root_folder):
    for root, dirs, files in os.walk(root_folder):
        for file_name in files:
            if not any([file_name.lower().endswith('.' + ext) for ext in CHECK_EXTS]):
                continue

            yield os.path.join(root, file_name)


def check_ffmpeg_installed():
    """Checks whether ffmpeg is installed on this system.

    Returns:
        True: ffmpeg is installed
        False: ffmpeg is not installed

    """
    thread = pexpect.spawn('ffmpeg')
    patterns = thread.compile_pattern_list(
        [
            pexpect.EOF,
            '.*(ffmpeg version).+',
            '(.+)',
        ]
    )

    while True:
        i = thread.expect_list(patterns, timeout=None)
        if i == 0:
            raise Exception
        elif i == 1:
            return True
        elif i == 2:
            return False


def parse_args():
    """Parses command-line arguments.

    """
    parser = argparse.ArgumentParser(
        description=__doc__,
    )

    parser.add_argument('-v', '--verbose', help="Verbose output — show files opening and files that pass the checks", action='store_true')

    parser.add_argument('--enable-movies', help="Include checks for MP4 and MOV files using ffmpeg", action='store_true')

    parser.add_argument('--enable-images', help="Include checks for PNG, JPG and JPEG files using PIL", action='store_true')

    parser.add_argument('--enable-exr', help="Include checks for EXR files using OpenEXR library", action='store_true')

    parser.add_argument('--log-file', help="Log file path, will only log to stdout if not specified")

    #   Add arguments below
    parser.add_argument('root_folder', help='Path to the root folder to check.')

    return parser.parse_args()


def main():
    args = parse_args()
    log_level = logging.WARN
    if args.verbose:
        log_level = logging.DEBUG

    if args.log_file:
        logging.basicConfig(
            level=log_level,
            format='%(asctime)20s %(message)s',
            filename=args.log_file
        )
    else:
        logging.basicConfig(
            level=log_level,
            format='%(asctime)20s %(message)s',
        )

    check_exts = ()

    if args.enable_images:
        check_exts += ('png', 'jpg', 'jpeg', )

    if args.enable_exr:
        if not openexr_enabled:
            logging.error("Please install OpenEXR (pip install openexr) to enable EXR checks")
            return 5
        check_exts += ('exr', )

    if args.enable_movies:
        if not PEXPECT_AVAILABLE:
            logging.error("Please, install pexpect (pip install pexpect) to enable movie checks with ffmpeg")
            return 10
        if not check_ffmpeg_installed():
            logging.error("Please install ffmpeg to enable movie file checks")
            return 20

        check_exts += ('mp4', 'mov', )

    global CHECK_EXTS
    CHECK_EXTS = check_exts

    if not check_exts:
        logging.error("Please enable one or more file check options, see --help for full list")
        return 25

    for image_path in iterate_files(args.root_folder):
        logging.info("OPEN_IMAGE %s", image_path)
        # pool.apply_async(process_image, [image_path, ])
        process_image(image_path)

    print
    print "Stats:"
    for k, v in stats_counter.items():
        print "{}: {}".format(k, v)

    return 0


if __name__ == '__main__':
    sys.exit(main())
