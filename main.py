import argparse
import datetime
import glob
import logging
import re
import time
import sys


from tqdm import tqdm

import postprocessing
from extract import SubtitleExtractor

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(funcName)s() - %(levelname)s - %(message)s',level=logging.CRITICAL)


def main(args):
    files = []
    for f in glob.iglob(args.path + '**/**', recursive=True):
        if re.search("(?i)\.(mkv|mp4|webm|ts|ogg)$",f) != None:
            files.append(f)

    if args.progress_bar == 'on':
        progress_bar = tqdm(files,desc=f'[{datetime.datetime.now()}] Subtitle Extract',unit='file')
    else:
        progress_bar = files

    for f in progress_bar:
        try:
            extractor = SubtitleExtractor(args.formats,args.languages,args.overwrite)
            subtitle_files = extractor.extract(f)
        
            if args.postprocessing != None:
                logger.info("Post processing subtitle file")
                postprocessing.standardize(args.postprocessing,subtitle_files)
        
        except KeyboardInterrupt:
            exit(1)

        except:
            root_logger.critical("An error has occurred",exc_info=True)
            continue
    
    logging.info("Extraction Complete!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', help="Path to media file/folder",default="/media")
    parser.add_argument('--formats', help="Subtitles formats to extract to",nargs='+',default=['srt'])
    parser.add_argument('--languages', help="Extract languages",nargs='+', default=['eng'])
    parser.add_argument('--overwrite', help="Overwrite existing subtitle file", action='store_true')
    parser.add_argument('--postprocessing', help="Apply postprocessing to subtitles file", type=str, default=None)
    parser.add_argument('--scan_interval', help="Interval to scan folder in mins (set 0 to disable and exit upon completion) ", type=int, default=0)
    parser.add_argument("--log_level",help="Setting logging level", default='CRITICAL')
    parser.add_argument("--log_file",help="log to file", default=None)
    parser.add_argument("--progress_bar",help="Enable tqdm progress bar", type=str, default='on', choices=['on','off'])

    args = parser.parse_args()

    root_logger = logging.getLogger()
    root_logger.setLevel(args.log_level)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(args.log_level)
    root_logger.addHandler(stdout_handler)

    if args.log_file != None:
        file_handler = logging.FileHandler(args.log_file)
        file_handler.setLevel(args.log_level)
        root_logger.addHandler(file_handler)

    
    main(args)

    if args.scan_interval > 0:
        while True:
            time.sleep(args.scan_interval * 60)
            main(args)






