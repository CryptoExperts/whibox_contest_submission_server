import time
from sqlalchemy.dialects import mysql
from app import db
from app import login_manager
from passlib.hash import pbkdf2_sha256


class User(db.Model):

    _id = db.Column(db.Integer, primary_key=True)
    _email = db.Column(db.String(64), nullable=False, unique=True)
    _username = db.Column(db.String(64), index=True, unique=True)
    _nickname = db.Column(db.String(64), index=True, default=None, unique=True)
    _password_hash = db.Column(db.String(256))
    _bananas = db.Column(mysql.DOUBLE, default=None)
    _bananas_ranking = db.Column(db.BigInteger, default=None)
    _strawberries = db.Column(mysql.DOUBLE, default=0)
    _strawberries_ranking = db.Column(db.BigInteger, default=None)
    programs = db.relationship('Program', backref='user')

    @property
    def bananas_ranking(self):
        return self._bananas_ranking

    @property
    def published_programs(self):
        return [p for p in self.programs if p.is_published]

    @property
    def strawberries_ranking(self):
        return self._strawberries_ranking

    @property
    def strawberries(self):
        return self._strawberries

    @property
    def bananas(self):
        return self._bananas

    @property
    def username(self):
        return self._username

    @property
    def nickname(self):
        return self._nickname

    @nickname.setter
    def nickname(self, nickname):
        self._nickname = nickname
        db.session.commit()

    # The following properties are required by LoginManager
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self._id)

    def update_bananas(self, strawberries):
        if self._bananas is None or strawberries > self._bananas:
            self._bananas = strawberries
        User.refresh_all_banana_rankings()

    def update_strawberries(self, strawberries):
        if strawberries > self._strawberries:
            self._strawberries = strawberries

    @staticmethod
    def refresh_all_banana_rankings():
        users = User.query.filter(User._bananas.isnot(None)) \
                          .order_by(User._bananas.desc()).all()
        if len(users) == 0:
            return
        users[0]._bananas_ranking = 1
        r = 1
        b = users[0]._bananas
        skipped = 0
        for user in users[1:]:
            if user._bananas < b:
                r += 1 + skipped
                skipped = 0
            else:
                skipped += 1
            user._bananas_ranking = r
            b = user._bananas

    @login_manager.user_loader
    def load_user(id):
        return User.query.filter(User._id == int(id)).first()

    @staticmethod
    def refresh_all_strawberry_rankings():
        users = User.query.filter(
            User._strawberries > 0
        ).order_by(User._strawberries.desc()).all()
        if len(users) == 0:
            return

        users[0]._strawberries_ranking = 1
        r = 1
        b = users[0]._strawberries
        skipped = 0
        for user in users[1:]:
            if user._strawberries < b:
                r += 1 + skipped
                skipped = 0
            else:
                skipped += 1
            user._strawberries_ranking = r
            b = user._strawberries

    # User creation and password verification
    @staticmethod
    def create(username, nickname, password, email):
        password_hash = pbkdf2_sha256.hash(password)
        user = User(_username=username,
                    _nickname=nickname,
                    _password_hash=password_hash,
                    _email=email)
        db.session.add(user)
        db.session.commit()

    @staticmethod
    def validate(username, password):
        user = User.query.filter(User._username == username).first()
        if user is not None and \
           pbkdf2_sha256.verify(password, user._password_hash):
            return user
        else:
            return None

    @staticmethod
    def get(username):
        user = User.query.filter(User._username == username).first()
        return user

    @staticmethod
    def get_all_sorted_by_bananas():
        return User.query.filter(
            User._bananas_ranking.isnot(None)
        ).order_by(User._bananas.desc()).all()

    @staticmethod
    def get_total_number_of_users():
        return User.query.count()

    def verify(self, password):
        return pbkdf2_sha256.verify(password, self._password_hash)

    @staticmethod
    def _now():
        return int(time.time())

    def __repr__(self):
        return '<User %r>' % (self._username)
