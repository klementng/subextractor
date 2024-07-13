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

from tqdm_loggable.auto import tqdm
from tqdm_loggable.tqdm_logging import tqdm_logging

logger = logging.getLogger(__name__)


def run(threads, function, files, disable_progress_bar=False):

    with tqdm(total=len(files), unit="file", disable=disable_progress_bar) as pbar:
        run_output = []

        def _run_callback(out):
            nonlocal run_output
            nonlocal pbar
            pbar.update(1)
            run_output.append(out)

        def _error_callback(e):
            logger.critical(
                f"An Error occurred in thread...: {''.join(traceback.format_exception(e))}"
            )

        with multiprocessing.Pool(threads) as pool:

            for i in range(pbar.total):
                pool.apply_async(
                    function,
                    args=(files[i],),
                    callback=_run_callback,
                    error_callback=_error_callback,
                )
            pool.close()
            pool.join()

        return run_output


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
