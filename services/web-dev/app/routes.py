import binascii
from datetime import datetime
import hashlib
import os
import random
import string
import time

from Crypto.Cipher import AES
from traceback import print_exc
from flask import render_template, url_for, request, send_from_directory, \
    request_started, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app
from app import login_manager
from app import utils
from app import db
from .forms import LoginForm, UserCreationForm, WhiteboxSubmissionForm, \
    WhiteboxBreakForm, WhiteboxInvertForm, UserUpdateForm
from .models.user import User
from .models.program import Program
from .models.whiteboxbreak import WhiteboxBreak
from .models.whiteboxinvert import WhiteboxInvert
from .utils import crx_flash, redirect

from werkzeug.contrib.atom import AtomFeed


def need_to_check(url_rule):
    if url_rule.startswith('/static/') \
       or (url_rule.startswith('/user/') and url_rule != "/user/show") \
       or url_rule == '/rules' \
       or url_rule == '/submit/candidate':
        return False
    return True


def update_strawberries_and_carrots(sender, **extra):
    url_rule = str(request.url_rule)
    if not need_to_check(url_rule):
        return

    now = int(time.time())
    try:
        programs = Program.get_programs_requiring_update(now)

        # update the strawberries and carrots for each program
        for program in programs:
            program.update_strawberries(now)
            program.update_carrots(now)

        # refresh program and user ranking
        Program.refresh_all_strawberry_rankings()
        User.refresh_all_strawberry_rankings()

        db.session.commit()
    except:
        db.session.rollback()
        print_exc()


request_started.connect(update_strawberries_and_carrots, app)


@app.route('/', methods=['GET'])
def index():
    total_number_of_users = User.get_total_number_of_users()
    users = User.get_all_sorted_by_bananas()
    programs_to_plot = Program.get_all_published_sorted_by_ranking(
        max_rank=app.config['MAX_RANK_OF_PLOTED_CHALLENGES'])
    programs = Program.get_all_published_sorted_by_ranking()
    number_of_unbroken_programs = Program.get_number_of_unbroken_programs()
    number_of_uninverted_programs = number_of_unbroken_programs - \
        Program.get_number_of_inverted_programs()
    wb_breaks = WhiteboxBreak.get_all()
    wb_inversions = WhiteboxInvert.get_all()
    programs_broken_by_current_user = None
    programs_inverted_by_current_user = None
    if current_user and current_user.is_authenticated:
        wb_breaks_by_current_user = WhiteboxBreak.get_all_by_user(current_user)
        programs_broken_by_current_user = [
            wb_break.program for wb_break in wb_breaks_by_current_user]
        wb_inversions_by_current_user = WhiteboxInvert.get_all_by_user(
            current_user)
        programs_inverted_by_current_user = [
            wb_inversion.program for wb_inversion in wb_inversions_by_current_user
        ]

    return render_template(
        'index.html',
        active_page='index',
        users=users,
        total_number_of_users=total_number_of_users,
        programs=programs,
        wb_breaks=wb_breaks,
        wb_inversions=wb_inversions,
        programs_broken_by_current_user=programs_broken_by_current_user,
        programs_inverted_by_current_user=programs_inverted_by_current_user,
        number_of_unbroken_programs=number_of_unbroken_programs,
        number_of_uninverted_programs=number_of_uninverted_programs,
        programs_to_plot=programs_to_plot
    )


@app.route('/user/signin', methods=['GET', 'POST'])
def user_signin():
    if current_user.is_authenticated:
        return redirect(url_for('user_show'))
    form = LoginForm()
    if not form.validate_on_submit():
        return render_template('signin.html', form=form, active_page='user_signin', testing=app.testing)
    else:
        username = form.username.data
        password = form.password.data
        user = User.validate(username, password)
        if user is None:
            crx_flash('BAD_USERNAME_OR_PWD')
            return render_template('signin.html', form=form, active_page='user_signin', testing=app.testing)
        else:
            login_user(user, remember=False)
            crx_flash('WELCOME_BACK', user.username)
            next = request.args.get('next')
            if next is not None and utils.is_safe_url(request, next):
                return redirect(next)
            else:
                return redirect(url_for('user_show'))


@app.route('/user/signout', methods=['GET'])
def signout():
    logout_user()
    crx_flash('SIGNOUT')
    return redirect(url_for('index'))


@app.route('/user/create', methods=['GET', 'POST'])
def user_create():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = UserCreationForm()
    if not form.validate_on_submit():
        return render_template('create.html', form=form, active_page='user_create', testing=app.testing)
    else:
        username = form.username.data
        displayname = form.displayname.data
        password = form.password1.data
        email = form.email1.data
        try:
            User.create(username=username, displayname=displayname,
                        password=password, email=email)
        except:
            crx_flash('ERROR_USER_EXISTS')
            return redirect(url_for('user_create'))
        crx_flash('ACCOUNT_CREATED', username)
        return redirect(url_for('user_signin'))


