# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Some utils for all the pages """
import logging
import os
from typing import List, Dict

import flask
from gridfs import GridFS
from flask import redirect, url_for
from flask.views import MethodView
from werkzeug.exceptions import NotFound, NotAcceptable

from inginious.client.client import Client
from inginious.common import custom_yaml
from inginious.frontend.environment_types import get_all_env_types
from inginious.frontend.environment_types.env_type import FrontendEnvType
from inginious.frontend.plugin_manager import PluginManager
from inginious.frontend.submission_manager import WebAppSubmissionManager
from inginious.frontend.template_helper import TemplateHelper
from inginious.frontend.user_manager import UserManager
from inginious.frontend.parsable_text import ParsableText
from pymongo.database import Database

from inginious.frontend.taskset_factory import TasksetFactory
from inginious.frontend.task_factory import TaskFactory
from inginious.frontend.lti_outcome_manager import LTIOutcomeManager


class INGIniousPage(MethodView):
    """
    A base for all the pages of the INGInious webapp.
    Contains references to the PluginManager, the CourseFactory, and the SubmissionManager
    """

    @property
    def is_lti_page(self):
        """ True if the current page allows LTI sessions. False else. """
        return False

    @property
    def app(self):
        """ Returns the web application singleton """
        return flask.current_app

    def _pre_check(self, sessionid):
        # Check for language
        if "lang" in flask.request.args and flask.request.args["lang"] in self.app.l10n_manager.translations.keys():
            self.user_manager.set_session_language(flask.request.args["lang"])
        elif "language" not in flask.session:
            best_lang = flask.request.accept_languages.best_match(self.app.l10n_manager.translations.keys(),
                                                                  default="en")
            self.user_manager.set_session_language(best_lang)

        return ""

    def get(self, sessionid, *args, **kwargs):
        pre_check = self._pre_check(sessionid)
        return pre_check if pre_check else self.GET(*args, **kwargs)

    def post(self, sessionid, *args, **kwargs):
        pre_check = self._pre_check(sessionid)
        return pre_check if pre_check else self.POST(*args, **kwargs)

    @property
    def plugin_manager(self) -> PluginManager:
        """ Returns the plugin manager singleton """
        return self.app.plugin_manager

    @property
    def taskset_factory(self) -> TasksetFactory:
        """ Returns the course factory singleton """
        return self.app.taskset_factory

    @property
    def course_factory(self) -> TaskFactory:
        """ Returns the task factory singleton """
        return self.app.course_factory

    @property
    def task_factory(self) -> TaskFactory:
        """ Returns the task factory singleton """
        return self.app.task_factory

    @property
    def submission_manager(self) -> WebAppSubmissionManager:
        """ Returns the submission manager singleton"""
        return self.app.submission_manager

    @property
    def user_manager(self) -> UserManager:
        """ Returns the user manager singleton """
        return self.app.user_manager

    @property
    def template_helper(self) -> TemplateHelper:
        """ Returns the Template Helper singleton """
        return self.app.template_helper

    @property
    def database(self) -> Database:
        """ Returns the database singleton """
        return self.app.database

    @property
    def gridfs(self) -> GridFS:
        """ Returns the GridFS singleton """
        return self.app.gridfs

    @property
    def client(self) -> Client:
        """ Returns the INGInious client """
        return self.app.client

    @property
    def default_allowed_file_extensions(self) -> List[str]:  # pylint: disable=invalid-sequence-index
        """ List of allowed file extensions """
        return self.app.default_allowed_file_extensions

    @property
    def default_max_file_size(self) -> int:
        """ Default maximum file size for upload """
        return self.app.default_max_file_size

    @property
    def backup_dir(self) -> str:
        """ Backup directory """
        return self.app.backup_dir

    @property
    def environments(self) -> Dict[str, List[str]]:  # pylint: disable=invalid-sequence-index
        """ Available environments """
        return self.app.submission_manager.get_available_environments()

    @property
    def environment_types(self) -> Dict[str, FrontendEnvType]:
        """ Available environment types """
        return get_all_env_types()

    @property
    def webterm_link(self) -> str:
        """ Returns the link to the web terminal """
        return self.app.webterm_link

    @property
    def lti_outcome_manager(self) -> LTIOutcomeManager:
        """ Returns the LTIOutcomeManager singleton """
        return self.app.lti_outcome_manager

    @property
    def webdav_host(self) -> str:
        """ True if webdav is available """
        return self.app.webdav_host

    @property
    def logger(self) -> logging.Logger:
        """ Logger """
        return logging.getLogger('inginious.webapp.pages')


