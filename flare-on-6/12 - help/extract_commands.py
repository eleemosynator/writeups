''' Volatility script to extract leaked command packets
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
# volatilty script to extract implant commands kept around due to memory leak bug

import struct
import volatility.win32 as win32
import volatility.utils as utils

cmd_codes = [
    0x0CD762BFA, 0x34B30F3B, 0x427906F4, 0x8168AD41, 0x0D180DAB5, 0x0D44D6B6C
    ]

# Find process by bid, given kernel A/S
def find_proc(vm, pid):
    for proc in win32.tasks.pslist(vm):
        if proc.UniqueProcessId.v() == pid:
            return proc
    return None

# call run(addrspace()) from volshell
def run(vmk):
    proc = find_proc(vmk, 876)       # Get infected svchost process
    if proc is None:
        print 'Failed to find process 876'
        return
    vmp = proc.get_process_address_space()
    n = 0
    with open('cmd_stream.bin', 'wb') as fout:
        for offset, size in vmp.get_available_pages():
            if (offset & 0xffff) != 0:
                continue                # We only want 64kb aligned blocks
            hdr = vmp.read(offset, 8)
            if hdr is None:
                continue
            if len(hdr) != 8:
                continue
            l, cmd = struct.unpack('<LL', hdr)
            if cmd not in cmd_codes:
                continue
            print '%016x: %08x %08x' % (offset, l, cmd)
            pkt = vmp.read(offset, l)
            if len(pkt) != l:
                print 'Failed to read packet'
            else:
#                for ofs, hexchars, chars in utils.Hexdump(pkt[:0x180]):
#                    print '%06x %-48s  %s' % (ofs, hexchars, ''.join(chars))
                fout.write(pkt)
            n += 1
    print '%d command packets extracted' % n

