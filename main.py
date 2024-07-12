import argparse
import datetime
import logging

import time
from itertools import chain


import extract
import postprocessing

logger = logging.getLogger(__name__)


from utils import *


def main(args):

    if args.postprocess_only == True:
        files = get_subtitles_filelist(args)

        postprocesser = postprocessing.SubtitleFormatter(args.postprocessing)

        run(args.threads, postprocesser.format, files, args.disable_progress_bar)

        if args.exclude_mode == "e+a" and args.exclude_subtitles != None:
            with open(args.exclude_subtitles, "a") as f:
                f.write("\n".join(files))

    else:
        files = get_video_filelist(args)

        if len(files) > 0:
            logger.info("Extracting subtitles...")

            extractor = extract.SubtitleExtractor(
                args.formats,
                args.languages,
                args.overwrite,
                args.unknown_language_as,
                args.disable_bitmap_extraction,
            )

            output = run(
                args.threads, extractor.extract, files, args.disable_progress_bar
            )

            output_files = list(chain.from_iterable(output))

            if args.postprocessing != None:
                logger.info("Postprocessing subtitles...")
                postprocesser = postprocessing.SubtitleFormatter(args.postprocessing)

                run(
                    args.threads,
                    postprocesser.format,
                    output_files,
                    args.disable_progress_bar,
                )

            if args.exclude_mode == "e+a" and args.exclude_videos != None:
                with open(args.exclude_videos, "a") as f:
                    f.write("\n".join(files))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="path to media file/folder", default="/media")
    parser.add_argument(
        "--formats",
        help="output subtitles formats",
        nargs="+",
        default=["srt", "ass"],
        choices=extract.SUPPORTED_FORMATS,
    )
    parser.add_argument(
        "--languages",
        help="extract subtitle for selected languages, use 'all' to extract all languages",
        nargs="+",
        default=["all"],
    )
    parser.add_argument(
        "--unknown_language_as",
        help="treat unknown language as",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--overwrite", help="overwrite existing subtitle file", action="store_true"
    )
    parser.add_argument(
        "--disable_bitmap_extraction",
        help="disable extraction for bitmap based subtitle extraction via OCR",
        action="store_true",
    )
    parser.add_argument(
        "--postprocess_only",
        help="only do conduct post processing",
        action="store_true",
    )
    parser.add_argument(
        "--postprocessing",
        help="path to postprocessing config file",
        type=str,
        default="postprocess.yml",
    )
    parser.add_argument(
        "--scan_interval",
        help="interval to monitor and scan folder in mins (set 0 to disable and exit upon completion) ",
        type=int,
        default=0,
    )
    parser.add_argument("--log_level", help="setting logging level", default="INFO")
    parser.add_argument("--log_file", help="path to log file", default=None)
    parser.add_argument(
        "--disable_progress_bar",
        help="enable progress bar",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--exclude_videos",
        help="path to a newline separated file with paths to video files to exclude (applied when --postprocess_only flag is NOT set)",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--exclude_subtitles",
        help="path to a newline separated file with paths to subtitles files to exclude (applied only when --postprocess_only flag is set)",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--exclude_mode",
        help="set file exclusion behavior, e = exclude only, e+a = exclude and append newly processed file",
        type=str,
        default="e",
        choices=["e", "e+a"],
    )
    parser.add_argument(
        "--threads", help="set number of extraction threads", type=int, default=4
    )

    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(funcName)s() - %(levelname)s - %(message)s",
        level=args.log_level,
    )
    if args.log_file != None:
        logging.getLogger().addHandler(logging.FileHandler(args.log_file))

    main(args)

    if args.scan_interval > 0:
        while True:
            logger.info(
                "Running next scan on: "
                + str(
                    datetime.datetime.now()
                    + datetime.timedelta(minutes=args.scan_interval)
                )
            )
            time.sleep(args.scan_interval * 60)
            main(args)
