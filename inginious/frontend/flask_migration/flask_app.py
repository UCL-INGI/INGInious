from flask import Flask
from flask import session

app = Flask(__name__)


@app.route('/flask')
def hello():
    return 'Hello from Flask {} !'.format(str(session.get("realname", "anonymous")))