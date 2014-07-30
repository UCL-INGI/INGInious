""" Manages the sessions in web.py """
import web
import copy
from frontend.base import get_database
from frontend.session_mongodb import MongoStore

def get_session():
    """ Returns the current session """
    return get_session.session


def init(app, session_test=None):
    """ 
        Init the session. Should be call before starting the web.py server
        session_test is specified to emulate a session (used for tests)
    """
    if session_test is None:
        if web.config.get('_session') is None:
            get_session.session = web.session.Session(app, MongoStore(get_database(), 'sessions'))
            web.config._session = get_session.session  # pylint: disable=protected-access
        else:
            get_session.session = web.config._session  # pylint: disable=protected-access
    else:
        get_session.session = AttrDict(copy.deepcopy(session_test))

class AttrDict(dict):
    '''
        Used to fake a ThreadedDict for sessions
    '''
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
