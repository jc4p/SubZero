from flask import Flask, request
from flask import jsonify
from flask.ext.sqlalchemy import SQLAlchemy

from secrets import *
import os
import boto

app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgres://subzero@localhost/subzero')

db = SQLAlchemy(app)

import models

@app.route("/")
def hello():
    return "This host is used by <a href='https://github.com/jc4p/KeepItCool'>https://github.com/jc4p/KeepItCool</a>"


@app.route("/register", methods=["POST"])
def incoming():
    uid = request.form.get("uid", None)
    deviceToken = request.form.get("deviceToken", None)
    if not (uid and deviceToken):
        raise InvalidRequestError("Both uid and deviceToken are required")

    sns = boto.connect_sns(aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    endpoint = sns.create_platform_endpoint(platform_application_arn=SNS_APPLICATION,
        token=deviceToken, custom_user_data=uid)
    subscription = sns.subscribe(topic=SNS_TOPIC, protocol="application", endpoint=endpoint)

    user = models.User(uid, deviceToken, endpoint)
    db.session.add(user)
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

if __name__ == "__main__":
    app.run()
