import pysubs2
import yaml
import re
import logging
import copy

from pysubs2 import SSAFile

logger = logging.getLogger(__name__)

import actions as WORKFLOW_ACTIONS


class SubtitleRunner:

    def __init__(self, workflows: list) -> None:

        self.workflows = workflows
        self.outputs = {}

    def validate_workflow(self):
        pass

    def _run_task(self, args, uses, kwargs: dict = {}):
        func = getattr(WORKFLOW_ACTIONS, uses)
        outputs = self.outputs
        for k in kwargs.keys():
            m = re.match(r"{{(.*)}}", str(kwargs[k]))
            if m:
                eval_str = m.group(1).strip()
                kwargs[k] = eval(eval_str)

        return func(*args, **kwargs)

    def run_selector(self, ssafile: SSAFile, conf: dict):
        id = conf.get("id")
        func_name = conf["uses"]
        kwargs = conf.get("with", {})

        out: list = self._run_task([ssafile], func_name, kwargs)

        if id is not None:
            self.outputs[id] = out

        return out

    def run_filter(self, ssafile: SSAFile, selections: list, conf: dict):
        id = conf.get("id")
        func_name = conf["uses"]
        kwargs = conf.get("with", {})

        out = [
            item
            for item in selections
            if self._run_task([ssafile, item], func_name, kwargs)
        ]

        if id is not None:
            self.outputs[id] = out

        return out

    def run_actions(self, ssafile: SSAFile, items: list, conf: dict):
        id = conf.get("id")
        func_name = conf["uses"]
        kwargs = conf.get("with", {})

        output = []

        for i in items:
            out = self._run_task([ssafile, i], func_name, kwargs)
            output.append(out)

        if id is not None:
            self.outputs[id] = output

        return output

    def run_misc(self, ssafile: SSAFile, conf: dict):
        id = conf.get("id")
        func_name = conf["uses"]
        kwargs = conf.get("with", {})

        out = self._run_task([ssafile], func_name, kwargs)

        if id is not None:
            self.outputs[id] = out

        return out

    def run_workflow(self, ssafile):

        for task in self.workflows:

            selections = []
            selectors = task.get("selectors", [])
            filters = task.get("filter", [])
            actions = task.get("actions", [])
            misc = task.get("misc", [])

            for s_conf in selectors:
                out = self.run_selector(ssafile, s_conf)
                selections.extend(out)

            for f_conf in filters:
                selections = self.run_filter(ssafile, selections, f_conf)

            for a_conf in actions:
                self.run_actions(ssafile, selections, a_conf)

            for e_conf in misc:
                self.run_misc(ssafile, e_conf)

    def format(self, path, ext=None, save=True):
        ssafile = pysubs2.load(path, format_=ext)
        # _format will prevent the auto detection error from rasing in mutliprocessing thread which causes all thread to crash
        # related = https://stackoverflow.com/questions/70883678/python-multiprocessing-get-hung
        self.run_workflow(ssafile)

        if save == True:
            ssafile.save(path)

        return ssafile


class SubtitleFormatter:

    def __init__(self, config_path: str) -> None:
        self.log = logging.getLogger("SubtitleFormatter")

        with open(config_path) as cfg_file:
            self.config: dict = yaml.safe_load(cfg_file.read())

        self.workflows = {fmt: self.config[fmt]["tasks"] for fmt in self.config}

    def format(self, path, save=True):
        path = str(path)

        for ext in self.workflows:

            if path.endswith(f".{ext}"):
                runner = SubtitleRunner(self.workflows[ext])
                self.log.debug(f"Formatting subtitle: {path}")

                try:
                    runner.format(path, ext=ext, save=save)
                except pysubs2.FormatAutodetectionError as e:
                    raise RuntimeError(str(e))
                return path

        else:
            raise ValueError(f"Unsupported format: {path}")
