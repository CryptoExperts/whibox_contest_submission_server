#!/usr/bin/env python3

import binascii
import json
import resource
import subprocess
import sys


def execute(executable, plaintext):
    ps = subprocess.run(
        executable,
        check=True,
        input=plaintext,
        stdout=subprocess.PIPE,
        shell=True
    )
    ciphertext = binascii.hexlify(bytes(ps.stdout)).decode()

    resource_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu_time = resource_usage.ru_stime + resource_usage.ru_utime
    max_ram = resource_usage.ru_maxrss

    return (ciphertext, cpu_time, max_ram)


if __name__ == "__main__":
    executable = sys.argv[1]
    plaintext = bytes.fromhex(sys.argv[2])
    ciphertext, cpu_time, max_ram = execute(executable, plaintext)
    output = json.dumps(
        [ciphertext, cpu_time, max_ram]
    )
    print(output)
