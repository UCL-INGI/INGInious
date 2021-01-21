import logging

logger = logging.getLogger('inginious.webapp.plugin.ltiautobind')
auth_id = None


def get_lti_user(ltipage):
    data = ltipage.user_manager.session_lti_info()
    lti_email = data['email']
    lti_name = data['realname']
    # we use the first part of the email as username -- not the LMS username in data['username']
    lti_id = lti_email.split('@')[0]

    # New user, create an account using lti_id
    logger.info("ltiautobind: create user %s (%s)", lti_id, lti_name)

    # must match
    # LTILoginPage.GET -- inginious/frontend/pages/lti.py
    # RegistrationPage.register_user -- inginious/frontend/pages/register.py
    user_profile = {"username": lti_id,
                    "realname": lti_name,
                    "email": lti_email,  #
                    "ltibindings": {data["task"][0]: {data["consumer_key"]: data["username"]}},
                    "language": ltipage.user_manager._session.get("language", "en"),
                    }
    if auth_id:
        user_profile["bindings"] = {auth_id: [lti_id.lower(), {}]}

    ltipage.database.users.insert(user_profile)

    return user_profile


def init(plugin_manager, _course_factory, _client, config):
    global auth_id
    auth_id = config.get("id", None)
    plugin_manager.add_hook('get_lti_user', get_lti_user)
