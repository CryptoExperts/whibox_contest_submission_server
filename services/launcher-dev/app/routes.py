import sys
import docker
import html
import shutil
import os
import inspect
import time
import binascii
from app import app
from app import db
from app import utils
from flask import request
from .models.program import Program
from .models.user import User

CODE_SUCCESS = 0
ERR_CODE_COMPILATION_FAILED = 1
ERR_CODE_BIN_TOO_LARGE = 2
ERR_CODE_LINK_FAILED = 3
ERR_CODE_EXECUTION_FAILED = 4


@app.route('/compile_and_test', methods=['GET', 'POST'])
def compile_and_test():

    Program.clean_programs_which_failed_to_compile_or_test()
    db.session.commit()

    client = docker.from_env()
    api_client = docker.APIClient(app.config['SOCK'])

    if utils.service_runs_already(client, app.config['NAME_OF_COMPILE_AND_TEST_SERVICE']):
        utils.console('A program is currently being compiled or tested. Exiting.')
        return ""

    utils.console('Looking for a program to compile and test.')
    program_to_compile_and_test = Program.get_next_program_to_compile()
    if program_to_compile_and_test is None:
        utils.console('There is no program to compile and test. Exiting')
        return ""
    basename = os.path.splitext(program_to_compile_and_test.filename)[0]
    key_string = program_to_compile_and_test.key
    # Make sure the key can be converted in a 16-byte string
    try:
        key_bytes = bytes.fromhex(key_string)
        if len(key_bytes) != 16:
            raise
    except:
        utils.console("The key is invalid")
        return ""

    utils.console('Preparing to compile and test a program (basename=%s)'%basename)

    nonce = program_to_compile_and_test.generate_nonce()
    db.session.commit()

    # TODO: add more constraints on the service, use https instead of http, do not hardcode the urls
    restart_policy = docker.types.RestartPolicy(condition='on-failure', max_attempts=1)
    mem_limit = 2**20 * max(app.config['CHALLENGE_MAX_MEM_COMPILATION_IN_MB'], app.config['CHALLENGE_MAX_MEM_EXECUTION_IN_MB']) # in Bytes
    resources = docker.types.Resources(mem_limit=mem_limit)
    networks = [app.config['COMPILE_AND_TEST_SERVICE_NETWORK']]
    env = ['UPLOAD_FOLDER=/uploads',
           'FILE_BASENAME=%s'%basename,
           'URL_TO_PING_BACK=%s'%'http://launcher:5000/compile_and_test_result/%s/%s/'%(basename, nonce),
           'URL_FOR_FETCHING_PLAINTEXTS=%s'%'http://launcher:5000/get_plaintexts/%s/%s'%(basename, nonce),
           'CHALLENGE_MAX_MEM_COMPILATION_IN_MB=%d'%app.config['CHALLENGE_MAX_MEM_COMPILATION_IN_MB'],
           'CHALLENGE_MAX_TIME_COMPILATION_IN_SECS=%d'%app.config['CHALLENGE_MAX_TIME_COMPILATION_IN_SECS'],
           'CHALLENGE_MAX_BINARY_SIZE_IN_MB=%d'%app.config['CHALLENGE_MAX_BINARY_SIZE_IN_MB'],
           'CHALLENGE_MAX_MEM_EXECUTION_IN_MB=%d'%app.config['CHALLENGE_MAX_MEM_EXECUTION_IN_MB'],
           'CHALLENGE_MAX_TIME_EXECUTION_IN_SECS=%d'%app.config['CHALLENGE_MAX_TIME_EXECUTION_IN_SECS'],
           'CHALLENGE_NUMBER_OF_TEST_VECTORS=%d'%app.config['CHALLENGE_NUMBER_OF_TEST_VECTORS'],
    ]
    mounts = ['/whitebox_program_uploads:/uploads:ro']
    service = client.services.create(image='crx/compile_and_test',
                                     mounts=mounts,
                                     env=env,
                                     constraints=['node.labels.vm == node-sandbox'],
                                     name=app.config['NAME_OF_COMPILE_AND_TEST_SERVICE'],
                                     restart_policy=restart_policy,
                                     labels={'basename': str(basename)},
                                     networks=networks,
                                     resources=resources)

    while len(service.tasks()) == 0:
        time.sleep(0.1)
    task = service.tasks()[0]
    task_id = task['ID']
    program_to_compile_and_test.task_id = task_id
    db.session.commit()

    utils.console(program_to_compile_and_test)

    return "youpi"


@app.route('/get_plaintexts/<basename:basename>/<basename:nonce>', methods=['GET'])
def get_plaintexts(basename, nonce):
    if not utils.basename_and_nonce_are_valid(basename, nonce):
        return ""

    path_to_plaintexts_file = os.path.join('/tmp', basename + '.plaintext.bin')

    # If it doesn't already exist, create the file containting the plaintexts
    if not os.path.exists(path_to_plaintexts_file):
        with open(path_to_plaintexts_file, 'wb') as f:
            f.write(os.urandom(16 * app.config['CHALLENGE_NUMBER_OF_TEST_VECTORS']))

    plaintexts = b''
    with open(path_to_plaintexts_file, 'rb') as f:
        plaintexts = f.read()

    return plaintexts



