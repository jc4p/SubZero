from main import db

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String())
    deviceToken = db.Column('deviceToken', db.Unicode(length=64))
    snsId = db.column(db.String())

    def __init__(self, uid, token, snsId):
        self.uid = uid
        self.deviceToken = token
        self.snsId = snsId

    def __repr__(self):
        return '<User {}>'.format(self.uid)

    @staticmethod
    def get_by_uid(uid):
        return User.query.filter_by(uid=uid).first()
