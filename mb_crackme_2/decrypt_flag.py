''' all-in-one flag decrypter for Malwarebytes crackme #2
    WARNING: DOWNLOADS AND EXECUTES FILES FROM IMGUR: USE AT YOUR OWN RISK
    Requires unpacked challenge files (another) and dependencies in the same
    directory.

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
import another
import pefile
import zlib
from Crypto.Cipher import XOR
from colorama import *

# download the payload and decrypt flag
URL = 'https://i.imgur.com/dTHXed7.png'
BLOB_RVA = 0x32000
BLOB_SIZE = 0x269
BLOB_KEY = 'dump_the_key'

# RC4-like encryption/decryption function at 0x100016F0

def rc4like_decrypt(key, data):
    # Substitution box
    S = bytearray(xrange(0x100))

    # setkey
    bh = 0
    for i in xrange(len(S)):
        bl = S[i]
        al = ord(key[i % len(key)])
        al += bl
        bh += al
        bh &= 0xff
        al = S[bh]
        S[i] = al
        S[bh] = bl

    ct = bytearray(data)
    k = 0   # ebx
    l = 0   # pb_dump_the_key
    for i in xrange(len(ct)):
        k = (k + 1) & 0xff
        k, l = (l + S[k]) & 0xff, k
        ct[i] ^= S[(S[k] + S[l]) & 0xff]
    return ct

def main():
    payload = another.get_encoded_data(another.fetch_url(URL))
    pe = pefile.PE(data=payload)
    blob_offset = pe.get_offset_from_rva(BLOB_RVA)
    pe = None
    blob = payload[blob_offset:blob_offset + BLOB_SIZE]
    cleartext = rc4like_decrypt(BLOB_KEY, blob)
    print 'a64 blob: ', len(cleartext)
    decomped = zlib.decompress(cleartext.decode('base64'))
    print 'decompressed: ', len(decomped)

    exec(XOR.new('\x80\x00\x80').decrypt(decomped))

if __name__ == '__main__':
    main()

