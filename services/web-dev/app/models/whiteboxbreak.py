import time
from app import db
from sqlalchemy.sql import func


class WhiteboxBreak(db.Model):

    _id = db.Column(db.Integer, primary_key=True)
    _user_id = db.Column(db.Integer, db.ForeignKey('user._id'), nullable=False)
    _program_id = db.Column(db.Integer,
                            db.ForeignKey('program._id'),
                            nullable=False)
    _timestamp = db.Column(db.BigInteger, nullable=False)
    # Broken challenge's strawberries at the time it is broken
    _strawberries = db.Column(db.BigInteger, nullable=False)

    user = db.relationship("User", backref='breaks')
    program = db.relationship("Program")

    # TODO: force the pair (user, program) to be unique

    @property
    def strawberries(self):
        return self._strawberries

    @property
    def datetime_broken(self):
        return self._format_timestamp(self._timestamp)

    @staticmethod
    def _format_timestamp(timestamp):
        if timestamp is None:
            return None
        return time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(timestamp))

    @staticmethod
    def create(user, program, timestamp, strawberries):
        wb_break = WhiteboxBreak(_user_id=user._id,
                                 _program_id=program._id,
                                 _timestamp=timestamp,
                                 _strawberries=strawberries)
        user.update_bananas(strawberries)
        return wb_break

    @staticmethod
    def get_all():
        wb_breaks = WhiteboxBreak.query.all()
        return wb_breaks

    @staticmethod
    def get(user, program):
        wb_break = WhiteboxBreak.query.filter(
            WhiteboxBreak._user_id == user._id,
            WhiteboxBreak._program_id == program._id
        ).first()
        return wb_break

    @staticmethod
    def get_all_by_user(user):
        wb_breaks = WhiteboxBreak.query.filter(
            WhiteboxBreak._user_id == user._id).all()
        return wb_breaks

    @staticmethod
    def bananas_for_user(user_id):
        return WhiteboxBreak.query(
            func.max(WhiteboxBreak._strawberries).label('bananas')
        ).first()
