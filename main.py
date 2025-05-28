import argparse
import datetime
import logging
import os
import queue
import signal
import sys
import time

from watchdog.events import DirCreatedEvent, FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer

import config
from extract.constants import SUPPORTED_VIDEO_EXTENSION
from module import ExtractionModule, PostprocessorModule

logger = logging.getLogger(__name__)


class EventWatcher(FileSystemEventHandler):
    def __init__(self, queue) -> None:
        super().__init__()
        self.queue = queue

    def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        path = str(event.src_path)

        if any(path.endswith(ext) for ext in SUPPORTED_VIDEO_EXTENSION):
            logger.info(f"Detected change: {path}, adding to queue")
            self.queue.put(path)
        else:
            logger.debug(f"Detected change: {path}, skipping... (not supported file)")


def main(mainpath: str):
    extract_mod = ExtractionModule.from_dict(
        {
            "excluded_enable": config.EXTRACTOR_EXCLUDE_ENABLE,
            "excluded_filelist": config.EXTRACTOR_EXCLUDE_FILE,
            "excluded_append": config.EXTRACTOR_EXCLUDE_APPEND,
            "extract_bitmap": config.EXTRACTOR_EXTRACT_BITMAP,
            "config": {
                "overwrite": config.EXTRACTOR_CONFIG_OVERWRITE,
                "desired_formats": config.EXTRACTOR_CONFIG_DESIRED_FORMATS,
                "languages": config.EXTRACTOR_CONFIG_LANGUAGES,
                "unknown_language_as": config.EXTRACTOR_CONFIG_UNKNOWN_LANGUAGE_AS,
            },
        }
    )

    post_mod = PostprocessorModule.from_dict(
        {
            "excluded_enable": config.EXTRACTOR_EXCLUDE_ENABLE,
            "excluded_filelist": config.POSTPROCESSOR_EXCLUDE_FILE,
            "excluded_append": config.POSTPROCESSOR_EXCLUDE_APPEND,
            "config": {"workflow_file": config.POSTPROCESSOR_CONFIG_WORKFLOW_FILE},
        }
    )

    def run(path):
        try:
            if config.APP_ENABLED_EXTRACTOR and config.APP_ENABLED_POSTPROCESSOR:
                post_mod.process(extract_mod.process(extract_mod.get_filelist(path)))
            elif config.APP_ENABLED_EXTRACTOR:
                extract_mod.process(extract_mod.get_filelist(path))
            elif config.APP_ENABLED_POSTPROCESSOR:
                post_mod.process(post_mod.get_filelist(path))
            else:
                logger.warning("No modules are enabled!")
        except Exception as e:
            logger.critical(f"An unexpected error has occurred: {e}")

    if config.APP_SCAN_INTERVAL == 0 and not config.APP_WATCH:
        run(mainpath)
        return

    task_queue = queue.SimpleQueue()
    if config.APP_WATCH:
        logger.info(f"Monitoring {os.path.abspath(mainpath)} for changes")
        event_handler = EventWatcher(task_queue)
        observer = Observer()
        observer.schedule(event_handler, os.path.abspath(mainpath), recursive=True)
        observer.start()

    next_run = datetime.datetime.now() + datetime.timedelta(
        minutes=config.APP_SCAN_INTERVAL * 60
    )

    try:
        while True:
            if not task_queue.empty():
                p = task_queue.get(block=False)
                logger.info(
                    f"Processing queue item: {p} (remaining: {task_queue.qsize()})"
                )
                run(p)
            elif config.APP_SCAN_INTERVAL > 0 and datetime.datetime.now() > next_run:
                run(mainpath)
                logger.info("Running next run on: " + str(next_run))
            else:
                time.sleep(5)
    finally:
        if config.APP_WATCH:
            observer.stop()
            observer.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("path", help="Path to media file/folder", default="/media")
    parser.add_argument("--log_level", help="Logging level", default="INFO")
    parser.add_argument("--log_file", help="Path to log file", default=None)

    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(funcName)s() - %(levelname)s - %(message)s",
        level=args.log_level.upper(),
    )
    if args.log_file is not None:
        logging.getLogger().addHandler(logging.FileHandler(args.log_file))

    signal.signal(signal.SIGTERM, lambda x, y: sys.exit(0))

    try:
        main(args.path)
    except KeyboardInterrupt:
        sys.exit(0)
