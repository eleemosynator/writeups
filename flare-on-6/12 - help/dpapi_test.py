''' Volatility script: Test dpapi decoder
    Compile dpapi_test.cpp, run on a VM and take a crash-dump
    This script finds and attempts to decrypt the DPAPI-encrypted data in
    the dpapi_test process in the crash dump
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

import dpapi
import volatility.win32 as win32

DEBUG = False
VERBOSE = False

def verify_hit(vm, proc, addr):
    pid = proc.UniqueProcessId.v()
    data = proc.get_process_address_space().read(addr + 16, 32 * 3 + 8 * 3)
    if data is None:
        print ' [-] failed to read encrypted data from 0x%08x in process %d' % (addr, pid)
        return
    if DEBUG:
        open('dptest_blob_%d.bin' % pid, 'wb').write(data)
    types = 'SAME_PROCESS CROSS_PROCESS SAME_LOGON'.split(' ')
    for i in xrange(3):
        print '   AES%-20s %s' % ('[' + types[i] + ']:', dpapi.unprotect_memory(vm, pid, addr + 16 + 32 * i, 32, i, verbose=VERBOSE))
        print '  3DES%-20s %s' % ('[' + types[i] + ']:', dpapi.unprotect_memory(vm, pid, addr + 16 + 32 * 3 + 8 * i, 8, i, verbose=VERBOSE))
    print ''

def run_test(vm, proc):
    print 'Scanning pid %d' % proc.UniqueProcessId.v()
    for addr in proc.search_process_memory([ '16bytemagictagXX' ]):
        verify_hit(vm, proc, addr)
        return
    print ' [-] failed to find magic tag in dpapi_test process %d' % proc.UniqueProcessId.v()

def run(vm):
    n = 0
    for proc in win32.tasks.pslist(vm):
        if proc.ImageFileName.__format__('s').lower() == 'dpapi_test.exe':
            run_test(vm, proc)
            n += 1
    if n == 0:
        print ' [-] failed to find dpapi_test process in image'

