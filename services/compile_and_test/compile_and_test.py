#!/usr/bin/env python3

import binascii
import json
import os
import subprocess
import sys
import urllib.request
from urllib.parse import urljoin

CODE_SUCCESS = 0
ERR_CODE_COMPILATION_FAILED = 1
ERR_CODE_BIN_TOO_LARGE = 2
ERR_CODE_LINK_FAILED = 3
ERR_CODE_EXECUTION_FAILED = 4
ERR_CODE_EXCEED_RAM_LIMAT = 5
ERR_CODE_EXCEED_EXECUTION_TIME_LIMAT = 6


def exit_after_notifying_launcher(code, post_data=None):
    sys.stdout.flush()
    url_to_ping_back = os.environ['URL_TO_PING_BACK']
    url = urljoin(url_to_ping_back, './%d' % code)
    print("Contacting %s" % url)
    sys.stdout.flush()
    try:
        req = urllib.request.Request(
            url,
            data=post_data,
            headers={'content-type': 'application/json'}
        )
        urllib.request.urlopen(req)
    except Exception as e:
        print(e)
        print("!!! Could not contact %s" % url)
        sys.exit(1)
    sys.stdout.flush()
    sys.exit(0)


def try_fetch_plaintexts():
    try:
        url = os.environ['URL_FOR_FETCHING_PLAINTEXTS']
        print("Contacting %s" % url)
        sys.stdout.flush()
        return urllib.request.urlopen(url).read()
    except:
        print("Could not fetch plaintexts")
        sys.stdout.flush()
        sys.exit(1)


def compile(basename, compiler, source, obj):
    try:
        max_ram = 5000 + 2**10 * \
            int(os.environ['CHALLENGE_MAX_MEM_COMPILATION_IN_MB'])  # in kiB
        max_cpu_time = 10 + \
            int(os.environ['CHALLENGE_MAX_TIME_COMPILATION_IN_SECS'])
        cmd_ulimit_ram = 'ulimit -v %d' % (max_ram)
        cmd_ulimit_cpu_time = 'ulimit -t %d' % (max_cpu_time)
        # TODO: check tcc and gcc
        cmd_gcc = 'gcc -nostdinc -c %s -o %s' % (source, obj)
        cmd_tcc = 'tcc -c %s -o %s' % (source, obj)
        cmd_compiler = cmd_tcc if compiler == 'tcc' else cmd_gcc
        subprocess.run(
            '%s; %s; %s' % (cmd_ulimit_ram, cmd_ulimit_cpu_time, cmd_compiler),
            check=True, shell=True)
    except:
        print("The compilation of file %s.c failed." % basename)
        print("The compile command is:\t%s\t" % cmd_compiler)
        sys.stdout.flush()
        exit_after_notifying_launcher(ERR_CODE_COMPILATION_FAILED)
    print("The compilation of the file with basename %s succeeded." % basename)
    sys.stdout.flush()


def link(basename, compiler, obj, executable):
    try:
        # TODO: to update main object location
        subprocess.run(
            [compiler, '/main.o', obj, '-o', executable],
            check=True)
    except:
        print("The link of the file with basename %s failed." % basename)
        sys.stdout.flush()
        exit_after_notifying_launcher(ERR_CODE_LINK_FAILED)
    print("The link of the file with basename %s succeeded." % basename)
    sys.stdout.flush()
    pass


def performance_measure(executable,
                        plaintexts,
                        number_of_tests,
                        ram_limit,
                        cpu_time_limit):
    current_test_index = 0
    ciphertexts = b''
    max_cpu_time = 0
    max_ram = 0
    cmd = '/execute.py %s %s'
    while current_test_index < number_of_tests:
        current_plaintext = plaintexts[
            current_test_index * 16:(current_test_index+1)*16
        ]
        current_pt_as_text = binascii.hexlify(current_plaintext).decode()
        try:
            ps = subprocess.run(cmd % (executable, current_pt_as_text),
                                check=True,
                                stdout=subprocess.PIPE, shell=True)
            ct_as_text, cpu_time, ram = json.loads(ps.stdout)
            ciphertexts += bytes.fromhex(ct_as_text)

            # check whether we reach the limitation
            if cpu_time > cpu_time_limit:
                print("Reach memory limit")
                sys.stdout.flush()
                exit_after_notifying_launcher(ERR_CODE_EXCEED_RAM_LIMAT)
            if ram > ram_limit:
                print("Reach execution time limit")
                sys.stdout.flush()
                exit_after_notifying_launcher(
                    ERR_CODE_EXCEED_EXECUTION_TIME_LIMAT)

            if cpu_time > max_cpu_time:
                max_cpu_time = cpu_time
            if ram > max_ram:
                max_ram = ram
            current_test_index += 1
        except:
            print("Execution failed")
            sys.stdout.flush()
            exit_after_notifying_launcher(ERR_CODE_EXECUTION_FAILED)

    if len(ciphertexts) != len(plaintexts):
        raise
    print("The execution succeeded and we retrieved the ciphertexts.")
    sys.stdout.flush()
    return (ciphertexts, max_cpu_time, max_ram)


def main():
    # Compile
    upload_folder = os.environ['UPLOAD_FOLDER']
    basename = os.environ['FILE_BASENAME']
    compiler = os.environ['COMPILER']
    source_file = basename + '.c'
    object_file = basename + '.o'
    path_to_source = os.path.join(upload_folder, source_file)
    path_to_object = os.path.join('/tmp', object_file)
    compile(basename, compiler, path_to_source, path_to_object)

    # Check the binary size
    max_bin_size = 2**20 * int(os.environ['CHALLENGE_MAX_BINARY_SIZE_IN_MB'])
    bin_size = os.path.getsize(path_to_object)
    if bin_size > max_bin_size:
        exit_after_notifying_launcher(ERR_CODE_BIN_TOO_LARGE)

    # Link
    path_to_executable = '/tmp/main'
    link(basename, compiler, path_to_object, path_to_executable)

    # Fetch the plaintexts to encrypt
    plaintexts = try_fetch_plaintexts()

    # performance measure
    number_of_tests = int(os.environ['CHALLENGE_NUMBER_OF_TEST_VECTORS'])
    cpu_time_limit = int(os.environ['CHALLENGE_MAX_TIME_EXECUTION_IN_SECS'])
    ram_limit = 2**20 * int(os.environ['CHALLENGE_MAX_MEM_EXECUTION_IN_MB'])
    ciphertexts, max_cpu_time, max_ram = performance_measure(
        path_to_executable, plaintexts, number_of_tests,
        ram_limit, cpu_time_limit
    )
    size_factor = os.path.getsize(path_to_object) / max_bin_size
    ram_factor = max_ram * 1.0 / ram_limit
    time_factor = max_cpu_time * 1.0 / cpu_time_limit

    # If we reach this line, everything went fine
    post_data = {
        "ciphertexts": binascii.hexlify(ciphertexts).decode(),
        "size_factor": size_factor,
        "ram_factor": ram_factor,
        "time_factor": time_factor
    }
    post_data = json.dumps(post_data).encode('utf8')
    print(post_data)
    exit_after_notifying_launcher(CODE_SUCCESS, post_data=post_data)


if __name__ == "__main__":
    main()
