import os.path

_BASE_STATIC_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static')
_BASE_STATIC_URL = r'/plugins/problem_bank/files/'
_PLUGIN_FOLDER = os.path.dirname(os.path.realpath(__file__))
_REACT_BUILD_FOLDER = os.path.join(_PLUGIN_FOLDER, 'react_app', 'build')
_REACT_BASE_URL = '/plugins/problem_bank/react/'
