# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Registration page"""

import hashlib
import random
import re
import flask
import logging
import asyncio

from pydantic import ValidationError
from beanie.operators import Or

from smtplib import SMTPException
from flask_mail import Message
from werkzeug.exceptions import Forbidden
from inginious.frontend.pages.utils import INGIniousPage
from inginious.frontend.flask.mail import mail
from inginious.frontend.user_manager import UserManager
from inginious.frontend.models.user import User


class RegistrationPage(INGIniousPage):
    """ Registration page for DB authentication """

    _logger = logging.getLogger("inginious.register")

    def GET(self):
        """ Handles GET request """
        if self.user_manager.session_logged_in() or not self.app.allow_registration:
            raise Forbidden(description=_("You're not allow to register."))

        error = False
        reset = None
        msg = ""
        data = flask.request.args

        if "activate" in data:
            error = self.user_manager.activate_user(data["activate"])
            msg = _("Invalid activation hash.") if error else _("User successfully activated.")
        elif "reset" in data:
            future = asyncio.run_coroutine_threadsafe(self.get_reset_data(data), flask.current_app.motor_loop)
            msg, error, reset = future.result()  # blocks

        return self.template_helper.render("register.html", terms_page=self.app.terms_page,
                                           privacy_page=self.app.privacy_page, reset=reset, msg=msg, error=error)

    async def get_reset_data(self, data):
        """ Returns the user info to reset """
        error = False
        reset = None
        msg = ""
        user = await User.find_one(User.reset == data.get("reset", ""))
        if user is None:
            error = True
            msg = "Invalid reset hash."
        else:
            reset = {"hash": data["reset"], "username": user.username, "realname": user.realname}

        return msg, error, reset

    async def register_user(self, data):
        """ Parses input and register user """
        error = False
        msg = ""
        user_missing_fields_msg = {"username": "Username is missing", "realname": "Complete name is missing",
                                   "email": "Email is missing", "password": "Password is missing"}

        try:
            user = User(username=data["username"], realname=data["realname"], email=data["email"], password=data["passwd"])
        except ValidationError as e:
            error = True
            e = e.errors()[0]
            if e["type"] == "empty_field":
                msg = user_missing_fields_msg.get(e["ctx"]["field_name"], "Missing field") # better way to handle this ?
            else:
                msg = str(e["ctx"]["error"])

            return msg, error


        # Check input format
        if data["passwd"] != data["passwd2"]:
            error = True
            msg = _("Passwords don't match !")
        elif self.app.terms_page is not None and self.app.privacy_page is not None and "term_policy_check" not in data:
            error = True
            msg = _("Please accept the Terms of Service and Data Privacy")

        if not error:
            existing_user = await User.find(Or(User.username == user.username, User.email == user.email)).first_or_none()
            if existing_user is not None:
                error = True
                if existing_user.username == user.username:
                    msg = _("This username is already taken !")
                else:
                    msg = _("This email address is already in use !")
            else:
                passwd_hash = UserManager.hash_password(data["passwd"])
                activate_hash = UserManager.hash_password_sha512(str(random.getrandbits(256)))
                user.activate, user.password = activate_hash, passwd_hash
                user.language = self.user_manager._session.get("language", "en")
                user.tos_accepted = True
                await user.save()

                try:
                    subject = _("Welcome on INGInious")
                    body = _("""Welcome on INGInious !
To activate your account, please click on the following link :
""") + flask.request.url_root + "register?activate=" + activate_hash
                    message = Message(recipients=[(user.realname, user.email)],
                                      subject=subject,
                                      body=body)
                    mail.send(message)
                    msg = _("You are succesfully registered. An email has been sent to you for activation.")
                except Exception as ex:
                    # Remove newly inserted user (do not add after to prevent email sending in case of failure)
                    await user.delete()
                    error = True
                    msg = _("Something went wrong while sending you activation email. Please contact the administrator.")
                    self._logger.error("Couldn't send email : {}".format(str(ex)))

        return msg, error

    async def lost_passwd(self, data):
        """ Send a reset link to user to recover its password """
        error = False
        msg = ""

        # Check input format
        email_re = re.compile(
            r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
            r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'  # quoted-string
            r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$', re.IGNORECASE)  # domain
        if email_re.match(data["recovery_email"]) is None:
            error = True
            msg = _("Invalid email format.")

        if not error:
            user = await User.find_one(User.email == data["recovery_email"])
            if user is None:
                error = True
                msg = _("This email address was not found in database.")
            else:
                reset_hash = UserManager.hash_password_sha512(str(random.getrandbits(256)))
                user.reset = reset_hash
                await user.save()
                try:
                    subject = _("INGInious password recovery")

                    body = _("""Dear {realname},

Someone (probably you) asked to reset your INGInious password. If this was you, please click on the following link :
""").format(realname=user.realname) + flask.request.url_root + "register?reset=" + reset_hash

                    message = Message(recipients=[(user.realname, data["recovery_email"])],
                                      subject=subject,
                                      body=body)
                    mail.send(message)

                    msg = _("An email has been sent to you to reset your password.")
                except Exception as ex:
                    error = True
                    msg = _("Something went wrong while sending you reset email. Please contact the administrator.")
                    self._logger.error("Couldn't send email : {}".format(str(ex)))

        return msg, error

    async def reset_passwd(self, data):
        """ Reset the user password """
        error = False
        msg = ""

        # Check input format
        if len(data["passwd"]) < 6:
            error = True
            msg = _("Password too short.")
        if data["passwd"] != data["passwd2"]:
            error = True
            msg = _("Passwords don't match !")

        if not error:
            user = await User.find_one(User.reset == data["reset"])
            if user is None:
                error = True
                msg = _("Invalid reset hash.")
            else:
                user.password = UserManager.hash_password(data["passwd"])
                user.reset, user.activate = None, None
                await user.save()
                msg = _("Your password has been successfully changed.")

        return msg, error

    def POST(self):
        """ Handles POST request """
        if self.user_manager.session_logged_in() or not self.app.allow_registration:
            raise Forbidden(description=_("You're not allow to register."))

        reset = None
        msg = ""
        error = False
        data = flask.request.form
        loop = flask.current_app.motor_loop
        if "register" in data:
            future = asyncio.run_coroutine_threadsafe(self.register_user(data), loop)
            msg, error = future.result() # blocks
        elif "lostpasswd" in data:
            future = asyncio.run_coroutine_threadsafe(self.lost_passwd(data), loop)
            msg, error = future.result()
        elif "resetpasswd" in data:
            future = asyncio.run_coroutine_threadsafe(self.get_reset_data(data), loop)
            msg, error, reset = future.result()
            if reset:
                future = asyncio.run_coroutine_threadsafe(self.reset_passwd(data), loop)
                msg, error = future.result()
            if not error:
                reset = None

        return self.template_helper.render("register.html", terms_page=self.app.terms_page,
                                           privacy_page=self.app.privacy_page, reset=reset, msg=msg, error=error)
