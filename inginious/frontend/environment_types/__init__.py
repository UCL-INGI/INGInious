import abc

from inginious.frontend.environment_types.docker import DockerEnvType
from inginious.frontend.environment_types.kata import KataEnvType
from inginious.frontend.environment_types.mcq import MCQEnvType

__env_types = {}


def get_env_type(idx):
    """ Return the FrontendEnvType with id idx. If this object does not exists, returns None."""
    return __env_types.get(idx, None)


def get_all_env_types():
    return __env_types


def register_env_type(env_obj):
    """ env_obj is an instance of FrontendEnvType """
    __env_types[env_obj.id] = env_obj


def register_base_env_types():
    # register standard env types here
    register_env_type(DockerEnvType())
    register_env_type(KataEnvType())
    register_env_type(MCQEnvType())


