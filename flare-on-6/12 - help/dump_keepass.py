''' Volatility script: Dump KeePass 1.x databases in crash dump
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
# Volatility script
# Dump contents of opened KeePass databases
# only tested with KeePass 1.37, may work with other KeePass 1.x versions

import volatility.win32 as win32
import volatility.utils as utils
import struct
import dpapi

# Constants
PWENTRY_SIZE = 0x58

def read_string(vm, ptr):
    if ptr == 0:
        return '<null>'
    data = vm.zread(ptr, 256)
    return data[:(data + '\0').find('\0')]

# dump single PwEntry
def dump_entry(vm, proc, data):
    p_title, p_url, p_user_name, dw_password_len, p_password, p_additional = struct.unpack('<LLLLLL', data[0x18:0x30])
    print '  Title:      ' + read_string(vm, p_title)
    print '  URL:        ' + read_string(vm, p_url)
    print '  User Name:  ' + read_string(vm, p_user_name)
    dpapi_len = (dw_password_len + 15) & ~0x0f
    pwd = dpapi.unprotect_memory(vm, proc.UniqueProcessId.v(), p_password, dpapi_len, dpapi.SAME_PROCESS, verbose=False)
    print '  Password:   ' + pwd[:dw_password_len]
    print '  Additional: ' + read_string(vm, p_additional)
    print ''


# Dump entry array
def dump_entries(vm, proc, data):
    for p in xrange(0, len(data), PWENTRY_SIZE):
        dump_entry(vm, proc, data[p:p+PWENTRY_SIZE])

# Dump DB contents given address of DB header in CPwManager structure
def dump_kdb(proc, addr):
    vm = proc.get_process_address_space()
    hdr = vm.read(addr - 24, 24)
    if hdr is None:
        return
    p_entries, max_entries, num_entries, p_groups, max_groups, num_groups = struct.unpack('<LLLLLL', hdr)
    if p_entries == 0:
        return
    if num_entries >= max_entries or num_groups >= max_groups:
        return
    if num_entries == 0:
        return
    # Heuristic
    if num_entries > 0x100:
        print ' Skipping possibly malformed CPwManager object at 0x%08x' % addr
        return
    # Read all the entries
    data = vm.read(p_entries, num_entries * PWENTRY_SIZE)
    if data is None:
        print ' CPwManager at 0x%08x: failed to read PwEntry array from 0x%08x' % (addr, p_entries)
        return
    print ' kdb header at 0x%08x: %d entries' % (addr, num_entries)
    dump_entries(vm, proc, data)

def dump_proc(vm, proc):
    print '{0}: {1}'.format(proc.ImageFileName, proc.UniqueProcessId) 
    db_tag = '03d9a29a65fb4bb5'.decode('hex')
    for addr in proc.search_process_memory([ db_tag ]):
        dump_kdb(proc, addr)

# Main entry-point - requries address space object
def run(vm):
    for proc in win32.tasks.pslist(vm):
        if proc.ImageFileName.__format__('s').lower() == 'keepass.exe':
            dump_proc(vm, proc)