@app.route('/user/update', methods=['GET', 'POST'])
def user_update():
    if not current_user.is_authenticated:
        return redirect(url_for('index'))
    form = UserUpdateForm()
    if not form.validate_on_submit():
        return render_template('update.html', form=form, active_page='update_update', testing=app.testing)
    else:
        displayname = form.displayname.data
        import sys
        print(displayname, file=sys.stderr)
        try:
            current_user.displayname = displayname
        except:
            crx_flash('ACCOUNT_UPDATE_FAILED')
            return redirect(url_for('index'))
        crx_flash('ACCOUNT_UPDATED')
        return redirect(url_for('index'))


@app.route('/submit/candidate', methods=['GET', 'POST'])
@login_required
def submit_candidate():
    now = int(time.time())
    if now < app.config['STARTING_DATE']:
        return render_template('submit_candidate_before_starting_date.html',
                               active_page='submit_candidate',
                               starting_date=utils.format_timestamp(app.config['STARTING_DATE']))
    if now > app.config['POSTING_DEADLINE']:
        return render_template('submit_candidate_deadline_exceeded.html',
                               active_page='submit_candidate',
                               posting_deadline=utils.format_timestamp(app.config['POSTING_DEADLINE']))
    form = WhiteboxSubmissionForm()
    if request.method != 'POST':
        return render_template('submit_candidate.html', form=form, active_page='submit_candidate', testing=app.testing)
    elif not form.validate_on_submit():
        return render_template('submit_candidate.html', form=form, active_page='submit_candidate', testing=app.testing), 400
    else:
        upload_folder = app.config['UPLOAD_FOLDER']
        basename = ''.join(random.SystemRandom().choice(
            string.ascii_lowercase + string.digits) for _ in range(32))
        filename = basename + '.c'
        key = form.key.data
        compiler = form.compiler.data
        form_data = form.program.data
        form_data.save(os.path.join(upload_folder, filename))
        Program.create(basename=basename,
                       key=key,
                       compiler=compiler,
                       user=current_user)
        db.session.commit()
        return redirect(url_for('submit_candidate_ok'))


# This route is called directly when the user has js activated (see file-progress.js)
@app.route('/submit/candidate/ok', methods=['GET'])
@login_required
def submit_candidate_ok():
    crx_flash('CHALLENGE_SUBMITTED')
    return redirect(url_for('user_show'))


@app.route('/show/candidate/<int:identifier>.c', methods=['GET'])
def show_candidate(identifier):
    program = Program.get_by_id(identifier)
    if program is None:
        return redirect(url_for('index'))
    do_show = False
    if program.is_published:
        do_show = True
    if current_user is not None and \
       current_user.is_authenticated and \
       current_user == program.user:
        do_show = True
    if not do_show:
        return redirect(url_for('index'))
    # If we reach this point, we can show the source code
    upload_folder = app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, program.filename)


@app.route('/candidate/<int:identifier>', methods=['GET'])
def candidate(identifier):
    program = Program.get_by_id(identifier)
    if program is None:
        return redirect(url_for('index'))
    do_show = False
    if program.is_published:
        do_show = True
    if current_user is not None and \
       current_user.is_authenticated and \
       current_user == program.user:
        do_show = True
    if not do_show:
        return redirect(url_for('index'))

    programs_broken_by_current_user = None
    programs_inverted_by_current_user = None
    if current_user and current_user.is_authenticated:
        wb_breaks_by_current_user = WhiteboxBreak.get_all_by_user(current_user)
        programs_broken_by_current_user = [
            wb_break.program for wb_break in wb_breaks_by_current_user]
        wb_inversions_by_current_user = WhiteboxInvert.get_all_by_user(
            current_user)
        programs_inverted_by_current_user = [
            wb_inversion.program for wb_inversion in wb_inversions_by_current_user
        ]

    # If we reach this point, we can show the source code
    return render_template(
        'candidate.html',
        program=program,
        programs_broken_by_current_user=programs_broken_by_current_user,
        programs_inverted_by_current_user=programs_inverted_by_current_user,
    )


@app.route('/show/candidate/<int:identifier>/testvectors', methods=['GET'])
def show_candidate_sample(identifier):
    program = Program.get_by_id(identifier)
    if program is None or not program.is_published:
        return redirect(url_for('index'))

    number_of_test_vectors = int(len(program.plaintexts) / 16)
    test_vectors = list()
    for i in range(number_of_test_vectors):
        test_vectors.append({
            "plaintext": binascii.hexlify(
                program.plaintexts[i*16:(i+1)*16]).decode(),
            "ciphertext": binascii.hexlify(
                program.ciphertexts[i*16:(i+1)*16]).decode()
        })

    res = {
        "id": program._id,
        "test_vectors": test_vectors
    }

    return jsonify(res)


