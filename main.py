import argparse
import datetime
import glob
import logging
import re
import time
import tqdm

import multiprocessing

import os
import postprocessing
import extract

logger = logging.getLogger(__name__)

def get_files_list(args):
    excluded_files = []

    if args.postprocess_only == True:
        if 'all' not in args.languages:
            regex = f"(?i)\.({'|'.join(args.languages)})\.({'|'.join(args.formats)})$"
        else:
            regex = f"(?i)\.({'|'.join(args.formats)})$"

        if args.exclude_subtitles != None:
            with open(args.exclude_subtitles) as f:
                excluded_files = f.read().splitlines()

    else:
        regex = "(?i)\.(mkv|mp4|webm|ts|ogg)$"

        if args.exclude_videos != None:
            with open(args.exclude_videos) as f:
                excluded_files = f.read().splitlines()
    
    files = []

    for f in glob.iglob(args.path + '**/**', recursive=True):
        if re.search(regex, f) and f not in excluded_files and f not in files:
            files.append(f)      

    return files


def run(threads,function,files):

    run_output = []

    def _run_callback(out):   
        nonlocal run_output
        run_output.extend(out)
    
    with multiprocessing.Pool(threads) as p:
        p.map_async(
            function,
            files,
            callback=_run_callback
        )
        p.close()
        p.join()

    return run_output

def main(args):

    files = get_files_list(args)

    if args.postprocess_only == True:
        output = run(args.threads,postprocessing.standardize,files)
    
    else:
        extractor = extract.SubtitleExtractor(
            args.formats, 
            args.languages, 
            args.overwrite, 
            args.unknown_language_as, 
            not args.disable_bitmap_extraction
        )

        output = run(args.threads,extractor.extract,files)

    print(output)



    # if args.postprocess_only == True:

    #     for f in progress:

    #         if f in _scanned_files:
    #             continue
    #         else:
    #             _scanned_files.setdefault(f)

    #         try:
    #             postprocessing.standardize(args.postprocessing, [f])
    #         except KeyboardInterrupt:
    #             exit(1)

    #         except:
    #             logger.critical("An error has occurred", exc_info=True)
    #             continue

    # else:
    #     extractor = extract.SubtitleExtractor(
    #         args.formats, args.languages, args.overwrite, args.unknown_language_as, not args.disable_bitmap_extraction)

    #     for f in progress:

    #         if f in _scanned_files:
    #             continue
    #         else:
    #             _scanned_files.setdefault(f)

    #         try:
    #             subtitle_files = extractor.extract(f)

    #             if args.postprocessing != None:
    #                 postprocessing.standardize(
    #                     args.postprocessing, subtitle_files)

    #         except KeyboardInterrupt:
    #             exit(1)

    #         except:
    #             logger.critical("An error has occurred", exc_info=True)
    #             continue

    # if args.exclude != None:
    #     if args.exclude_mode == 'e+a':
    #         with open(args.exclude, 'w') as f:
    #             f.write("\n".join(_scanned_files.keys()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'path', help="path to media file/folder", default="/media")
    parser.add_argument(
        '--formats', help="output subtitles formats", nargs='+', default=['srt'], choices=extract.SUPPORTED_FORMATS)
    parser.add_argument(
        '--languages', help="extract subtitle for selected languages, use 'all' to extract all languages", nargs='+', default=['all'])
    parser.add_argument(
        '--unknown_language_as', help="treat unknown language as", type=str, default=None)
    parser.add_argument(
        '--overwrite', help="overwrite existing subtitle file", action='store_true')
    parser.add_argument(
        '--disable_bitmap_extraction', help="disable extraction for bitmap based subtitle extraction via OCR", action='store_true')
    parser.add_argument(
        '--postprocess_only', help="only do conduct post processing", action='store_true')
    parser.add_argument(
        '--postprocessing', help="path to postprocessing config file", type=str, default=None)
    parser.add_argument(
        '--scan_interval', help="interval to monitor and scan folder in mins (set 0 to disable and exit upon completion) ", type=int, default=0)
    parser.add_argument(
        "--log_level", help="setting logging level", default='WARNING')
    parser.add_argument(
        "--log_file", help="path to log file", default=None)
    parser.add_argument(
        "--progress_bar", help="enable progress bar", type=str, default='on', choices=['on', 'off'])
    parser.add_argument(
        "--exclude_videos", help="path to a newline separated file with paths to video files to exclude", type=str, default=None)
    parser.add_argument(
        "--exclude_subtitles", help="path to a newline separated file with paths to subtitles files to exclude", type=str, default=None)
    parser.add_argument(
        "--exclude_mode", help="set file exclusion behavior, e = exclude only, e+a = exclude and append new extracted file", type=str, default='e', choices=['e', 'e+a'])
    parser.add_argument(
        '--threads', help="treat unknown language as", type=int, default=4)

    args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(funcName)s() - %(levelname)s - %(message)s', level=args.log_level)
    if args.log_file != None:
        logging.getLogger().addHandler(logging.FileHandler(args.log_file))


    main(args)

    if args.scan_interval > 0:
        while True:
            logger.info("Running next scan on: " + str(datetime.datetime.now() +
                                                       datetime.timedelta(minutes=args.scan_interval)))
            time.sleep(args.scan_interval * 60)
            main(args)