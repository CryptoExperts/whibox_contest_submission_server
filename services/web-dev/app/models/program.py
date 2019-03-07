import time
import random
import string
from decimal import Decimal
from math import log
from enum import Enum, unique
from app import app
from app import db
from app import utils
from app.funny_name_generator import get_funny_name
from sqlalchemy import or_, and_
from sqlalchemy.dialects import mysql
from .whiteboxbreak import WhiteboxBreak
from .whiteboxinvert import WhiteboxInvert


class Program(db.Model):

    @unique
    class Status(Enum):
        submitted = 'submitted'
        compilation_failed = 'compilation_failed'
        link_failed = 'link_failed'
        execution_failed = 'execution_failed'
        test_failed = 'test_failed'
        unbroken = 'unbroken'
        broken = 'broken'
        inverted = 'inverted'

        def __str__(self):
            if self == self.submitted:
                return 'Submitted'
            elif self == self.compilation_failed:
                return 'Compilation failed'
            elif self == self.link_failed:
                return 'Link failed'
            elif self == self.execution_failed:
                return 'Execution failed'
            elif self == self.test_failed:
                return 'Test failed'
            elif self == self.unbroken:
                return 'Unbroken'
            elif self == self.inverted:
                return 'Inverted'
            elif self == self.broken:
                return 'Broken'
            else:
                return '-'

        @staticmethod
        def authorized_status_change(current_status, new_status):
            all_authorized_status_change = [
                (Program.Status.submitted, Program.Status.compilation_failed),
                (Program.Status.submitted, Program.Status.link_failed),
                (Program.Status.submitted, Program.Status.execution_failed),
                (Program.Status.submitted, Program.Status.test_failed),
                (Program.Status.submitted, Program.Status.unbroken),
                (Program.Status.unbroken, Program.Status.broken),
                (Program.Status.unbroken, Program.Status.inverted),
                (Program.Status.inverted, Program.Status.inverted),
                (Program.Status.inverted, Program.Status.broken),
                (Program.Status.broken, Program.Status.broken)
            ]
            return (current_status, new_status) in all_authorized_status_change

    def _now(context):
        return int(time.time())

    _id = db.Column(db.Integer, primary_key=True)
    _funny_name = db.Column(db.Text)
    _basename = db.Column(db.String(32))
    _user_id = db.Column(db.Integer, db.ForeignKey('user._id'))
    _nonce = db.Column(db.String(32), default=None)
    _timestamp_submitted = db.Column(db.BigInteger, default=_now)
    _timestamp_published = db.Column(db.BigInteger, default=None)
    _timestamp_first_break = db.Column(db.BigInteger, default=None)
    _status = db.Column(db.String(100), default=Status.submitted.value)
    _key = db.Column(db.String(32), default=None)
    _compiler = db.Column(db.String(16), default='gcc')
    _performance_factor = db.Column(mysql.DOUBLE, default=1.0)
    _size_factor = db.Column(mysql.DOUBLE, default=1.0)
    _ram_factor = db.Column(mysql.DOUBLE, default=1.0)
    _time_factor = db.Column(mysql.DOUBLE, default=1.0)
    # ID of the docker task responsible for the compilation
    _task_id = db.Column(db.String(32), default=None)
    _timestamp_compilation_start = db.Column(db.BigInteger, default=None)
    _timestamp_compilation_finished = db.Column(db.BigInteger, default=None)
    _error_message = db.Column(db.Text, default=None)
    _plaintexts = db.Column(db.LargeBinary, default=None)
    _ciphertexts = db.Column(db.LargeBinary, default=None)
    _plaintext_sha256_for_inverting = db.Column(db.String(64), default=None)
    _ciphertext_for_inverting = db.Column(db.LargeBinary, default=None)
    # First set when the program is published
    _strawberries_peak = db.Column(mysql.DOUBLE, default=0)
    _strawberries_last = db.Column(mysql.DOUBLE, default=0)
    _strawberries_ranking = db.Column(db.BigInteger, default=None)
    _carrots_peak = db.Column(mysql.DOUBLE, default=0)
    _carrots_last = db.Column(mysql.DOUBLE, default=0)
    _timestamp_first_inversion = db.Column(db.BigInteger, default=None)

    @property
    def position_in_the_compilation_queue(self):
        if self.status != Program.Status.submitted:
            return None
        if self._task_id is not None:
            return 'In progress'
        pos = Program.query.filter(
            Program._status == Program.Status.submitted.value,
            Program._task_id.is_(None),
            Program._timestamp_submitted < self._timestamp_submitted
        ).count()
        if pos == 0:
            return "Next"
        else:
            return str(pos+1)

    @property
    def funny_name(self):
        return self._funny_name

    @property
    def task_id(self):
        return self._task_id

    @task_id.setter
    def task_id(self, val):
        if type(val) == str and len(val) <= 32 and self._task_id is None:
            self._task_id = val
            self._timestamp_compilation_start = int(time.time())

    @property
    def strawberries_last(self):
        return self._strawberries_last

    @property
    def strawberries_peak(self):
        return self._strawberries_peak

    @property
    def strawberries_ranking(self):
        return self._strawberries_ranking

    @property
    def carrots_peak(self):
        return self._carrots_peak

    @property
    def carrots_last(self):
        return self._carrots_last

    @property
    def hsl_color(self):
        return 'hsl(%d, 100%%, %d%%)' % \
            (self._timestamp_submitted % 360,
             self._timestamp_published % 47 + 20)

    @property
    def datetime_submitted(self):
        return utils.format_timestamp(self._timestamp_submitted)

    @property
    def datetime_published(self):
        return utils.format_timestamp(self._timestamp_published)

    @property
    def filename(self):
        return self._basename + '.c'

    @property
    def status(self):
        return Program.Status(self._status)

    @property
    def key(self):
        return self._key

    @property
    def performance_factor(self):
        return self._performance_factor

    @property
    def size_factor(self):
        return self._size_factor

    @property
    def ram_factor(self):
        return self._ram_factor

    @property
    def time_factor(self):
        return self._time_factor

    @property
    def compiler(self):
        return self._compiler

    @property
    def error_message(self):
        return self._error_message

    @property
    def plaintexts(self):
        return self._plaintexts

    @plaintexts.setter
    def plaintexts(self, val):
        assert type(val) == bytes
        if self._plaintexts is None:
            self._plaintexts = val

    @property
    def plaintext_sha256_for_inverting(self):
        return self._plaintext_sha256_for_inverting

    @plaintext_sha256_for_inverting.setter
    def plaintext_sha256_for_inverting(self, val):
        if self._plaintext_sha256_for_inverting is None:
            self._plaintext_sha256_for_inverting = val

    @property
    def ciphertexts(self):
        return self._ciphertexts

    @ciphertexts.setter
    def ciphertexts(self, val):
        assert type(val) == bytes
        if self._ciphertexts is None:
            self._ciphertexts = val

    @property
    def ciphertext_for_inverting(self):
        return self._ciphertext_for_inverting

    @ciphertext_for_inverting.setter
    def ciphertext_for_inverting(self, val):
        assert type(val) == bytes
        if self._ciphertext_for_inverting is None:
            self._ciphertext_for_inverting = val

    @property
    def datetime_first_break(self):
        if self._timestamp_first_break is None:
            return None
        else:
            return utils.format_timestamp(self._timestamp_first_break)

    @property
    def datetime_first_inversion(self):
        if self._timestamp_first_inversion is None:
            return None
        else:
            return utils.format_timestamp(self._timestamp_first_inversion)

    def update_strawberries(self, now):
        if not self.is_published:
            return

        strawberries = self.current_strawberries(now)
        self._strawberries_last = strawberries
        if self._strawberries_peak < strawberries:
            self._strawberries_peak = strawberries

    def update_carrots(self, now):
        if not self.is_published:
            return

        carrots = self.current_carrots(now)
        self._carrots_last = carrots
        if self._carrots_peak < carrots:
            self._carrots_peak = carrots

    @staticmethod
    def clean_programs_which_timeout_to_compile_or_test():
        programs = Program.get_all_programs_being_compiled_or_tested()

        # We ensure the first program has not been compiled/tested for too long
        for p in programs[:1]:
            max_compile_time = app.config['CHALLENGE_MAX_TIME_COMPILATION_IN_SECS']
            max_exec_time = app.config['CHALLENGE_MAX_TIME_EXECUTION_IN_SECS'] * \
                app.config['CHALLENGE_NUMBER_OF_TEST_VECTORS']
            max_time = 10 + max_compile_time + max_exec_time
            now = int(time.time())
            if now > p._timestamp_compilation_start + max_time:
                p.set_status_to_execution_failed(
                    'Compilation and/or testing took too much time. Timeout!')
        # Any other unpublished program with a lower 'timestamp_compilation_start' must have crashed their docker
        for p in programs[1:]:
            p.set_status_to_execution_failed(
                'Compilation and/or testing failed for unknown reason.')

    @staticmethod
    def refresh_all_strawberry_rankings():
        programs = Program.query.filter(or_(
            Program._status == Program.Status.unbroken.value,
            Program._status == Program.Status.inverted.value,
            Program._status == Program.Status.broken.value)
        ).order_by(Program._strawberries_peak.desc()).all()
        if len(programs) == 0:
            return
        programs[0]._strawberries_ranking = 1
        r = 1
        p = programs[0]._strawberries_peak
        skipped = 0
        for program in programs[1:]:
            if program._strawberries_peak < p:
                r += 1 + skipped
                skipped = 0
            else:
                skipped += 1
            program._strawberries_ranking = r
            p = program._strawberries_peak

    def strawberries_grow(self, start_timestamp, end_timestamp):
        seconds_in_minute = app.config['NBR_SECONDS_PER_MINUTE']
        seconds_in_hour = app.config['NBR_SECONDS_PER_HOUR']
        seconds_in_day = app.config['NBR_SECONDS_PER_DAY']

        strawberries = {}
        current_timestamp = start_timestamp

        days = 0
        while end_timestamp - current_timestamp > 1.5 * seconds_in_day:
            strawberries[current_timestamp] = days**2
            current_timestamp += seconds_in_day
            days += 1

        hours = 0
        while end_timestamp - current_timestamp > 1.5 * seconds_in_hour:
            strawberries[current_timestamp] = (days + hours/24) ** 2
            current_timestamp += seconds_in_hour
            hours += 1

        mintues = 0
        while end_timestamp - current_timestamp > seconds_in_minute:
            strawberries[current_timestamp] = (
                days + hours/24 + mintues/1440
            ) ** 2
            current_timestamp += seconds_in_minute
            mintues += 1

        strawberries[end_timestamp] = (
            days + hours/24 + mintues/1440
        ) ** 2
        return strawberries

    def strawberries_decrease(self, start_timestamp, end_timestamp):
        seconds_in_minute = app.config['NBR_SECONDS_PER_MINUTE']
        seconds_in_hour = app.config['NBR_SECONDS_PER_HOUR']
        seconds_in_day = app.config['NBR_SECONDS_PER_DAY']

        strawberries = {}
        current_timestamp = start_timestamp

        days = 0
        while end_timestamp - current_timestamp > 1.5 * seconds_in_day:
            strawberries[current_timestamp] = days**2
            current_timestamp += seconds_in_day
            days += 1

        hours = 0
        while end_timestamp - current_timestamp > 1.5 * seconds_in_hour:
            strawberries[current_timestamp] = (days + hours/24.0) ** 2
            current_timestamp += seconds_in_hour
            hours += 1

        mintues = 0
        while end_timestamp - current_timestamp > seconds_in_minute:
            strawberries[current_timestamp] = (
                days + hours/24.0 + mintues/1440.0
            ) ** 2
            current_timestamp += seconds_in_minute
            mintues += 1

        return strawberries

    def current_strawberries(self, end_timestamp):
        if not self.is_published:
            return None
        final_deadline = app.config['FINAL_DEADLINE']
        end_timestamp = min(end_timestamp, final_deadline)

        if self.is_broken:
            if end_timestamp < self._timestamp_first_break:
                return None
            surviving_minutes = (
                self._timestamp_first_break-self._timestamp_published
            ) / 60
            minutes_after_broken = (
                end_timestamp - self._timestamp_first_break
            ) / 60
            if minutes_after_broken > surviving_minutes:
                strawberries = 0
            else:
                strawberries = (
                    (surviving_minutes-minutes_after_broken)/1440.0)**2
        else:
            surviving_minutes = (end_timestamp-self._timestamp_published) / 60
            strawberries = (surviving_minutes/1440.0) ** 2
        return strawberries * float(self._performance_factor)

    def current_carrots(self, end_timestamp):
        if not self.is_published:
            return None

        final_deadline = app.config['FINAL_DEADLINE']
        end_timestamp = min(end_timestamp, final_deadline)

        if self.is_broken or self.is_inverted:
            peak_timestamp = end_timestamp
            if self.is_inverted:
                peak_timestamp = self._timestamp_first_inversion
            elif self.is_broken:
                peak_timestamp = self._timestamp_first_break
            surviving_minutes = (peak_timestamp-self._timestamp_published)/60
            minutes_after_peak = (end_timestamp - peak_timestamp) / 60
            if minutes_after_peak > surviving_minutes:
                carrots = 0
            else:
                carrots = ((surviving_minutes-minutes_after_peak)/1440.0)**2
        else:
            surviving_minutes = (end_timestamp-self._timestamp_published) / 60
            carrots = (surviving_minutes/1440.0) ** 2
        return carrots * float(self._performance_factor) * 0.5

    def strawberries(self, now=int(time.time())):
        if not self.is_published:
            return None
        strawberries = {}

        if not self.is_broken:
            final_deadline = app.config['FINAL_DEADLINE']
            start_timestamp = self._timestamp_published
            end_timestamp = min(now, final_deadline)
            strawberries.update(
                self.strawberries_grow(start_timestamp, end_timestamp)
            )
        else:
            start_timestamp = self._timestamp_published
            end_timestamp = self._timestamp_first_break
            strawberries.update(
                self.strawberries_grow(start_timestamp, end_timestamp)
            )
            # TODO: add decrease
            # running_val = max(running_val - 1, 0)
            # for running_timestamp in range(self._timestamp_first_break, min(now, final_deadline)+1, seconds_in_minute):
            #     strawberries[running_timestamp] = running_val
            #     running_val_diff = max(running_val_diff - 1, 0)
            #     running_val = max(running_val - running_val_diff, 0)

        return {
            k: Decimal(v)*Decimal(self._performance_factor) for k, v in strawberries.items()
        }

    def set_status_to_compilation_failed(self, error_message=None):
        utils.console(
            "Setting the status to compilation_failed for program with id %s" % str(self._id))
        if Program.Status.authorized_status_change(
                self.status, Program.Status.compilation_failed):
            self._status = Program.Status.compilation_failed.value
            if error_message is not None and type(error_message) == str:
                self._error_message = error_message

    def set_status_to_link_failed(self):
        if Program.Status.authorized_status_change(self.status,
                                                   Program.Status.link_failed):
            self._status = Program.Status.link_failed.value

    def set_status_to_execution_failed(self, error_message=None):
        if Program.Status.authorized_status_change(
                self.status, Program.Status.execution_failed):
            self._status = Program.Status.execution_failed.value
            if error_message is not None and type(error_message) == str:
                self._error_message = error_message

    def set_status_to_test_failed(self, error_message=None):
        if Program.Status.authorized_status_change(self.status,
                                                   Program.Status.test_failed):
            self._status = Program.Status.test_failed.value
            if error_message is not None and type(error_message) == str:
                self._error_message = error_message

    def set_status_to_unbroken(self):
        if Program.Status.authorized_status_change(self.status,
                                                   Program.Status.unbroken):
            now = int(time.time())
            if now > app.config['FINAL_DEADLINE']:
                utils.console("Submission rejected after final deadline")
                self.set_status_to_compilation_failed(
                    "Submission rejected after final deadline")
                return
            self._status = Program.Status.unbroken.value
            self._key = None
            if self._timestamp_published is None:
                self._timestamp_published = now
            self.update_strawberries(now)
            self._funny_name = get_funny_name(self._id)

    def set_status_to_broken(self, user, now):
        if now > app.config['FINAL_DEADLINE']:
            return
        if Program.Status.authorized_status_change(self.status,
                                                   Program.Status.broken):
            self._status = Program.Status.broken.value
            if self._timestamp_first_break is None:
                self._timestamp_first_break = now
        else:
            utils.console("Could NOT set status to broken")

        whitebox_break = WhiteboxBreak.create(
            user, self, now, self._strawberries_last)
        db.session.add(whitebox_break)

    def set_status_to_inverted(self, user, now):
        if now > app.config['FINAL_DEADLINE']:
            return
        if Program.Status.authorized_status_change(self.status,
                                                   Program.Status.inverted):
            self._status = Program.Status.inverted.value
        else:
            utils.console("Could NOT set status to inverted")

        if self._timestamp_first_inversion is None:
            self._timestamp_first_inversion = now

        whitebox_inversion = WhiteboxInvert.create(
            user, self, now, self._carrots_last)
        db.session.add(whitebox_inversion)

    @property
    def is_published(self):
        return (self._status == Program.Status.unbroken.value) or \
            (self._status == Program.Status.inverted.value) or \
            (self._status == Program.Status.broken.value)

    @property
    def is_broken(self):
        return self._status == Program.Status.broken.value

    @property
    def is_inverted(self):
        return self._status == Program.Status.inverted.value

    @staticmethod
    def create(user, basename, key, compiler):
        program = Program(_basename=basename,
                          _key=key,
                          _compiler=compiler,
                          _user_id=user._id)
        db.session.add(program)

    def generate_nonce(self):
        self._nonce = ''.join(random.SystemRandom().choice(
            string.ascii_lowercase + string.digits) for _ in range(32))
        return self._nonce

    def compare_nonces(self, nonce):
        return self._nonce == nonce

    def set_performance_factor(self, size_factor, ram_factor, time_factor):
        self._size_factor = size_factor
        self._ram_factor = ram_factor
        self._time_factor = time_factor
        self._performance_factor = 1 - log(size_factor, 2) - \
            log(ram_factor, 2) - log(time_factor, 2)

    @staticmethod
    def get_number_of_submitted_programs():
        return Program.query.count()

    @staticmethod
    def get_number_of_unbroken_programs():
        return Program.query.filter(or_(
            Program._status == Program.Status.unbroken.value,
            Program._status == Program.Status.inverted.value,
        )).count()

    @staticmethod
    def get_number_of_inverted_programs():
        return Program.query.filter(
            Program._status == Program.Status.inverted.value,
        ).count()

    @staticmethod
    def get_next_program_to_compile():
        return Program.query.filter(
            Program._status == Program.Status.submitted.value,
            Program._task_id.is_(None)
        ).order_by(Program._timestamp_submitted).first()

    @staticmethod
    def get(basename):
        return Program.query.filter(Program._basename == basename).first()

    @staticmethod
    def get_by_id(_id):
        return Program.query.filter(Program._id == _id).first()

    @staticmethod
    def get_unbroken_or_broken_by_id(_id):
        program = Program.query.filter(Program._id == _id).first()
        if program.status in [
                Program.Status.unbroken,
                Program.Status.inverted,
                Program.Status.broken
        ]:
            return program
        else:
            return None

    @staticmethod
    def get_inverted_or_broken_by_id(_id):
        program = Program.query.filter(Program._id == _id).first()
        if program.status in [Program.Status.inverted, Program.Status.broken]:
            return program
        else:
            return None

    @staticmethod
    def get_all_published_sorted_by_ranking(max_rank=None):
        if max_rank is not None:
            programs = Program.query.filter(or_(
                Program._status == Program.Status.unbroken.value,
                Program._status == Program.Status.inverted.value,
                Program._status == Program.Status.broken.value
            )).filter(
                Program._strawberries_ranking <= max_rank
            ).order_by(Program._strawberries_ranking).all()
        else:
            programs = Program.query.filter(or_(
                Program._status == Program.Status.unbroken.value,
                Program._status == Program.Status.inverted.value,
                Program._status == Program.Status.broken.value
            )).order_by(Program._strawberries_ranking).all()
        return programs

    @staticmethod
    def get_user_programs(user, status):
        return Program.query.filter(
            Program._user_id == user._id,
            Program._status == status.value
        ).all()

    @staticmethod
    def get_user_program_by_id(user, _id):
        return Program.query.filter(
            Program._user_id == user._id,
            Program._id == _id
        ).first()

    @staticmethod
    def get_user_queued_programs(user):
        return Program.query.filter(
            Program._user_id == user._id,
            Program._status == Program.Status.submitted.value
        ).order_by(Program._timestamp_submitted).all()

    @staticmethod
    def get_user_rejected_programs(user):
        return Program.query.filter(
            Program._user_id == user._id,
            or_(Program._status == Program.Status.compilation_failed.value,
                Program._status == Program.Status.link_failed.value,
                Program._status == Program.Status.execution_failed.value,
                Program._status == Program.Status.test_failed.value)
        ).order_by(Program._timestamp_submitted).all()

    @staticmethod
    def get_user_competing_programs(user):
        return Program.query.filter(
            Program._user_id == user._id,
            or_(Program._status == Program.Status.unbroken.value,
                Program._status == Program.Status.inverted.value,
                Program._status == Program.Status.broken.value)
        ).order_by(Program._timestamp_submitted).all()

    @staticmethod
    def get_programs_requiring_update(now):
        return Program.query.filter(
            or_(
                Program._status == Program.Status.unbroken.value,
                Program._status == Program.Status.inverted.value,
                and_(
                    Program._status == Program.Status.broken.value,
                    Program._strawberries_last > 0
                )
            )).all()

    @staticmethod
    def rank_of_challenge(strawberries_peak):
        if strawberries_peak is None:
            return 1 + Program.query.filter(
                or_(Program._status == Program.Status.unbroken.value,
                    Program._status == Program.Status.inverted.value,
                    Program._status == Program.Status.broken.value)
            ).count()
        else:
            return 1 + Program.query.filter(
                or_(Program._status == Program.Status.unbroken.value,
                    Program._status == Program.Status.inverted.value,
                    Program._status == Program.Status.broken.value),
                Program._strawberries_peak > strawberries_peak
            ).count()

    @staticmethod
    def get_program_being_compiled(running_task_id):
        return Program.query.filter(
            Program._status == Program.Status.submitted.value,
            Program._task_id == running_task_id
        ).first()

    @staticmethod
    def get_all_programs_being_compiled_or_tested():
        return Program.query.filter(
            Program._status == Program.Status.submitted.value,
            Program._task_id.isnot(None)
        ).order_by(Program._timestamp_compilation_start.desc()).all()

    def __str__(self):
        s = '[Program %d]\n' % (self._id)
        s += '\t funny_name:                         %s\n' % (
            str(self._funny_name))
        s += '\t basename:                           %s\n' % (
            str(self._basename))
        s += '\t user_id:                            %s\n' % (
            str(self._user_id))
        s += '\t nonce:                              %s\n' % (str(self._nonce))
        s += '\t timestamp_submitted:                %s\n' % (
            str(self._timestamp_submitted))
        s += '\t timestamp_published:                %s\n' % (
            str(self._timestamp_published))
        s += '\t timestamp_first_break:              %s\n' % (
            str(self._timestamp_first_break))
        s += '\t status:                             %s\n' % (
            str(self._status))
        s += '\t key:                                %s\n' % (str(self._key))
        s += '\t compiler:                           %s\n' % (
            str(self._compiler))
        s += '\t task_id:                            %s\n' % (
            str(self._task_id))
        s += '\t timestamp_compilation_start:        %s\n' % (
            str(self._timestamp_compilation_start))
        s += '\t error_message:                      %s\n' % (
            str(self._error_message))
        s += '\t plaintexts:                         %s...\n' % (
            str(self._plaintexts)[0:32])
        s += '\t ciphertexts:                        %s...\n' % (
            str(self._ciphertexts)[0:32])
        s += '\t strawberries_peak:                  %s\n' % (
            str(self._strawberries_peak))
        s += '\t strawberries_last:                  %s\n' % (
            str(self._strawberries_last))
        return s