@app.route('/compile_and_test_result/<basename:basename>/<basename:nonce>/<int:ret>', methods=['GET', 'POST'])
def compile_and_test_result(basename, nonce, ret):
    utils.console("Entering compile_and_test_result(basename=%s, nonce=%s, ret=%d)"%(basename, nonce, ret))
    if not utils.basename_and_nonce_are_valid(basename, nonce) or ret is None:
        return ""
    program = Program.get(basename)
    if ret == ERR_CODE_COMPILATION_FAILED:
        program.set_status_to_compilation_failed('Compilation failed for unknown reason (may be due to an excessive memory usage).')
        utils.console('Compilation failed for file with basename %s'%str(basename))
    elif ret == ERR_CODE_BIN_TOO_LARGE:
        program.set_status_to_compilation_failed('Compiled binary file size exceeds the limit of %dMB.'%app.config['CHALLENGE_MAX_BINARY_SIZE_IN_MB'])
        utils.console('Compilation failed for file with basename %s'%str(basename))
    elif ret == ERR_CODE_LINK_FAILED:
        program.set_status_to_link_failed()
        utils.console('Link failed for file with basename %s'%str(basename))
    elif ret == ERR_CODE_EXECUTION_FAILED:
        program.set_status_to_execution_failed()
        utils.console('Code execution failed for file with basename %s'%str(basename))
    else:
        utils.console('We received an unexpected return code for file with basename %s'%str(basename))
    db.session.commit()
    client = docker.from_env()
    utils.remove_compiler_service_for_basename(client, basename, app)
    if ret != CODE_SUCCESS:
        return ""

    # If we reach this point, the program was successfuly compiled, we can test the ciphertexts

    ciphertexts = request.get_data()
    number_of_test_vectors = app.config['CHALLENGE_NUMBER_OF_TEST_VECTORS']
    if len(ciphertexts) != 16 * number_of_test_vectors:
        utils.console("The length of the ciphertexts is %d, we were expecting %d."%(len(ciphertexts), 16 * number_of_test_vectors))
        error_message = "The stream of ciphertexts does not have the appropriate length."
        utils.console(error_message)
        program.error_message = error_message
        program.set_status_to_test_failed()
        db.session.commit()
        return ""

    # If we reach this point, the ciphertexts stream has the appropriate length

    utils.console("We received the appropriate number of ciphertexts.")
    utils.console("Testing the plaintexts against the ciphertexts using the announced key...")

    # Retrieve the plaintexts from the saved file
    path_to_plaintexts_file = os.path.join('/tmp', basename + '.plaintext.bin')
    plaintexts = b''
    with open(path_to_plaintexts_file, 'rb') as f:
        plaintexts = f.read()

    # Check the ciphertexts against the plaintext and key.
    key = bytes.fromhex(program.key) # TODO the db should always return the key as 16 bytes
    try:
        expected_ciphertexts = utils.compute_ciphertexts(plaintexts, key, number_of_test_vectors)
        if len(expected_ciphertexts) != 16 * number_of_test_vectors:
            raise
    except:
        error_message = "Could not compute the test vectors for the given key."
        program.set_status_to_test_failed(error_message)
        db.session.commit()
        return ""
    for i in range(number_of_test_vectors):
        ciphertext = ciphertexts[16*i:16*(i+1)]
        expected_ciphertext = expected_ciphertexts[16*i:16*(i+1)]
        if ciphertext != expected_ciphertext:
            plaintext = plaintexts[16*i:16*(i+1)]
            utils.console("One of the ciphertext failed the test (plaintext=%s, key=%s, ciphertext=%s)."%(plaintext, key, ciphertext))
            error_message = '''One of the tests failed:
- plaintext   %s
- key         %s
- ciphertext  %s
- expected    %s'''%(binascii.hexlify(plaintext).decode(),
                     binascii.hexlify(key).decode(),
                     binascii.hexlify(ciphertext).decode(),
                     binascii.hexlify(expected_ciphertext).decode())
            program.set_status_to_test_failed(error_message)
            db.session.commit()
            return ""

    # If we reach this point, all the tests were successful. We save 10 test vectors in the database so that we can test
    # key candidates in the future.

    plaintexts = plaintexts[0:10*16]
    ciphertexts = ciphertexts[0:10*16]
    program.plaintexts = plaintexts
    program.ciphertexts = ciphertexts
    program.set_status_to_unbroken()
    db.session.commit()
    utils.console("The program is unbroken!")

    # Cleanup
    try:
        os.remove(path_to_plaintexts_file)
        utils.console("We removed the file %s"%path_to_plaintexts_file)
    except:
        utils.console("Could NOT remove the file %s"%path_to_plaintexts_file)

    # Look for another program to compile and test
    compile_and_test()

    return ""
