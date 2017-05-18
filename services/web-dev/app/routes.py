import os
import time
import random
import string
import binascii
import sys
from Crypto.Cipher import AES
from traceback import print_exc
from flask import render_template, url_for, request, send_from_directory, request_started
from flask_login import login_user, logout_user, login_required, current_user
from app import app
from app import login_manager
from app import utils
from app import db
from .forms import LoginForm, UserCreationForm, WhiteboxSubmissionForm, WhiteboxBreakForm
from .models.user import User
from .models.program import Program
from .models.whiteboxbreak import WhiteboxBreak
from .utils import crx_flash, redirect

def update_strawberries(sender, **extra):
    now = int(time.time())
    try:
        programs = Program.get_programs_requiring_straberries_update(now)
        for program in programs:
            program.update_strawberries_and_next_update_timestamp(now)
        db.session.commit()
    except:
        db.session.rollback()
        print_exc()

def clean_programs_which_failed_to_compile_or_test(sender, **extra):
    Program.clean_programs_which_failed_to_compile_or_test()
    db.session.commit()

request_started.connect(update_strawberries, app)
request_started.connect(clean_programs_which_failed_to_compile_or_test, app)



def plot_data_for_program(program, now):
    data_flot = '['
    strawberries = program.strawberries(now)
    if len(strawberries) > 0:
        for key, val in sorted(strawberries.items()):
            data_flot += '[%d, %d], '%(key*1000, val)
        data_flot = data_flot[:-2]
    data_flot += ']'

    series = '{'
    series += 'color: "%s",'%program.hsl_color
    series += 'label: "%d",'%program._id
    series += 'data: ' + data_flot + '}'
    return series



@app.route('/', methods=['GET'])
def index():
    total_number_of_users = User.get_total_number_of_users()
    users = User.get_all_sorted_by_bananas()
    programs_to_plot = Program.get_all_published_sorted_by_ranking(max_rank=app.config['MAX_RANK_OF_PLOTED_CHALLENGES'])
    programs = Program.get_all_published_sorted_by_ranking()
    number_of_unbroken_programs = Program.get_number_of_unbroken_programs()
    wb_breaks = WhiteboxBreak.get_all()
    programs_broken_by_current_user = None
    if current_user and current_user.is_authenticated:
        wb_breaks_by_current_user = WhiteboxBreak.get_all_by_user(current_user)
        programs_broken_by_current_user = [wb_break.program for wb_break in wb_breaks_by_current_user]
    # plot data
    data_flot = None
    if len(programs_to_plot) > 0:
        data_flot = '[ '
        now = int(time.time())
        for program in programs_to_plot:
            data_flot += plot_data_for_program(program, now) + ', '
        data_flot = data_flot[:-2] + ' ]'
    return render_template('index.html',
                           active_page='index',
                           users=users,
                           total_number_of_users=total_number_of_users,
                           programs=programs,
                           wb_breaks=wb_breaks,
                           programs_broken_by_current_user=programs_broken_by_current_user,
                           number_of_unbroken_programs=number_of_unbroken_programs,
                           data_flot=data_flot)



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
        password = form.password1.data
        email = form.email1.data
        try:
            User.create(username=username, password=password, email=email)
        except:
            crx_flash('ERROR_USER_EXISTS')
            return redirect(url_for('user_create'))
        crx_flash('ACCOUNT_CREATED', username)
        return redirect(url_for('user_signin'))



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
        basename = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(32))
        filename = basename + '.c'
        key = form.key.data
        form_data = form.program.data
        form_data.save(os.path.join(upload_folder, filename))
        Program.create(basename=basename, key=key, user=current_user)
        db.session.commit()
        utils.launch_compilation_and_test()
        return redirect(url_for('submit_candidate_ok'))



# This route is called directly when the user has js activated (see file-progress.js)
@app.route('/submit/candidate/ok', methods=['GET'])
@login_required
def submit_candidate_ok():
    crx_flash('CHALLENGE_SUBMITTED')
    return redirect(url_for('user_show'))



@app.route('/show/candidate/<int:identifier>', methods=['GET'])
def show_candidate(identifier):
    program = Program.get_by_id(identifier)
    if program is None:
        return redirect(url_for('index'))
    do_show = False
    if program.is_published:
        do_show = True
    if current_user is not None and current_user.is_authenticated and current_user == program.user:
        do_show = True
    if not do_show:
        return redirect(url_for('index'))
    # If we reach this point, we can show the source code
    upload_folder = app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, program.filename)



@app.route('/user/show', methods=['GET'])
@login_required
def user_show():
    programs = Program.get_user_competing_programs(current_user)
    programs_queued = Program.get_user_queued_programs(current_user)
    programs_rejected = Program.get_user_rejected_programs(current_user)
    wb_breaks = WhiteboxBreak.get_all_by_user(current_user)
    return render_template('user_show.html',
                           active_page='user_show',
                           user=current_user,
                           programs=programs,
                           programs_queued=programs_queued,
                           programs_rejected=programs_rejected,
                           wb_breaks=wb_breaks)



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
                               datetime_strawberries_next_update=program.datetime_strawberries_next_update,
                               strawberries=program.strawberries_last,
                               identifier=identifier,
                               testing=app.testing)

    if program.plaintexts is None or program.ciphertexts is None:
        return redirect(url_for('index'))
    if len(program.plaintexts) != len(program.ciphertexts):
        return redirect(url_for('index'))
    if len(program.plaintexts) % 16 != 0:
        return redirect(url_for('index'))

    number_of_test_vectors = len(program.plaintexts) // 16
    key = bytes.fromhex(form.key.data)
    try:
        aes = AES.new(key, AES.MODE_ECB)
    except:
        return redirect(url_for('index'))
    for i in range(number_of_test_vectors):
        plaintext = program.plaintexts[16*i:16*(i+1)]
        ciphertext = program.ciphertexts[16*i:16*(i+1)]
        try:
            computed_ciphertext = aes.encrypt(plaintext)
        except:
            computed_ciphertext = None
        if computed_ciphertext is None or ciphertext != computed_ciphertext:
            plaintext_as_text = binascii.hexlify(plaintext).decode()
            ciphertext_as_text = binascii.hexlify(ciphertext).decode()
            return render_template('challenge_break_ko.html',
                                   identifier=identifier,
                                   current_user=current_user,
                                   plaintext=plaintext_as_text,
                                   ciphertext=ciphertext_as_text)

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




@app.route('/rules', methods=['GET'])
def rules():
    return render_template('rules.html',
                           challenge_max_source_size_in_mb=app.config['CHALLENGE_MAX_SOURCE_SIZE_IN_MB'],
                           challenge_max_mem_for_compilation_in_mb=app.config['CHALLENGE_MAX_MEM_COMPILATION_IN_MB'],
                           challenge_max_time_for_compilation_in_secs=app.config['CHALLENGE_MAX_TIME_COMPILATION_IN_SECS'],
                           challenge_max_binary_size_in_mb=app.config['CHALLENGE_MAX_BINARY_SIZE_IN_MB'],
                           challenge_max_mem_execution_in_mb=app.config['CHALLENGE_MAX_MEM_EXECUTION_IN_MB'],
                           challenge_max_time_execution_in_secs=app.config['CHALLENGE_MAX_TIME_EXECUTION_IN_SECS'])


def unauthorized_handler():
    crx_flash('PLEASE_SIGN_IN')
    try:
        return redirect(url_for('user_signin', next=url_for(request.endpoint)))
    except:
        return redirect(url_for('index'))

login_manager.unauthorized_handler(unauthorized_handler)
