''' Break the encryption keys of the responses using the cleartext at the end of the streams
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

def getkey(fname):
    data = open(fname, 'rb').read()
    if len(data) < 16:
        return None
    # look for plaintext data size at the end
    for p in xrange(len(data) - 8, 8, -1):
        if struct.unpack('<L', data[p:p+4])[0] == p:
            # hit
#            print fname[-5:] + ' data: ' + data[p:p+16].encode('hex')
            return XOR.new(data[0:8]).decrypt(data[p:p+8])
    return None

def main():
    ports = map(str, [ x * 1111 for x in [ 6, 7, 8 ] ]) # omitting port 4444
    sdir = 'streams'
    keys = {}
    for fn in os.listdir(sdir):
        if len(fn) < 5 or fn[-5] != '0':
            continue
        port = fn[-4:]
        if port not in ports:
            continue
        key = getkey(os.path.join(sdir, fn))
        if key is None:
            print '%s: getkey() failed' % fn
            continue
        if port in keys:
            if key != keys[port]:
                print '%s: new key: %s' % (port, key.encode('hex'))
        else:
            print '%s: key: %s' % (port, key.encode('hex'))
            keys[port] = key

if __name__ == '__main__':
    main()
