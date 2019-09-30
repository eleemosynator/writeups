''' Parse the command stream
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
# parse the command stream
import sys
sys.path.append('../tools')
sys.path.append('../../tools')
from py_re_util import *
import struct
import os
import re

def load_processes(fname):
    processes = {}
    for l in open(fname, 'rt'):
        if not l.startswith('0x'):
            continue
        cols = re.sub('\s+', ' ', l).split(' ')
        processes[int(cols[2])] = (cols[1], int(cols[0][2:], 16))
    return processes

# map pid => (name, handle)
processes = load_processes('scans/pslist.txt') 

# Extract a binary name using the pdb string
def get_binary_name(data):
    n = 0
    while n < len(data):
        n = data.find('RSDS', n + 1)
        if n < 0:
            break
        k = data.find('.pdb', n)
        if k > n + 256:
            continue
        return data[n + 24:k].split('\\')[5]
    return None

# global map tags => plugin
tag_map = {}

# command handlers
def cmd_install_plugin(idx, p0, p1, pkt):
    global tag_map, processes
    size, cmd, tag, pid, port = struct.unpack('<LLLLL', pkt[:0x14])
    if pid in processes:
        psname = processes[pid][0]
    else:
        psname = 'unknown'
    bin_name = get_binary_name(pkt[0x1c:])
    tag_map[tag] = bin_name
    print '%02x install-plugin%d%d(%s, tag=0x%08x, pid=%d %s, port=%d' % (
            idx, p0, p1, bin_name, tag, pid, psname, port)

def cmd_call_plugin(idx, pkt):
    size, cmd, tag, subcmd, arg_size = struct.unpack('<LLLLL', pkt[:0x14])
    args = pkt[0x14:]
    if tag in tag_map:
        name = tag_map[tag]
    else:
        name = 'unknown_%08x' % tag
    # handle sub-arguments
    arg_string = ''
    if arg_size > 0:
        if name == 'filedll':
            if subcmd == 0x7268f598:
                arg_string = ', '.join([ '', '"' + trim_asciiz(pkt[0x14:0x118]) + '"', '"' + trim_asciiz(pkt[0x118:]) + '"'])
            elif subcmd == 0x1e3258ab:
                arg_string = ', "' + trim_asciiz(pkt[0x14:]) + '"'# + ', %d' % ord(pkt[0x14+0x104])
        elif name == 'keylogdll':
            arg_string = ', ' + '%d' % struct.unpack('<L', pkt[0x14:0x18])[0]
        if arg_string == '':
            arg_string = ', ' + ''.join([ '%02x' % ord(x) for x in pkt[0x14:0x14 + arg_size] ])
    print '%02x call-plugin(%s, 0x%08x%s)' % (idx, name, subcmd, arg_string)

def cmd_ioctl(idx, pkt):
    ioctl, data_size = struct.unpack('<LL', pkt[0x10c:0x114])
    data = pkt[0x114:0x114 + data_size]
    print '%02x ioctl(%s, 0x%08x, { %s })' % (idx, trim_asciiz(pkt[0x08:0x10c]), ioctl, ' '.join([ '%02x' % ord(x) for x in data ]))

def cmd_install_driver(idx, pkt):
    print '%02x install-driver(%s)' % (idx, get_binary_name(pkt[0x0c:]))

cmds = {
        0x34B30F3B:lambda x, y: cmd_install_plugin(x, 0, 1, y),
        0x8168AD41:lambda x, y: cmd_install_plugin(x, 1, 0, y),
        0xCD762BFA:lambda x, y: cmd_install_plugin(x, 0, 0, y),
        0xD180DAB5:cmd_call_plugin,
        0xD44D6B6C:cmd_install_driver,
        0x427906F4:cmd_ioctl
        }


def cmd_parser(data):
    p = 0
    while p < len(data):
        pkt_len = struct.unpack('<L', data[p:p+4])[0]
        yield data[p:p+pkt_len]
        p += pkt_len


def main():
    if not os.path.isdir('commands'):
        os.mkdir('commands')
    n = 0
    excess = ''
    for pkt in cmd_parser(open('cmd_stream.bin', 'rb').read()):
        hdr = struct.unpack('<LLLL', pkt[:16])
        name = get_binary_name(pkt)
        if name is None:
            name = ''
        else:
            if pkt[0x1c:0x1e] == 'MZ':
                fname = name + '.dll'
                ofs = 0x1c
            else:
                fname = name + '.sys'
                ofs = 0x0c
            fname = 'binaries/' + fname
            if not os.path.isfile(fname):
                open(fname, 'wb').write(pkt[ofs:])
        open('commands/cmd%02x.bin' % n, 'wb').write(pkt)
#        print '%02x' % n + (' %08x' * 4) % hdr, name
#        print '\n' * 6
#        hexdump(pkt[:0x20])
#        print hex(hdr[1])
        cmds[hdr[1]](n, pkt)
        excess += pkt[-6:]
        n += 1
    hexdump(excess)
    print '%d total commands' % n

main()
