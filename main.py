from flask import Flask, request, redirect
from flask import jsonify
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

from secrets import *
from static import *

import os
import boto
import requests


app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgres://subzero@localhost/subzero')

db = SQLAlchemy(app)
import models

@app.route("/")
def hello():
    return "This host is used by <a href='https://github.com/jc4p/KeepItCool'>https://github.com/jc4p/KeepItCool</a>"


@app.route("/register", methods=["POST"])
def register():
    uid = request.form.get("uid", "")
    deviceToken = request.form.get("deviceToken", "")
    if not (uid and deviceToken):
        raise InvalidRequestError("Both uid and deviceToken are required")

    user = models.User.get_by_uid(uid)

    if user and user.deviceToken == deviceToken:
        return ""

    if not user:
        user = models.User(uid, deviceToken)
        db.session.add(user)
    else:
        user.deviceToken = deviceToken
        ontherocks('unsubscribe', {'user': user.uid})

    ontherocks('subscribe', {'user': user.uid, 'type': 'ios', 'token': user.deviceToken})

    db.session.commit()
    
    return ""

@app.route("/settings", methods=["POST"])
def settings():
    uid = request.form.get("uid", "")
    useUntappd = request.form.get("useUntappd", False) in [True, 'true', 'True', 1, '1']
    useSwarm = request.form.get("useSwarm", False) in [True, 'true', 'True', 1, '1']

    if not uid:
        raise InvalidRequestError("uid is required")

    user = models.User.get_by_uid(uid)
    if not user:
        raise InvalidRequestError("Unknown user")

    user.untappdEnabled = useUntappd
    user.swarmEnabled = useSwarm

    db.session.add(user)
    db.session.commit()

    return ""


@app.route("/untappd_callback")
def untappd_callback():
    code = request.args.get("code", "")

    if not code:
        raise InvalidRequestError("code is required")

    authorize_url = "https://untappd.com/oauth/authorize/?"
    authorize_url += "client_id={}&".format(UNTAPPD_CLIENT_ID)
    authorize_url += "client_secret={}&".format(UNTAPPD_CLIENT_SECRET)
    authorize_url += "response_type=code&redirect_url={}&".format(UNTAPPD_REDIRECT_URL)
    authorize_url += "&code={}".format(code)

    res = requests.get(authorize_url).json()

    if 'error_type' in res['meta']:
        return res['meta']['error_detail']

    ios_uri = "keepitcool://untappd/#{}".format(res['response']['access_token'])

    return redirect(ios_uri)


@app.route("/tokens/untappd", methods=["POST"])
def tokens_untappd():
    uid = request.form.get("uid", "")
    untappdToken = request.form.get("untappdToken", "")

    if not (uid and untappdToken):
        raise InvalidRequestError("uid and untappdToken are required")

    user = models.User.get_by_uid(uid)

    if not user:
        raise InvalidRequestError("Unknown user")

    for u in db.session.query(models.UntappdToken).filter_by(user_id=user.id):
        db.session.delete(u)
    db.session.commit()

    token = models.UntappdToken(user.id, untappdToken)
    db.session.add(token)
    db.session.commit()
    return ""


@app.route("/tokens/swarm", methods=["POST"])
def tokens_swarm():
    uid = request.form.get("uid", "")
    swarmToken = request.form.get("swarmToken", "")

    if not (uid and swarmToken):
        raise InvalidRequestError("uid and swarmToken are required")

    user = models.User.get_by_uid(uid)

    if not user:
        raise InvalidRequestError("Unknown user")

    for u in db.session.query(models.FoursquareToken).filter_by(user_id=user.id):
        db.session.delete(u)
    db.session.commit()

    token = models.FoursquareToken(user.id, untappdToken)
    db.session.add(token)
    db.session.commit()
    return ""


class InvalidRequestError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(InvalidRequestError)
def handle_invalid_request_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def ontherocks(url, data):
    return requests.post(ONTHEROCKS + url, headers={'X-Auth-Key': ONTHEROCKS_TOKEN}, data=data)


if __name__ == "__main__":
    app.run()
