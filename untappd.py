from datetime import datetime
import requests

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
    users = User.query.filter(User.quarantined == False, User.untappdEnabled).all()

    for user in users:
        # should_quarantine = _check_untappd_feed_for_user(user)
        should_quarantine = True
        if should_quarantine:
            payload = {'users': [user.uid], 'ios': {'aps': {'content-available': 1, 'sound': ''}, 'quarantine': 1}}
            requests.post(ONTHEROCKS + "send", headers={'x-auth-key': ONTHEROCKS_TOKEN}, data=payload)
            user.quarantined = True
            # db.session.add(user)
            # db.session.commit()
            print "Quarantined {}".format(user.uid)


if __name__ == "__main__":
    process_all()