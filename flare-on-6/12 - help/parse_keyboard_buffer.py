''' Parse the scancodes from the i8042prt keyboard buffer
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
import json
import struct
import os
import operator
import sys

def load_scancode_map(filename = 'scancode_map.json'):
    if not os.path.isfile(filename):
        raise Exception('Cannot find ' + filename)
    js = json.load(open(filename, 'rt'))
    shifts = js['shifts']
    scans = { int(k):v for k, v in js['scans'].iteritems() }
    shifted_scans = { int(k):v for k, v in js['shifted_scans'].iteritems() }
    shift_map = {}
    for shift_name, values in shifts.iteritems():
        for v in values:
            shift_map[v] = shift_name.upper()
    return scans, shifted_scans, shift_map, shifts

# parse a keyboard buffer image
# returns array of key events
def parse_buffer(data):
    scans, shifted_scans, shift_map, shifts = load_scancode_map()
    state = bytearray(256)
    parsed = []
    def get_shift_state(shift_name):
        return operator.truth(reduce(operator.or_, [ state[x] for x in shifts[shift_name] ]))
    for i in xrange(0, len(data), 12):
        _, scan, updown = struct.unpack('<HHH', data[i:i+6])
        if updown >= 2:
            continue        # unsupported
        if updown:
            # Key Up
            state[scan] = 0
            continue
        else:
            state[scan] = 1
            if scan in shift_map:
                continue
            out = []
            for shift_name in [ 'ctrl', 'alt' ]:
                if get_shift_state(shift_name):
                    out.append(shift_name.upper())
            shift = get_shift_state('shift')
            if shift and scan in shifted_scans:
                out.append(shifted_scans[scan])
            else:
                if shift:
                    out.append('SHIFT')
                if scan in scans:
                    out.append(scans[scan])
                else:
                    out.append('<0x%02x>' % scan)
            parsed.append('-'.join(out))
    return parsed



def main(filename):
    parsed = parse_buffer(open(filename, 'rb').read())
    print len(parsed), 'keystrokes'
    print ''.join(parsed)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'Usage: parse_keyboard_buffer.py <filename>'
        sys.exit(1)
    else:
        main(sys.argv[1])

