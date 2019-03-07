import sys
import datetime
from Crypto.Cipher import AES
from .models.program import Program


def console(s):
    date = str(datetime.datetime.now())
    date_and_s = date + ' -- ' + str(s)
    print(str(date_and_s), file=sys.stderr)
    sys.stderr.flush()


def basename_and_nonce_are_valid(basename, nonce):
    if basename is None or nonce is None:
        console("Received a bad request (%s is not a proper basename)" % basename)
        return False
    program_compiled = Program.get(basename)
    if program_compiled is None:
        console("Could not find program with basename %s in database" % basename)
        return False
    if not program_compiled.compare_nonces(nonce):
        console("The nonce received does not match the nonce stored in database for program with basename %s" % basename)
        return False
    return True


def compute_ciphertexts(plaintexts, key, number_of_test_vectors):
    expected_ciphertexts = b''
    aes = AES.new(key, AES.MODE_ECB)
    for i in range(number_of_test_vectors):
        plaintext = plaintexts[16*i:16*(i+1)]
        expected_ciphertext = aes.encrypt(plaintext)
        expected_ciphertexts += expected_ciphertext
    return expected_ciphertexts


# Docker related routines


def get_service(client, service_name):
    services = client.services.list(filters={'name': service_name})
    if len(services) == 0:
        return None
    elif len(services) == 1:
        return services[0]
    else:
        assert False


def service_runs_already(client, service_name):
    compiler_service = get_service(client, service_name)
    if compiler_service is None:
        console("\tDEBUG compiler_service is None")
        return False
    else:
        console("\tDEBUG compiler_service is *not* None")
        tasks = compiler_service.tasks()
        console("\tDEBUG The compiler service has %d task" % len(tasks))
        # We look for a running task which id corresponds to a 'submitted' program
        for task in tasks:
            if task['Status']['State'] != 'running':
                continue
            running_task_id = task['ID']
            program_being_compiled = Program.get_program_being_compiled(
                running_task_id)
            if program_being_compiled is not None:
                return True
    # If reach this point, there is no program being compiled (but there is a compiler_service to remove)
    compiler_service.remove()
    return False


def remove_compiler_service_for_basename(client, basename, app):
    compiler_service = get_service(
        client, app.config['NAME_OF_COMPILE_AND_TEST_SERVICE'])
    if compiler_service is None:
        return
    if 'Labels' not in compiler_service.attrs['Spec'] or \
       'basename' not in compiler_service.attrs['Spec']['Labels']:
        return
    if compiler_service.attrs['Spec']['Labels']['basename'] != basename:
        return
    compiler_service.remove()
    console("We just removed a compiler service for basename %s" % basename)
