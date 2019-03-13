#!/usr/bin/env python3

import binascii
import json
import mmap
import os
import re
import subprocess
import sys
import traceback
import urllib.request
from urllib.parse import urljoin
from statistics import mean

CODE_SUCCESS = 0
ERR_CODE_CONTAININT_FORBIDDEN_STRING = 1
ERR_CODE_COMPILATION_FAILED = 2
ERR_CODE_BIN_TOO_LARGE = 3
ERR_CODE_LINK_FAILED = 4
ERR_CODE_EXECUTION_FAILED = 5
ERR_CODE_EXECUTION_EXCEED_RAM_LIMIT = 6
ERR_CODE_EXECUTION_EXCEED_TIME_LIMIT = 7

forbidden_strings = [b'#include', b'extern', b'__FILE__', b'__DATE__',
                     b'__TIME__', b'__STDC__', b'__asm__']
forbidden_pattern = [re.compile(p) for p in [b'\sasm\W', ]]


def exit_after_notifying_launcher(code, post_data=None):
    url_to_ping_back = os.environ['URL_TO_PING_BACK']
    url = urljoin(url_to_ping_back, './%d' % code)
    print("Contacting %s" % url, flush=True)

    # post data
    try:
        if post_data:
            post_data = json.dumps(post_data).encode('utf8')
            print(post_data, flush=True)
        req = urllib.request.Request(
            url,
            data=post_data,
            headers={'content-type': 'application/json'}
        )
        urllib.request.urlopen(req)

        if code == ERR_CODE_EXECUTION_FAILED:
            os._exit(1)
        else:
            os._exit(0)
    except Exception as e:
        print(e)
        print("!!! Could not contact %s" % url, flush=True)
        os._exit(1)


def try_fetch_plaintexts():
    try:
        url = os.environ['URL_FOR_FETCHING_PLAINTEXTS']
        print("Contacting %s" % url, flush=True)
        sys.stdout.flush()
        return urllib.request.urlopen(url).read()
    except:
        print("Could not fetch plaintexts", flush=Truep)
        os._exit(1)


def preprocess(source):
    with open(source, 'rb', 0) as f, \
            mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as contents:
        for string in forbidden_strings:
            if contents.find(string) != -1:
                error_message = "Forbidden string '%s' is found." % string.decode()
                print(error_message, flush=True)
                post_data = {"error_message": error_message}
                exit_after_notifying_launcher(
                    ERR_CODE_CONTAININT_FORBIDDEN_STRING, post_data
                )

        for pattern in forbidden_pattern:
            match = re.search(pattern, contents)
            if match is not None:
                error_message = "The string '%s' in the source code matches forbidden pattern '%s'." % (
                    match.group(0).decode(), pattern.pattern.decode())
                print(error_message, flush=True)
                post_data = {"error_message": error_message}
                exit_after_notifying_launcher(
                    ERR_CODE_CONTAININT_FORBIDDEN_STRING, post_data)


def compile(basename, compiler, source, obj):
    try:
        # max ram in KB
        max_ram = int(os.environ['CHALLENGE_MAX_MEM_COMPILATION_IN_MB']) \
            * (2**10) + 5000
        max_cpu_time = int(
            os.environ['CHALLENGE_MAX_TIME_COMPILATION_IN_SECS']) + 10
        cmd_ulimit_ram = 'ulimit -v %d' % (max_ram)
        cmd_ulimit_cpu_time = 'ulimit -t %d' % (max_cpu_time)

        # TODO: check tcc and gcc
        cmd_gcc = 'gcc -nostdinc -c %s -o %s' % (source, obj)
        cmd_tcc = 'tcc -c %s -o %s' % (source, obj)
        cmd_compiler = cmd_tcc if compiler == 'tcc' else cmd_gcc
        subprocess.run(
            '%s; %s; %s' % (cmd_ulimit_ram, cmd_ulimit_cpu_time, cmd_compiler),
            check=True, shell=True
        )
    except Exception as e:
        print("The compilation of file %s.c failed." % basename)
        print("The compile command is:\t%s\t" % cmd_compiler, flush=True)
        traceback.print_exc()
        exit_after_notifying_launcher(ERR_CODE_COMPILATION_FAILED)
    print("The compilation of the file with basename %s succeeded." % basename,
          flush=True)


