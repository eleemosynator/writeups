''' Common Python utilities for reverse engineering
    Copyright (C) 2016-2022 eleemosynator

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
# py_re_util.py :- common python utilities for reverse engineering
import itertools
import os

# rotation

# rotate left a value num_bits wide by n bits
def rol(v, n, num_bits):
    n %= num_bits
    mask = (1 << num_bits) - 1
    return ((v << n) & mask) | (v >> (num_bits - n))

def ror(v, n, num_bits):
    n %= num_bits
    mask = (1 << num_bits) - 1
    return (v >> n) | ((v << (num_bits - n)) & mask)

# hex dumps

# hex line
def hexline(data):
    return ' '.join([ "%02x" % x for x in data])

def charline(data):
    return ''.join([ chr(x) if (x >= 0x20 and x < 0x7f) else '.' for x in data ])

def pad(line, size):
    return (line + ' ' * size)[:size]

# hexdump a byte array
def hexdump(data, address=0):
    if type(data) == str:
        data = data.encode('utf-8')      # lame
    for i in range(0, len(data), 16):
        l = 16;
        if i + l > len(data):
            l = len(data) - i
        print(('%08x: ' % (i + address)) + pad(hexline(data[i:i+l]), 16 * 3) + ' ' + charline(data[i:i+l]))

# simple load/save file
def save_file(filename, data, binary=True, overwrite=False):
    if not overwrite and os.path.isfile(filename):
        return
    with open(filename, 'wb' if binary else 'wt') as fout:
        fout.write(data)
        fout.close()

def save_text(fname, data, overwrite=False):
    save_file(fname, data, binary=False, overwrite=overwrite)

def save_bin(fname, data, overwrite=False):
    save_file(fname, data, binary=True, overwrite=overwrite)


def load_file(fname, binary=True):
    with open(fname, 'rb' if binary else 'wt') as fin:
        data = fin.read()
        fin.close()
    return data

def load_text(fname):
    return load_file(fname, binary=False)

def load_bin(fname):
    return load_file(fname, binary=True)


# general util

def trim_asciiz(s):
	if type(s) is bytes or type(s) is bytearray:
		sep = b'\0'
	elif type(s) is str:
		sep = '\0'
	else:
		raise RuntimeError(f'trim_asciiz: unsupported type: {repr(type(s))}')

	if s == sep:
		return s[:0]
	elif sep in s:
		return s[:s.find(sep)]
	else:
		return s

def read_asciiz(data, offset, maxsize=1024):
    return trim_asciiz(data[offset:offset + maxsize])

def xorbytes(d, k):
    return bytes([ x ^ y for x, y in zip(d, itertools.cycle(k)) ])

def xorbytes2(d, k):
    return bytes([ x if x == '\0' or x == y else x ^ y for x, y in zip(d, itertools.cycle(k)) ])

