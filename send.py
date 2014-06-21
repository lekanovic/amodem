from matplotlib import pyplot as plt
import subprocess as sp
import numpy as np

import os
import sys
import time
import signal
import logging
import itertools

logging.basicConfig(level=0, format='%(message)s')
log = logging.getLogger(__name__)

import sigproc
from common import *

dev_null = open('/dev/null')

def play(fd):
    args = ['aplay', fd.name, '-q', '-f', 'S16_LE', '-c', '1', '-r', str(int(Fs))]
    ret = sp.call(args=args)
    assert ret == 0

def record(fname):
    args = ['arecord', fname, '-q', '-f', 'S16_LE', '-c', '1', '-r', str(int(Fs))]
    p = sp.Popen(args=args)
    p.stop = lambda: os.kill(r.pid, signal.SIGINT)
    return p


class Symbol(object):
    t       = np.arange(0, Nsym) * Ts
    carrier = [ np.exp(2j * np.pi * F * t) for F in frequencies ]

sym = Symbol()

data = open('data.send', 'r').read()

def start(sig, c):
    sig.send(c*0, n=100)
    sig.send(c*1, n=300)
    sig.send(c*0, n=100)

def train(sig, c):
    for i in range(20):
        sig.send(c*1, n=10)
        sig.send(c*0, n=10)
    sig.send(c*0, n=100)

def modulate(sig, bits):
    symbols_iter = sigproc.modulator.encode(list(bits))
    symbols_iter = itertools.chain(symbols_iter, itertools.repeat(0))
    carriers = np.array(sym.carrier) / len(sym.carrier)
    while True:
        symbols = itertools.islice(symbols_iter, len(sym.carrier))
        symbols = np.array(list(symbols))
        sig.send(np.dot(symbols, carriers))
        if all(symbols == 0):
            break

if __name__ == '__main__':

    bps = baud * sigproc.modulator.bits_per_symbol * len(sym.carrier)
    log.info('Running MODEM @ {:.1f} kbps'.format(bps / 1e3))

    with open('tx.int16', 'wb') as fd:
        sig = Signal(fd)
        start(sig, sym.carrier[carrier_index])
        for c in sym.carrier:
            train(sig, c)

        bits = to_bits(pack(data))
        modulate(sig, bits)


    r = record('rx.int16')
    start = time.time()
    p = play(fd)
    log.debug('Took %.2f seconds', time.time() - start)
    time.sleep(0.1)
    r.stop()