def link(basename, compiler, obj, executable):
    try:
        subprocess.run(
            [compiler, '/main.o', obj, '-o', executable],
            check=True
        )
    except:
        print("The link of the file with basename %s failed." % basename,
              flush=True)
        exit_after_notifying_launcher(ERR_CODE_LINK_FAILED)
    print("The link of the file with basename %s succeeded." % basename,
          flush=True)


def performance_measure(executable,
                        plaintexts,
                        number_of_tests,
                        ram_limit,
                        cpu_time_limit):
    current_test_index = 0
    ciphertexts = b''
    all_cpu_time = list()
    all_max_ram = list()
    cmd = '/execute.py %s %s %d'
    while current_test_index < number_of_tests:
        current_plaintext = plaintexts[
            current_test_index * 16:(current_test_index+1)*16
        ]
        current_pt_as_text = binascii.hexlify(current_plaintext).decode()
        try:
            ps = subprocess.run(
                cmd % (executable, current_pt_as_text, current_test_index),
                check=True,
                stdout=subprocess.PIPE,
                shell=True)
            ct_as_text, cpu_time, ram = json.loads(ps.stdout)
            current_ciphertext = bytes.fromhex(ct_as_text)
            if len(current_ciphertext) != 16:
                raise Exception("ciphertext is too short")
            ciphertexts += current_ciphertext

            # check whether we reach the limitation
            if cpu_time > cpu_time_limit:
                print("Execution reaches memory limit: %.2fs was used!" % cpu_time, flush=True)
                post_data = {"cpu_time": cpu_time}
                exit_after_notifying_launcher(
                    ERR_CODE_EXECUTION_EXCEED_TIME_LIMIT,
                    post_data=post_data)
            if ram > ram_limit:
                print("Execution reaches time limit: %.2fMB" % (ram/1024.), flush=True)
                post_data = {"ram": ram/1024.}
                exit_after_notifying_launcher(
                    ERR_CODE_EXECUTION_EXCEED_RAM_LIMIT,
                    post_data=post_data)

            all_cpu_time.append(cpu_time)
            all_max_ram.append(ram)
            current_test_index += 1
        except Exception as e:
            print("Execution failed", flush=True)
            traceback.print_exc()
            print("===========")
            print(e, flush=True)
            exit_after_notifying_launcher(ERR_CODE_EXECUTION_FAILED)

    print("The execution succeeded and we retrieved the ciphertexts.", flush=True)
    all_cpu_time.sort()
    all_max_ram.sort()
    average_cpu_time = mean(all_cpu_time[5:-5])
    average_max_ram = mean(all_max_ram[5:-5])

    return (ciphertexts, average_cpu_time, average_max_ram)


def main():
    # Compile
    upload_folder = os.environ['UPLOAD_FOLDER']
    basename = os.environ['FILE_BASENAME']
    compiler = os.environ['COMPILER']
    source_file = basename + '.c'
    object_file = basename + '.o'
    path_to_source = os.path.join(upload_folder, source_file)
    path_to_object = os.path.join('/tmp', object_file)

    # check forbidden string and pattern
    preprocess(path_to_source)

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
    ram_limit = 2**10 * int(os.environ['CHALLENGE_MAX_MEM_EXECUTION_IN_MB'])
    ciphertexts, average_cpu_time, average_max_ram = performance_measure(
        path_to_executable, plaintexts, number_of_tests,
        ram_limit, cpu_time_limit
    )
    size_factor = os.path.getsize(path_to_object) / max_bin_size
    ram_factor = average_max_ram * 1.0 / ram_limit
    time_factor = average_cpu_time * 1.0 / cpu_time_limit

    # If we reach this line, everything went fine
    post_data = {
        "ciphertexts": binascii.hexlify(ciphertexts).decode(),
        "size_factor": size_factor,
        "ram_factor": ram_factor,
        "time_factor": time_factor
    }
    exit_after_notifying_launcher(CODE_SUCCESS, post_data=post_data)


if __name__ == "__main__":
    main()
