from flask import url_for, send_from_directory
from flask_login import current_user

from app import app
from app.models.program import Program
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
