from inginious.frontend.environment_types.docker import DockerEnvType


class KataEnvType(DockerEnvType):
    @property
    def id(self):
        return "kata"

    @property
    def name(self):
        return _("Kata container")