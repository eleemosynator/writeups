''' Utility script that parses x86 binary snippets using distorm3 or capstone
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

# Parse binary snippets using distorm3 or capstone


# Enables debugging messages

DEBUG = False

# Disassemblers only needed when dealing with Windows 10

HAVE_DISTORM3 = False
HAVE_CAPSTONE = False

try:
    import distorm3
    HAVE_DISTORM3 = True
    if DEBUG:
        print ' [+] distorm3 available'
except:
    pass

try:
    import capstone
    import capstone.x86_const as csx86
    HAVE_CAPSTONE = True
    if DEBUG:
        print ' [+] capstone engine available'
finally:
    if DEBUG:
        print ' [-] failed to load either distorm3 or capstone'

if DEBUG:
    if HAVE_DISTORM3:
        print ' [+] Using distorm3'
    elif HAVE_CAPSTONE:
        print ' [+] Using capstone engine'
    else:
        print ' [-] No disassembly engine available'

#print 'Testing capstone'
#HAVE_DISTORM3 = False

# Find rip-relative mov using distorm3
def find_rr_writes_distorm3(address, data):
    writes = []
    for insn in distorm3.Decompose(address, data, type=distorm3.Decode64Bits):
        if insn.mnemonic[:3] == 'RET':
            break
        if insn.mnemonic[:3] != 'MOV':
            continue

        # potential write
        opnd = insn.operands[0]
        if opnd.type != 'AbsoluteMemory' or opnd.index is None:
            continue
        # Absolute mov, with target that is register-based
        if distorm3.Registers[opnd.index] != 'RIP':
            continue
        # RIP-relative write, this is what we are looking for
        # distorm3 opnd.size is measured in bits, need to adjust to bytes
        writes.append((insn.address + insn.size + opnd.disp, opnd.size / 8))
    return writes

# Find rip-relative mov using capstone
def find_rr_writes_capstone(address, data):
    #print 'Using capstone'
    cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    cs.detail = True
    writes = []
    for insn in cs.disasm(data, address):
        if insn.mnemonic[:3] == 'ret':
            break
        if insn.mnemonic[:3] != 'mov':
            continue

        # potential write
        opnd = insn.operands[0]
        if opnd.type != csx86.X86_OP_MEM:
            continue
        if opnd.mem.base != csx86.X86_REG_RIP:
            continue
        # RIP-relative write
        writes.append((insn.address + insn.size + opnd.mem.disp, opnd.size))
    return writes

# Consolidate contiguous writes into single segments
def consolidate_writes(writes):
    addresses = sorted(writes)
    out = []
    i = 0
    while i < len(addresses):
        addr, size = addresses[i]
        j = i + 1
        while j < len(addresses):
            addr2, size2 = addresses[j]
            if addr + size != addr2:
                break
            else:
                size += size2
            j += 1
        i = j
        out.append((addr, size))
    return out

if DEBUG:
    print consolidate_writes([(0, 4), (8, 4), (4, 4), (12, 4), (32, 16), (64, 16), (80, 16)])


# Main export - find rip-relative writes in x64 code

def find_rip_relative_writes(address, data, consolidate=False):
    if HAVE_DISTORM3:
        writes = find_rr_writes_distorm3(address, data)
    elif HAVE_CAPSTONE:
        writes = find_rr_writes_capstone(address, data)
    else:
        raise Exception('code_parser.find_rip_relative_writes: Neither distorm3 nor capstone are available')
    if consolidate:
        writes = consolidate_writes(writes)
    return writes

