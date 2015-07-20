from flask import Flask, request
from flask import jsonify
from flask.ext.sqlalchemy import SQLAlchemy

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

    user = User.get_by_uid(uid)

    if user and user.deviceToken == deviceToken:
        return ""

    sns = boto.connect_sns(aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

    if user:
        sns.delete_endpoint(user.snsId)

    response = sns.create_platform_endpoint(platform_application_arn=SNS_APPLICATION,
        token=deviceToken, custom_user_data=uid)

    endpoint = response['CreatePlatformEndpointResponse']['CreatePlatformEndpointResult']['EndpointArn']
    sns.subscribe(topic=SNS_TOPIC, protocol="application", endpoint=endpoint)

    if not User:
        user = models.User(uid, deviceToken, endpoint)
        db.session.add(user)
    else:
        user.deviceToken = deviceToken
        user.snsId = endpoint

    db.session.commit()
    
    return ""

@app.route("/untappd_callback")
def untappd_callback():
    code = request.form.get("code", "")

    if not code:
        return InvalidRequestError("code is required")

    authorize_url = "https://untappd.com/oauth/authorize/?"
    authorize_url += "client_id={}&".format(UNTAPPD_CLIENT_ID)
    authorize_url += "client_secret={}&".format(UNTAPPD_CLIENT_SECRET)
    authorize_url += "response_type=code&redirect_url={}&".format(UNTAPPD_REDIRECT_URL)
    authorize_url += "&code={}".format(code)

    res = requests.get(authorize_url).json()

    ios_uri = "keepitcool://untappd?token={}".format(res['response']['access_token'])

    return redirect(ios_uri)


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

if __name__ == "__main__":
    app.run()
