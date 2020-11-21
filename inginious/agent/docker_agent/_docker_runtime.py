# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
from typing import NamedTuple


class DockerRuntime(NamedTuple):
    """
    Represents a runtime available in this Docker instance
    """
    runtime: str  # runtime name (as set in the configuration of Docker)
    run_as_root: bool  # indicates weither the runtime runs the container as root or not
    envtype: str  # environment type to be returned to the backend/client (for example, "docker" or "kata")
                  # the envtype must be unique in the same DockerAgent.
