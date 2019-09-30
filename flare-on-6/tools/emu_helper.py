''' Simple setup file for using the Unicorn emulator
    Copyright (C) 2017-2019 eleemosynator

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
# Generic tools for emulating scraps of code
import struct
from unicorn import *
from unicorn.x86_const import *
import capstone
import sys
from py_re_util import *

try:
    import pefile
except:
    pass

try:
    from elftools.elf.elffile import ELFFile
except:
    pass

def trim_asciiz(s):
    if s == '\0':
        return ''
    elif '\0' in s:
        return s[:s.find('\0')]
    else:
        return s

def show_strings(tag, strs, offsets=None):
    if offsets is None:
        offsets = sorted(strs.keys())
    print 'stack strings for ' + tag + ':'
    print '\n'.join([ ' %03x %s' % (k, strs[k]) for k in offsets ]) + '\n'

class Emu(object):
    def __init__(self):
        self.mu = None
        self.shim_base = 0
        self.shim_len = 0x4000

    def dis(self, va_start, va_end, max_insn = -1):
        for insn in self.md.disasm(self.mu.mem_read(va_start, va_end - va_start), va_start):
            if max_insn == 0:
                break
            max_insn -= 1
            print '0x%06x %s %s' % (insn.address, insn.mnemonic, insn.op_str)

    #setup memory map and reg names for mode
    def set_mode(self, mode):
        if mode == UC_MODE_32:
            self.md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
            self.reg_rsp = UC_X86_REG_ESP
            self.reg_rbp = UC_X86_REG_EBP
            self.reg_rip = UC_X86_REG_EIP
        elif mode == UC_MODE_64:
            self.md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
            self.reg_rsp = UC_X86_REG_RSP
            self.reg_rbp = UC_X86_REG_RBP
            self.reg_rip = UC_X86_REG_RIP
        elif mode == UC_MODE_16:
            self.md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)
            self.reg_rsp = UC_X86_REG_SP
            self.reg_rbp = UC_X86_REG_BP
            self.reg_rip = UC_X86_REG_IP
        else:
            raise Exception('Unknown x86 mode: %d' % mode)
        self.mode = mode


    def init_pe(self, filename):
        if 'pefile' not in globals():
            raise Exception('emu_helper: Please install pefile before loading PE binaries')
        self.pe = pefile.PE(filename)
        machine = self.pe.FILE_HEADER.Machine
        if machine == 0x014c:
            self.set_mode(UC_MODE_32)
        elif machine == 0x8664:
            self.set_mode(UC_MODE_64)
        else:
            raise Exception('Uknown Machine type: 0x%04x' % machine)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
#        print 'loading base: 0x%08x' % self.base
        mem = self.pe.get_memory_mapped_image()
#        print 'image: %08x' % len(mem)
        # we'll map mem at base, then our shim and then stack
        self.shim_base = self.base + ((len(mem) + 0x1fff) & 0xfffff000)
        self.stack_len = 0x10000
        self.mu = Uc(UC_ARCH_X86, self.mode)
        self.mu.mem_map(self.base, self.shim_base - self.base + self.shim_len + self.stack_len)
        self.mu.mem_write(self.base, mem)
        self.rsp0 = self.shim_base + self.shim_len + self.stack_len
        self.init_stack()
        return

    def init_binary_pe(self, filename, base, mode_bits):
        if mode_bits == 32:
            self.set_mode(UC_MODE_32)
        elif mode_bits == 64:
            self.set_mode(UC_MODE_64)
        else:
            raise Exception('Unsupported mode buts: %d' % mode_bits)
        self.base = base
#        print 'loading base: 0x%08x' % self.base
        mem = open(filename, 'rb').read()
#        print 'image: %08x' % len(mem)
        # we'll map mem at base, then our shim and then stack
        self.shim_base = self.base + ((len(mem) + 0x1fff) & 0xfffff000)
        self.stack_len = 0x10000
        self.mu = Uc(UC_ARCH_X86, self.mode)
        self.mu.mem_map(self.base, self.shim_base - self.base + self.shim_len + self.stack_len)
        self.mu.mem_write(self.base, mem)
        self.rsp0 = self.shim_base + self.shim_len + self.stack_len
        self.init_stack()
        return

    def init_elf(self, filename):
        if 'ELFFile' not in globals():
            raise Exception('emu_helper: Please install pyelftools before loading ELF binaries')
        self.elf = ELFFile(open(filename, 'rb'))
        # loadable segments
        segs = filter(lambda x: x.header.p_type == 'PT_LOAD', self.elf.iter_segments())
        self.base = min(map(lambda x: x.header.p_vaddr, segs))
        # FIXME
        self.set_mode(UC_MODE_64)
        self.mu = Uc(UC_ARCH_X86, self.mode)
        mem_top = self.base
        for seg in segs:
            va = seg.header.p_vaddr
            vbot = va & ~0xfff
            vtop = (seg.header.p_vaddr + seg.header.p_memsz + 0xfff) & ~0xfff
            print 'map 0x%08x .. 0x%08x' % (vbot, vtop)
            self.mu.mem_map(vbot, vtop - vbot)
            self.mu.mem_write(va, seg.data())
            mem_top = max(mem_top, vtop)
        self.shim_base = mem_top
        self.stack_len = 0x10000
        print 'shim_base at: 0x%08x' % self.shim_base
        self.mu.mem_map(self.shim_base, self.shim_len + self.stack_len)
        self.rsp0 = self.shim_base + self.shim_len + self.stack_len
        self.init_stack()

    def init_stack(self, delta = 0):
        self.mu.reg_write(self.reg_rsp, self.rsp0 - delta)
        self.mu.reg_write(self.reg_rbp, self.rsp0)

    def get_stack_strings(self, va_start, va_end, rbp_offset_list):
        maxdata = max(rbp_offset_list)
        self.init_stack()
        rbp = self.rsp0
        self.mu.mem_write(rbp - maxdata, '\0' * maxdata)
        # we don't setup any args or check esp etc
        #self.dis(va_start, va_end)
        self.mu.emu_start(va_start, va_end)
        data = self.mu.mem_read(rbp - maxdata, maxdata)
        #hexdump(data)
        return { x:trim_asciiz(data[maxdata - x:]) for x in rbp_offset_list }

    def get_stack_blob(self, va_start, va_end, rbp_offset, size):
        self.init_stack();
        rbp = self.rsp0
        self.mu.mem_write(rbp - rbp_offset, '\0' * rbp_offset)
        self.mu.emu_start(va_start, va_end)
        return self.mu.mem_read(rbp - rbp_offset, size)


    def show_stack_strings(self, tag, va_start, va_end, rbp_offset_list):
        strs = self.get_stack_strings(va_start, va_end, rbp_offset_list)
        show_strings(tag, strs, rbp_offset_list)


if __name__ == '__main__':
    emu = Emu()
    emu.init_pe('notepad.exe')
    emu.show_stack_strings('main', 0x1013a0b, 0x1013c42, [ 0x10, 0xd8, 0xac, 0xc0, 0x84, 0x98 ])
    emu.show_stack_strings('munge_binary', 0x10146CB, 0x10149D3, [ 0x24, 0x14, 0x5c, 0x23c, 0x224, 0x200 ])
    #print get_stack_string(mu, 0x1013a0b, 0x1013a43, 0x10)
    #print get_stack_string(mu, 0x1013a43, 0x1013add, 0xd8)
    #print get_stack_string(mu, 0x1013add, 0x1013b38, 0xac)
    #print get_stack_string(mu, 0x1013b38, 0x1013bbd, 0xc0)
    #print get_stack_string(mu, 0x1013bbd, 0x1013bf5, 0x84)
    #print get_stack_string(mu, 0x1013bf5, 0x1013c42, 0x98)

