import re
from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField
from wtforms.fields.html5 import EmailField
from wtforms.validators import (
    DataRequired, EqualTo, ValidationError, Length, Email
)
from .text_contents import flash_texts_and_categories


class LoginForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    recaptcha = RecaptchaField()


class UserRegisterForm(FlaskForm):
    username = StringField('username',
                           validators=[DataRequired(), Length(min=3, max=32)])
    nickname = StringField('nickname', validators=[Length(max=20)])
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
    pubkey = StringField('pubkey', validators=[DataRequired()])
    proof_of_knowledge = StringField(
        'proof_of_knowledge', validators=[DataRequired()])
    recaptcha = RecaptchaField()

    def validate_pubkey(self, pubkey):
        if re.fullmatch('^[0-9a-fA-F]{128}$', pubkey.data) is None:
            raise ValidationError(
                flash_texts_and_categories['INVALID_PUB_KEY'][0])

    def validate_proof_of_knowledge(self, proof_of_knowledge):
        if re.fullmatch('^[0-9a-fA-F]{128}$', proof_of_knowledge.data) is None:
            raise ValidationError(
                flash_texts_and_categories['INVALID_PROOF_OF_KNOWLEDGE'][0])


class WhiteboxBreakForm(FlaskForm):
    prikey = StringField('prikey', validators=[DataRequired()])
    recaptcha = RecaptchaField()

    def validate_prikey(self, key):
        if re.fullmatch('^[0-9a-fA-F]{64}$', key.data) is None:
            raise ValidationError(
                flash_texts_and_categories['INVALID_PRI_KEY'][0])
