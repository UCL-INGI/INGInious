from flask import Flask
from werkzeug.routing import BaseConverter

from inginious.frontend.flask_migration.helloview import HelloView

app = Flask(__name__)


class CookielessConverter(BaseConverter):
    # Parse the cookieless sessionid at the beginning of the url
    regex = r"((@)([a-f0-9A-F_]*)(@/))?"

    def to_python(self, value):
        return value[1:-2]

    def to_url(self, value):
        return "@" + str(value) + "@/"


app.url_map.converters['cookieless'] = CookielessConverter

app.add_url_rule('/<cookieless:sessionid>flask', view_func=HelloView.as_view('helloview'))