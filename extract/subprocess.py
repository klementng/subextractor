"""
Subprocess execution with proper error handling.
"""

import atexit
import logging
import subprocess

logger = logging.getLogger(__name__)


running_subprocesses: list[subprocess.Popen] = []


@atexit.register
def cleanup(*args, **kwargs):
    for proc in running_subprocesses:
        proc.terminate()


class SubprocessError(Exception):
    pass


class SubprocessRunner:
    """Handles subprocess execution with proper error handling and logging."""

    def __init__(self, timeout: int = 300):
        self.timeout = timeout

    def run(self, args: list[str]) -> subprocess.CompletedProcess:
        """
        Run a subprocess with proper error handling.

        Args:
            args: Command and arguments to execute
            check: Whether to raise exception on non-zero exit code

        Returns:
            ProcessResult object

        Raises:
            CalledProcessError: If process fails and check=True
        """
        logger.debug(f"Running command: {' '.join(args)}")

        process = None

        try:
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            running_subprocesses.append(process)
            out, err = process.communicate()

            result = subprocess.CompletedProcess(
                args=args, returncode=process.returncode, stdout=out, stderr=err
            )

            if result.returncode != 0:
                error_msg = (
                    f"Command failed with code {result.returncode}: {' '.join(args)}"
                )
                if result.stderr:
                    error_msg += f"\nSTDERR: {result.stderr}"

                logger.error(error_msg)

                raise SubprocessError(error_msg)

            return result

        except subprocess.TimeoutExpired as e:
            error_msg = f"Command timed out after {self.timeout}s: {' '.join(args)}"
            logger.error(error_msg)
            raise SubprocessError(error_msg)

        except Exception as e:
            error_msg = f"Subprocess execution failed: {e}"
            logger.error(error_msg)
            raise SubprocessError(error_msg)

        finally:
            if process is not None:
                running_subprocesses.remove(process)
