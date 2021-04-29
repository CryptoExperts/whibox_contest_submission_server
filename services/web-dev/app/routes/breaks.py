import time
from flask import url_for, render_template, request
from flask_login import current_user, login_required

from app import app
from app.forms import WhiteboxBreakForm
from app.models.program import Program
from app.models.whiteboxbreak import WhiteboxBreak
from app.utils import redirect, format_timestamp, crx_flash


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
    print(program, flush=True)
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

    if program.plaintexts is None or program.ciphertexts is None:
        return redirect(url_for('index'))
    number_of_test_vectors = 10
    plaintexts = program.plaintexts
    ciphertexts = program.ciphertexts
    if len(plaintexts) != len(ciphertexts) or len(plaintexts) % 16 != 0 or \
       len(plaintexts) == 0:
        return redirect(url_for('index'))

    key = bytes.fromhex(form.key.data)
    try:
        aes = AES.new(key, AES.MODE_ECB)
    except:
        return redirect(url_for('index'))
    for i in range(number_of_test_vectors):
        pt = plaintexts[16*i:16*(i+1)]
        ct = ciphertexts[16*i:16*(i+1)]
        try:
            computed_ct = aes.encrypt(pt)
        except:
            computed_ct = None
        if computed_ct is None or ct != computed_ct:
            pt_as_text = binascii.hexlify(pt).decode()
            ct_as_text = binascii.hexlify(ct).decode()
            return render_template('challenge_break_ko.html',
                                   identifier=identifier,
                                   current_user=current_user,
                                   plaintext=pt_as_text,
                                   ciphertext=ct_as_text)

    # If we reach this point, the submitted key is correct
    program.set_status_to_broken(current_user, now)
    db.session.commit()

    return redirect(url_for('break_candidate_ok', identifier=identifier))


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
    return render_template('challenge_break_ok.html', wb_break=wb_break, current_user=current_user)
