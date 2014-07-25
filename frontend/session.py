""" Manages the sessions in web.py """
import web


def get_session():
    """ Returns the current session """
    return get_session.session


def init(app):
    """ Init the session. Should be call before starting the web.py server """
    if web.config.get('_session') is None:
        get_session.session = web.session.Session(app, web.session.DiskStore('sessions'), {'count': 0})
        web.config._session = get_session.session  # pylint: disable=protected-access
    else:
        get_session.session = web.config._session  # pylint: disable=protected-access
