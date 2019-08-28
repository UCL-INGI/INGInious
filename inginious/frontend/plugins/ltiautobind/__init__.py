def enable_ltiautobind(course):
    course.enable_lti_auto_bind()
    return course

def init(plugin_manager, course_factory, client, config):
    plugin_manager.add_hook('course_created', enable_ltiautobind)
