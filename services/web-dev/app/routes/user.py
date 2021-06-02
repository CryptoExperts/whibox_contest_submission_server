from flask import render_template, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError

from app import app
from app.forms import LoginForm, UserRegisterForm
from app.models.user import User
from app.models.program import Program
from app.models.whiteboxbreak import WhiteboxBreak
from app.utils import crx_flash, redirect, is_safe_url


@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if current_user.is_authenticated:
        return redirect(url_for('user_show'))
    form = LoginForm()
    if not form.validate_on_submit():
        return render_template('login.html', form=form, testing=app.testing)
    else:
        username = form.username.data
        password = form.password.data
        user = User.validate(username, password)
        if user is None:
            crx_flash('BAD_USERNAME_OR_PWD')
            return render_template('login.html', form=form, testing=app.testing)
        else:
            login_user(user, remember=False)
            crx_flash('WELCOME_BACK', user.username)
            next = request.args.get('next')
            if next is not None and is_safe_url(request, next):
                return redirect(next)
            else:
                return redirect(url_for('user_show'))


@app.route('/user/logout', methods=['GET'])
def logout():
    logout_user()
    crx_flash('LOGOUT')
    return redirect(url_for('index'))


@app.route('/user/register', methods=['GET', 'POST'])
def user_register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = UserRegisterForm()
    if not form.validate_on_submit():
        return render_template('register.html', form=form, testing=app.testing)
    else:
        username = form.username.data
        nickname = form.nickname.data
        password = form.password1.data
        email = form.email1.data
        print(username, nickname, password, email, flush=True)
        try:
            User.create(username=username, nickname=nickname,
                        password=password, email=email)
        except IntegrityError as e:
            app.logger.warning(f"Integrity Error: {e}")
            crx_flash('ERROR_USER_EXISTS')
            return redirect(url_for('user_register'))
        except Exception as e:
            app.logger.warning(f"Unknown Error: {e}")
            crx_flash('ERROR_UNKNOWN')
            return redirect(url_for('user_register'))

        app.logger.info(f"User created: {username}, {nickname}, {email}")
        crx_flash('ACCOUNT_CREATED', username)
        return redirect(url_for('user_login'))


@app.route('/user/show', methods=['GET'])
@login_required
def user_show():
    programs = Program.get_user_competing_programs(current_user)
    programs_queued = Program.get_user_queued_programs(current_user)
    programs_rejected = Program.get_user_rejected_programs(current_user)
    wb_breaks = WhiteboxBreak.get_all_by_user(current_user)
    User.refresh_all_strawberry_rankings()
    total_breaks_by_program = WhiteboxBreak.get_total_breaks_group_by_program()
    return render_template('user_show.html',
                           active_page='user_show',
                           user=current_user,
                           programs=programs,
                           programs_queued=programs_queued,
                           programs_rejected=programs_rejected,
                           wb_breaks=wb_breaks,
                           total_breaks_by_program=total_breaks_by_program)
