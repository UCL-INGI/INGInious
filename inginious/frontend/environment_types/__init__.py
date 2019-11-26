import abc

from inginious.common.hook_manager import HookManager
from inginious.frontend.environment_types.docker import DockerEnvType

__env_types = {}


def get_env_type(idx):
    """ Return the FrontendEnvType with id idx. If this object does not exists, returns None."""
    return __env_types.get(idx, None)

def get_all_env_types():
    return __env_types

def register_env_type(env_obj):
    """ env_obj is an instance of FrontendEnvType """
    __env_types[env_obj.id] = env_obj

def register_base_env_types(hook_manager: HookManager):
    hook_manager.add_hook("register_env_type", register_env_type, 0)

    # register standard env types here
    register_env_type(DockerEnvType())