@app.route('/user/show', methods=['GET'])
@login_required
def user_show():
    programs = Program.get_user_competing_programs(current_user)
    programs_queued = Program.get_user_queued_programs(current_user)
    programs_rejected = Program.get_user_rejected_programs(current_user)
    wb_breaks = WhiteboxBreak.get_all_by_user(current_user)
    wb_inversions = WhiteboxInvert.get_all_by_user(current_user)
    return render_template('user_show.html',
                           active_page='user_show',
                           user=current_user,
                           programs=programs,
                           programs_queued=programs_queued,
                           programs_rejected=programs_rejected,
                           wb_breaks=wb_breaks,
                           wb_inversions=wb_inversions
                           )


@app.route('/break/candidate/<int:identifier>', methods=['GET', 'POST'])
@login_required
def break_candidate(identifier):
    now = int(time.time())
    if now < app.config['STARTING_DATE']:
        return redirect(url_for('index'))
    if now > app.config['FINAL_DEADLINE']:
        return render_template('break_candidate_deadline_exceeded.html',
                               active_page='submit_candidate',
                               final_deadline=utils.format_timestamp(app.config['FINAL_DEADLINE']))

    # Only published programs can be broken
    program = Program.get_unbroken_or_broken_by_id(identifier)
    if program is None or not program.is_published:
        return redirect(url_for('index'))

    # If the current user is the one who submitted the program, redirect to index
    if program.user == current_user:
        crx_flash('CANNOT_BREAK_OWN')
        return redirect(url_for('index'))

    # A user cannot break the same challenge twice
    wb_break = WhiteboxBreak.get(current_user, program)
    if wb_break is not None:
        crx_flash('CANNOT_BREAK_TWICE')
        return redirect(url_for('index'))

    form = WhiteboxBreakForm()
    if request.method != 'POST' or not form.validate_on_submit():
        return render_template('break_candidate.html',
                               form=form,
                               strawberries=program.strawberries_last,
                               identifier=identifier,
                               testing=app.testing)

    if program.plaintexts is None or program.ciphertexts is None:
        return redirect(url_for('index'))
    number_of_test_vectors = 10
    plaintexts = program.plaintexts
    ciphertexts = program.ciphertexts
    if len(plaintexts) != len(ciphertexts) or len(plaintexts) % 16 != 0 or \
       len(plaintexts) == 0:
        return redirect(url_for('index'))

    key = bytes.fromhex(form.key.data)
    try:
        aes = AES.new(key, AES.MODE_ECB)
    except:
        return redirect(url_for('index'))
    for i in range(number_of_test_vectors):
        pt = plaintexts[16*i:16*(i+1)]
        ct = ciphertexts[16*i:16*(i+1)]
        try:
            computed_ct = aes.encrypt(pt)
        except:
            computed_ct = None
        if computed_ct is None or ct != computed_ct:
            pt_as_text = binascii.hexlify(pt).decode()
            ct_as_text = binascii.hexlify(ct).decode()
            return render_template('challenge_break_ko.html',
                                   identifier=identifier,
                                   current_user=current_user,
                                   plaintext=pt_as_text,
                                   ciphertext=ct_as_text)

    # If we reach this point, the submitted key is correct
    program.set_status_to_broken(current_user, now)
    db.session.commit()

    return redirect(url_for('break_candidate_ok', identifier=identifier))


@app.route('/break/candidate/ok/<int:identifier>', methods=['GET'])
@login_required
def break_candidate_ok(identifier):
    # Check that the program is broken
    program = Program.get_unbroken_or_broken_by_id(identifier)
    if program is None or not program.is_broken:
        return redirect(url_for('index'))
    # Check that the user indeed broke the challenge
    wb_break = WhiteboxBreak.get(current_user, program)
    if wb_break is None:
        return redirect(url_for('index'))
    # If we reach this point, the user indeed broke the challenge
    return render_template('challenge_break_ok.html', wb_break=wb_break, current_user=current_user)


