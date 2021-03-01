from inginious.frontend.environment_types.generic_docker_oci_runtime import GenericDockerOCIRuntime


class KataEnvType(GenericDockerOCIRuntime):
    @property
    def id(self):
        return "kata"

    @property
    def name(self):
        return _("Container running as root (Kata)")