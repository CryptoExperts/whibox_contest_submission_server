import sys
import time
import flask
from urllib.parse import urlparse, urljoin
from flask import flash
from app.text_contents import flash_texts_and_categories


def console(s):
    print(str(s), file=sys.stderr)
    sys.stderr.flush()


def is_safe_url(request, target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


def format_timestamp(timestamp, textual=False, aoe=False, js=False):
    if timestamp is None:
        return None
    # Convert to AoE time
    if aoe is True:
        # AoE time is 12 hours behind UTC, so retrieve them
        timestamp = (timestamp - (12 * 60 * 60))
        suffix = 'AoE'
    else:
        suffix = 'UTC'
    if textual is True:
        return time.strftime('%B %d, %Y @ %H:%M '+suffix, time.gmtime(timestamp))
    else:
        if js is True:
            # Javascript format
            return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(timestamp))
        else:
            return time.strftime('%Y-%m-%d %H:%M '+suffix, time.gmtime(timestamp))


def crx_flash(text_and_category_key, *args):
    text = flash_texts_and_categories[text_and_category_key][0]
    category = flash_texts_and_categories[text_and_category_key][1]
    flash(text % (args), category)


class Response(flask.Response):
    def get_wsgi_headers(self, environ):
        return self.headers


def redirect(url):
    return flask.redirect(url, Response=Response)
