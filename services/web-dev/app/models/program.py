import random
import string
import time

from enum import Enum, unique
from math import log
from sqlalchemy import or_, and_
from sqlalchemy.dialects import mysql

from app import app
from app import db
from app import utils
from app.funny_name_generator import get_funny_name
from .whiteboxbreak import WhiteboxBreak


class Program(db.Model):

    @unique
    class Status(Enum):
        submitted = 'submitted'
        preprocess_failed = 'preprocess_failed'
        compilation_failed = 'compilation_failed'
        link_failed = 'link_failed'
        execution_failed = 'execution_failed'
        test_failed = 'test_failed'
        unbroken = 'unbroken'
        broken = 'broken'

        def __str__(self):
            if self == self.submitted:
                return 'Submitted'
            elif self == self.preprocess_failed:
                return 'Preprocess failed'
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
            elif self == self.broken:
                return 'Broken'
            else:
                return '-'

        @staticmethod
        def authorized_status_change(current_status, new_status):
            all_authorized_status_change = [
                (Program.Status.submitted, Program.Status.preprocess_failed),
                (Program.Status.submitted, Program.Status.compilation_failed),
                (Program.Status.submitted, Program.Status.link_failed),
                (Program.Status.submitted, Program.Status.execution_failed),
                (Program.Status.submitted, Program.Status.test_failed),
                (Program.Status.submitted, Program.Status.unbroken),
                (Program.Status.unbroken, Program.Status.broken),
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
    _pubkey = db.Column(db.String(128), default=None, unique=True)
    _proof_of_knowledge = db.Column(db.String(128), default=None)
    _performance_factor = db.Column(mysql.DOUBLE, default=1.0)
    _size_factor = db.Column(mysql.DOUBLE, default=1.0)
    _ram_factor = db.Column(mysql.DOUBLE, default=1.0)
    _time_factor = db.Column(mysql.DOUBLE, default=1.0)
    # ID of the docker task responsible for the compilation
    _task_id = db.Column(db.String(32), default=None)
    _timestamp_compilation_start = db.Column(db.BigInteger, default=None)
    _timestamp_compilation_finished = db.Column(db.BigInteger, default=None)
    _error_message = db.Column(db.Text, default=None)
    _hashes = db.Column(db.LargeBinary, default=None)
    _signatures = db.Column(db.LargeBinary, default=None)

    # First set when the program is published
    _strawberries_peak = db.Column(mysql.DOUBLE, default=0)
    _strawberries_last = db.Column(mysql.DOUBLE, default=0)
    _strawberries_ranking = db.Column(db.BigInteger, default=None)
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
    def pubkey(self):
        return self._pubkey

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
    def proof_of_knowledge(self):
        return self._proof_of_knowledge

    @property
    def error_message(self):
        return self._error_message

    @property
    def hashes(self):
        return self._hashes

    @hashes.setter
    def hashes(self, val):
        assert type(val) == bytes
        if self._hashes is None:
            self._hashes = val

    @property
    def signatures(self):
        return self._signatures

    @signatures.setter
    def signatures(self, val):
        assert type(val) == bytes
        if self._signatures is None:
            self._signatures = val

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

    @property
    def timestamp_last_update(self):
        last_update = self._timestamp_published
        if self._timestamp_first_break:
            last_update = self._timestamp_first_break
        if self._timestamp_first_inversion and \
           last_update < self._timestamp_first_inversion:
            last_update = self._timestamp_first_inversion

        return last_update

    def update_strawberries(self, now):
        if not self.is_published:
            return

        strawberries = self.current_strawberries(now)
        self._strawberries_last = strawberries
        if self._strawberries_peak < strawberries:
            self._strawberries_peak = strawberries

    @staticmethod
    def clean_programs_which_timeout_to_compile_or_test():
        programs = Program.get_all_programs_being_compiled_or_tested()

        # We ensure the first program has not been compiled/tested for too long
        for p in programs[:1]:
            max_compile_time = app.config['CHALLENGE_MAX_TIME_COMPILATION_IN_SECS']
            max_exec_time = app.config['CHALLENGE_MAX_TIME_EXECUTION_IN_SECS'] * \
                app.config['CHALLENGE_NUMBER_OF_TEST_VECTORS']
            # buffer for forking processes
            buffer_time_for_forking = 100
            max_time = 10 + max_compile_time + max_exec_time + buffer_time_for_forking
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

    def current_strawberries(self, end_timestamp):
        if not self.is_published:
            return None
        final_deadline = app.config['FINAL_DEADLINE']
        end_timestamp = min(end_timestamp, final_deadline)

        if self.is_broken:
            if end_timestamp < self._timestamp_first_break:
                return None
            surviving_minutes = int(
                (self._timestamp_first_break-self._timestamp_published) / 60)
            minutes_after_broken = int(
                (end_timestamp - self._timestamp_first_break) / 60)
            if minutes_after_broken > surviving_minutes:
                strawberries = 0
            else:
                strawberries = (
                    (surviving_minutes-minutes_after_broken)/1440.0)**2
        else:
            surviving_minutes = int(
                (end_timestamp-self._timestamp_published) / 60)
            strawberries = (surviving_minutes/1440.0) ** 2
        return strawberries * float(self._performance_factor)

    def set_status_to_compilation_failed(self, error_message=None):
        utils.console(
            "Setting the status to compilation_failed for program with id %s" % str(self._id))
        if Program.Status.authorized_status_change(
                self.status, Program.Status.compilation_failed):
            self._status = Program.Status.compilation_failed.value
            if error_message is not None and type(error_message) == str:
                self._error_message = error_message

    def set_status_to_preprocess_failed(self, error_message=None):
        utils.console(
            "Setting the status to preprocess_failed for program with id %s" % str(self._id))
        if Program.Status.authorized_status_change(
                self.status, Program.Status.preprocess_failed):
            self._status = Program.Status.preprocess_failed.value
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

    @property
    def is_published(self):
        return (self._status == Program.Status.unbroken.value) or \
            (self._status == Program.Status.broken.value)

    @property
    def is_broken(self):
        return self._status == Program.Status.broken.value

    @staticmethod
    def create(user, basename, pubkey, proof_of_knowledge):
        program = Program(_basename=basename,
                          _pubkey=pubkey,
                          _proof_of_knowledge=proof_of_knowledge,
                          _user_id=user._id)
        app.logger.info(f"New submission received: {program}")
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
        return Program.query.filter(
            Program._status == Program.Status.unbroken.value,
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
                Program.Status.broken
        ]:
            return program
        else:
            return None

    @staticmethod
    def get_all_published_sorted_by_ranking(max_rank=None):
        if max_rank is not None:
            programs = Program.query.filter(or_(
                Program._status == Program.Status.unbroken.value,
                Program._status == Program.Status.broken.value
            )).filter(
                Program._strawberries_ranking <= max_rank
            ).order_by(Program._strawberries_ranking).all()
        else:
            programs = Program.query.filter(or_(
                Program._status == Program.Status.unbroken.value,
                Program._status == Program.Status.broken.value
            )).order_by(Program._strawberries_ranking).all()
        return programs

    @staticmethod
    def get_all_published_sorted_by_published_time():
        programs = Program.query.filter(or_(
            Program._status == Program.Status.unbroken.value,
            Program._status == Program.Status.broken.value
        )).order_by(Program._timestamp_published).all()
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
            or_(Program._status == Program.Status.preprocess_failed.value,
                Program._status == Program.Status.compilation_failed.value,
                Program._status == Program.Status.link_failed.value,
                Program._status == Program.Status.execution_failed.value,
                Program._status == Program.Status.test_failed.value)
        ).order_by(Program._timestamp_submitted).all()

    @staticmethod
    def get_user_competing_programs(user):
        return Program.query.filter(
            Program._user_id == user._id,
            or_(Program._status == Program.Status.unbroken.value,
                Program._status == Program.Status.broken.value)
        ).order_by(Program._timestamp_submitted).all()

    @staticmethod
    def get_programs_requiring_update(now):
        return Program.query.filter(
            or_(
                Program._status == Program.Status.unbroken.value,
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
                    Program._status == Program.Status.broken.value)
            ).count()
        else:
            return 1 + Program.query.filter(
                or_(Program._status == Program.Status.unbroken.value,
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

    def __repr__(self):
        s = (
            f'[Program {self._id}]\n'
            f'\t funny_name:              {self._funny_name}\n'
            f'\t basename:                {self._basename}\n'
            f'\t user_id:                 {self._user_id}\n'
            f'\t nonce:                   {self._nonce}\n'
            f'\t timestamp_submitted:     {self._timestamp_submitted}\n'
            f'\t timestamp_published:     {self._timestamp_published}\n'
            f'\t timestamp_first_break:   {self._timestamp_first_break}\n'
            f'\t status:                  {self._status}\n'
            f'\t pubkey:                  {self._pubkey}\n'
            f'\t proof_of_knowledge:      {self._proof_of_knowledge}\n'
            f'\t task_id:                 {self._task_id}\n'
            f'\t ts_compilation_start:    {self._timestamp_compilation_start}\n'
            f'\t error_message:           {self._error_message}\n'
            f'\t hashes:                  {self._hashes}\n'
            f'\t signatures:              {self._signatures}\n'
            f'\t strawberries_peak:       {self._strawberries_peak}\n'
            f'\t strawberries_last:       {self._strawberries_last}\n'
        )
        return s
