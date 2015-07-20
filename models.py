from main import db

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String())
    deviceToken = db.Column('deviceToken', db.Unicode(length=64))
    snsId = db.column(db.String())
    untappdEnabled = db.column(db.Boolean())
    swarmEnabled = db.column(db.Boolean())

    def __init__(self, uid, token, snsId):
        self.uid = uid
        self.deviceToken = token
        self.snsId = snsId

    def __repr__(self):
        return '<User {}>'.format(self.uid)

    @staticmethod
    def get_by_uid(uid):
        return User.query.filter_by(uid=uid).first()


class UntappdToken(db.Model):
    __tablename__ = 'untappdToken'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    token = db.Column(db.String())

    def __init__(self, uid, token):
        self.user_id = uid
        self.token = token

    def __repr__(self):
        return '<Untappd Token for User {}>'.format(self.user_id)

    @staticmethod
    def get_by_user_id(user_id):
        return UntappdToken.query.filter_by(user_id=user_id).first()


class FoursquareToken(db.Model):
    __tablename__ = 'foursquareToken'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    token = db.Column(db.String())

    def __init__(self, uid, token):
        self.user_id = uid
        self.token = token

    def __repr__(self):
        return '<Foursquare Token for User {}>'.format(self.user_id)

    @staticmethod
    def get_by_user_id(user_id):
        return FoursquareToken.query.filter_by(user_id=user_id).first()

