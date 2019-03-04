import re
from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, EqualTo, ValidationError, Length, Email, AnyOf
from .text_contents import flash_texts_and_categories


class LoginForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    recaptcha = RecaptchaField()


class UserCreationForm(FlaskForm):
    username = StringField('username', validators=[
                           DataRequired(), Length(min=3, max=32)])
    email1 = EmailField('email1', validators=[DataRequired(), Email()])
    email2 = EmailField('email2', validators=[DataRequired(), Email(), EqualTo(
        'email1', message=flash_texts_and_categories['EMAIL_MUST_MATCH'][0])])
    password1 = PasswordField('password1', validators=[DataRequired()])
    password2 = PasswordField('password2', validators=[DataRequired(), EqualTo(
        'password1', message=flash_texts_and_categories['PWD_MUST_MATCH'][0])])
    recaptcha = RecaptchaField()


class WhiteboxSubmissionForm(FlaskForm):
    program = FileField(validators=[FileRequired(), FileAllowed(
        ['c'], flash_texts_and_categories['ONLY_EXT_IS_C'][0])])
    key = StringField('key', validators=[DataRequired()])
    compiler = StringField('compiler',
                           validators=[DataRequired(), AnyOf(['gcc', 'tcc'])])
    recaptcha = RecaptchaField()

    def validate_key(self, key):
        if re.fullmatch('^[0-9a-fA-F]{32}$', key.data) is None:
            raise ValidationError(flash_texts_and_categories['INVALID_KEY'][0])


class WhiteboxBreakForm(FlaskForm):
    key = StringField('key', validators=[DataRequired()])
    recaptcha = RecaptchaField()

    def validate_key(self, key):
        if re.fullmatch('^[0-9a-fA-F]{32}$', key.data) is None:
            raise ValidationError(flash_texts_and_categories['INVALID_KEY'][0])


class WhiteboxInvertForm(FlaskForm):
    plaintext = StringField('plaintext', validators=[DataRequired()])
    ciphertext = StringField('ciphertext', validators=[DataRequired()])
    recaptcha = RecaptchaField()

    def validate_key(self, key):
        if re.fullmatch('^[0-9a-fA-F]{32}$', plaintext.data) is None:
            raise ValidationError(flash_texts_and_categories['INVALID_KEY'][0])
