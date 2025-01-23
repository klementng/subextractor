import argparse
import datetime
import logging

import os
import time
from itertools import chain

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


logger = logging.getLogger(__name__)


import extract
import queue
import postprocessing
from extract import SubtitleExtractor

from postprocessing import SubtitleFormatter

from utils import (
    run,
    get_filelist_with_ext,
    postprocess_subtitles,
    extract_subtitles,
    add_excluded_files,
)


def main(args, vid_args, sub_args):

    def run_format(files):
        postprocesser = SubtitleFormatter(sub_args.postprocessing)
        output_files = postprocess_subtitles(
            postprocesser, files, args.threads, args.disable_progress_bar
        )

        if args.exclude_mode == "e+a" and sub_args.exclude_subtitles != None:
            add_excluded_files(sub_args.exclude_subtitles, output_files)

        return output_files

    def run_extract(files):
        extractor = SubtitleExtractor(
            vid_args.output_formats,
            vid_args.languages,
            vid_args.overwrite,
            vid_args.unknown_language_as,
            vid_args.disable_bitmap_extraction,
        )

        output_files = extract_subtitles(
            extractor, files, args.threads, args.disable_progress_bar
        )

        if args.exclude_mode == "e+a" and vid_args.exclude_videos != None:
            add_excluded_files(vid_args.exclude_videos, output_files)

        return output_files

    def run(files):
        if args.mode == "format":
            return [], run_format(files)

        elif args.mode == "extract":
            return run_extract(files), []
        else:

            out = run_extract(files)
            return out, run_format(out)

    #### Local functions ^^^^
    if args.scan_interval <= 0 and args.monitor == False:
        if args.mode == "format":
            files, excluded = get_filelist_with_ext(
                args.path,
                ["mkv", "mp4", "webm", "ts", "ogg"],
                exclude_filepath=vid_args.exclude_videos,
            )

        elif args.mode == "extract":
            files, excluded = get_filelist_with_ext(
                args.path,
                ["srt", "ass", "vtt"],
                exclude_filepath=sub_args.exclude_subtitles,
            )

        else:
            files = []

        run(files)
        return

    else:

        task_queue = queue.Queue()

        class DirectoryEventHandler(FileSystemEventHandler):

            def on_any_event(self, event):

                if (
                    event.event_type in ("created", "modified")
                    and not event.is_directory
                ):
                    path = str(event.src_path)

                    if any(
                        path.endswith(ext)
                        for ext in ["mkv", "mp4", "webm", "ts", "ogg"]
                    ):
                        logger.info(f"Detected change: {path}, running processor")
                        task_queue.put(path)
                    else:
                        logger.debug(
                            f"Detected change: {path}, skipping... (not supported file)"
                        )

        if args.monitor:
            logger.info(f"Mointoring {os.path.abspath(args.path)} for changes")
            event_handler = DirectoryEventHandler()
            observer = Observer()
            observer.schedule(event_handler, os.path.abspath(args.path), recursive=True)
            observer.start()

        try:
            while True:
                if not task_queue.empty():
                    run([task_queue.get()])

                elif args.scan_interval > 0:
                    logger.info(
                        "Running next run on: "
                        + str(
                            datetime.datetime.now()
                            + datetime.timedelta(minutes=args.scan_interval)
                        )
                    )
                    time.sleep(args.scan_interval * 60)

                    files, excluded = get_filelist_with_ext(
                        args.path,
                        ["mkv", "mp4", "webm", "ts", "ogg"],
                        exclude_filepath=vid_args.exclude_videos,
                    )
                    run(files)

                else:
                    time.sleep(30)

        except KeyboardInterrupt:
            if args.monitor:
                observer.stop()
                observer.join()


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
        help="interval to scan folder in mins (set 0 to disable and exit upon completion)",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--monitor",
        help="monitor for any new file created",
        default=False,
        action="store_true",
    )

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
    if args.log_file is not None:
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
            help='extract subtitle for selected languages, use "all" to extract all languages',
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
