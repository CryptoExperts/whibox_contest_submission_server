import os
import random
import string
import time

from flask import render_template, url_for, request
from flask_login import login_required, current_user

from app import app
from app import db
from app.forms import WhiteboxSubmissionForm
from app.models.program import Program
from app.utils import format_timestamp, redirect


@app.route('/submit/candidate', methods=['GET', 'POST'])
@login_required
def submit_candidate():
    now = int(time.time())
    if now < app.config['STARTING_DATE']:
        return render_template(
            'submit_candidate_before_starting_date.html',
            active_page='submit_candidate',
            starting_date=format_timestamp(app.config['STARTING_DATE']))

    if now > app.config['POSTING_DEADLINE']:
        return render_template(
            'submit_candidate_deadline_exceeded.html',
            active_page='submit_candidate',
            posting_deadline=format_timestamp(app.config['POSTING_DEADLINE']))

    form = WhiteboxSubmissionForm()
    if request.method != 'POST':
        return render_template('submit_candidate.html', form=form,
                               active_page='submit_candidate',
                               testing=app.testing)
    elif not form.validate_on_submit():
        return render_template('submit_candidate.html', form=form,
                               active_page='submit_candidate',
                               testing=app.testing), 400
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
