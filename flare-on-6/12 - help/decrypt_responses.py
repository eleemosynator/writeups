''' Decrypt all reponse packets
    Copyright (C) 2019 eleemosynator

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
import os
from Crypto.Cipher import XOR
import struct
from ctypes import *
from Crypto.Cipher import ARC4
import sys
sys.path.append('../tools')
sys.path.append('../../tools')
from py_re_util import *

ntdll = windll.ntdll

ntdll.RtlDecompressBuffer.argtypes =  [ c_uint, c_char_p, c_uint, c_char_p, c_uint, POINTER(c_uint) ]
ntdll.RtlDecompressBuffer.restype = c_uint

def decompress(data):
    d_len = c_uint(0)
    outbuff = ('\0' * (8 * len(data)))
    v = ntdll.RtlDecompressBuffer(0x102, outbuff, len(outbuff), data, len(data), byref(d_len))
#    print hex(v), d_len.value
    if v != 0:
        return None
    return outbuff[:d_len.value]

def decrypt_data(data):
    buff = ARC4.new('FLARE ON 2019\0').decrypt(data)
    return decompress(buff)

keys = {
    4444:'5df34a484848dd23',
    7777:'4a1f4b1cb0d825c7',
    6666:'d56994fa25ecdfda',
    8888:'f78f7848471a449c'
    }

# filenames for results
names = {
    4444:'cmd-%05d.bin',
    7777:'screenshot-%05d.bmp',
    8888:'keylog-%05d.bin',
    6666:'file-%05d.bin'
    }

def decode_stream(fn):
    data = open(fn, 'rb').read()
    port = int(fn[-5:])
    if port not in keys or port == 4444:    # We don't bother with commands - already have them
        return False
    pt = fn.find('-')
    seq = int(fn[pt-5:pt])                  # Use source port as sequence number
    # find the key
    key = keys[port]
    data = XOR.new(key.decode('hex')).decrypt(data)       # Remove stmedit layer
    fl = names[port] % seq
    size = struct.unpack('<L', data[:4])[0]
#    print hex(size), hex(len(data[4:size])), hex(len(data))
    if port == 7777:
        # Bitmaps don't go through cryptodll
        ptext = data[4:size]
    else:
        ptext = decrypt_data(data[4:size])  # Don't forget to trim the stmedit leaked data
    if ptext is None:
        print 'Failed to decrypt: %05d -> %05d' % (seq, port)
    else:
        open(os.path.join('traffic/', fl), 'wb').write(ptext)


def decode_all_dir(dirname):
    for fn in os.listdir(dirname):
        if '-' not in fn:
            continue
        if '192.168.001.243' not in fn:
            continue
        decode_stream(os.path.join(dirname, fn))


if __name__ == '__main__':
    if not os.path.isdir('traffic'):
        os.mkdir('traffic')
    decode_all_dir('streams')
