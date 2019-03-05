import time
import random
import string
from traceback import print_exc
from enum import Enum, unique
from app import app
from app import db
from app import utils
from app.funny_name_generator import get_funny_name
from sqlalchemy import or_
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
    # ID of the docker task responsible for the compilation and plaintext/ciphertext pairs generation
    _task_id = db.Column(db.String(32), default=None)
    _timestamp_compilation_start = db.Column(db.BigInteger, default=None)
    _timestamp_compilation_finished = db.Column(db.BigInteger, default=None)
    _error_message = db.Column(db.Text, default=None)
    _plaintexts = db.Column(db.LargeBinary, default=None)
    _ciphertexts = db.Column(db.LargeBinary, default=None)
    # First set when the program is published
    _strawberries_peak = db.Column(db.BigInteger, default=None)
    # First set when the program is published
    _strawberries_last = db.Column(db.BigInteger, default=None)
    _strawberries_ranking = db.Column(db.BigInteger, default=None)
    _timestamp_strawberries_next_update = db.Column(
        db.BigInteger, default=None)  # First set when the program is published
    _carrots_last = db.Column(db.BigInteger, default=None)
    _timestamp_first_inversion = db.Column(db.BigInteger, default=None)

    @property
    def position_in_the_compilation_queue(self):
        if self.status != Program.Status.submitted:
            return None
        if self._task_id != None:
            return 'In progress'
        pos = Program.query.filter(Program._status == Program.Status.submitted.value,
                                   Program._task_id == None,
                                   Program._timestamp_submitted < self._timestamp_submitted)\
            .count()
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
    def carrots_last(self):
        return self._carrots_last

    @property
    def hsl_color(self):
        return 'hsl(%d, 100%%, %d%%)' % (self._timestamp_submitted % 360, self._timestamp_published % 47 + 20)

    @property
    def datetime_submitted(self):
        return utils.format_timestamp(self._timestamp_submitted)

    @property
    def datetime_strawberries_next_update(self):
        return utils.format_timestamp(self._timestamp_strawberries_next_update)

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
    def ciphertexts(self):
        return self._ciphertexts

    @ciphertexts.setter
    def ciphertexts(self, val):
        assert type(val) == bytes
        if self._ciphertexts is None:
            self._ciphertexts = val

    @property
    def datetime_first_break(self):
        if self._timestamp_first_break is None:
            return None
        else:
            return utils.format_timestamp(self._timestamp_first_break)

    def update_strawberries_and_next_update_timestamp(self, now):
        if not self.is_published:
            return
        strawberries = self.strawberries(now)
        # Update the strawberries peak and last value in DB
        new_peak = max(strawberries.values())
        if self._strawberries_peak != new_peak:
            self._strawberries_peak = new_peak
            Program.refresh_all_strawberry_rankings()
        last_timestamp = max(strawberries.keys())
        self._strawberries_last = strawberries[last_timestamp]
        self._timestamp_strawberries_next_update = last_timestamp + \
            app.config['NBR_SECONDS_PER_DAY']
        if self.user.strawberries is None or self._strawberries_peak > self.user.strawberries:
            self.user.refresh_strawberries_count_and_rank()

    @staticmethod
    def clean_programs_which_failed_to_compile_or_test():
        now = int(time.time())

        programs = Program.query.filter(
            Program._status == Program.Status.submitted.value,
            Program._task_id != None
        ).order_by(Program._timestamp_compilation_start.desc()).all()
        # We ensure the first program has not been compiled/tested for too long
        for p in programs[:1]:
            max_compile_time = app.config['CHALLENGE_MAX_TIME_COMPILATION_IN_SECS']
            max_exec_time = app.config['CHALLENGE_MAX_TIME_EXECUTION_IN_SECS'] * \
                app.config['CHALLENGE_NUMBER_OF_TEST_VECTORS']
            max_time = 10 + max_compile_time + max_exec_time
            if now > p._timestamp_compilation_start + max_time:
                p.set_status_to_execution_failed(
                    'Compilation and/or testing took too much time. Timeout!')
        # Any other unpublished program with a lower 'timestamp_compilation_start' must have crashed their docker
        for p in programs[1:]:
            p.set_status_to_execution_failed(
                'Compilation and/or testing failed for unknown reason.')

    @staticmethod
    def refresh_all_strawberry_rankings():
        programs = Program.query.filter(or_(Program._status == Program.Status.unbroken.value,
                                            Program._status == Program.Status.broken.value))\
            .order_by(Program._strawberries_peak.desc())\
            .all()
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

    def strawberries(self, now=int(time.time())):
        if not self.is_published:
            return None

        strawberries = {}
        running_val = 0
        running_val_diff = 0

        if not self.is_broken:
            for running_timestamp in range(self._timestamp_published, min(now, app.config['FINAL_DEADLINE'])+1, app.config['NBR_SECONDS_PER_DAY']):
                running_val += running_val_diff
                running_val_diff += 1
                strawberries[running_timestamp] = running_val
        else:
            for running_timestamp in range(self._timestamp_published, self._timestamp_first_break, app.config['NBR_SECONDS_PER_DAY']):
                running_val += running_val_diff
                running_val_diff += 1
                strawberries[running_timestamp] = running_val
            running_val = max(running_val - 1, 0)
            for running_timestamp in range(self._timestamp_first_break, min(now, app.config['FINAL_DEADLINE'])+1, app.config['NBR_SECONDS_PER_DAY']):
                strawberries[running_timestamp] = running_val
                running_val_diff = max(running_val_diff - 1, 0)
                running_val = max(running_val - running_val_diff, 0)

        return strawberries

    def set_status_to_compilation_failed(self, error_message=None):
        utils.console(
            "Setting the status to compilation_failed for program with id %s" % str(self._id))
        if Program.Status.authorized_status_change(self.status, Program.Status.compilation_failed):
            self._status = Program.Status.compilation_failed.value
            if error_message is not None and type(error_message) == str:
                self._error_message = error_message

    def set_status_to_link_failed(self):
        if Program.Status.authorized_status_change(self.status, Program.Status.link_failed):
            self._status = Program.Status.link_failed.value

    def set_status_to_execution_failed(self, error_message=None):
        if Program.Status.authorized_status_change(self.status, Program.Status.execution_failed):
            self._status = Program.Status.execution_failed.value
            if error_message is not None and type(error_message) == str:
                self._error_message = error_message

    def set_status_to_test_failed(self, error_message=None):
        if Program.Status.authorized_status_change(self.status, Program.Status.test_failed):
            self._status = Program.Status.test_failed.value
            if error_message is not None and type(error_message) == str:
                self._error_message = error_message

    def set_status_to_unbroken(self):
        if Program.Status.authorized_status_change(self.status, Program.Status.unbroken):
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
            self.update_strawberries_and_next_update_timestamp(now)
            self._funny_name = get_funny_name(self._id)

    def set_status_to_broken(self, user, now):
        if now > app.config['FINAL_DEADLINE']:
            return
        if Program.Status.authorized_status_change(self.status, Program.Status.broken):
            self._status = Program.Status.broken.value
            if self._timestamp_first_break is None:
                self._timestamp_first_break = now
                # + app.config['NBR_SECONDS_PER_DAY']
                self._timestamp_strawberries_next_update = now
            whitebox_break = WhiteboxBreak.create(
                user, self, now, self._strawberries_last)
            db.session.add(whitebox_break)
        else:
            utils.console("Could NOT set status to broken")

    def set_status_to_inverted(self, user, now):
        if now > app.config['FINAL_DEADLINE']:
            return
        if Program.Status.authorized_status_change(self.status, Program.Status.inverted):
            self._status = Program.Status.inverted.value
        if self._timestamp_first_inversion is None:
            self._timestamp_first_inversion = now
            self._timestamp_carrots_next_update = now
            # TODO:
            self._carrots_last = 0
            whitebox_inversion = WhiteboxInvert.create(
                user, self, now, self._carrots_last)
            db.session.add(whitebox_inversion)
        else:
            utils.console("Could NOT set status to broken")

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

    @staticmethod
    def get_number_of_submitted_programs():
        return Program.query.count()

    @staticmethod
    def get_number_of_unbroken_programs():
        return Program.query.filter(
            Program._status == Program.Status.unbroken.value
        ).count()

    @staticmethod
    def get_next_program_to_compile():
        return Program.query.filter(
            Program._status == Program.Status.submitted.value,
            Program._task_id == None
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
        if program.status in [Program.Status.unbroken, Program.Status.broken]:
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
        return Program.query.filter(Program._user_id == user._id, Program._status == status.value).all()

    @staticmethod
    def get_user_program_by_id(user, _id):
        return Program.query.filter(Program._user_id == user._id, Program._id == _id).first()

    @staticmethod
    def get_user_queued_programs(user):
        return Program.query.filter(Program._user_id == user._id,
                                    Program._status == Program.Status.submitted.value)\
            .order_by(Program._timestamp_submitted)\
            .all()

    @staticmethod
    def get_user_rejected_programs(user):
        return Program.query.filter(Program._user_id == user._id,
                                    or_(Program._status == Program.Status.compilation_failed.value,
                                        Program._status == Program.Status.link_failed.value,
                                        Program._status == Program.Status.execution_failed.value,
                                        Program._status == Program.Status.test_failed.value))\
            .order_by(Program._timestamp_submitted)\
            .all()

    @staticmethod
    def get_user_competing_programs(user):
        return Program.query.filter(Program._user_id == user._id,
                                    or_(Program._status == Program.Status.unbroken.value,
                                        Program._status == Program.Status.broken.value))\
            .order_by(Program._timestamp_submitted)\
            .all()

    @staticmethod
    def get_programs_requiring_straberries_update(now):
        return Program.query.filter(or_(Program._status == Program.Status.unbroken.value,
                                        Program._status == Program.Status.broken.value),
                                    Program._timestamp_strawberries_next_update < now)\
            .all()

    @staticmethod
    def rank_of_challenge(strawberries_peak):
        if strawberries_peak is None:
            return 1 + Program.query.filter(or_(Program._status == Program.Status.unbroken.value,
                                                Program._status == Program.Status.broken.value))\
                .count()
        else:
            return 1 + Program.query.filter(or_(Program._status == Program.Status.unbroken.value,
                                                Program._status == Program.Status.broken.value),
                                            Program._strawberries_peak > strawberries_peak)\
                .count()

    @staticmethod
    def get_program_being_compiled(running_task_id):
        return Program.query.filter(Program._status == Program.Status.submitted.value,
                                    Program._task_id == running_task_id)\
            .first()

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
        s += '\t timestamp_strawberries_next_update: %s\n' % (
            str(self._timestamp_strawberries_next_update))
        return s
