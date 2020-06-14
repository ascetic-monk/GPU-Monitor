# author: zeyang

import os
import sys
import time
import argparse
import numpy as np

cmd = 'python /path/to/script.py'


def parse_args():
    """Parse input arguments"""
    parser = argparse.ArgumentParser(description='GPU resource monitoring.')
    parser.add_argument(
        '-n-gpus', '--num-gpus', type=int, default=8,
        help='Number of GPUs you need.')
    parser.add_argument(
        '-m', '--memory', type=int, required=True,
        help='Estimated GPU memory you need (MB per GPU).')
    parser.add_argument(
        '-inv', '--interval', type=int, default=2,
        help='Interval time (s) between queries of GPU status.')

    return parser.parse_args()


def gpu_info(args):
    memory_total = list(map(int, os.popen('nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits')
                            .read().strip().split('\n')))
    memory_used = list(map(int, os.popen('nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits')
                           .read().strip().split('\n')))
    memory_free = list(map(int, os.popen('nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits')
                           .read().strip().split('\n')))
    power = list(map(float, os.popen('nvidia-smi --query-gpu=power.draw --format=csv,noheader,nounits')
                           .read().strip().split('\n')))
    power_limit = list(map(float, os.popen('nvidia-smi --query-gpu=power.limit --format=csv,noheader,nounits')
                               .read().strip().split('\n')))
    num_gpus = len(memory_total)
    assert num_gpus >= args.num_gpus, f'{num_gpus} GPU(s) detected, however {args.num_gpus} GPU(s) needed.'

    # number of GPUs that have memory in design larger than the required memory
    n_sat = np.sum(np.array(memory_total) >= args.memory)
    assert n_sat >= args.num_gpus, \
        f'Require {args.num_gpus} GPU(s) that have memory in design larger than {args.memory} MB, ' \
            f'however only {n_sat} GPU(s) satisfied.'

    # number of GPUs that have free memory larger than the required memory
    id = np.nonzero(np.array(memory_free) >= args.memory)[0]  # the id list of GPU(s) that are ready for the task.
    ready = id.size >= args.num_gpus

    return ready, id, zip(range(num_gpus), power, power_limit, memory_used, memory_total)


def main(args):
    ready, id, info = gpu_info(args)
    i = 0
    while not ready:  # set waiting condition
        ready, id, info = gpu_info(args)
        i = i % 5
        sys.stdout.write('\r|  GPU  |  Pwr:Usage/Cap  |     Memory-Usage    |\r\n')
        gpu_info_format = '|{:^7d}|   {:>3.0f}W / {:>3.0f}W   | {:>5d}MiB / {:>5d}MiB |\r\n'
        gpu_info_print = ''.join([gpu_info_format.format(*data) for data in info])
        symbol = 'monitoring' + '.' * i
        sys.stdout.write(gpu_info_print + symbol)
        sys.stdout.flush()
        time.sleep(args.interval)
        i += 1
    print('\n' + cmd)
    os.system(cmd)


if __name__ == '__main__':
    args = parse_args()
    main(args)