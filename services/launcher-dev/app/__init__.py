import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .converters import BasenameConverter

app = Flask(__name__)
app.config.from_object('app.config')
app.url_map.converters['basename'] = BasenameConverter

db = SQLAlchemy(app)

login_manager = LoginManager()

from app import routes, models
