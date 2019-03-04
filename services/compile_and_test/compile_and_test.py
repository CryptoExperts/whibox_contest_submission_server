#!/usr/bin/env python3

import sys
import urllib.request
import os
import subprocess
from urllib.parse import urljoin

CODE_SUCCESS = 0
ERR_CODE_COMPILATION_FAILED = 1
ERR_CODE_BIN_TOO_LARGE = 2
ERR_CODE_LINK_FAILED = 3
ERR_CODE_EXECUTION_FAILED = 4


def exit_after_notifying_launcher(code, post_data=None):
    sys.stdout.flush()
    url_to_ping_back = os.environ['URL_TO_PING_BACK']
    url = urljoin(url_to_ping_back, './%d' % code)
    print("Contacting %s" % url)
    sys.stdout.flush()
    try:
        urllib.request.urlopen(url, data=post_data)
    except:
        print("!!! Could not contact %s" % url)
    sys.stdout.flush()
    sys.exit(0)


def try_fetch_plaintexts():
    url = os.environ['URL_FOR_FETCHING_PLAINTEXTS']
    print("Contacting %s" % url)
    sys.stdout.flush()
    return urllib.request.urlopen(url).read()


def main():

    #########
    # Compile
    #########

    upload_folder = os.environ['UPLOAD_FOLDER']
    basename = os.environ['FILE_BASENAME']
    compiler = os.environ['COMPILER']
    source_file = basename + '.c'
    object_file = basename + '.o'
    path_to_source = os.path.join(upload_folder, source_file)
    path_to_o = os.path.join('/tmp', object_file)
    try:
        max_ram = 5000 + 2**10 * \
            int(os.environ['CHALLENGE_MAX_MEM_COMPILATION_IN_MB'])  # in kiB
        max_cpu_time = 10 + \
            int(os.environ['CHALLENGE_MAX_TIME_COMPILATION_IN_SECS']
                )  # in seconds
        cmd_ulimit_ram = 'ulimit -v %d' % (max_ram)
        cmd_ulimit_cpu_time = 'ulimit -t %d' % (max_cpu_time)
        # TODO: check tcc and gcc
        cmd_gcc = 'gcc -nostdinc -c %s -o %s' % (path_to_source, path_to_o)
        cmd_tcc = 'tcc -c %s -o %s' % (path_to_source, path_to_o)
        cmd_compiler = cmd_tcc if compiler == 'tcc' else cmd_gcc
        subprocess.run(
            '%s; %s; %s' % (cmd_ulimit_ram, cmd_ulimit_cpu_time, cmd_compiler),
            check=True,
            shell=True)
    except:
        print("The compilation of the file with basename %s failed." % basename)
        print("The compile command is:\t%s\t" % cmd_compiler)
        sys.stdout.flush()
        exit_after_notifying_launcher(ERR_CODE_COMPILATION_FAILED)
    print("The compilation of the file with basename %s succeeded." % basename)
    sys.stdout.flush()

    #######################
    # Check the binary size
    #######################

    max_bin_size = 2**20 * int(os.environ['CHALLENGE_MAX_BINARY_SIZE_IN_MB'])
    if os.path.getsize(path_to_o) > max_bin_size:
        exit_after_notifying_launcher(ERR_CODE_BIN_TOO_LARGE)

    ######
    # Link
    ######

    path_to_executable = '/tmp/main'
    try:
        subprocess.run(
            [compiler, '/main.o', path_to_o, '-o', path_to_executable],
            check=True)
    except:
        print("The link of the file with basename %s failed." % basename)
        sys.stdout.flush()
        exit_after_notifying_launcher(ERR_CODE_LINK_FAILED)
    print("The link of the file with basename %s succeeded." % basename)
    sys.stdout.flush()

    #################################
    # Fetch the plaintexts to encrypt
    #################################

    try:
        plaintexts = try_fetch_plaintexts()
    except:
        print("Could not fetch plaintexts")
        sys.stdout.flush()
        sys.exit(1)

    #########
    # Execute
    #########

    ciphertexts = b''
    max_ram = 5000 + 2**10 * \
        int(os.environ['CHALLENGE_MAX_MEM_EXECUTION_IN_MB'])  # in kiB
    max_cpu_time = 10 + int(os.environ['CHALLENGE_NUMBER_OF_TEST_VECTORS']) * int(
        os.environ['CHALLENGE_MAX_TIME_EXECUTION_IN_SECS'])  # in seconds
    cmd_ulimit_ram = 'ulimit -v %d' % (max_ram)
    cmd_ulimit_cpu_time = 'ulimit -t %d' % (max_cpu_time)
    cmd_execution = '%s' % (path_to_executable)
    try:
        ps = subprocess.run('%s; %s; %s' % (cmd_ulimit_ram, cmd_ulimit_cpu_time, cmd_execution),
                            check=True,
                            input=plaintexts,
                            stdout=subprocess.PIPE,
                            shell=True)
        ciphertexts = bytes(ps.stdout)
        if len(ciphertexts) != len(plaintexts):
            raise
    except:
        print("Execution failed")
        sys.stdout.flush()
        exit_after_notifying_launcher(ERR_CODE_EXECUTION_FAILED)
    print("The execution succeeded and we retrieved the ciphertexts.")
    sys.stdout.flush()

    #############################################
    # If we reach this line, everything went fine
    #############################################

    post_data = ciphertexts
    exit_after_notifying_launcher(CODE_SUCCESS, post_data=post_data)


if __name__ == "__main__":
    main()
