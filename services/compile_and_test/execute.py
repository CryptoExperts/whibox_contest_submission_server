#!/usr/bin/env python3

import binascii
import json
import resource
import subprocess
import sys


def execute(executable, message):
    ps = subprocess.run(
        executable,
        check=True,
        input=message,
        stdout=subprocess.PIPE,
        shell=True
    )
    signature = binascii.hexlify(bytes(ps.stdout)).decode()

    resource_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu_time = resource_usage.ru_stime + resource_usage.ru_utime
    max_ram = resource_usage.ru_maxrss

    return (signature, cpu_time, max_ram)


if __name__ == "__main__":
    executable = sys.argv[1]
    message = bytes.fromhex(sys.argv[2])
    signature, cpu_time, max_ram = execute(executable, message)
    output = json.dumps(
        [signature, cpu_time, max_ram]
    )
    print(output)