@app.route('/invert/candidate/<int:identifier>', methods=['GET', 'POST'])
@login_required
def invert_candidate(identifier):
    now = int(time.time())
    if now < app.config['STARTING_DATE']:
        return redirect(url_for('index'))
    if now > app.config['FINAL_DEADLINE']:
        return render_template(
            'break_candidate_deadline_exceeded.html',
            active_page='submit_candidate',
            final_deadline=utils.format_timestamp(app.config['FINAL_DEADLINE'])
        )

    # Only published programs can be broken
    program = Program.get_unbroken_or_broken_by_id(identifier)
    if program is None or not program.is_published:
        return redirect(url_for('index'))

    # If the current user is the one who submitted the program,
    # redirect to index
    if program.user == current_user:
        crx_flash('CANNOT_INVERT_OWN')
        return redirect(url_for('index'))

    # A user cannot invert the same challenge twice
    wb_invert = WhiteboxInvert.get(current_user, program)
    if wb_invert is not None:
        crx_flash('CANNOT_INVERT_TWICE')
        return redirect(url_for('index'))

    if program.plaintexts is None or program.ciphertexts is None:
        return redirect(url_for('index'))
    plaintext_sha256 = program.plaintext_sha256_for_inverting
    ciphertext = program.ciphertext_for_inverting
    if len(plaintext_sha256) != 64 or len(ciphertext) != 16:
        return redirect(url_for('index'))

    form = WhiteboxInvertForm()
    if request.method != 'POST' or not form.validate_on_submit():
        ciphertext_as_text = binascii.hexlify(ciphertext).decode()
        return render_template(
            'invert_candidate.html',
            form=form,
            carrots=program._carrots_last,
            ciphertext=ciphertext_as_text,
            identifier=identifier,
            testing=app.testing)

    # todo: return pt in some way
    plaintext_submitted = bytes.fromhex(form.plaintext.data)
    plaintext_submitted_sha256 = hashlib.sha256(
        plaintext_submitted).hexdigest()

    if len(plaintext_submitted_sha256) != 64 or \
       plaintext_sha256 != plaintext_submitted_sha256:
        return render_template('challenge_inversion_ko.html',
                               identifier=identifier,
                               current_user=current_user,
                               plaintext=form.plaintext.data,
                               ciphertext=form.ciphertext.data)

    # If we reach this point, the submitted key is correct
    program.set_status_to_inverted(current_user, now)
    db.session.commit()

    return redirect(url_for('invert_candidate_ok', identifier=identifier))


@app.route('/invert/candidate/ok/<int:identifier>', methods=['GET'])
@login_required
def invert_candidate_ok(identifier):
    program = Program.get_inverted_or_broken_by_id(identifier)
    if program is None:
        return redirect(url_for('index'))

    # Check that the user indeed broke the challenge
    wb_inversion = WhiteboxInvert.get(current_user, program)
    if wb_inversion is None:
        return redirect(url_for('index'))
    # If we reach this point, the user indeed broke the challenge
    return render_template('challenge_inversion_ok.html',
                           wb_inversion=wb_inversion,
                           current_user=current_user)


@app.route('/rules', methods=['GET'])
def rules():
    return render_template(
        'rules.html',
        challenge_max_source_size_in_mb=app.config['CHALLENGE_MAX_SOURCE_SIZE_IN_MB'],
        challenge_max_mem_for_compilation_in_mb=app.config['CHALLENGE_MAX_MEM_COMPILATION_IN_MB'],
        challenge_max_time_for_compilation_in_secs=app.config[
            'CHALLENGE_MAX_TIME_COMPILATION_IN_SECS'],
        challenge_max_binary_size_in_mb=app.config['CHALLENGE_MAX_BINARY_SIZE_IN_MB'],
        challenge_max_mem_execution_in_mb=app.config['CHALLENGE_MAX_MEM_EXECUTION_IN_MB'],
        challenge_max_time_execution_in_secs=app.config['CHALLENGE_MAX_TIME_EXECUTION_IN_SECS']
    )


@app.route('/rss.xml', methods=['GET'])
def recent_feed():
    feed = AtomFeed('WhibOx 2nd Edition -- CHES 2019 CTF',
                    feed_url=request.url, url=request.url_root,
                    author="WhibOx organizing committee",
                    subtitle="Submitted challenged order by published date descending"
                    )
    programs = Program.get_all_published_sorted_by_published_time()

    for program in programs:
        item_url = "%scandidate/%d" % (
            request.url_root, program._id)
        title = 'New challenge "<strong>%s</strong>" submitted' % program.funny_name
        author = program.user.displayname
        content = render_template('candidate.html', program=program, feed=True)

        if not author or not author.strip():
            author = program.user.username
        feed.add(id=item_url,
                 title=title,
                 title_type='html',
                 updated=datetime.fromtimestamp(program._timestamp_published),
                 author=author,
                 url=item_url,
                 categories=[{'term': program.status}],
                 content=content,
                 content_type='html',
                 )
    return feed.get_response()


def unauthorized_handler():
    crx_flash('PLEASE_SIGN_IN')
    try:
        return redirect(url_for('user_signin', next=url_for(request.endpoint)))
    except:
        return redirect(url_for('index'))


login_manager.unauthorized_handler(unauthorized_handler)
