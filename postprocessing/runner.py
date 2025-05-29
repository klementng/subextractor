import logging
from pathlib import Path

import pysubs2
import yaml

from .task import Task

logger = logging.getLogger(__name__)


class WorkflowRunner:
    """Executes subtitle processing workflows on SSA files."""

    def __init__(self, workflows: list[dict], ssafile: pysubs2.SSAFile) -> None:
        self.outputs: dict = {}
        self.ssafile = ssafile
        self.workflow: list[dict[str, list[Task]]] = []

        # Convert each workflow task to Task objects
        for workflow_task in workflows:
            converted_task = {}

            # Process each section (selectors, filters, actions, misc)
            for section_name, task_list in workflow_task.items():
                if task_list is None:
                    converted_task[section_name] = []
                    continue

                converted_tasks = []
                for task_dict in task_list:
                    task = Task.from_dict(task_dict, self.outputs, self.ssafile)
                    converted_tasks.append(task)

                converted_task[section_name] = converted_tasks

            self.workflow.append(converted_task)

    def _run_selectors(self, selectors: list[Task]) -> list:
        selections = []

        for task in selectors:
            result = task.execute()
            if isinstance(result, list):
                selections.extend(result)
            else:
                selections.append(result)

        return selections

    def _run_filters(self, filters: list[Task], items: list) -> list:
        filtered = items

        for task in filters:
            filtered = task.execute(filtered)

        return filtered

    def _run_actions(self, actions: list[Task], items: list) -> None:
        for action in actions:
            action.execute(items)

    def _run_misc(self, misc_actions: list[Task]) -> None:
        for misc in misc_actions:
            misc.execute()

    def process(self) -> pysubs2.SSAFile:
        """Process the SSA file through all tasks."""

        for task in self.workflow:
            selections = []

            if "selectors" in task:
                selections = self._run_selectors(task["selectors"])

            if "filters" in task:
                selections = self._run_filters(task["filters"], selections)

            if "actions" in task:
                self._run_actions(task["actions"], selections)

            if "misc" in task:
                self._run_misc(task["misc"])

        return self.ssafile


class SubtitleFormatter:
    """Main formatter class that handles different subtitle formats."""

    def __init__(self, workflow_path: str) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.workflows = self._load_config(workflow_path)

    def _load_config(self, path) -> dict[str, list[dict]]:
        """Load and parse the YAML configuration file."""
        logger.info(f"Loading postprocesssing file from: {path}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            return {fmt: config[fmt]["tasks"] for fmt in config}
        except Exception as e:
            raise RuntimeError(f"Failed to load config from {path}: {e}")

    def format(self, filepath: str) -> list[str]:
        """Format a subtitle file based on its extension."""
        path = Path(filepath)
        extension = path.suffix[1:].lower()  # Remove dot and lowercase

        if extension not in self.workflows:
            raise RuntimeError(f"Unsupported format: {extension}")

        self.logger.debug(f"Processing {extension} file: {path}")

        try:
            # Load subtitle file
            ssafile = pysubs2.load(str(path))

            # Process with appropriate workflow
            runner = WorkflowRunner(self.workflows[extension], ssafile)
            processed_file = runner.process()

            processed_file.save(str(path))
            self.logger.info(f"Saved processed file: {path}")

            return [filepath]

        except pysubs2.FormatAutodetectionError as e:
            raise RuntimeError(f"Could not detect subtitle format for {path}: {e}")

        except Exception as e:
            self.logger.error(f"Error processing {path}: {e}")
            raise
