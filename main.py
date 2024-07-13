import argparse
import datetime
import logging

import time
from itertools import chain


import extract
import postprocessing

logger = logging.getLogger(__name__)


from utils import *


def postprocess_subtitles(files, args, pp_args):

    postprocesser = postprocessing.SubtitleFormatter(pp_args.postprocessing)

    output = run(args.threads, postprocesser.format, files, args.disable_progress_bar)
    output_files = list(chain.from_iterable(output))

    if args.exclude_mode == "e+a" and pp_args.exclude_subtitles != None:
        with open(pp_args.exclude_subtitles, "a") as f:
            f.write("\n".join(output_files))

    return output_files


def extract_subtitles(files, args, vid_args):

    extractor = extract.SubtitleExtractor(
        vid_args.output_formats,
        vid_args.languages,
        vid_args.overwrite,
        vid_args.unknown_language_as,
        vid_args.disable_bitmap_extraction,
    )

    output = run(args.threads, extractor.extract, files, args.disable_progress_bar)

    output_files = list(chain.from_iterable(output))

    if args.exclude_mode == "e+a" and vid_args.exclude_videos != None:
        with open(vid_args.exclude_videos, "a") as f:
            f.write("\n".join(output_files))

    return output_files


def main(args, vid_args, sub_args):

    if args.mode == "extract":
        files = get_video_filelist(args.path, exclude_filepath=vid_args.exclude_videos)
        extract_subtitles(files, args, vid_args)

    elif args.mode == "format":
        files = get_subtitles_filelist(
            args.path, exclude_filepath=sub_args.exclude_subtitles
        )
        postprocess_subtitles(files, args, sub_args)

    else:
        files = get_video_filelist(args.path, exclude_filepath=vid_args.exclude_videos)
        output = extract_subtitles(files, args, vid_args)
        postprocess_subtitles(output, args, sub_args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "mode", help="select mode", choices=["extract", "format", "full"]
    )
    parser.add_argument("path", help="path to media file/folder", default="/media")

    parser.add_argument(
        "--threads", help="set number of running threads", type=int, default=4
    )
    parser.add_argument(
        "--scan_interval",
        help="interval to scan folder in mins (set 0 to disable and exit upon completion) ",
        type=int,
        default=0,
    )
    # parser.add_argument(
    #     "--monitor",
    #     help="monitor for any new file created",
    #     default=False,
    #     action="store_true",
    # )
    parser.add_argument(
        "--disable_progress_bar",
        help="enable progress bar",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--exclude_mode",
        help="set file exclusion behavior, e = exclude only, e+a = exclude and append newly processed file",
        type=str,
        default="e+a",
        choices=["e", "e+a"],
    )

    parser.add_argument("--log_level", help="setting logging level", default="INFO")
    parser.add_argument("--log_file", help="path to log file", default=None)

    args, vid_args, sub_args = None, None, None

    args, unknown = parser.parse_known_args()

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(funcName)s() - %(levelname)s - %(message)s",
        level=args.log_level,
    )
    if args.log_file != None:
        logging.getLogger().addHandler(logging.FileHandler(args.log_file))

    if args.mode in ["extract", "full"]:

        parser_vid = argparse.ArgumentParser(
            description="extract subtitle from video files",
            add_help=True,
            parents=[parser],
        )

        parser_vid.add_argument(
            "--output_formats",
            help="output subtitles formats",
            nargs="+",
            default=["srt", "ass"],
            choices=extract.SUPPORTED_FORMATS,
        )

        parser_vid.add_argument(
            "--languages",
            help="extract subtitle for selected languages, use 'all' to extract all languages",
            nargs="+",
            default=["all"],
        )
        parser_vid.add_argument(
            "--unknown_language_as",
            help="treat unknown language as",
            type=str,
            default=None,
        )
        parser_vid.add_argument(
            "--disable_bitmap_extraction",
            help="disable extraction for bitmap based subtitle extraction via OCR",
            action="store_true",
        )

        parser_vid.add_argument(
            "--overwrite", help="overwrite existing subtitle file", action="store_true"
        )

        parser_vid.add_argument(
            "--exclude_videos",
            help="path to a newline separated file with paths to video files to exclude",
            type=str,
            default=None,
        )

        vid_args, unknown = parser_vid.parse_known_args()

    if args.mode in ["format", "full"]:
        parser_sub = argparse.ArgumentParser(
            description="Postprocessing of subtitles",
            add_help=True,
            parents=[parser],
        )

        parser_sub.add_argument(
            "--postprocessing",
            help="path to postprocessing config file",
            type=str,
            default="postprocess.yml",
        )

        parser_sub.add_argument(
            "--exclude_subtitles",
            help="path to a newline separated file with paths to subtitles files to exclude",
            type=str,
            default=None,
        )

        sub_args, unknown = parser_sub.parse_known_args()

    main(args, vid_args, sub_args)

    if args.scan_interval > 0:

        while True:
            logger.info(
                "Running next run on: "
                + str(
                    datetime.datetime.now()
                    + datetime.timedelta(minutes=args.scan_interval)
                )
            )
            time.sleep(args.scan_interval * 60)
            main(args, vid_args, sub_args)
