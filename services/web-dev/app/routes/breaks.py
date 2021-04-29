import time
from flask import url_for, render_template, request
from flask_login import current_user, login_required

from app import app, db
from app.forms import WhiteboxBreakForm
from app.models.program import Program
from app.models.whiteboxbreak import WhiteboxBreak
from app.utils import redirect, format_timestamp, crx_flash

from commands import validate_private_key


@app.route('/break/candidate/<int:identifier>', methods=['GET', 'POST'])
@login_required
def break_candidate(identifier):
    now = int(time.time())
    if now < app.config['STARTING_DATE']:
        crx_flash('BEFORE_STARTING_DATE')
        return redirect(url_for('index'))
    if now > app.config['FINAL_DEADLINE']:
        crx_flash('EXCEED_DEADLINE')
        return render_template(
            'break_candidate_deadline_exceeded.html',
            final_deadline=format_timestamp(app.config['FINAL_DEADLINE']))

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
                               strawberries=program.strawberries_last,
                               identifier=identifier,
                               testing=app.testing)

    submitted_prikey = form.prikey.data

    if program.pubkey is None:
        return redirect(url_for('index'))

    if validate_private_key(submitted_prikey, program.pubkey):
        app.logger.info(f"Implementation is broken at {now}")
        program.set_status_to_broken(current_user, now)
        db.session.commit()

        return redirect(url_for('break_candidate_ok', identifier=identifier))
    else:
        app.logger.info("Invalid private key")
        return render_template('challenge_break_ko.html',
                               identifier=identifier,
                               current_user=current_user,
                               submitted_prikey=submitted_prikey,
                               pubkey=program.pubkey)


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
    return render_template('challenge_break_ok.html', wb_break=wb_break,
                           current_user=current_user)
