''' Decrypt FLEGGO flag and build animation
    Copyright (C) 2018 eleemosynator

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
import struct
from Crypto.Cipher import ARC4
import sys
sys.path.append('../tools')
from py_re_util import *
from collections import namedtuple

Brick = namedtuple('Brick', 'idx, flag, password, size, brick')

path = 'FLEGGO'
fleggo_animation_fname = 'fleggo_animation.gif'
fleggo = []
for fn in os.listdir(path):
    if not fn.endswith('.exe'):
        continue
    data = load_file(os.path.join(path, fn))
    password = trim_asciiz(data[0x2AB0:0x2AD0:2])
    brick_fname = xorbytes(trim_asciiz(data[0x2AD0:0x2AF0:2]), chr(0x85))
    flag = xorbytes(trim_asciiz(data[0x2AF0:0x2AFA:2]), chr(0x1a))
    idx, brick_size = struct.unpack('<HL', data[0x2AFA:0x2B00])
    brick_crypted = data[0x2B00:0x2B00 + brick_size]
    brick = ARC4.new(password).decrypt(brick_crypted)
    save_file(os.path.join(path, brick_fname), brick)
    fleggo.append(Brick(idx, flag, password, brick_size, brick))

fleggo = sorted(fleggo)     # sort by idx
print ''.join([ x.flag for x in fleggo ])

if not os.path.isfile(fleggo_animation_fname):
    try:
        from PIL import Image
        import io
        images = [ Image.open(io.BytesIO(x.brick)) for x in fleggo ]
        images[0].save('fleggo_animation.gif', save_all=True, append_images=images[1:], duration=200, loop=0)
    except:
        pass

