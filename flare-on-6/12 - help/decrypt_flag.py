''' Standalone script for Flare-On 6 challenge 12
    Decrypt DAPI-encrypted flag blob from KeePass memory Image
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
from Crypto.Cipher import AES
from Crypto.Hash import SHA1
import struct

def get_hex(s):
    return s.translate(None, ' -').decode('hex')

flag_crypted = open('flag_protected.bin', 'rb').read()

# Prepare the AES key
ctx = SHA1.new()
ctx.update(get_hex('1c 81 87 7b 81 73 be 1b 99 da 11 35 10 43 4e da 97 9e b0 0e 37 cd 31 2b')) # from hex dump
ctx.update(struct.pack('<LQ', 0x14c044f5, 0x1d5493fc578c885))    # Process cookie and Creation Time
aes_key = ctx.digest()[:16]

iv = get_hex('35 3a d5 b5 19 db b2 64-ba e3 85 9e d7 b1 02 e8') # copy/pasted from the hex dump

flag = AES.new(aes_key, AES.MODE_CBC, IV=iv).decrypt(flag_crypted)

print flag[:flag.find('\0')]