class INGIniousAuthPage(INGIniousPage):
    """
    Augmented version of INGIniousPage that checks if user is authenticated.
    """

    def POST_AUTH(self, *args, **kwargs):  # pylint: disable=unused-argument
        raise NotAcceptable()

    def GET_AUTH(self, *args, **kwargs):  # pylint: disable=unused-argument
        raise NotAcceptable()

    def GET(self, *args, **kwargs):
        """
        Checks if user is authenticated and calls GET_AUTH or performs logout.
        Otherwise, returns the login template.
        """
        if self.user_manager.session_logged_in():
            if (not self.user_manager.session_username() or (self.app.terms_page is not None and
                                                             self.app.privacy_page is not None and
                                                             not self.user_manager.session_tos_signed())) \
                    and not self.__class__.__name__ == "ProfilePage":
                return redirect("/preferences/profile")

            if not self.is_lti_page and self.user_manager.session_lti_info() is not None:  # lti session
                self.user_manager.disconnect_user()
                return self.template_helper.render("auth.html", auth_methods=self.user_manager.get_auth_methods())

            return self.GET_AUTH(*args, **kwargs)
        elif self.preview_allowed(*args, **kwargs):
            return self.GET_AUTH(*args, **kwargs)
        else:
            error = ''
            if "binderror" in flask.request.args:
                error = _("An account using this email already exists and is not bound with this service. "
                          "For security reasons, please log in via another method and bind your account in your profile.")
            if "callbackerror" in flask.request.args:
                error = _("Couldn't fetch the required information from the service. Please check the provided "
                          "permissions (name, email) and contact your INGInious administrator if the error persists.")
            return self.template_helper.render("auth.html", auth_methods=self.user_manager.get_auth_methods(),
                                               error=error)

    def POST(self, *args, **kwargs):
        """
        Checks if user is authenticated and calls POST_AUTH or performs login and calls GET_AUTH.
        Otherwise, returns the login template.
        """
        if self.user_manager.session_logged_in():
            if not self.user_manager.session_username() and not self.__class__.__name__ == "ProfilePage":
                return redirect("/preferences/profile")

            if not self.is_lti_page and self.user_manager.session_lti_info() is not None:  # lti session
                self.user_manager.disconnect_user()
                return self.template_helper.render("auth.html", auth_methods=self.user_manager.get_auth_methods())

            return self.POST_AUTH(*args, **kwargs)
        else:
            user_input = flask.request.form
            if "login" in user_input and "password" in user_input:
                if self.user_manager.auth_user(user_input["login"].strip(), user_input["password"]) is not None:
                    return self.GET_AUTH(*args, **kwargs)
                else:
                    return self.template_helper.render("auth.html", auth_methods=self.user_manager.get_auth_methods(),
                                                       error=_("Invalid login/password"))
            elif self.preview_allowed(*args, **kwargs):
                return self.POST_AUTH(*args, **kwargs)
            else:
                return self.template_helper.render("auth.html", auth_methods=self.user_manager.get_auth_methods())

    def preview_allowed(self, *args, **kwargs):
        """
            If this function returns True, the auth check is disabled.
            Override this function with a custom check if needed.
        """
        return False


