import argparse
import datetime
import glob
import logging
import multiprocessing
import os
import re
import time
import traceback
from itertools import chain
import functools

from tqdm_loggable.auto import tqdm
from tqdm_loggable.tqdm_logging import tqdm_logging

logger = logging.getLogger(__name__)


def run(threads, function, files, disable_progress_bar=False):

    output = []

    with tqdm(total=len(files), unit="file", disable=disable_progress_bar) as pbar:

        def worker(func):

            @functools.wraps(func)
            def wrapped_func(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except:
                    logger.critical(f"An error occurred in thread....", exc_info=True)

            return wrapped_func

        def _run_callback(result):
            pbar.update(1)
            output.append(result)

        # def _error_callback(error):
        #     pbar.update(1)
        #     logger.critical(f"An error occurred in thread....")
        #     traceback.print_exception(type(error), error, error.__traceback__)

        with multiprocessing.Pool(threads) as pool:
            for fp in files:
                pool.apply_async(
                    worker(function),
                    args=(fp,),
                    callback=_run_callback,
                    # error_callback=_error_callback,
                )

            pool.close()
            pool.join()

    return output


def get_filelist(path, regex, excluded_files=[]):
    files = []

    if os.path.isdir(path):
        for f in glob.iglob(path + "**/**", recursive=True):
            if re.search(regex, f) and f not in excluded_files and f not in files:
                files.append(f)
    else:
        files = [path]

    logger.info(
        f"Found {len(files)} files to be processed, {len(excluded_files)} excluded"
    )

    return files


def get_subtitles_filelist(path, formats=["srt", "ass", "vtt"], exclude_filepath=None):

    fom = "|".join(formats)
    logger.info(f"Searching for subtitles files that end with {fom}")

    regex = "(?i)\\.({})$".format(fom)

    if exclude_filepath != None:
        with open(exclude_filepath) as f:
            excluded_files = f.read().splitlines()
    else:
        excluded_files = []

    return get_filelist(path, regex, excluded_files)


def get_video_filelist(
    path, formats=["mkv", "mp4", "webm", "ts", "ogg"], exclude_filepath=None
):
    fom = "|".join(formats)
    logger.info(f"Searching for video {fom} files")

    regex = "(?i)\\.({})$".format(fom)

    if exclude_filepath != None:
        with open(exclude_filepath) as f:
            excluded_files = f.read().splitlines()
    else:
        excluded_files = []

    return get_filelist(path, regex, excluded_files)
