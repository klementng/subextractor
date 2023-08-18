import argparse
import datetime
import glob
import logging
import re
import time
import tqdm

import postprocessing
import extract

logger = logging.getLogger(__name__)

_scanned_files = {}

def main(args):
    files = []

    if args.postprocess_only == True:
        if 'all' not in args.languages:
            regex = f"(?i)\.({'|'.join(args.languages)})\.({'|'.join(args.formats)})$"
        else:
            regex = f"(?i)\.({'|'.join(args.formats)})$"

    else:
        regex = "(?i)\.(mkv|mp4|webm|ts|ogg)$"

    for f in glob.iglob(args.path + '**/**', recursive=True):
        if re.search(regex, f) != None:
            files.append(f)

    progress = tqdm.tqdm(files, desc=f'{datetime.datetime.now()} - Progress',
                         unit='file') if args.progress_bar == 'on' else files

    if args.postprocess_only == True:
        
        for f in progress:
            
            if f in _scanned_files:
                continue
            else:
                _scanned_files.setdefault(f)

            try:
                postprocessing.standardize(args.postprocessing, [f])
            except KeyboardInterrupt:
                exit(1)

            except:
                logger.critical("An error has occurred", exc_info=True)
                continue


    else:
        extractor = extract.SubtitleExtractor(
            args.formats, args.languages, args.overwrite, args.unknown_language_as, not args.disable_bitmap_extraction)

        for f in progress:

            if f in _scanned_files:
                continue
            else:
                _scanned_files.setdefault(f)

            try:
                subtitle_files = extractor.extract(f)

                if args.postprocessing != None:
                    postprocessing.standardize(
                        args.postprocessing, subtitle_files)

            except KeyboardInterrupt:
                exit(1)

            except:
                logger.critical("An error has occurred", exc_info=True)
                continue


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--path',       help="Path to media file/folder", default="/media")
    parser.add_argument(
        '--formats', help="Subtitles formats to extract to", nargs='+', default=['srt'], choices=extract.SUPPORTED_FORMATS)
    parser.add_argument(
        '--languages', help="Select subtitle languages stream to extract from, use 'all' to extract all languages", nargs='+', default=['eng'])
    parser.add_argument(
        '--unknown_language_as', help="Treat unknown language as", type=str, default=None)
    parser.add_argument(
        '--overwrite', help="Overwrite existing subtitle file", action='store_true')
    parser.add_argument(
        '--disable_bitmap_extraction', help="Disable bitmap subtitle extraction via OCR", action='store_true')
    parser.add_argument(
        '--postprocess_only', help="Only do conduct post processing", action='store_true')
    parser.add_argument(
        '--postprocessing', help="Path to postprocessing config file", type=str, default=None)
    parser.add_argument(
        '--scan_interval', help="Interval to scan folder in mins (set 0 to disable and exit upon completion) ", type=int, default=0)
    parser.add_argument(
        "--log_level", help="Setting logging level", default='INFO')
    parser.add_argument(
        "--log_file", help="Path to log file", default=None)
    parser.add_argument(
        "--progress_bar", help="Enable progress bar", type=str, default='on', choices=['on', 'off'])

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
