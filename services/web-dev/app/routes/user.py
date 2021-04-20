from flask import render_template, url_for, request
from flask_login import current_user, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from app import app
from app.forms import LoginForm, UserRegisterForm
from app.models.user import User
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
