from inginious.frontend.environment_types.generic_docker_oci_runtime import GenericDockerOCIRuntime


class NvidiaEnvType(GenericDockerOCIRuntime):
    @property
    def id(self):
        return "nvidia"

    @property
    def name(self):
        return _("Container with GPUs (NVIDIA)")
