import sys
import time
import urllib.request
import threading
import flask
from urllib.parse import urlparse, urljoin
from flask import flash
from app import app
from app.text_contents import flash_texts_and_categories


def console(s):
    print(str(s), file=sys.stderr)
    sys.stderr.flush()


def is_safe_url(request, target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


def format_timestamp(timestamp):
    if timestamp is None:
        return None
    return time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(timestamp))


def crx_flash(text_and_category_key, *args):
    text = flash_texts_and_categories[text_and_category_key][0]
    category = flash_texts_and_categories[text_and_category_key][1]
    flash(text % (args), category)


class Response(flask.Response):
    def get_wsgi_headers(self, environ):
        return self.headers


def redirect(url):
    return flask.redirect(url, Response=Response)
