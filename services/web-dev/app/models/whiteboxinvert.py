import time
from app import db
from sqlalchemy.sql import func
from sqlalchemy.dialects import mysql


class WhiteboxInvert(db.Model):

    _id = db.Column(db.Integer, primary_key=True)
    _user_id = db.Column(db.Integer, db.ForeignKey('user._id'), nullable=False)
    _program_id = db.Column(db.Integer,
                            db.ForeignKey('program._id'),
                            nullable=False)
    _timestamp = db.Column(db.BigInteger, nullable=False)
    # Broken challenge's carrots at the time it is broken
    _carrots = db.Column(mysql.DOUBLE, nullable=False)

    user = db.relationship("User", backref='inverts')
    program = db.relationship("Program")

    # TODO: force the pair (user, program) to be unique

    @property
    def carrots(self):
        return self._carrots

    @property
    def datetime_inverted(self):
        return self._format_timestamp(self._timestamp)

    @staticmethod
    def _format_timestamp(timestamp):
        if timestamp is None:
            return None
        return time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(timestamp))

    @staticmethod
    def create(user, program, timestamp, carrots):
        wb_invert = WhiteboxInvert(_user_id=user._id,
                                   _program_id=program._id,
                                   _timestamp=timestamp,
                                   _carrots=carrots)
        user.update_bananas(carrots)
        return wb_invert

    @staticmethod
    def get_all():
        wb_inverts = WhiteboxInvert.query.all()
        return wb_inverts

    @staticmethod
    def get(user, program):
        wb_invert = WhiteboxInvert.query.filter(
            WhiteboxInvert._user_id == user._id,
            WhiteboxInvert._program_id == program._id
        ).first()
        return wb_invert

    @staticmethod
    def get_all_by_user(user):
        wb_inverts = WhiteboxInvert.query.filter(
            WhiteboxInvert._user_id == user._id
        ).all()
        return wb_inverts

    @staticmethod
    def bananas_for_user(user_id):
        return WhiteboxInvert.query(
            func.max(WhiteboxInvert._strawberries).label('bananas')
        ).first()
