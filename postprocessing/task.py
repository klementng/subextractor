import copy
import logging
import re

import pysubs2

from . import actions as WORKFLOW_ACTIONS

logger = logging.getLogger(__name__)


class Task:

    def __init__(
        self,
        func: str,
        id: str | None,
        params: dict,
        outputs: dict,
        ssafile: pysubs2.SSAFile,
    ) -> None:
        self.func_name: str = func
        self.id: str | None = id
        self.params: dict = params or {}
        self.outputs = outputs
        self.ssafile = ssafile

    @classmethod
    def from_dict(
        cls, task_dict: dict, outputs: dict, ssafile: pysubs2.SSAFile
    ) -> "Task":
        uses = task_dict["uses"]
        id = task_dict.get("id")
        params = task_dict.get("with", {})

        return cls(uses, id, params, outputs, ssafile)

    def get_kwargs(self) -> dict:
        resolved_kwargs = {}

        for key, value in self.params.items():
            if not isinstance(value, str):
                resolved_kwargs[key] = value
                continue

            match = re.match(r"{{(.+)}}", value)
            if match:
                try:
                    resolved_kwargs[key] = eval(
                        match.group(1), {"outputs": self.outputs}
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to resolve template variable '{value}': {e}"
                    )
                    resolved_kwargs[key] = value  # Use original value as fallback
            else:
                resolved_kwargs[key] = value

        return resolved_kwargs

    def execute(self, *args):
        try:
            func = getattr(WORKFLOW_ACTIONS, self.func_name)
        except AttributeError:
            raise ValueError(f"Unknown action: {self.func_name}")

        result = func(self.ssafile, *args, **self.get_kwargs())

        if self.id:
            self.outputs[self.id] = copy.deepcopy(result)

        return result
