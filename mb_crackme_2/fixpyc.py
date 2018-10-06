''' fix header in unpacked pyc files

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
import sys

if __name__ == '__main__':
    hdr = '03f30d0a00000000'.decode('hex')
    assert len(hdr) == 8
    for fn in sys.argv[1:]:
        with open(fn, 'rb') as f:
            data = f.read()
            f.close()
        if data[:4] == hdr[:4]:
            print 'Skipping ' + fn
            continue
        with open(fn, 'wb') as f:
            f.write(hdr + data)
            f.close()

