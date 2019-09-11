def get_lti_user(ltipage):
    data = ltipage.user_manager.session_lti_info()
    lti_email = data['email']
    lti_name = data['realname']
    lti_id = lti_email[0:lti_email.find('@')]
    user_profile = ltipage.database.users.find_one({"username": lti_id})
    if not user_profile:
        # New user, create an account using email address
        user_profile = {"username": lti_id,
                        "realname": lti_name,
                        "email": lti_email,
                        "bindings": {data["consumer_key"]: [lti_id, {}]},
                        "language": ltipage.app.get_session().get("language", "en")}
        ltipage.database.users.insert(user_profile)

    return user_profile


def init(plugin_manager, course_factory, client, config):
    plugin_manager.add_hook('get_lti_user', get_lti_user)
