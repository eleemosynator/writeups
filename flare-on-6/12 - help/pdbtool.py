''' Voltility script that determines the pdb id of an image in a crash dump
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
# Find the pdb id for a given binary
import struct

# find codeview entry in debug directory
def find_codeview(vm, base, rva_debug, sz_debug):
    sz_entry = 0x1c
    if sz_debug % sz_entry != 0:
        raise Exception('pdbtool: image at 0x%016x has invalid debug directory size: 0x%04x' % (base, sz_debug))
    for p_entry in xrange(rva_debug, rva_debug + sz_debug, sz_entry):
        entry = vm.read(base + p_entry, sz_entry)
        if entry is None or entry == '\0' * sz_entry:
            raise Exception('pdbtool: Missing or paged out debug directory entry at 0x%016x for image: 0x%016x' % (base + p_entry, base))
        chars, tstamp, version, d_type, sz_data, rva_data, ofs_data = struct.unpack('<LLLLLLL', entry)
        if d_type == 2:        # Codeview
            return rva_data, sz_data
    raise Exception('pdbtool: image at 0x%016x has no Codeview debug directory entry' % base)


# returns pdb id as tuple pdb_name, guid_string
def get_pdb_id(vm, base):
    if vm.read(base, 2) != 'MZ':
        raise Exception('pdbtool: no MZ header for image at 0x%016x' % base)
    pe_base = base + struct.unpack('<L', vm.read(base + 0x3c, 4))[0]
    if vm.read(pe_base, 2) != 'PE':
        raise Exception('pdbtool: no PE header for image at 0x%016x' % base)
    rva_debug, sz_debug = struct.unpack('<LL', vm.read(pe_base + 0xb8, 8))
    if rva_debug == 0 or sz_debug == 0:
        raise Exception('pdbtool: empty debug section for image at 0x%016x' % base)
    rva_cv, sz_cv = find_codeview(vm, base, rva_debug, sz_debug)
    if sz_cv <= 24:
        raise Exception('pdbtool: Codeview debug entry is too small for image at 0x%016x' % base)
    cv = vm.read(base + rva_cv, sz_cv)
    if cv is None or cv == '\0' * sz_cv:
        raise Exception('pdbtool: Missing or paged out Codeview entry for image at 0x%016x' % base)
    if cv[:4] != 'RSDS':
        raise Exception('pdbtool: Codeview entry has invalid header for image at 0x%016x' % base)
    gdw, gw1, gw2 = struct.unpack('<LHH', cv[4:12])
    age = struct.unpack('<L', cv[20:24])[0]
    fname = cv[24:]
    fname = fname[:(fname + '\0').find('\0')]
    tag = (('%08x%04x%04x' % (gdw, gw1, gw2)) + cv[12:20].encode('hex') + ('%1x' % age)).upper()
    return fname, tag

