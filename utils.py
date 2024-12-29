import argparse
import datetime
import functools
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

import extract
import postprocessing

logger = logging.getLogger(__name__)


def run(threads, function, files, disable_progress_bar=False):

    with tqdm(total=len(files), unit="file", disable=disable_progress_bar) as pbar:

        output = []

        def _run_callback(result):
            nonlocal pbar
            nonlocal output

            pbar.update(1)
            output.append(result)

        def _error_callback(error):
            nonlocal pbar
            nonlocal output

            pbar.update(1)
            logger.critical(f"An error occurred in thread....")
            traceback.print_exception(type(error), error, error.__traceback__)

        with multiprocessing.Pool(threads) as pool:
            for fp in files:
                pool.apply_async(
                    function,
                    args=(fp,),
                    callback=_run_callback,
                    error_callback=_error_callback,
                )

            pool.close()
            pool.join()

        return output


def postprocess_subtitles(
    postprocesser: postprocessing.SubtitleFormatter,
    files,
    threads=4,
    disable_progress_bar=False,
):
    logger.info("Postprocessing subtitles...")

    output = run(threads, postprocesser.format, files, disable_progress_bar)
    output_files = list(chain.from_iterable(output))

    return output_files


def extract_subtitles(
    extractor: extract.SubtitleExtractor,
    files,
    threads=4,
    disable_progress_bar=False,
):
    logger.info("Extracting subtitles...")

    output = run(threads, extractor.extract, files, disable_progress_bar)
    output_files = list(chain.from_iterable(output))

    return output_files


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


def get_excluded_files(exclude_filepath: str) -> set:
    excluded_files = set()

    if exclude_filepath != None:
        if os.path.exists(exclude_filepath):
            with open(exclude_filepath) as f:
                excluded_files = set(f.read().splitlines())
    else:
        with open(exclude_filepath, "w") as f:
            f.write("")

    return excluded_files


def add_excluded_files(exclude_filepath: str, new_data: set | list) -> set:
    excluded_files = get_excluded_files(exclude_filepath)
    new = set(new_data)

    combined = excluded_files.union(new)

    with open(exclude_filepath, "a") as f:
        f.write("\n".join(combined))

    return combined


def get_filelist_with_ext(
    path: str, formats: list[str], exclude_filepath: str | None = None
):

    fom = "|".join(formats)
    logger.info(f"Searching for files that end with {fom}")

    regex = "(?i)\\.({})$".format(fom)

    excluded_files = set()
    if exclude_filepath is not None:
        excluded_files = get_excluded_files(exclude_filepath)

    return get_filelist(path, regex, excluded_files), excluded_files
