_python_tutor_url = "http://localhost:8003/"
_linter_url = "http://localhost:4567/"

def set_python_tutor_url(new_python_tutor_url):
    global _python_tutor_url
    _python_tutor_url = new_python_tutor_url

def set_linter_url(new_linter_url):
    global _linter_url
    _linter_url = new_linter_url

def get_python_tutor_url():
    return _python_tutor_url

def get_linter_url():
    return _linter_url
