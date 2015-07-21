from datetime import datetime
import requests
import boto

from main import db
from models import *
from secrets import *

UNTAPPD_BASE = "https://api.untappd.com/v4/"

def _check_untappd_feed_for_user(user):
    token = UntappdToken.get_by_user_id(user.id)
    if not token:
        return False
    token = token.token

    res = requests.get(UNTAPPD_BASE + "user/checkins/?access_token={}".format(token)).json()
    if not res['response']:
        return False

    checkins = res['response']['checkins']['items']
    if not checkins:
        return False

    latest_checkin_time = datetime.strptime(checkins[0]['created_at'], '%a, %d %b %Y %H:%M:%S +0000')
    now = datetime.utcnow()

    td = now - latest_checkin_time
    if td.days < 0 and td.seconds < (60 * 30):
        return True
    return False

def process_all():
    sns = boto.connect_sns(aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    users = User.query.filter(User.quarantined == False, User.untappdEnabled).all()
    message = '{"APNS_SANDBOX": "{\\"aps\\":{\\"content-available\\": 1},\\"quarantine\\": 1}"}'

    for user in users:
        # should_quarantine = _check_untappd_feed_for_user(user)
        should_quarantine = True
        if should_quarantine:
            res = sns.publish(message=message, message_structure="json", target_arn=user.snsId)
            user.quarantined = True
            # db.session.add(user)
            # db.session.commit()
            print "Quarantined {}".format(user.uid)


if __name__ == "__main__":
    process_all()