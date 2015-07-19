from main import db

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String())
    deviceToken = db.Column('deviceToken', db.Binary(32))

    def __init__(self, uid, token):
        self.uid = uid
        self.deviceToken = token

    def __repr__(self):
        return '<User {}>'.format(self.uid)
