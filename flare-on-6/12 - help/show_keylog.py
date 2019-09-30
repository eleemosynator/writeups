''' Parse the keylogger files
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
import struct

def parse_keylog(data):
    p = 0
    while p < len(data):
        p_end = data.find('\0', p)
        if p_end < 0:
            break
        title = data[p:p_end]
        keys_size = struct.unpack('<L', data[p_end + 1:p_end + 5])[0]
        keys = data[p_end+5:p_end+5+keys_size]
        p = p_end + keys_size + 5
        yield title, keys

def show_keylog(fname):
    data = open(fname, "rb").read()
    for title, keys in parse_keylog(data):
        if len(keys) == 0:
            continue
        disp_keys = keys.replace('\n', '<ENTER>\n  ').replace('\t', '<TAB>')
        # trim trailing spaces
        if disp_keys.endswith('\n  '):
            disp_keys = disp_keys[:-3]
        print title + ':\n  ' + disp_keys


def main():
    for fname in os.listdir('traffic'):
        if not fname.startswith('keylog'):
            continue
        print fname
        show_keylog(os.path.join('traffic', fname))
        print ''


if __name__ == '__main__':
    main()

