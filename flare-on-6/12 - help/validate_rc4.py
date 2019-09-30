''' Prove that man.sys uses RC4 to decrypt its stack strings
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

import win32api
from win32con import *
from Crypto.Cipher import ARC4
from ctypes import *

data = open('binaries/man_sys_img.bin', 'rb').read()

mem = windll.kernel32.VirtualAlloc(0, len(data), MEM_RESERVE | MEM_COMMIT,
                                    PAGE_EXECUTE_READWRITE)
assert mem
memmove(mem, data, len(data))
decrypt_string = WINFUNCTYPE(c_bool, c_char_p, c_uint, c_void_p, c_uint)(mem + 0x1190)
key='rc4-key'
text = 'This IS RC4!'
#print ARC4.new(key).encrypt(text).encode('hex')
buf = bytearray(ARC4.new(key).encrypt(text))
array = ARRAY(c_char, len(text)).from_buffer(buf)
decrypt_string(key, len(key), byref(array), len(array))
print str(buf)
