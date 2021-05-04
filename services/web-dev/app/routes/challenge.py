from flask import url_for, send_from_directory, jsonify, render_template
from flask_login import current_user

from app import app
from app.models.program import Program
from app.models.whiteboxbreak import WhiteboxBreak
from app.utils import redirect


@app.route('/candidate/<int:identifier>/source.c', methods=['GET'])
def down_candidate(identifier):
    program = Program.get_by_id(identifier)
    if program is None:
        return redirect(url_for('index'))

    do_show = False
    if program.is_published:
        do_show = True
    if current_user is not None and \
       current_user.is_authenticated and \
       current_user == program.user:
        do_show = True
    if not do_show:
        return redirect(url_for('index'))

    # If we reach this point, we can show the source code
    upload_folder = app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, program.filename)


@app.route('/candidate/<int:identifier>/pubkey', methods=['GET'])
def get_candidate_pubkey(identifier):
    program = Program.get_by_id(identifier)
    if program is None:
        return redirect(url_for('index'))

    do_show = False
    if program.is_published:
        do_show = True
    if current_user is not None and \
       current_user.is_authenticated and \
       current_user == program.user:
        do_show = True
    if not do_show:
        return redirect(url_for('index'))

    if not program.pubkey:
        return "Public key was erased for some reason, contact administrator."
    else:
        return program.pubkey


@app.route('/candidate/<int:identifier>/proof-of-knowledge', methods=['GET'])
def get_candidate_proof_of_knowledge(identifier):
    program = Program.get_by_id(identifier)
    if program is None:
        return redirect(url_for('index'))

    do_show = False
    if program.is_published:
        do_show = True
    if current_user is not None and \
       current_user.is_authenticated and \
       current_user == program.user:
        do_show = True
    if not do_show:
        return redirect(url_for('index'))

    return program.proof_of_knowledge


@app.route('/candidate/<int:identifier>', methods=['GET'])
def show_candidate_sample(identifier):
    program = Program.get_by_id(identifier)
    if program is None or not program.is_published:
        return redirect(url_for('index'))

    number_of_test_vectors = int(len(program.hashes) / 32)
    test_vectors = list()
    for i in range(number_of_test_vectors):
        test_vectors.append({
            "hash": program.hashes[i*32:(i+1)*32].hex().upper(),
            "signature": program.signatures[i*64:(i+1)*64].hex().upper()
        })

    res = {
        "id": program._id,
        "public_key": program.pubkey,
        "proof_of_knowledge": program.proof_of_knowledge,
        "test_vectors": test_vectors
    }
    return jsonify(res)


@app.route('/candidate/<int:identifier>.html', methods=['GET'])
def candidate(identifier):
    program = Program.get_by_id(identifier)
    if program is None or not program.is_published:
        return redirect(url_for('index'))

    programs_broken_by_current_user = None
    if current_user and current_user.is_authenticated:
        wb_breaks_by_current_user = WhiteboxBreak.get_all_by_user(current_user)
        programs_broken_by_current_user = [
            wb_break.program for wb_break in wb_breaks_by_current_user]
    # If we reach this point, we can show the source code
    return render_template(
        'candidate.html',
        program=program,
        programs_broken_by_current_user=programs_broken_by_current_user,
    )
