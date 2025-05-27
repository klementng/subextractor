import argparse

import argparse
import datetime
import logging

import logging
import os
import sys
import signal
import time

import yaml
from watchdog.events import DirCreatedEvent, FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from extract.constants import SUPPORTED_VIDEO_EXTENSION

logger = logging.getLogger(__name__)


import queue

import extract
import postprocessing
from module import ExtractionModule, PostprocessorModule
from postprocessing import SubtitleFormatter


class Watcher(FileSystemEventHandler):
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


def load_settings(path):
    with open(path) as file:
        config = yaml.safe_load(file)

    return config["app"], config["extractor"], config["postprocessor"]


def main(settings_file: str, mainpath: str):

    app_conf, extract_conf, postprocessor_conf = load_settings(settings_file)

    extract_mod = ExtractionModule.from_dict(extract_conf)
    postprocess_mod = PostprocessorModule.from_dict(postprocessor_conf)

    def run(path):
        try:
            if (
                app_conf["enabled"]["extractor"]
                and app_conf["enabled"]["postprocessor"]
            ):
                postprocess_mod.process(
                    extract_mod.process(extract_mod.get_filelist(path))
                )

            elif app_conf["enabled"]["extractor"]:
                extract_mod.process(extract_mod.get_filelist(path))

            elif app_conf["enabled"]["postprocessor"]:
                postprocess_mod.process(postprocess_mod.get_filelist(path))
            else:
                logger.warning("No modules are enabled!")
                return
        except Exception as e:
            logger.critical(f"An unexpected error has occured: {e}")

    if app_conf["scan_interval"] == 0 and app_conf["watch"] == False:
        run(mainpath)
        return

    task_queue = queue.SimpleQueue()
    if app_conf["watch"]:
        logger.info(f"Mointoring {[os.path.abspath(mainpath)]} for changes")
        event_handler = Watcher(task_queue)
        observer = Observer()
        observer.schedule(event_handler, os.path.abspath(mainpath), recursive=True)
        observer.start()

    next_run = datetime.datetime.now() + datetime.timedelta(
        minutes=app_conf["scan_interval"] * 60
    )

    try:
        while True:

            if not task_queue.empty():
                p = task_queue.get(block=False)

                logger.info(
                    f"Processing queue item: {p} (remaining: {task_queue.qsize()})"
                )
                run(p)

            elif app_conf["scan_interval"] > 0 and datetime.datetime.now() > next_run:
                run(mainpath)
                logger.info("Running next run on: " + str(next_run))

            else:
                time.sleep(5)
    finally:
        if app_conf["watch"]:
            observer.stop()
            observer.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("path", help="path to media file/folder", default="/media")
    parser.add_argument(
        "--settings", help="setting file path", default="./settings.yaml"
    )
    parser.add_argument("--log_level", help="setting logging level", default="INFO")
    parser.add_argument("--log_file", help="path to log file", default=None)

    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(funcName)s() - %(levelname)s - %(message)s",
        level=args.log_level,
    )
    if args.log_file is not None:
        logging.getLogger().addHandler(logging.FileHandler(args.log_file))

    signal.signal(signal.SIGTERM, lambda x, y: sys.exit(0))

    try:
        main(args.settings, args.path)
    except KeyboardInterrupt:
        sys.exit(0)
