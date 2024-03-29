import os
import random
import string
import time

import sqlalchemy

from flask import render_template, url_for, request
from flask_login import login_required, current_user

from app import app
from app import db
from app.forms import WhiteboxSubmissionForm
from app.models.program import Program
from app.utils import crx_flash, format_timestamp, redirect


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
        crx_flash("CHALLENGE_INVALID")
        return render_template('submit_candidate.html', form=form,
                               active_page='submit_candidate',
                               testing=app.testing), 400
    else:
        upload_folder = app.config['UPLOAD_FOLDER']
        basename = ''.join(random.SystemRandom().choice(
            string.ascii_lowercase + string.digits) for _ in range(32))
        filename = basename + '.c'
        pubkey = form.pubkey.data
        proof_of_knowledge = form.proof_of_knowledge.data
        form_data = form.program.data
        form_data.save(os.path.join(upload_folder, filename))
        Program.create(basename=basename,
                       pubkey=pubkey,
                       proof_of_knowledge=proof_of_knowledge,
                       user=current_user)
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            db.session.rollback()
            crx_flash("DUPLICATE_KEY")
            app.logger.error(e)
            new_form = WhiteboxSubmissionForm()
            return render_template('submit_candidate.html',
                                   form=new_form,
                                   active_page='submit_candidate',
                                   testing=app.testing), 400
        else:
            return redirect(url_for('submit_candidate_ok'))


@app.route('/submit/candidate/ok', methods=['GET'])
@login_required
def submit_candidate_ok():
    """ This route is called directly when the user has js activated (see file-progress.js)"""
    crx_flash('CHALLENGE_SUBMITTED')
    return redirect(url_for('user_show'))