class INGIniousAdministratorPage(INGIniousAuthPage):
    """
       Augmented version of INGIniousAuthPage that checks if user is administrator (superadmin).
    """

    def GET(self, *args, **kwargs):
        """
        Checks if user is superadmin and calls GET_AUTH or performs logout.
        Otherwise, returns the login template.
        """
        username = self.user_manager.session_username()
        if self.user_manager.session_logged_in():
            if not self.user_manager.user_is_superadmin(username):
                return self.template_helper.render("forbidden.html",
                                                   message=_("Forbidden"))
            return self.GET_AUTH(*args, **kwargs)
        return INGIniousAuthPage.GET(self, *args, **kwargs)

    def POST(self, *args, **kwargs):
        """
        Checks if user is superadmin and calls POST_AUTH.
        Otherwise, returns the forbidden template.
        """

        username = self.user_manager.session_username()
        if self.user_manager.session_logged_in() and self.user_manager.user_is_superadmin(username):
            return self.POST_AUTH()
        return self.template_helper.render("forbidden.html",
                                           message=_("You have not sufficient right to see this part."))


class SignInPage(INGIniousAuthPage):
    def GET_AUTH(self, *args, **kwargs):
        return redirect("/mycourses")

    def POST_AUTH(self, *args, **kwargs):
        return redirect("/mycourses")

    def GET(self):
        return INGIniousAuthPage.GET(self)


class LogOutPage(INGIniousAuthPage):
    def GET_AUTH(self, *args, **kwargs):
        self.user_manager.disconnect_user()
        return redirect("/courselist")

    def POST_AUTH(self, *args, **kwargs):
        self.user_manager.disconnect_user()
        return redirect("/courselist")


class INGIniousStaticPage(INGIniousPage):
    cache = {}

    def GET(self, pageid):
        return self.show_page(pageid)

    def POST(self, pageid):
        return self.show_page(pageid)

    def show_page(self, page):
        static_directory = self.app.static_directory
        language = self.user_manager.session_language()

        # Check for the file
        filename = None
        mtime = None
        filepaths = [os.path.join(static_directory, page + ".yaml"),
                     os.path.join(static_directory, page + "." + language + ".yaml")]

        for filepath in filepaths:
            if os.path.exists(filepath):
                filename = filepath
                mtime = os.stat(filepath).st_mtime

        if not filename:
            raise NotFound(description=_("File doesn't exist."))

        # Check and update cache
        if INGIniousStaticPage.cache.get(filename, (0, None))[0] < mtime:
            with open(filename, "r") as f:
                INGIniousStaticPage.cache[filename] = mtime, custom_yaml.load(f)

        filecontent = INGIniousStaticPage.cache[filename][1]
        title = filecontent["title"]
        content = ParsableText.rst(filecontent["content"], initial_header_level=2)

        return self.template_helper.render("static.html", pagetitle=title, content=content)


def generate_user_selection_box(user_manager: UserManager, render_func, current_users: List[str],
                                name: str, id: str, placeholder: str = None, single=False):
    """
    Returns the HTML for a user selection box.
    The user using the box must have admin/tutors rights on the course with id course_id.

    The box will return, when submitted using a form, a list of usernames separated by commas, under the given name.

    NB: this function is available in the templates directly as "$user_selection_box(current_users, name, id)".
    You must ignore the first argument (template_helper) in the templates.

    :param user_manager: UserManager instance
    :param render_func: template generator
    :param current_users: a list of usernames currently selected
    :param course_id: the course id
    :param name: HTML name given to the box
    :param id: HTML id given to the box
    :param single: False for multiple user selection, True for single user selection
    :return: HTML code for the box
    """
    current_users = [{"realname": y.realname if y is not None else x, "username": x} for x, y in
                     user_manager.get_users_info(current_users).items()]
    return render_func("user_selection_box.html", current_users=current_users,
                       name=name, id=id, placeholder=placeholder, single=single)


def register_utils(database, user_manager, template_helper: TemplateHelper):
    """
    Registers utils in the template helper
    """
    template_helper.add_to_template_globals("user_selection_box",
                                            lambda current_users, name, id, placeholder=None, single=False:
                                            generate_user_selection_box(user_manager, template_helper.render,
                                                                        current_users, name, id, placeholder,
                                                                        single)
                                            )
