import argparse
import datetime
import glob
import logging
import multiprocessing
import os
import re
import time
from itertools import chain

from tqdm_loggable.auto import tqdm
from tqdm_loggable.tqdm_logging import tqdm_logging

import extract
import postprocessing

logger = logging.getLogger(__name__)



def run(threads, function, files, disable_progress_bar=False):

    with tqdm(total=len(files), unit='file', disable=disable_progress_bar) as pbar:
        run_output = []

        def _run_callback(out):
            nonlocal run_output
            nonlocal pbar
            pbar.update(1)
            run_output.append(out)

        def _error_callback(e):
            logger.critical(f"An Error occurred in thread...: {e}")

        with multiprocessing.Pool(threads) as pool:

            for i in range(pbar.total):
                pool.apply_async(
                    function,
                    args=(files[i],),
                    callback=_run_callback,
                    error_callback=_error_callback
                )
            pool.close()
            pool.join()

        return run_output
    
    
def get_filelist(path, regex, excluded_files=[]):
    files = []

    if os.path.isdir(path):
        logger.info(f"Scanning directories...")
        for f in glob.iglob(path + '**/**', recursive=True):
            if re.search(regex, f) and f not in excluded_files and f not in files:
                files.append(f)
    else:
        files = [path]

    logger.info(
        f"Found {len(files)} files to be processed, {len(excluded_files)} excluded")

    return files


def get_subtitles_filelist(args):
    logger.info("Searching for subtitles files")

    if 'all' not in args.languages:
        regex = f"(?i)\\.({'|'.join(args.languages)})\\.({
            '|'.join(args.formats)})$"
    else:
        regex = f"(?i)\\.({'|'.join(args.formats)})$"

    if args.exclude_subtitles != None:
        with open(args.exclude_subtitles) as f:
            excluded_files = f.read().splitlines()
    else:
        excluded_files = []

    return get_filelist(args.path, regex, excluded_files)


def get_video_filelist(args):
    logger.info("Searching for video .(mkv|mp4|webm|ts|ogg) files")

    regex = r"(?i)\.(mkv|mp4|webm|ts|ogg)$"

    if args.exclude_videos != None:
        with open(args.exclude_videos) as f:
            excluded_files = f.read().splitlines()
    else:
        excluded_files = []

    return get_filelist(args.path, regex, excluded_files)
